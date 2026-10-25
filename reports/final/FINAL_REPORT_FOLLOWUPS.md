# Final report follow-ups

Created October 24, 2026, after reviewing the team's final midterm report. This is a forward-looking checklist, not a list of blockers to the completed baseline or a claim that future experiments have run.

## Current project boundary

- Completed: 258 cases × six assertive cues × two orders = 3,096 baseline requests; score replay, technical review, and human acceptance; midterm report preparation.
- Planned: normalizer training and evaluation. The training objective, supervision, splits, and final configurations are not yet finalized.
- [Final midterm PDF](../midterm/midterm_report.pdf) is preserved as supplied. Course submission is not verified here.

## 1. Framework and model architecture diagram

- [ ] Add a readable full pipeline diagram to the final report. The team deferred this suggested diagram from midterm because of the page limit.
- [ ] Show raw query/tool information → controlled description edit → normalizer encoder/decoder → normalized description → downstream agent → parsed calls → scoring.
- [ ] Show tool names and schemas preserved separately; distinguish the completed baseline path (normalizer bypassed) from the proposed/implemented normalizer path.
- [ ] Route expected calls/arguments **only to the scorer**. They are evaluation ground truth, not inference input to the agent or normalizer.
- [ ] After training, show the actual implemented architecture and training path; label anything still planned.

## 2. Clarify method, data, and formulas

- [ ] Rewrite the midterm phrase “BFCL case and expected call → … → Qwen” to separate model inputs from scoring ground truth; the existing sentence is ambiguous, not evidence that leakage actually occurred.
- [ ] Distinguish canonical source records from constructed evaluation records. Edited/original role mapping is created during experiment construction; do not imply it is a raw BFCL field.
- [ ] Use a clear indicator such as \(\mathbf{1}[\cdot]\) in the CR formula and define it, or use \(\max(I_{ie},I_{io})\) for binary indicators.
- [ ] State denominators explicitly: 258 per cue/order; 516 per pooled cue. Distinguish fractional metric formulas from percentages in tables.
- [ ] Keep BFCL citations for dataset/answer provenance and Faghih et al. citations for the reproduction/scoring protocol.
- [ ] Explain the implemented normalizer input/target construction, backbone rationale, loss with all variables defined, optimizer, seeds, and configurations once finalized.
- [ ] Keep evaluation goals (preference gap, CR, clean-input performance) separate from the training loss. Fix any performance-preservation tolerance before evaluating held-out test results.
- [ ] If the deployed normalizer processes both candidates or all tools, document that policy and match clean-through-normalizer controls to it; avoid presenting the “edited-description-only” diagnostic as the full deployment setting.

## 3. Experiments and unresolved baseline limitations

- [ ] Freeze leakage-resistant grouped train/dev/test splits and held-out cue styles before generating expanded variants.
- [ ] Evaluate clean, manipulated, normalized, and clean-through-normalizer conditions with matched downstream settings and semantic-preservation checks.
- [ ] Add clean-vs-clean controls and, where feasible, separate tool position from name-suffix identity. Current order comparisons change both and cannot establish a pure causal position effect.
- [ ] Record multiple training configurations/runs and meaningful ablations where feasible. Use paired/group-aware uncertainty analysis because the same 258 cases recur across conditions.
- [ ] Investigate the local-versus-paper CR gap (4.08–5.86 percentage points) with controlled comparisons. Backend/sampling differences remain hypotheses, not proven causes.
- [ ] Retain the one parse failure in the baseline denominator. Preserve documented BFCL empty-array and optional-answer edge cases. Any alternative scoring/sensitivity analysis must be versioned separately from accepted original scores.
- [ ] Report preference reduction together with correctness and semantic preservation before claiming successful mitigation. No normalizer effectiveness has yet been demonstrated.

## 4. Final publication and presentation

- [ ] Add a matching final Overleaf/LaTeX source export; the existing root source ZIP is an earlier upload and is not verified against the final midterm PDF.
- [ ] Describe actual completed contributions and ensure they match the runtime/work performed.
- [ ] Check page limit, reference formatting, readable figures/formulas, citation links, GitHub links, and submission requirements for the final deliverable.
- [ ] Improve the widely spaced model/revision paragraph and hide colored PDF link borders if desired.
- [ ] Keep the midterm PDF and accepted baseline evidence immutable as historical artifacts; publish subsequent report/result versions separately.

Related evidence: [baseline current status](../../handoffs/table3-baseline/2026-10-20/CURRENT_STATUS.md), [technical review](../../handoffs/table3-baseline/2026-10-20/reviews/part3/REVIEW_REPORT.md), [checker cases](../../handoffs/table3-baseline/2026-10-20/reviews/part3/evidence/CASE_REVIEW.md).
