# Pinned BFCL checker source

`bfcl/` is the checker subset archived in the team's verified Table 3 handoff bundle, copied from the official upstream BFCL repository at the recorded pinned source commit `05be5f136f00fe66acf0aa853d7bcd44c300946c`.

Official source repository: https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard

The evaluator uses this snapshot to call the same `simple_function_checker` used by the historical score replay. It does not execute any external tools. See the team's handoff `SOURCES_AND_ATTRIBUTION.md` and `table3/sources/manifest.json` for provenance. Keep this source snapshot unchanged; any checker update must be a separately versioned experiment.
