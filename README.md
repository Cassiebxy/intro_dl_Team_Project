# Controlled Qwen baseline

This directory is a new, isolated experimental pipeline. It does not overwrite `table3/generated/`, the existing `results/`, or the archived 3,096-request MPS baseline.

For the current status, successful Delta smoke evidence, reproducibility notes, metric definitions, and next steps, see [BASELINE_STATUS_2026-11-11.md](BASELINE_STATUS_2026-11-11.md).

For the completed 7,224-request AutoDL run, runtime manifest, integrity checks, descriptive results, and a copy/paste teammate context packet, see [AUTODL_FULL_RUN_HANDOFF_2026-11-12.md](AUTODL_FULL_RUN_HANDOFF_2026-11-12.md).

## Design

`generate_controlled_inputs.py` crosses description (`clean` + six cues), role order (2), and suffix/name mapping (2) over the same 258 BFCL cases. Full size is 7,224 requests. Both tools retain their role-specific names/descriptions/schemas when their list order changes. Names no longer follow position. One case-derived seed is shared by all 28 cells for that case. See [the audit and design note](AUDIT_AND_DESIGN_2026-11-06.md) for factor definitions, reuse policy, metric numerators/denominators, limitations, and the old-baseline audit.

## Generate and validate locally (CPU only)

From the repository root:

```bash
python table3/controlled_baseline/generate_controlled_inputs.py \
  --output-dir table3/controlled_baseline/generated/full_factorial_v2
python table3/controlled_baseline/run_qwen_controlled.py \
  --input table3/controlled_baseline/generated/full_factorial_v2/controlled_inputs.jsonl \
  --mapping table3/controlled_baseline/generated/full_factorial_v2/controlled_mapping.jsonl \
  --limit 16 --validate-only
```

Create the 16-request sample used for the first GPU smoke:

```bash
python table3/controlled_baseline/generate_controlled_inputs.py \
  --smoke-cases 16 \
  --output-dir table3/controlled_baseline/generated/smoke_16_ta_reviewed_v2
```

The sample uses 16 distinct cases, varies clean/cue, order, and suffix assignment, and includes the three legacy long-output cases (`live_simple_188-113-0`, `live_simple_67-31-0`, `live_simple_70-34-0`). It is a smoke sample, not a balanced estimate of treatment effects.

## Delta run

The batch file defaults to smoke mode and 16 requests. Upload this folder, `table3/generated/`, and `table3/table3_cues.json`. The controlled runner has its own Qwen adapter and does not depend on `run_qwen_table3.py`. Keep the Qwen checkpoint at `/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct` or set `MODEL_DIR`.

From the Delta project checkout, after the smoke JSONL files exist:

```bash
TABLE3_DIR=/path/to/intro_dl_Team_Project/table3 sbatch \
  --export=ALL,TABLE3_DIR=/path/to/intro_dl_Team_Project/table3,MODE=smoke \
  table3/controlled_baseline/run_controlled.sbatch
```

Set `TABLE3_DIR` to the actual checkout path. Review the job state, logs, 16 raw outputs, failures, token lengths, throughput, and GPU memory before considering more work. All output is isolated under `table3/results/qwen-controlled-smoke-v1/`. The smoke script requests a 30-minute interactive allocation.

To rerun the November 6 smoke in place, upload the corrected `controlled_baseline/` code and submit:

```bash
sbatch --export=ALL,TABLE3_DIR=/scratch/bjfu/mzhao9/diagnostics/qwen-controlled/table3,MODE=smoke,RETRY_ERRORS=1 \
  table3/controlled_baseline/run_controlled.sbatch
```

Successful IDs are skipped; `status=error` IDs are retried by default (`RETRY_ERRORS=1`). Each response is fsynced to the checkpoint. Do not change the manifest-pinned input/settings while reusing an output folder. Use a new output folder for any protocol change. The evaluator distinguishes `complete` (every request has a response record) from `inference_successful` (every expected request has `status=ok`); the smoke batch exits nonzero unless all 16 succeed.

### Seeding and reproducibility

`generate()` in Transformers does not accept a `generator` keyword in the Delta environment used for the first smoke. The runner now calls `torch.manual_seed(case_seed)` and `torch.cuda.manual_seed_all(case_seed)` immediately before each `generate()` call. This retains the shared per-case seed across all factorial conditions without passing an unsupported model kwarg. It pairs the pseudorandom seed; it does **not** guarantee token-by-token identical randomness when prompts differ, and CUDA kernels/backends may be nondeterministic. The exact RNG implementation and limitation are recorded in `run_manifest.json`. This repair preserves the existing input hashes, decode settings, output directory, and manifest compatibility so the prior `status=error` smoke rows can be retried in place.

## Full-run gate

The separate full-run script requires explicit `ALLOW_FULL_RUN=1`; it uses the standard `gpuA100x4` queue and checkpoints the 7,224-request run in 8-hour chunks:

```bash
TABLE3_DIR=/actual/path/to/table3 sbatch \
  --export=ALL,TABLE3_DIR=/actual/path/to/table3,ALLOW_FULL_RUN=1 \
  table3/controlled_baseline/run_controlled_long.sbatch
```

Do not submit full mode before reviewing the 16-request Delta smoke and estimating cost against the remaining 30 GPU-hours. Delta documents a 1-hour limit for `gpuA100x4-interactive` and 48 hours for `gpuA100x4`. Historical MPS timing gives inconsistent extrapolations (roughly 5.8–89 hours for this matrix); it is not a trustworthy Delta estimate.

## Outputs and metrics

Inference writes a resumable `raw_responses.jsonl`, append-only `attempts.jsonl`, and hash-pinned `run_manifest.json`. Evaluation writes `per_case_structured_results.jsonl`, `summary_by_condition.csv/.json`, `paired_factor_contrasts.csv/.json`, and `evaluation_status.json`. The strict single-call overall correctness rule is provisional and explicitly flagged for TA/team confirmation. Legacy CUR/CR are separately preserved.

The November 6 smoke failed because the installed Transformers version rejected an unsupported `generator` argument. A corrected 16-request Delta smoke later completed successfully as job `23742884` (16/16 inference successes, Slurm exit code 0). The full controlled baseline has not been run. Detailed evidence and limitations are recorded in [BASELINE_STATUS_2026-11-11.md](BASELINE_STATUS_2026-11-11.md).
