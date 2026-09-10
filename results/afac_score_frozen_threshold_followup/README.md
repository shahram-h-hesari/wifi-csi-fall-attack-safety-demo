# AFAC-Score Frozen Validation-Threshold Follow-Up

Status: **Stage 1 (validation-only threshold selection) and Stage 2 (held-out test application)
both complete.** Outcome: **negative under the pre-registered primary rule** — see summary below.

Promotes D8b (AFAC-score, `optionB_maxscore`) from post-hoc test FAR-sweep evidence toward frozen
validation-selected-threshold held-out-test evidence, following the two-stage protocol in
`AFAC_PRE_RUN_STRATEGY.md`.

## Contents

| File | What it is |
|------|-----------|
| `AFAC_PRE_RUN_STRATEGY.md` | Full advisory report: artifact inventory, threshold/variant-selection reasoning, protocol, decision rule |
| `afac_score_stage1_validation_summary.md` | Stage 1 results: frozen thresholds at all four FAR caps, bootstrap stability, buffer assessment |
| `afac_score_threshold_selection_validation.csv` | Machine-readable frozen thresholds + validation metrics per FAR cap |
| `afac_score_bootstrap_stability_validation.csv` | Bootstrap threshold/recall stability per FAR cap |
| `afac_score_validation_frontier.csv` | Full validation recall/FAR frontier (455 distinct thresholds) |
| `val_eval/*.csv` | Per-window validation scores/logits (clean, FGSM, PGD) |
| `afac_score_frozen_threshold_summary.md` | **Stage 2 headline: test results, verdict, comparison to D8b/D10/D11** |
| `afac_score_frozen_threshold_summary.csv` | Machine-readable comparison table (AFAC + D8b + D10/D11) |
| `afac_score_test_metrics_by_far_cap.csv` | Full locked-test metrics at each frozen threshold |
| `afac_score_clean_condition_at_primary_threshold.csv` | Clean-condition recall/FAR at the primary threshold |
| `afac_score_false_alarm_source_breakdown.csv` | FP true-class sources at each frozen threshold |
| `afac_score_missed_fall_destination_breakdown.csv` | FN argmax destination classes at each frozen threshold |
| `PROVENANCE.md` | Checkpoint, commit, data-split, and protocol details (both stages) |
| `COMMANDS_RUN.txt` | Exact commands executed (both stages) |

## Stage 1 frozen thresholds (validation only, PGD eps=0.030) — unmodified in Stage 2

| FAR cap | Role | Threshold | Val recall | Val FAR |
|---|---|---|---|---|
| **0.18** | **Primary** | **0.170908** | 0.7727 | 0.1571 |
| 0.20 | Comparison | 0.147881 | 0.8182 | 0.1947 |
| 0.15 | Diagnostic | 0.181992 | 0.7045 | 0.1438 |
| 0.10 | R90F10 diagnostic | 0.234373 | 0.3864 | 0.0907 |

## Stage 2 headline: locked test results (PGD eps=0.030, split verified 500/45/455)

| Role | FAR cap | Test recall | Test FAR | F20? |
|---|---|---|---|---|
| **Primary** | **0.18** | **0.6889** | **0.1824** | **No — FAILURE band** |
| Comparison | 0.20 | 0.8000 | 0.2088 | No (near-miss: ties D8b recall, FAR 4 FPs over cap) |
| Diagnostic | 0.15 | 0.6667 | 0.1758 | No |
| R90F10 diagnostic | 0.10 | 0.3333 | 0.1121 | No |

**Verdict: AFAC-score does not survive frozen validation-threshold promotion under the
pre-registered primary rule.** D8b remains post-hoc characterization only; no method in the ledger
(D10, D11a, D11b, AFAC-score) has yet demonstrated F20 under a frozen validation-selected threshold.
Full analysis in `afac_score_frozen_threshold_summary.md`.

## Evidence-type warning

Rows labeled "held-out test, frozen validation-selected threshold" (Stage 2, this folder) are
locked-test evidence. The D8b reference row is a separately labeled "test post-hoc FAR sweep" and
must not be conflated with the Stage 2 rows.
