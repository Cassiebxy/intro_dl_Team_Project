# Part 3 evidence check for report integration

Date: October 22, 2026. Reviewer: Codex assistant. Scope: repository maintenance and consistency of published records, not a new independent scoring run.

Source inspected: commit `2ea3f2f2551d2ee11e7bad652428832aca1b491e`.

- Part 3 STATUS records technical PASS, Kyrie human PASS, no blocking issues, and unchanged original scores.
- Its source ZIP SHA256 matches PACKAGE_METADATA: `7523548350c7fe67091efd1ea5b13027ee04da8927905897543f82f8534b283a`.
- Its source manifest SHA256 matches PACKAGE_METADATA and replay output: `691ba4a65d6d156005bc358eb99d514a4c698e784d21b49458a73bb07bdddc2b`.
- Published replay JSON records 3,096 unique requests, 12 conditions, denominators 258/order and 516/cue, equal per-request scores and summaries, and 3,034 official nonempty-call comparisons.
- Published audit JSON records PASS, 3,096 strict JSON/BFCL checks, six pooled rows and twelve order rows, and original scores retained.
- CASE_REVIEW documents role/name mapping, phantom/alias handling, the parse failure, empty-array checker behavior, optional-answer behavior, and multi-call cases.
- Earlier audit/replay PENDING fields predate the later human signoff. Local-only publication labels in the signed delivery are historical; the review is now on GitHub.

Conclusion: the published baseline scores have a traceable completed review and human acceptance. Retain order/name confounding, paired-case dependence, backend differences, checker caveats, and the parse failure in report interpretation.

The published paper-comparison table records an October20 verification against the formal paper PDF. This maintenance check does not claim a new independent re-extraction of the paper's reference values or a reconstruction of the team's historical Part4 workflow. A completed five-page report is now available at the [report entry](../../../../../reports/midterm/README.md).

