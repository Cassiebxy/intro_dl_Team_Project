"""Small local-only Qwen chat-template adapter for controlled Table 3 inputs."""
from __future__ import annotations

import ast
import copy
import json
import re
from pathlib import Path
from typing import Any

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
TYPE_MAP = {
    "integer": "integer", "number": "number", "float": "number", "string": "string",
    "boolean": "boolean", "bool": "boolean", "array": "array", "list": "array",
    "dict": "object", "object": "object", "tuple": "array", "any": "string",
    "byte": "integer", "short": "integer", "long": "integer", "double": "number",
    "char": "string", "ArrayList": "array", "Array": "array", "HashMap": "object",
    "Hashtable": "object", "Queue": "array", "Stack": "array", "Any": "string",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def flatten_messages(question: Any, request_id: str) -> list[dict[str, str]]:
    if not isinstance(question, list) or len(question) != 1 or not isinstance(question[0], list):
        raise ValueError(f"{request_id}: expected one live_simple turn")
    messages = []
    for msg in question[0]:
        if (not isinstance(msg, dict) or set(msg) != {"role", "content"} or
                msg["role"] not in {"system", "user", "assistant"} or not isinstance(msg["content"], str)):
            raise ValueError(f"{request_id}: malformed message {msg!r}")
        messages.append({"role": msg["role"], "content": msg["content"]})
    if not any(m["role"] == "user" for m in messages):
        raise ValueError(f"{request_id}: missing user message")
    return messages


def convert_schema(node: dict[str, Any], path: str) -> dict[str, Any]:
    out = copy.deepcopy(node)
    raw_type = out.get("type", "string")
    if raw_type not in TYPE_MAP:
        raise ValueError(f"Unsupported BFCL schema type {raw_type!r} at {path}")
    if raw_type == "float":
        out["format"] = "float"
        hint = "This is a float type value."
        if hint not in out.get("description", ""):
            out["description"] = (out.get("description", "") + " " + hint).strip()
    out["type"] = TYPE_MAP[raw_type]
    if "properties" in out:
        out["properties"] = {k: convert_schema(v, f"{path}.{k}") for k, v in out["properties"].items()}
    if "items" in out:
        out["items"] = convert_schema(out["items"], f"{path}.items")
    return out


def make_qwen_tools(functions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    tools, wire_to_canonical = [], {}
    for source in functions:
        canonical = source["name"]
        wire = canonical.replace(".", "_")
        if wire in wire_to_canonical:
            raise ValueError(f"Wire-name collision for {canonical}")
        wire_to_canonical[wire] = canonical
        fn = copy.deepcopy(source)
        fn["name"] = wire
        params = fn.get("parameters")
        if not isinstance(params, dict):
            raise ValueError(f"Missing object schema for {canonical}")
        params["type"] = "object"
        params["properties"] = {k: convert_schema(v, f"{canonical}.{k}")
                                for k, v in params.get("properties", {}).items()}
        tools.append({"type": "function", "function": fn})
    return tools, wire_to_canonical


def parse_qwen_response(raw_text: str, wire_to_canonical: dict[str, str]) -> tuple[list[dict], list[str]]:
    calls, errors = [], []
    blocks = TOOL_CALL_RE.findall(raw_text)
    if raw_text.count("<tool_call>") != len(blocks) or raw_text.count("</tool_call>") != len(blocks):
        errors.append("Malformed or unclosed tool_call tag")
    for index, block in enumerate(blocks, 1):
        try:
            try:
                obj = json.loads(block.strip())
            except json.JSONDecodeError:
                obj = ast.literal_eval(block.strip())
            if not isinstance(obj, dict) or not isinstance(obj.get("name"), str):
                raise ValueError("tool call must have a string name")
            args = obj.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = ast.literal_eval(args)
            if not isinstance(args, dict):
                raise ValueError("tool arguments must be an object")
            wire = obj["name"]
            calls.append({"wire_name": wire, "canonical_name": wire_to_canonical.get(wire),
                          "arguments": args, "unknown_tool_name": wire not in wire_to_canonical,
                          "raw_block": block})
        except Exception as exc:
            errors.append(f"tool_call[{index}]: {type(exc).__name__}: {exc}")
    return calls, errors
