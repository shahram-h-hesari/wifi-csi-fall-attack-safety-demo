# D10/D11 Locked Held-Out Test Follow-Up — Summary

Date: 2026-07-04. Analysis git commit: `1bcf6b8`. Training git commit (all three checkpoints): `7b9db40`.
Attack: PGD, epsilon = 0.030, eval PGD-10 (alpha = eps/6), byte-identical frozen pipeline
(`run_converged_attacks.generate_attacked_batch` via `export_probability_predictions.py`).
Split discipline: thresholds selected on the 496-window validation split ONLY (44 fall / 452 non-fall),
frozen, then applied exactly once to the 500-window held-out test split (45 fall / 455 non-fall).
No threshold was changed after seeing test results.

Claim boundary: window-level, processed-CSI-tensor, digital-domain, white-box, seed-42 LeNet-family
defense checkpoints. Not clinical, not deployment-validated, not certified robustness.

## Methods promoted

| ID | Method | Checkpoint | Validation source (threshold selection) |
|----|--------|-----------|------------------------------------------|
| D10 | GAIRAT-style boundary reweighting (GR1) | `seed42_basat_gairat_GR1_v2macroF1_best.pt` | `GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv` |
| D11a | SAT-family internal Stage-1/BASAT pilot (beta6p0) | `seed42_basat_stage1_beta6p0_v2lowFA_best.pt` | `ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` |
| D11b | SAT-style selective filtering pilot (SA1) | `seed42_basat_sat_SA1_v2lowFA_best.pt` | `SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` |

Checkpoint variants are the ones whose validation numbers appear in Internal Appendix IA
(validation AUROC match: D10 0.8712, D11a 0.8690, D11b 0.8728).

## Headline result: locked test, frozen validation thresholds (PGD eps=0.030)

| Method | FAR cap | Frozen tau | Val recall / FAR | Test TP/FN/FP/TN | Test recall | Test FAR | Test AUROC | F20? | R90F10? |
|--------|---------|-----------|------------------|------------------|-------------|----------|-----------|------|---------|
| **D8b ref (post-hoc sweep, NOT frozen)** | 0.20 | 0.1532 | — | 36/9/91/364 | **0.8000** | 0.2000 | 0.8439 | Yes | No |
| D10 | 0.20 | 0.0753 | 0.886 / 0.190 | 34/11/93/362 | 0.7556 | 0.2044 | **0.8470** | **No** | No |
| D10 | 0.15 | 0.1489 | 0.591 / 0.148 | 24/21/68/387 | 0.5333 | 0.1495 | 0.8470 | No | No |
| D10 | 0.10 | 0.2503 | 0.341 / 0.084 | 14/31/41/414 | 0.3111 | 0.0901 | 0.8470 | No | No |
| D11a | 0.20 | 0.0518 | 0.909 / 0.190 | 31/14/102/353 | 0.6889 | 0.2242 | 0.8199 | No | No |
| D11a | 0.15 | 0.1113 | 0.477 / 0.131 | 21/24/76/379 | 0.4667 | 0.1670 | 0.8199 | No | No |
| D11a | 0.10 | 0.1747 | 0.364 / 0.088 | 11/34/55/400 | 0.2444 | 0.1209 | 0.8199 | No | No |
| D11b | 0.20 | 0.0485 | 0.886 / 0.188 | 34/11/98/357 | 0.7556 | 0.2154 | 0.8278 | No | No |
| D11b | 0.15 | 0.0834 | 0.659 / 0.142 | 25/20/77/378 | 0.5556 | 0.1692 | 0.8278 | No | No |
| D11b | 0.10 | 0.1247 | 0.523 / 0.100 | 16/29/56/399 | 0.3556 | 0.1231 | 0.8278 | No | No |

**None of D10/D11a/D11b reaches F20 (recall >= 0.80 and FAR <= 0.20) on the locked held-out test
split.** None satisfies FAR <= 0.15 or FAR <= 0.10 with useful recall, and none approaches R90F10.
Frozen thresholds also slightly overshoot the FAR caps on test (e.g., D11a 0.224 vs cap 0.20),
showing a validation-to-test FAR generalization gap on top of the recall drop.

## Post-hoc test characterization (same evidence type as the D8b reference row)

Labeled explicitly as test post-hoc FAR-sweep characterization, not frozen-threshold evidence:

| Method | Best test recall @ FAR<=0.20 | @ FAR<=0.15 | @ FAR<=0.10 | Test AUROC |
|--------|------------------------------|-------------|-------------|-----------|
| D8b (reference) | **0.8000** (TP 36 / FP 91) | — | 0.2667 | 0.8439 |
| D10 | 0.7111 (TP 32 / FP 86) | 0.5333 | 0.3111 | 0.8470 |
| D11a | 0.6667 (TP 30 / FP 91) | 0.3333 | 0.2222 | 0.8199 |
| D11b | 0.6667 (TP 30 / FP 86) | 0.5333 | 0.2222 | 0.8278 |

Interpretation: even under the *same post-hoc sweep advantage that D8b enjoys*, D10/D11 stay below
D8b at FAR <= 0.20. D10's overall test AUROC (0.847) is nominally above D8b's (0.844), but its
low-FAR partial operating region is worse where it matters. The validation gap (val 0.886-0.909 vs
test post-hoc 0.667-0.711) is therefore a genuine score-separability generalization gap, not merely
a threshold-transfer artifact.

## Error structure at the FAR<=0.20 frozen threshold

- False-fall-alarm sources are dominated by **run** (45-48 of ~93-102 FPs) and **walk** (22-24),
  i.e., high-mobility classes account for roughly 70% of the false-alarm burden in all three methods.
- Missed falls under PGD are argmax-routed mostly to **walk** (6-9 of 11-14 FNs).

## Verdict

1. D10/D11 have now been evaluated on the 500-window held-out test split using frozen
   validation-selected thresholds. The promotion attempt is complete and the result is **negative**:
   they are weaker than the D8b AFAC-score post-hoc reference on test at every FAR cap.
2. F20 on locked test: **not met** by any method. FAR<=0.15 / FAR<=0.10 with recall >= 0.80: not met.
   R90F10: not met (not close; best test recall at FAR<=0.10 is 0.356 post-hoc).
3. Recommended thesis treatment: keep D10/D11 as validation pilots with a documented negative
   locked-test follow-up (this is publishable evidence discipline, not a wasted experiment);
   keep D8b AFAC-score as the proposal-level operating-region evidence.
