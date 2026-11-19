"""Run from the repository root: python -m person4_bart --help."""
import argparse
import json
from pathlib import Path

from .core import audit, load_inputs, load_pairs, read_jsonl, save_report, write_json, write_jsonl

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Person 4 local BART training, description rewriting and audit")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Write handwritten synthetic fixtures")
    prepare.add_argument("--output", type=Path, default=HERE / "data" / "synthetic_v1")
    env = sub.add_parser("check-env", help="Record versions and a device forward/backward check")
    env.add_argument("--output", type=Path, default=HERE / "environment_check.json")
    sub.add_parser("fetch-model", help="Download public BART base to this folder's local cache and pin its revision")
    fit = sub.add_parser("train", help="Train on externally supplied train/dev files, saving a fresh run directory")
    fit.add_argument("--train", type=Path, default=HERE / "data/synthetic_v1/pairs_train.jsonl")
    fit.add_argument("--dev", type=Path, default=HERE / "data/synthetic_v1/pairs_dev.jsonl")
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--model", help="Local pretrained model/checkpoint; otherwise use model_source.json")
    fit.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    fit.add_argument("--epochs", type=int, default=12)
    fit.add_argument("--batch-size", type=int, default=2)
    fit.add_argument("--accumulation-steps", type=int, default=4)
    fit.add_argument("--learning-rate", type=float, default=5e-5)
    fit.add_argument("--seed", type=int, default=42)
    fit.add_argument("--patience", type=int, default=4)
    fit.add_argument("--prefix", default="")
    fit.add_argument("--max-input-tokens", type=int, default=256)
    fit.add_argument("--max-target-tokens", type=int, default=128)
    fit.add_argument("--max-new-tokens", type=int, default=96)
    fit.add_argument("--protocol", type=Path, help="Load the versioned shared BFCL settings and verify data hashes")
    infer = sub.add_parser("predict", help="Description-only inference, with no target file")
    infer.add_argument("--model", required=True)
    infer.add_argument("--input", type=Path, required=True)
    infer.add_argument("--output", type=Path, required=True)
    infer.add_argument("--run-id", required=True)
    infer.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    infer.add_argument("--batch-size", type=int, default=2)
    infer.add_argument("--prefix", default="")
    infer.add_argument("--max-input-tokens", type=int, default=256)
    infer.add_argument("--max-new-tokens", type=int, default=96)
    infer.add_argument("--input-based-limit", action="store_true", help="Use the shared input-derived generation limit")
    inspect = sub.add_parser("audit", help="Join outputs to input IDs and optional separately supplied gold labels")
    inspect.add_argument("--input", type=Path, required=True)
    inspect.add_argument("--rewrites", type=Path, required=True)
    inspect.add_argument("--gold", type=Path)
    inspect.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        from .make_synthetic import prepare as build
        result = build(args.output)
    elif args.command == "check-env":
        from .model import environment
        result = environment(check=True)
        write_json(args.output, result)
    elif args.command == "fetch-model":
        from .model import fetch_model
        result = fetch_model()
    elif args.command == "train":
        from .train import train
        result = train(args)
        result = {k: result[k] for k in ("status", "device", "best_epoch", "wall_seconds")}
    elif args.command == "predict":
        from .model import device_for, generate, load_model, model_path
        if args.output.exists():
            raise FileExistsError(args.output)
        inputs = load_inputs(args.input)
        device = device_for(args.device)
        tokenizer, model = load_model(model_path(args.model), device)
        rows = generate(model, tokenizer, inputs, run_id=args.run_id, device=device, batch_size=args.batch_size,
                        prefix=args.prefix, max_input_tokens=args.max_input_tokens, max_new_tokens=args.max_new_tokens,
                        input_based_limit=args.input_based_limit)
        write_jsonl(args.output, rows)
        result = {"written": len(rows), "ok": sum(r["status"] == "ok" for r in rows), "output": str(args.output)}
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        metrics, details = audit(load_inputs(args.input), read_jsonl(args.rewrites), load_pairs(args.gold) if args.gold else None)
        save_report(args.output, metrics, details)
        result = metrics
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
