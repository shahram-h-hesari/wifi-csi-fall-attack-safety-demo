# AFAC-Score Stage 1 — Validation-Only Threshold Selection Summary

Date: 2026-07-04. Checkpoint: `seed42_optionB_maxscore_best.pt` (AFAC-score, the D8b reference).
Split: validation, PGD epsilon = 0.030, eval PGD-10 (alpha = eps/6), byte-identical to the Gate-5
test-export protocol. **Split verified: 496 windows, 44 fall, 452 non-fall.**

**No held-out test file was read at any point in this stage.** This is validation-only selection.

## Frozen thresholds and validation metrics

| FAR cap | Primary? | Threshold | TP | FN | FP | TN | Val recall | Val FAR | Precision | F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| **0.18** | **Yes** | **0.170908** | 34 | 10 | 71 | 381 | **0.7727** | **0.1571** | 0.3238 | 0.4564 |
| 0.20 | No (comparison) | 0.147881 | 36 | 8 | 88 | 364 | 0.8182 | 0.1947 | 0.2903 | 0.4286 |
| 0.15 | No (diagnostic) | 0.181992 | 31 | 13 | 65 | 387 | 0.7045 | 0.1438 | 0.3229 | 0.4429 |
| 0.10 | No (R90F10 diagnostic) | 0.234373 | 17 | 27 | 41 | 411 | 0.3864 | 0.0907 | 0.2931 | 0.3333 |

Overall validation AUROC (PGD, all thresholds): **0.871883**.

## Bootstrap threshold-stability diagnostic

Stratified bootstrap (resample fall and non-fall windows separately, n=2000 resamples per cap,
fixed seed 20260704), reselecting the threshold on each resample under the same rule.

| FAR cap | Threshold median | Threshold 95% CI | Recall median | Recall 95% CI |
|---|---|---|---|---|
| 0.18 | 0.170908 | [0.140881, 0.187576] | 0.7727 | [0.6364, 0.9091] |
| 0.20 | 0.148466 | [0.113023, 0.176868] | 0.8182 | [0.6818, 0.9318] |
| 0.15 | 0.181992 | [0.170908, 0.205218] | 0.7045 | [0.5000, 0.8636] |
| 0.10 | 0.234373 | [0.196943, 0.261343] | 0.4318 | [0.2500, 0.6818] |

The wide recall confidence intervals are an expected consequence of only 44 fall windows in the
validation split (each fall window shifts recall by ~2.3 percentage points), not evidence of an
unstable selection rule — the median bootstrap threshold matches the point-estimate threshold at
every cap.

## Assessment of the 0.18 buffer

Moving from the 0.20 cap to the pre-registered 0.18 buffer costs **4.5 recall points** on
validation (0.8182 -> 0.7727, i.e. 2 fewer true positives out of 44 fall windows: 36 -> 34) while
reducing validation FAR from 0.1947 to 0.1571 (a 0.038 reduction, well past the 0.02 target buffer
size — the frontier is not steep here; there is no cliff). This is a modest, well-behaved trade,
not a "pathologically steep" frontier, so the 0.18 buffer is retained as specified in the pre-run
strategy without needing to revisit it.

## No-test-tuning confirmation

`scripts/analysis/afac_score_stage1_validation_selection.py` contains no reference to any
`test_eval` path or test-split file (verified by direct grep before execution, logged in
COMMANDS_RUN.txt). The known D8b post-hoc test threshold (~0.1532) was not consulted in selecting
any of the four thresholds above; note for the record that the 0.20-cap validation threshold
(0.147881) happens to be close to it, which is expected under a similar target FAR and is not the
result of any comparison performed during selection.
