# AFAC-Score Stage 2 — Frozen Validation-Threshold Test Application Summary

Date: 2026-07-04. Checkpoint: `seed42_optionB_maxscore_best.pt` (AFAC-score, D8b reference).
Split: held-out test, PGD epsilon = 0.030, eval PGD-10 (alpha = eps/6). **Split verified: 500
windows, 45 fall, 455 non-fall.** Thresholds are exactly the four frozen in Stage 1
(`afac_score_threshold_selection_validation.csv`); none was modified, adjusted, or reselected after
seeing test results. Existing Gate-5 test score exports were reused; no new test-split inference
was performed.

## Headline result: locked test, frozen validation thresholds (PGD eps=0.030)

| Role | FAR cap | Frozen tau | Val recall/FAR | Test TP/FN/FP/TN | Test recall | Test FAR | AUROC | F20? |
|---|---|---|---|---|---|---|---|---|
| **Primary** | **0.18** | **0.170908** | 0.7727 / 0.1571 | 31/14/83/372 | **0.6889** | **0.1824** | 0.8439 | **No** |
| Comparison | 0.20 | 0.147881 | 0.8182 / 0.1947 | 36/9/95/360 | 0.8000 | 0.2088 | 0.8439 | No |
| Diagnostic | 0.15 | 0.181992 | 0.7045 / 0.1438 | 30/15/80/375 | 0.6667 | 0.1758 | 0.8439 | No |
| R90F10 diagnostic | 0.10 | 0.234373 | 0.3864 / 0.0907 | 15/30/51/404 | 0.3333 | 0.1121 | 0.8439 | No |

**Primary-row verdict (pre-registered): FAILURE.** Test recall 0.6889 < 0.72 on the primary
0.18-buffered threshold. Per the pre-registered decision rule, this means **AFAC-score reaches F20
only as post-hoc operating-region characterization (the existing D8b evidence), not as frozen
validation-threshold transfer.** The primary threshold does not become the headline defense result.

## A notable near-miss (comparison row, not the primary rule)

The FAR<=0.20 comparison threshold (0.147881) reproduces **exactly the same recall as the D8b
post-hoc reference** (TP=36/FN=9, recall=0.8000) — but at FP=95 instead of D8b's FP=91, so test
FAR = 0.2088, narrowly exceeding the 0.20 cap (4 false alarms over the 91-FP boundary at n=455).
This is the closest any frozen-threshold protocol has come to reproducing D8b's F20 operating
point in this ledger, and it is reported here for completeness — but it is **not the pre-registered
primary rule**, and per the pre-run strategy's explicit prohibition, the primary rule is not
switched to this row after seeing this result.

## Clean-condition check at the primary threshold (pre-registered in Stage 1 protocol)

| Threshold | Clean TP/FN/FP/TN | Clean recall | Clean FAR |
|---|---|---|---|
| 0.170908 (primary) | 44/1/41/414 | 0.9778 | 0.0901 |

The primary threshold's clean-condition behavior is good in isolation (high recall, moderate FAR).
This does not reverse the Gate-5 argmax rejection (test clean 7-class accuracy 0.694 < 0.70) — that
rejection concerns the checkpoint's default multi-class decision rule, not this specific binary
fall-vs-non-fall threshold. Both facts are disclosed together per the pre-run strategy.

## Comparison across all frozen-threshold methods evaluated to date (~FAR-0.20-level rows)

| Method | Threshold role | Test recall | Test FAR | F20? |
|---|---|---|---|---|
| D8b (reference, post-hoc — different evidence type) | post-hoc optimum | 0.8000 | 0.2000 | Yes |
| D10 (locked) | FAR cap 0.20 | 0.7556 | 0.2044 | No |
| D11a (locked) | FAR cap 0.20 | 0.6889 | 0.2242 | No |
| D11b (locked) | FAR cap 0.20 | 0.7556 | 0.2154 | No |
| **AFAC-score (locked, comparison)** | FAR cap 0.20 | **0.8000** | 0.2088 | No |
| **AFAC-score (locked, primary)** | **FAR cap 0.18 (pre-registered rule)** | **0.6889** | **0.1824** | **No** |

At the ~0.20 FAR-cap level, AFAC's comparison row has the highest recall of any frozen-threshold
result evaluated so far (tying D8b exactly) and a FAR below D11a's. At its pre-registered primary
(0.18-buffered) operating point, AFAC's recall (0.6889) ties D11a and trails D10/D11b (0.7556),
while its FAR (0.1824) is the lowest of any frozen-threshold row at this cap level.

## Error structure (primary threshold, FAR cap 0.18)

False alarms and missed falls are broken out per threshold in
`afac_score_false_alarm_source_breakdown.csv` and
`afac_score_missed_fall_destination_breakdown.csv`; consistent with D10/D11, false-fall alarms
are dominated by high-mobility non-fall classes (run/walk).

## Verdict

1. **AFAC-score does not survive frozen validation-threshold promotion under the pre-registered
   primary rule.** The 0.18-buffered threshold yields test recall 0.6889, FAR 0.1824 — in the
   FAILURE band of the pre-registered decision rule.
2. **AFAC does not clearly beat D10/D11 under matched frozen-threshold protocol.** At its primary
   operating point it ties D11a's recall while improving FAR; at the 0.20-cap comparison level it
   has the best recall/FAR trade-off of the four methods but still fails the FAR cap, same as all
   three D10/D11 rows.
3. **D8b remains the only F20-satisfying evidence in the ledger, and remains post-hoc
   characterization, not frozen-threshold evidence.** No method evaluated to date (D10, D11a,
   D11b, AFAC-score) has demonstrated F20 under a frozen validation-selected threshold.
4. Recommended appendix update (pending Shahram's review, no LaTeX edited yet): add an AFAC-score
   frozen-threshold row family to the ledger, parallel to the D10/D11 rows, with the same
   "locked test, frozen validation-selected threshold" evidence label, explicitly noting the
   near-miss on the comparison row and the disclosed Gate-5 argmax caveat.
