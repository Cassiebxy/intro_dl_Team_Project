"""Reuse the frozen controlled runner with a package-sized full-run guard.

Only FULL_REQUESTS changes; model loading, generation, resume and parsing remain
in the original runner. Explicit --input and --mapping are required.
"""
import argparse
import importlib.util
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    known, _ = parser.parse_known_args()
    runner_path = Path(__file__).resolve().parents[2] / 'table3/controlled_baseline/run_qwen_controlled.py'
    sys.path.insert(0, str(runner_path.parent))
    spec = importlib.util.spec_from_file_location('controlled_runner', runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    inputs = runner.read_jsonl(known.input)
    runner.validate(inputs, runner.read_jsonl(known.mapping))
    if not inputs:
        raise ValueError('Empty request package')
    runner.FULL_REQUESTS = len(inputs)
    return runner.main()


if __name__ == '__main__':
    raise SystemExit(main())
