# BFCL held-out tools and new cues

This dataset uses Person 2's tool groups and test split, with 42 BFCL questions, 19 source tool descriptions, and 13 tool groups. Each source description has six inputs, for 114 total. All cues are appended to the description.

| Slice | Description variants | Definition |
| --- | ---: | --- |
| Clean | 19 | Original tool descriptions |
| Seen cue | 19 | Table 3 cue 1 from training, applied to held-out tools |
| Unseen wording | 38 | Two new wordings from the priority recommendation family |
| Unseen family | 38 | One maintenance-frequency template and one adoption-count endorsement template |

`normalizer_inputs_test.jsonl` contains only `description_id` and `input_description`. `pairs_test.jsonl` contains original descriptions and slice labels for scoring. `cases_test.jsonl` maps downstream cases to tool groups. `cues.jsonl` records each cue's full text, source, closest train or dev match, and semantic review. Teammates can independently review the same IDs.

The tool groups, source tools, case IDs, and full target descriptions are disjoint from train and dev. Person 2's existing test wording probe also appears in dev. This package uses two other priority recommendation wordings. Unseen cues are defined relative to the fine-tuning and dev data for this run. All unseen cues are applied to held-out tools, so results reflect both held-out factors together. Each new family has one template.

`live_simple_115-71-0` shares its question text with training case `live_simple_116-72-0` and uses a different tool description and parameter schema. Both cases retain Person 2's grouping. The paired downstream analysis includes a sensitivity check that excludes the flagged test question.

The data protocol and hashes are available in the [protocol](../../protocols/shared_bfcl_v1.json) and [manifest](manifest.json). See also the [generalization design draft](../../protocols/GENERALIZATION_DRAFT.md) and [BART results](../../RESULTS_BFCL.md).
