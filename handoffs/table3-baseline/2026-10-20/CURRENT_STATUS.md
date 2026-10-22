# Current baseline and midterm status

Updated October 22, 2026. This page supersedes pending/local-only labels in the original October 20 handoff and October 21 Part 3 delivery snapshots.

| Workstream | Current state | Evidence |
|---|---|---|
| Baseline inference | COMPLETE — 3,096 requests | [Frozen archive](TABLE3_BASELINE_HANDOVER_2026-10-20.zip) |
| Scoring replay and technical review | PASS — original scores retained | [Review](reviews/part3/REVIEW_REPORT.md), [replay](reviews/part3/evidence/replay/verification_result.json) |
| Human signoff | PASS — Kyrie, October 21 | [Signed record](reviews/part3/HUMAN_SIGNOFF.md) |
| Part 3 publication | Published on GitHub | [Review files](reviews/part3/) |
| Paper comparison and midterm integration | Completed report available | [Report](../../../reports/midterm/README.md), [comparison](tables/PAPER_VS_LOCAL_TABLE3.md) |
| Description normalizer | Planned; no training/evaluation results published | [Next steps](../../../README.md#next-stage) |

There is no outstanding baseline execution or scoring blocker. Completion does not imply exact reproduction of the paper's numbers. Order/name coupling, checker caveats, and the one parse failure remain documented.

## Reading historical records

The ZIP and Part 3 delivery manifest are preserved unchanged. Part 3 preparation records may still say local-only/not pushed; the files are now published. Earlier replay/audit JSON files retain their original pre-signoff PENDING fields; the later [human signoff](reviews/part3/HUMAN_SIGNOFF.md) and [Part 3 status](reviews/part3/STATUS.json) record PASS.

Original first-session prompts and unchecked task lists are historical. Do not restart completed Part 3/4 work solely because they still describe it as pending. This October 22 update reviews published records and report availability; it does not claim a new model run or another independent score replay.

## Remaining work

Future experiments: clean-vs-clean controls, disentangled position/name controls, grouped splits, normalizer training, and downstream evaluation. Before course submission, add the repository URL to the current PDF and fix the missing closing parenthesis in the contributions section. Course submission itself has not been verified. These are report polish/administrative items, not baseline blockers.
