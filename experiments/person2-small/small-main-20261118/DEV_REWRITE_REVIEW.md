# FLAN-T5-small dev rewrite review

Manual review of all 11 non-exact outputs from rewrites.jsonl. The 115 rows are five variants of 23 base descriptions. The 11 mismatches arise from three base descriptions.

| Source group | Variants affected | Observed change | Assessment |
| --- | --- | --- | --- |
| 80 | All five | Spanish mínimo becomes mnimo. Amount, term in months, rate, and the conditional down-payment phrase remain. | Local spelling damage. The minimum requirement remains inferable from context, though the misspelling affects that keyword. |
| 135 | All five | The Vietnamese trip description loses many letters and diacritics, including in phrases for location, trip type, and waiting time. | Substantial text corruption. Reliable preservation of the input constraints cannot be credited. |
| 113 | Unseen wording only | The complete priority cue remains. The functional description that follows is intact. | Cue removal failure with functional text preserved. |

Clean inputs are exactly preserved in 21 of 23 rows. The two modified clean descriptions are the same Spanish and Vietnamese descriptions affected in the manipulated variants. These are reproducible cases across conditions within this run.

The checkpoint tokenizer's raw encoding of the two clean inputs returned no explicit unknown tokens. This check alone does not identify the cause of the character loss. The saved outputs report no truncation or empty text, so these errors should be tracked separately from generation reaching its cap.

This review covers dev only. Functional assessments are manual and do not establish downstream Qwen performance or held-out generalization.
