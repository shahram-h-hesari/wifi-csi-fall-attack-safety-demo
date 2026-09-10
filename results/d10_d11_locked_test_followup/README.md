# D10/D11 Locked Held-Out Test Follow-Up

Promotion attempt of the validation-only D10 (GAIRAT-style boundary reweighting), D11a
(internal Stage-1/BASAT SAT-family pilot), and D11b (SAT-style selective filtering pilot)
to documented held-out 500-window test evidence, using frozen validation-selected thresholds
at FAR caps 0.20 / 0.15 / 0.10 under PGD epsilon = 0.030 (eval PGD-10, alpha = eps/6).

**Outcome: negative.** None of the three methods reaches F20 (recall >= 0.80, FAR <= 0.20) on the
locked test split; none approaches R90F10. All three are weaker on test than the D8b AFAC-score
post-hoc reference, even when given the same post-hoc sweep advantage. See
`d10_d11_locked_test_summary.md` for the full result and interpretation.

## Contents

| File | What it is |
|------|-----------|
| `d10_d11_locked_test_summary.md` | Headline tables, interpretation, verdict |
| `d10_d11_locked_test_summary.csv` | D8b reference row + all frozen-threshold test rows |
| `d10_d11_threshold_selection_validation.csv` | Validation-only threshold selection (per method x FAR cap) |
| `d10_d11_test_metrics_by_far_cap.csv` | Full locked-test metrics at frozen thresholds |
| `d10_d11_posthoc_test_characterization.csv` | Test post-hoc FAR sweeps (characterization only; same evidence type as D8b row) |
| `d10_d11_false_alarm_source_breakdown.csv` | FP true-class sources at each frozen threshold |
| `d10_d11_missed_fall_destination_breakdown.csv` | FN argmax destination classes at each frozen threshold |
| `test_eval/*.csv` | Per-window test scores/logits (clean, FGSM, PGD per checkpoint) — the per-window score evidence |
| `PROVENANCE.md` | Checkpoints, commits, data splits, protocol details |
| `COMMANDS_RUN.txt` | Exact commands executed |

## Evidence-type warning

Rows labeled `held-out test, frozen validation-selected threshold` are the only locked-test
evidence here. Rows labeled `test post-hoc FAR sweep (characterization only)` are operating-region
characterization and must not be reported as deployment-validated threshold selection. Validation
columns are shown only to document the selection step; do not mix them with test claims.
