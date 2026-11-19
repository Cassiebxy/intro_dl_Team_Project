# Local Qwen results across four conditions

We selected one case from each of 13 held-out tool groups and evaluated 624 requests with a pinned 4-bit Qwen2.5-7B-Instruct checkpoint. Identical case, order, name mapping, and input combinations shared a deterministic generation, for 312 unique generations. Every generation ended naturally and parsed successfully. Scoring yielded 463 strictly correct calls and 161 argument errors. See the [run record](mlx-groups/run_status.json) and [scoring coverage](mlx-groups/summary.json).

Each cue has 52 paired comparisons across 13 cases, two orders, and two name mappings. The table gives the **signed selection-rate gap** for the edited candidate relative to the matched Clean condition. Clean and Clean → BART both had a 26/52 selection rate and a 40/52 strict call correctness rate.

| Cue | Selection gap to Clean before BART | Selection gap to Clean after BART | Strictly correct, before → after |
| --- | ---: | ---: | ---: |
| Seen priority cue | +19.23 pp | 0.00 pp | 39/52 → 40/52 |
| New priority wording 1 | +3.85 pp | +3.85 pp | 37/52 → 37/52 |
| New priority wording 2 | +36.54 pp | +7.69 pp | 39/52 → 40/52 |
| Maintenance frequency | +5.77 pp | 0.00 pp | 37/52 → 40/52 |
| Adoption-count endorsement | +13.46 pp | +13.46 pp | 37/52 → 37/52 |

Across five cues and four order and name combinations, the mean absolute selection-rate gap fell from **18.85 to 6.54 percentage points**. The two cues copied verbatim by BART had identical downstream results before and after normalization. The maintenance-frequency cue and the seen priority cue were fully restored to their matching Clean inputs. For each cue, the figure averages the absolute gaps calculated within the four order and name strata, so its values can be larger than the signed values in the table. See the [per-condition metrics](mlx-groups/condition_summary.csv), [paired effects](mlx-groups/paired_summary.csv), and [results figure](qwen_mlx_by_cue.png).

Strict REC rose from 189/260 to 194/260. Five paired requests improved and the other 255 kept the same score. The 95% paired tool-group bootstrap interval was 0.00 to 5.77 percentage points. Applying BART to clean descriptions yielded the same strict REC outcome for all 52 requests. Of the 144 Manipulated → BART requests for which both descriptions were exactly recovered, 32 still had argument errors. Each matched Clean input produced the same error. See the [rewrite and call correctness table](mlx-groups/rewrite_vs_call.csv).

These observations cover one training seed, 13 test groups, and one template per new family. Qwen used local MLX Metal, 4-bit weights, greedy decoding, and a 512-token cap. The 13 hash-selected cases already excluded the flagged cross-split duplicate question, so the sensitivity check yields the same results for this subset. AutoDL replay on all 42 familiar-cue cases provides separate results with the flagged question excluded. See the [local configuration and case IDs](mlx-groups/run_manifest.json) and [AutoDL paired results](autodl-replay/paired_summary.csv).
