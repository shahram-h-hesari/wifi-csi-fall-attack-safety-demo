# PGD-Epsilon Recall/FAR Frontier — Existing Artifacts + Designed Validation Sweep

Date: 2026-07-05. Evidence type: **validation-only re-analysis of saved probability exports.**
No training, no checkpoint loaded, no attack generated, no test file opened, no `.tex` edited,
nothing committed. Threshold selection everywhere uses the frozen ledger rule (max validation
recall s.t. validation FAR ≤ cap; tie-break lower FAR, then higher tau). Held-out test appears
nowhere in this analysis; prior test results are cited only as motivation for buffering, never
for selection.

Targets (evaluated on validation, 44 fall / 452 non-fall):
- **H15**: recall > 0.85 AND FAR < 0.15 (checked at the cap-0.15 operating point).
- **F20**: recall ≥ 0.80 AND FAR ≤ 0.20 (checked at the cap-0.20 operating point).

Script: `scripts/analysis/pgd_epsilon_frontier_plan.py`
Outputs: `results/defense_attempt_inventory/pgd_epsilon_frontier/` (3 required CSVs, 5 plots,
`frontier_key_numbers.json`).

---

## 1. Which saved PGD epsilon artifacts already exist?

**Usable for FAR-cap threshold selection (per-window fall-probability, validation split):**

| Condition | Epsilon | Coverage |
|---|---|---|
| clean (= PGD ε→0 limit) | **0.000** | all 24 saved defense score axes (9 families, 2 representations) |
| PGD-10, α=ε/6 | **0.030** | all 24 saved defense score axes |
| FGSM | 0.030 | all 24 axes (exists; out of scope — PGD only per task) |

That is the entire usable validation epsilon grid: **{0.000, 0.030}.**

**Existing epsilon sweeps that CANNOT be used for this question:**

- `results/epsilon_sweep_predictions/pgd_predictions_short_epsilon_*.csv` — 18 epsilons
  (0.000–0.075), undefended baseline, but (a) **argmax labels + max-confidence only, no
  fall-probability column** → no threshold selection possible, and (b) the "short" split is 996
  windows = validation+test concatenated (89 fall / 907 non-fall) → mixed-split, cannot be used
  as validation evidence without an extraction protocol that has never been validated.
- `results/converged_attacks/converged_seed4x_{pgd,fgsm}_sweep_predictions_{test,legacy}.csv` —
  same argmax-only schema, and on the **test**/legacy splits → doubly unusable here.
- `results/{pgd,fgsm}_epsilon_sweep_summary.csv`, thesis Tables 4/27 — argmax-rule summaries of
  the above; no score axis.

These are recorded in `missing_epsilon_artifacts.csv` as missing *score* artifacts.

---

## 2. Best validation recall at FAR caps 0.10 / 0.15 / 0.20 per model and epsilon

Full 24-axis table: `pgd_epsilon_frontier/epsilon_frontier_by_model.csv` (thresholds, recall,
realized FAR, TP/FN/FP/TN per cap, AUROC). Family representatives:

**ε = 0.000 (clean condition):**

| Model | recall@0.10 | recall@0.15 | recall@0.20 | AUROC | H15? | F20? |
|---|---|---|---|---|---|---|
| AFAC_maxscore | 1.000 | 1.000 | 1.000 | 0.9933 | PASS | PASS |
| GR1_macroF1 (D10) | 1.000 | 1.000 | 1.000 | 0.9971 | PASS | PASS |
| SA1_lowFA (D11b) | 0.977 | 1.000 | 1.000 | 0.9963 | PASS | PASS |
| ST1_lowFA | 0.977 | 1.000 | 1.000 | 0.9947 | PASS | PASS |
| ST1b6_lowFA (D11a) | 0.977 | 1.000 | 1.000 | 0.9938 | PASS | PASS |
| D14B_seed44 | 0.977 | 0.977 | 1.000 | 0.9900 | PASS | PASS |
| VD_seed42 | 0.977 | 0.977 | 0.977 | 0.9889 | PASS | PASS |
| G1_safety_s44 | 1.000 | 1.000 | 1.000 | 0.9945 | PASS | PASS |
| BLF_macroF1 (BiLSTM) | 1.000 | 1.000 | 1.000 | 0.9940 | PASS | PASS |

All 24 axes pass **both** H15 and F20 at ε=0.000.

**ε = 0.030 (PGD-10):**

| Model | recall@0.10 | recall@0.15 | recall@0.20 | AUROC | H15? | F20? |
|---|---|---|---|---|---|---|
| AFAC_maxscore | 0.386 | **0.705** | 0.818 | 0.8719 | fail | PASS |
| GR1_macroF1 (D10) | 0.341 | 0.591 | 0.886 | 0.8712 | fail | PASS |
| SA1_lowFA (D11b) | **0.523** | 0.659 | 0.886 | 0.8728 | fail | PASS |
| ST1_lowFA | 0.477 | 0.659 | 0.841 | 0.8640 | fail | PASS |
| ST1b6_lowFA (D11a) | 0.364 | 0.477 | **0.909** | 0.8690 | fail | PASS |
| D14B_seed44 | **0.523** | 0.659 | 0.818 | **0.8732** | fail | PASS |
| VD_seed42 | 0.000 | 0.000 | 0.000 | 0.6756 | fail | fail |
| G1_safety_s44 | 0.409 | 0.568 | 0.727 | 0.8518 | fail | fail |
| BLF_macroF1 (BiLSTM) | 0.000 | 0.114 | 0.250 | 0.7257 | fail | fail |

At ε=0.030: **0 of 24 axes pass H15** (best recall@0.15 = 0.705); **11 of 24 pass F20 on
validation** (best recall@0.20 = 0.909, ST1b6_lowFA).

---

## 3. Maximum epsilon where validation satisfies H15

**ε = 0.000 on the available grid** (every axis). H15 fails for every axis at the next available
grid point, 0.030. The true boundary lies strictly inside **(0.000, 0.030)** and cannot be
resolved from saved artifacts.

## 4. Maximum epsilon where validation satisfies F20

**ε = 0.030 on the available grid** — 11 of 24 axes (all healthy AFAC/GAIRAT/SAT/BASAT/D14
variants) satisfy F20 with validation-selected thresholds at 0.030. Whether F20 survives above
0.030 is unknown (no saved score artifacts beyond 0.030 on validation). Motivation-context only,
not used for any selection here: validation F20 at ε=0.030 previously failed to transfer to the
held-out test split, so a validation F20 pass at 0.030 should not be read as a test claim.

## 5. Does any model satisfy H15 at any epsilon?

Yes — **all 24 axes at ε = 0.000 (clean)**, with margin (recall 0.977–1.000 at FAR ≤ 0.10–0.15).
No axis satisfies H15 at ε = 0.030. Between those two points there are no artifacts.

## 6. Does any model satisfy F20 at any epsilon?

Yes — all 24 at ε = 0.000, and **11 of 24 at ε = 0.030** (validation-selected thresholds).

## 7. Exact epsilon boundary

- **H15 boundary: inside (0.000, 0.030), location unknown.** The available grid has no interior
  points; the designed sweep below is required to bisect it. Any number quoted today would be
  interpolation, not measurement.
- **F20 boundary: ≥ 0.030 on validation** (right edge unknown; no artifacts above 0.030).

## 8. Which model/defense has the best recall/FAR frontier?

Per cap at ε = 0.030 (the only attacked grid point):

- FAR ≤ 0.10: **SA1_lowFA and D14B_seed44** (0.523).
- FAR ≤ 0.15 (the H15-relevant cap): **AFAC_maxscore** (0.705).
- FAR ≤ 0.20: **ST1b6_lowFA** (0.909).
- Best AUROC: **D14B_seed44** (0.8732), with AFAC/SA1/GR1 within 0.002.

For the H15 question specifically (low/mid-FAR region), **AFAC_maxscore has the best frontier**,
with D14B_seed44 statistically indistinguishable; ST1b6's advantage exists only at the 0.20 cap.
No axis dominates all three caps. The designed sweep therefore carries the four leaders
(AFAC_maxscore, SA1_lowFA, D14B_seed44, ST1b6_lowFA) plus GR1_macroF1 as the D10 reference.

## 9. Additional validation-only epsilon sweeps needed (DESIGNED, NOT RUN)

**Gap:** no validation score exports exist for any PGD ε in (0, 0.030) or above 0.030, for any
model (`missing_epsilon_artifacts.csv`). All checkpoints exist; each point is regenerable
validation-only with the frozen export pipeline (PGD-10, α=ε/6, byte-identical attack code).

**Designed sweep (requires your explicit approval before any run):**

- Models (5): AFAC_maxscore, SA1_lowFA, D14B_seed44, ST1b6_lowFA, GR1_macroF1 (checkpoint paths
  in the script header / `missing_epsilon_artifacts.csv`).
- Epsilon grid (7): 0.005, 0.010, **0.015**, 0.020, 0.025 (interior, H15 boundary), 0.040, 0.050
  (outer, F20 right edge).
- Split: `--split val` only. Nothing else changes; thresholds re-selected per epsilon with the
  same frozen rule; H15/F20 evaluated exactly as above.
- Order: bisection-first — run ε=0.015 for all 5 models, then refine toward whichever side the
  H15 boundary falls (0.0075/0.0225 midpoints), then the outer points. This finds the boundary
  to ±0.004 in ≤ 3 rounds instead of 35 blind runs.
- Cost estimate: PGD-10 over 496 windows on CPU ≈ 1–3 min per (model, ε); full grid ≈ 35 runs
  ≈ 1–2 CPU-hours; bisection typically needs ~15.
- Template command (one per model × ε):

```
python scripts/export_probability_predictions.py \
  --checkpoint <checkpoint.pt> --model lenet \
  --epsilon <EPS> --run-name <run_name>_eps<EPS> \
  --out-dir results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep_eps<EPS> \
  --split val
```

Non-goal guard: the sweep characterizes where the frontier crosses H15/F20; the ε=0.030
evaluation point of the existing evidence is not being reselected by this analysis, and no
epsilon will be chosen *because* it flatters a model.

## 10. Exact first safe command

The frontier-from-saved-artifacts computation is already done
(`python scripts/analysis/pgd_epsilon_frontier_plan.py`, deterministic, rerunnable). The first
command of the designed sweep — **gated on your explicit approval, do not run before that** — is
the bisection midpoint for the best-frontier model:

```
python scripts/export_probability_predictions.py \
  --checkpoint checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt \
  --model lenet --epsilon 0.015 --run-name optionB_maxscore_eps0015 \
  --out-dir results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep_eps0015 \
  --split val
```

---

## Required tables and plots (all under `pgd_epsilon_frontier/`)

- `epsilon_frontier_by_model.csv` — 24 axes × {0.000, 0.030}: per-cap tau / recall / FAR /
  TP/FN/FP/TN, AUROC, H15/F20 pass flags.
- `epsilon_target_boundary.csv` — per axis: max ε passing H15 / F20, first ε failing each, with
  the grid-resolution caveat column.
- `missing_epsilon_artifacts.csv` — missing (model, ε, split) combinations and validation-only
  regenerability.
- Plots: `recall_vs_epsilon_far10/15/20.png`, `auroc_vs_epsilon.png`,
  `target_boundary_plot.png` (H15/F20 pass-fail regions; the orange band marks the
  artifact-free (0, 0.030) interval where the boundary is unresolved).

## Frontier characterization (one paragraph)

On validation, with validation-selected thresholds: **H15 is achievable everywhere at ε = 0.000
and nowhere at ε = 0.030; F20 is achievable at both grid points (11 of 24 axes at 0.030).** The
regime boundary of interest — where recall@FAR≤0.15 crosses 0.85 — lies strictly inside the
unmeasured (0.000, 0.030) band for every model, and locating it requires the designed
validation-only sweep above. The relative ordering of defenses is stable across caps at 0.030
(AFAC/D14B/SA1 lead at low FAR; ST1b6/GR1 lead only at the 0.20 cap), so the sweep's 5-model
subset preserves the frontier leaders without sweeping all 24 axes.
