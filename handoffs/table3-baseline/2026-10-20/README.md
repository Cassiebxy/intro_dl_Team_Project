# Table 3 baseline evidence and handoff

**October 22, 2026: baseline COMPLETE; technical review and human signoff PASS; midterm report available.**

Start with [current status](CURRENT_STATUS.md) or the [midterm report](../../../reports/midterm/README.md). Review the [paper comparison](tables/PAPER_VS_LOCAL_TABLE3.md), [order effects](tables/ORDER_EFFECTS.md), [technical review](reviews/part3/REVIEW_REPORT.md), and [human signoff](reviews/part3/HUMAN_SIGNOFF.md).

## Offline reproduction

[Download the evidence ZIP](TABLE3_BASELINE_HANDOVER_2026-10-20.zip) (GitHub file page → Download raw). It contains frozen inputs, all 3,096 raw responses and scores, source snapshots, and portable replay. It excludes model weights, virtual environments, and credentials.

Verify the archive against [PACKAGE_METADATA.json](PACKAGE_METADATA.json), then extract it without replacing internal files with the browsable documentation. From the extracted `TABLE3_BASELINE_HANDOVER_2026-10-20` directory run:

```bash
python3 -B -X utf8 -S scripts/verify_and_replay.py --output replay_check
```

This standard-library script checks saved evidence without loading a model or using the network. Inspect `replay_check/verification_result.json`.

## Evidence and historical handoffs

- [Per-request scores](reviews/part3/results/per_request_scores.csv), [cue summary](reviews/part3/results/summary_by_cue.csv), [order summary](reviews/part3/results/summary_by_order.csv), [failure counts](reviews/part3/results/response_failure_counts.csv).
- [Scoring edge cases](reviews/part3/evidence/CASE_REVIEW.md).
- [Zero-context handover](HANDOVER_NEW_SESSION_ZH.md), [Part 3 brief](PART3_SCORING_VALIDATION_HANDOVER_ZH.md), [Part 4 brief](PART4_PAPER_COMPARISON_MIDTERM_HANDOVER_ZH.md), [rubric checklist](MIDTERM_RUBRIC_CHECKLIST_ZH.md).
- [Part 3 publication note](reviews/part3/PUBLICATION_NOTE.md) explains historical local-only labels without modifying the signed delivery.
- [Part 4 status](reviews/part4/STATUS.json) and [remaining report polish](reviews/part4/LEFTOVERS.md).

The archive is immutable. Original prompts describe work that has since completed; consult [CURRENT_STATUS.md](CURRENT_STATUS.md) before continuing.
