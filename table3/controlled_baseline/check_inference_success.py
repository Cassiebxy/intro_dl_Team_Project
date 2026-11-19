#!/usr/bin/env python3
"""Exit nonzero unless every expected inference succeeded."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_inference_success.py evaluation_status.json", file=sys.stderr)
        return 2
    status = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    successful = status.get("successful_inference_responses", 0)
    expected = status.get("expected_requests", 0)
    passed = status.get("inference_successful") is True
    print(f"inference_success={successful}/{expected}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
