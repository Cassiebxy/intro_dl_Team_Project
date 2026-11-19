# Person 4 BART-base results and handoff

November 19, 2026. BART-base was fine-tuned using Person 2's BFCL pairs. On the held-out set, it removed the priority recommendation wording used in training and some new cues. For other phrasings, it retained the entire cue.

## Training and comparison setup

Training used Person 2's data at commit `b2552bb`. The 400 training pairs came from 100 source descriptions and 57 tool groups, with 25% clean identity pairs. BART was initialized from a pinned revision of `facebook/bart-base` and trained on an Apple M4 in FP32 with AdamW, a learning rate of 5e-5, an effective batch size of 16, and seed 42. The run completed three epochs and 75 optimizer updates. Training used only the descriptions. The evaluation code preserves the questions, tool names, and parameter schemas in the Qwen requests.

We used Person 2's published prompt, training budget, and checkpoint selection metric. At each epoch, we computed teacher-forced loss on 92 dev pairs with clean descriptions or familiar wording. Epoch 1 had the lowest loss and was selected. The 23 additional wording probes were used only to score dev generations. BART weights gradient accumulation by the number of valid target tokens, while Person 2's FLAN code weights by the number of examples per microbatch. Each model uses its own tokenizer. The run took 185.2 seconds and the highest sampled MPS driver allocation was about 4.91 GiB. After reloading, all 115 dev outputs matched the outputs from before saving. See the training settings, data, and checkpoint hashes in the [BART run record](results/bfcl_v1/bart_run.json) and [protocol](protocols/shared_bfcl_v1.json).

## Text recovery and generalization

| Dataset or slice | Exact recovery | Details |
| --- | ---: | --- |
| Person 2 dev | 112/115 | 23 source descriptions with five variants each |
| Person 2 test | 95/95 | 19 held-out source descriptions. The wording probe was previously included in dev evaluation. |
| New generalization set, clean | 19/19 | Clean inputs were preserved verbatim |
| New generalization set, seen priority cue | 19/19 | The training cue was applied to held-out tools |
| New priority wording 1 | 0/19 | All 19 outputs copied the input and retained the cue |
| New priority wording 2 | 15/19 | Four outputs copied the input and retained the cue |
| New family, maintenance frequency | 19/19 | All 19 outputs exactly recovered the original description |
| New family, adoption-count endorsement | 0/19 | All 19 outputs copied the input and retained the cue |

The new generalization set contains 114 examples from 19 source descriptions and 13 tool groups, with 42 BFCL questions for downstream evaluation. All conditions use the same groups. The three cue slices are defined relative to the fine-tuning and dev data. Each new family contains one candidate template. For each ID, we compared the BART output with its source description. The experiment used one random seed. The dataset records inputs, targets, cue sources, groups, the flagged duplicate question, and hashes. See the [generalization dataset](data/generalization_v1/README.md), [text metrics by slice](results/bfcl_v1/rewrite_summary.csv), and [recovery rate figure](results/bfcl_v1/rewrites_by_cue.png).

We paired BART and Person 2's FLAN-T5-small on the same 115 dev IDs. Both models recovered 104 examples, BART alone recovered eight, and neither model recovered three. Pretrained BART exactly recovered 0/115 under the same prompt and greedy decoding settings. The dev results count multiple variants of each description. The base models differ in tokenization, pretraining, and optimization. See the [paired dev results](results/bfcl_v1/paired_dev_vs_flan.csv).

## Failure analysis

All 42 nonmatching rewrites on the new generalization set copied the entire input, retaining both the functional description and the cue. This includes every example of unseen wording 1 and the adoption-count endorsement. The dev set also contained the following failures. See the [full mismatch records](results/bfcl_v1/rewrite_mismatches.jsonl).

| Case | Observation | Classification |
| --- | --- | --- |
| Inversion tool, dev wording probe | Dropped the separate instructions to reverse strings character by character and negate Booleans, described strings as being negated, and repeated the numeric condition. This can change how the tool's behavior is interpreted. | Functional error and over-deletion |
| Vietnamese trip tool, seen `prefix_2` | While removing the cue, shortened `loại chuyến đi` (trip type) to `loại` (type). Location and waiting time were retained, but the shortened condition depends on context. | Loss of functional detail |
| Same Vietnamese tool, dev wording probe | Copied the input verbatim, retaining the Vietnamese characters, functional text, and priority recommendation sentence. | Under-deletion |

These observations come from reviewing individual rewrites. Exact recovery provides literal evidence. Qwen behavior is measured separately with paired request scoring. All 115 dev inputs and 114 new generalization inputs produced nonempty outputs within the BART generation limit.

## AutoDL replay across four conditions

Replay requires an exact match to the archive on complete model input, case, tool order, name mapping, and seed. All responses are scored with the same pinned BFCL scorer. In normalized conditions, BART rewrites both candidate descriptions. In the Clean condition, `edited` identifies the candidate that receives the cue in the matched manipulated condition. Both familiar-cue cohorts have full coverage across all four conditions.

| Cases | Clean edited-tool selection | Manipulated | BART → Qwen | Strict REC in each of the four conditions |
| --- | ---: | ---: | ---: | ---: |
| Same 16 dev cases as Person 2, two tool orders, fixed name mapping | 5/32 | 7/32 | 5/32 | 28/32 |
| 42 held-out cases × two tool orders × two name mappings | 83/168 | 99/168 | 83/168 | 112/168 |

For the familiar cue, every normalized model input matched its corresponding Clean input. Clean → BART inputs also matched Clean. In the held-out cases, the selection-rate gap was +9.52 percentage points and fell to 0 after BART. Exact replay reuses the archived response for the recovered clean input. Even after exact text recovery, 56/168 requests failed strict REC, with the same failures in Clean. See the [four-condition metrics](results/bfcl_v1/autodl-replay/condition_summary.csv) and [paired effects](results/bfcl_v1/autodl-replay/paired_summary.csv).

The full matrix contains 2,144 conditions, with 1,060 exact matches in the AutoDL archive. The 1,084 unmatched conditions for new cues have Qwen input and scoring files ready to run with the team's final Qwen configuration. The historical AutoDL manifest lacks a base model revision. See the [request matrix](results/bfcl_v1/qwen_matrix.json) and [AutoDL coverage](results/bfcl_v1/autodl-replay/coverage.csv).

## Local Qwen evaluation across four conditions

Initial local timings for the full matrix were long, so we selected one case per held-out tool group using the SHA-256 of its case ID. The local run kept all five cues, both tool orders, both name mappings, and the matched Clean and Clean → BART controls, for 624 requests. Conditions with the same case, order, name mapping, and complete input shared one deterministic generation. The frozen 4-bit Qwen2.5-7B-Instruct checkpoint used Apple MLX Metal, greedy decoding, and a 512-token generation cap. The chat template hash matched the AutoDL archive. Quantization, backend, and decoding settings differed from AutoDL. See the [local run configuration](results/bfcl_v1/mlx-groups/run_manifest.json) and [MLX model card](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit).

All 624 requests were scored. Across the five cues, the mean absolute selection-rate gap fell from 18.85 to 6.54 percentage points, and strict call correctness rose from 189/260 to 194/260. The two cues copied verbatim retained their original downstream gaps. The 13 cases selected locally excluded the flagged duplicate question. See the [local Qwen results](results/bfcl_v1/MLX_RESULTS.md) and the [selection and correctness figure](results/bfcl_v1/qwen_mlx_by_cue.png).

## Team handoff

- Persons 2 and 3 can run their models on the shared descriptions and independently review cue family labels and functional equivalence. Use the [114 inference inputs](data/generalization_v1/normalizer_inputs_test.jsonl) and [scoring pairs](data/generalization_v1/pairs_test.jsonl).
- Person 1 can run the remaining requests. Both JSONL files passed `--validate-only` with the original controlled runner, which supports a smoke run or the full 7,224-request matrix. Use an entry point with custom batch sizes in the team's inference environment. If the Qwen checkpoint or backend changes, rerun the matched Clean and Manipulated controls under that configuration. See the [1,084 pending requests and scoring mappings](results/bfcl_v1/autodl_pending_requests.zip).
- Person 3 can add text and downstream metrics to the common comparison table once results from all three models are available. See the [results directory](results/bfcl_v1/).
- The local run at `runs/bfcl-person2-20261119-v1/` contains the weights, training logs, full Qwen inputs and outputs, and HTML rewrite comparisons. For the paper, see the [methods and results draft](BART_REPORT_EN.md).
