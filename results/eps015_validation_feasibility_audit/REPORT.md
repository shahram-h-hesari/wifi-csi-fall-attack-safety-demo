# Task 3 — Validation-Only PGD eps=0.015 False-Positive Audit and Operating-Point Feasibility

Generated: 2026-07-12T075117Z. Evidence type: **validation-only re-analysis of saved probability
exports.** No training, no attack generation, no checkpoint loaded, no held-out-test file opened.
No threshold in this report has been applied to test data; nothing here is a final threshold
selection or protocol freeze. All operating points below are `retrospective validation feasibility`
/ `candidate operating point`, `not yet protocol-frozen`, `not evaluated on held-out test`.

## Fixed context: already-published test aggregate (not re-derived, not re-opened here)

Protocol `H15-TEST-EPS0015-AFAC-20260705`: TP 41, FN 4, FP 60, TN 395, recall 0.911111, FAR 0.131868.

## Attack-norm verification (Task 3, Step 2)

Status: **VERIFIED_LINF**. scripts/run_converged_attacks.py:103 -- code comment "# PGD: untargeted L-infinity, projected after each step." immediately preceding an epsilon-ball projection implemented via torch.clamp(perturbation, min=-epsilon, max=epsilon) (an L-infinity projection). Found by reading existing code only; the attack implementation was not altered.

## Excluded artifact (documented reason)

results/epsilon_sweep_predictions/pgd_predictions_short_epsilon_0_015.csv and its FGSM counterpart were considered and EXCLUDED: per results/defense_attempt_inventory/PGD_EPSILON_RECALL_FAR_FRONTIER_PLAN.md section 1, the 'short' split is validation+test concatenated (996 windows = 89 fall / 907 non-fall) and cannot be proven to be validation-only; it also carries argmax labels only, no fall_probability score column, so no threshold sweep is possible on it regardless.

## 1. Is R90/F10 feasible on any existing saved validation score axis at eps=0.015?

**Yes** — at least one saved validation score axis has a candidate threshold satisfying
Rfall > 0.90 AND FAR < 0.10 simultaneously, on validation data. See `per_axis_summary.csv`
for the exact per-axis best-feasible candidate and margin.

## 2/3. Margin, or nearest achievable point, per axis

| Axis | Feasible? | # feasible thresholds | Reference (frozen/candidate) recall | Reference FAR | Nearest-to-target recall | Nearest-to-target FAR |
|---|---|---|---|---|---|---|
| AFAC_maxscore | no | 0 | 0.9091 | 0.1084 | 0.9091 | 0.1084 |
| D14B_seed44 | no | 0 | 0.9091 | 0.1239 | 0.9091 | 0.1239 |
| GR1_macroF1 | yes | 4 | 0.9091 | 0.0929 | 0.9091 | 0.0929 |
| SA1_lowFA | no | 0 | 0.9545 | 0.1128 | 0.9091 | 0.1040 |
| ST1b6_lowFA | yes | 9 | 0.9545 | 0.0951 | 0.9545 | 0.0951 |

## 4. Which validation activity classes dominate false alarms?

- run: 109 false positives (aggregated across all analyzed axes at their reference threshold)
- walk: 54 false positives (aggregated across all analyzed axes at their reference threshold)
- stand up: 34 false positives (aggregated across all analyzed axes at their reference threshold)
- lie down: 22 false positives (aggregated across all analyzed axes at their reference threshold)
- pickup: 14 false positives (aggregated across all analyzed axes at their reference threshold)
- sit down: 8 false positives (aggregated across all analyzed axes at their reference threshold)

## 5. Are false positives mostly threshold-near or deeply overlapping?

- AFAC_maxscore: near-threshold FP = 19, far-from-threshold FP = 30 (band = 0.05)
- D14B_seed44: near-threshold FP = 30, far-from-threshold FP = 26 (band = 0.05)
- GR1_macroF1: near-threshold FP = 13, far-from-threshold FP = 29 (band = 0.05)
- SA1_lowFA: near-threshold FP = 21, far-from-threshold FP = 30 (band = 0.05)
- ST1b6_lowFA: near-threshold FP = 13, far-from-threshold FP = 30 (band = 0.05)

## 6. Do existing axes have useful complementarity?

| Axis A | Axis B | Shared TP | Shared FP | Unique FP (A) | Unique FP (B) | Unique recovered fall (A) | Unique recovered fall (B) | Disagreements |
|---|---|---|---|---|---|---|---|---|
| AFAC_maxscore | D14B_seed44 | 39 | 44 | 5 | 12 | 1 | 1 | 19 |
| AFAC_maxscore | GR1_macroF1 | 38 | 30 | 19 | 12 | 2 | 2 | 35 |
| AFAC_maxscore | SA1_lowFA | 40 | 36 | 13 | 15 | 0 | 2 | 30 |
| AFAC_maxscore | ST1b6_lowFA | 39 | 34 | 15 | 9 | 1 | 3 | 28 |
| D14B_seed44 | GR1_macroF1 | 38 | 35 | 21 | 7 | 2 | 2 | 32 |
| D14B_seed44 | SA1_lowFA | 40 | 43 | 13 | 8 | 0 | 2 | 23 |
| D14B_seed44 | ST1b6_lowFA | 39 | 39 | 17 | 4 | 1 | 3 | 25 |
| GR1_macroF1 | SA1_lowFA | 39 | 34 | 8 | 17 | 1 | 3 | 29 |
| GR1_macroF1 | ST1b6_lowFA | 40 | 31 | 11 | 12 | 0 | 2 | 25 |
| SA1_lowFA | ST1b6_lowFA | 41 | 37 | 14 | 6 | 1 | 1 | 22 |

No new ensemble or gate was built or evaluated in this task; the table above is descriptive
overlap evidence only, for later, separately-decided experiment planning.

## 7. Which experiment families does this evidence support?

Evidence-supported candidate directions only -- not a final experiment verdict. Based on
the actual per-axis results in Section 2/3 above (this run's real numbers, not a generic
template):

- **Threshold/calibration — SUPPORTED BY DIRECT EVIDENCE.** GR1_macroF1, ST1b6_lowFA already reach a
  validation operating point satisfying Rfall>0.90 AND FAR<0.10 with the EXISTING saved
  scores, at a threshold that was never applied to test. This requires no new training --
  only a future, separately-authorized protocol freeze and single test read at the chosen
  threshold for one of these axes.
  ST1b6_lowFA (9 feasible thresholds) has more than a knife-edge margin (multiple adjacent feasible thresholds, not a single point).
- **Knife-edge caution:** AFAC_maxscore, SA1_lowFA sit just outside feasibility (recall already >0.90 but FAR
  just above 0.10) -- consistent with this program's prior D8b knife-edge experience; any
  future selection on these specific axes should budget FAR margin, not select at the boundary.
- **Low-FAR objective / partial-AUC training** — weakly supported: the axes that are already
  feasible make a from-scratch low-FAR training objective lower priority than simply selecting
  among existing axes; still relevant if a future test read on a feasible axis fails to transfer.
- **Hard-negative / source-aware training** — supported: false alarms concentrate heavily in
  'run' and 'walk' (Section 4) rather than spreading evenly across all six non-fall classes,
  which is consistent with source-aware or hard-negative training being a targeted, not diffuse, fix.
- **Temporal/event-level filtering** — this analysis is window-level only and cannot confirm
  or rule out event-level effects; supported only as an untested, literature-motivated direction.
- **Gating/ensemble** — some support: 5 axis pair(s) show 3 or more
  combined unique-recovered-fall windows (Section 6), i.e. genuine complementarity, not mere
  agreement -- but combining axes also tends to combine their unique false positives, so this
  is not a free win and would need its own validation-only evaluation.
- **Representation/architecture change** — NOT prioritized by this evidence: multiple
  existing axes already reach feasibility without any representation change, so this
  remains the lowest-priority family unless a future test read on a feasible axis fails.

## 8. What should be investigated in the literature next?

Prioritize categories directly motivated by the findings above (see per-axis and per-class
tables): Neyman-Pearson / FAR-constrained thresholding, partial-AUC low-FPR optimization,
selective prediction/abstention, temporal event-level confirmation, and adversarial-input
detection / ensemble disagreement -- weighted by which experiment families Section 7 actually
supports for this evidence, not by category popularity.

## Inventory

5 validation-proven axis file(s) analyzed. See `inventory.csv` for full detail.
