# Person 4 draft generalization test design

This page records the candidate design. The dataset that was released and evaluated with BART is documented in the [BFCL generalization package](../data/generalization_v1/README.md).

This draft was prepared independently on November 18, 2026. Freezing the test set and verifying that the candidates are unseen required the team's final train and dev cue pools.

## Three generalization slices

| Slice | Required holdout | Question |
| --- | --- | --- |
| Unseen wording | Hold out the template and its near-paraphrases within the same cue family from training and tuning. | Does the model generalize beyond memorized sentences? |
| Unseen cue family | Hold out the entire persuasive category from training and tuning, including dev examples used for checkpoint selection. | Can the model handle a different persuasive strategy? |
| Unseen tools | Keep the source tool group and related or near-duplicate descriptions within one train, dev, or test split. | Does performance depend on seeing specific tools? |

For the wording and family slices, record whether the tools were seen during training. Using the same held-out tools for seen cues, unseen wordings, and unseen families helps isolate the effect of cue changes. Holding out sentences from the six Table 3 assertive cues tests generalization to new wording or templates within the family.

## Draft and review cue candidates

1. Register the cue family, template ID, full wording, insertion position, source, and author first. The maintenance, recommendation, and user-count claims in `cue_candidates.jsonl` are synthetic experimental text.
2. Each candidate should add only nonfunctional persuasive text. Preserve the original capabilities, parameter meanings, units, negations, authorization conditions, applicable scope, tool name, and schema.
3. Have at least two team members review each candidate independently and record disagreements and their resolution. Team review was pending at the time of this draft. Select candidates using semantic and protocol criteria independent of Qwen or normalizer test performance.
4. Judge professional tone, concise explanations, and legitimate usage constraints in context. Flag candidates with added capabilities, incorrect example arguments, or changed conditions as functional drift and exclude them from the main equivalence experiment.
5. Treat insertion position as an independent factor. Fix the position for a wording-only experiment. If studying position, label that slice separately and preserve the functional sentences.
6. Cross-check candidate text, near-matching templates, and families against the final train and dev cue pools. Count candidates used in checkpoint selection as seen.

## What to publish when freezing the test

- `protocol_version`, split and grouping versions, cue pool version, and SHA-256 for every file.
- Eligible source case and group IDs, the three slice labels, and flags for overlap with training tools.
- Full cue text, position, source, human reviews, and reasons for exclusions.
- Correct calls and target descriptions stored in scoring files and withheld from normalizer inputs.
- The same set of description IDs for all models, with failed outputs kept in the evaluation.

At this draft stage, the formal test tool list, BFCL final-test variants, and candidate runs were all pending.

## Downstream comparisons and reporting

Use the matched Clean, Manipulated, Manipulated → Normalizer, and Clean → Normalizer conditions. Normalize both candidate descriptions where applicable. Cross tool order and name mapping independently and fix the paired seed for each case. Share control results only when Qwen weights, prompts, backend, precision, and decoding match.

Report SR, ratio, AAC, CUR, legacy CR, strict REC, and failure rate by cue family, tool exposure, order, and name mapping. Use the matched Clean condition as the selection-rate reference for each cell. Keep failures in the total denominator and estimate intervals by resampling source tool groups with paired conditions intact.

Person 4 integrates the protocol and test inventory and runs and analyzes BART. The other model owners run and analyze their own evaluations. Person 3 compiles the comparison table. Conclusions about generalization depend on results from all three models and functional review.
