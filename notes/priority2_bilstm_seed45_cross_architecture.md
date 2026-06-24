# Priority 2 — BiLSTM Seed 45 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **BiLSTM** architecture, **seed 45**,
extending the Priority 2 cross-architecture study from BiLSTM seeds 42/43/44 to a
fourth seed. Run under the **same fixed protocol** as BiLSTM seeds 42/43/44 and
the GRU cross-architecture seeds — same UT-HAR/SenseFi pipeline, same 500-window
test split (45 fall / 455 non-fall), same preprocessing, same fall/non-fall
mapping, same 18-point epsilon grid, same FGSM/PGD settings, same safety-proxy
metric scripts, same `--model bilstm` factory entry. No methodology,
hyperparameter, or protocol change was made for this seed.

This is the third of the remaining BiLSTM seeds being completed one by one (43, 44
done; **45 done here**; 46 remains). ResNet18 seed 47 is intentionally deferred and
is unrelated to this run.

> **Headline nuance (read before quoting):** unlike BiLSTM seeds 42–44 (which all
> collapse to exactly 0.000 fall recall at ε=0.03), **seed 45 does NOT reach
> 0.000 fall recall at ε=0.03** — FGSM 0.111, PGD 0.022. The collapse is still
> severe but partial at that budget; PGD reaches 0.000 only by ε=0.035, and FGSM
> bottoms out at 0.022 without reaching exactly 0 within the grid. Seed 45 is the
> most attack-tolerant BiLSTM seed and must be reported as such.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model bilstm
  --seed 45 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name bilstm_seed45 --results-dir results/cross_architecture/bilstm
  --checkpoint-dir checkpoints/cross_architecture/bilstm`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model bilstm
  --seed 45 --epsilon 0.03 --attacks both --run-name bilstm_seed45
  --checkpoint checkpoints/cross_architecture/bilstm/bilstm_seed45_best.pt
  --results-dir results/cross_architecture/bilstm`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `301adfe` (BiLSTM seed-44 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
BiLSTM seed-42/43/44 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 188 (best epoch 168).

| Metric | BiLSTM seed 45 | seed 44 (ref) | seed 43 (ref) | seed 42 (ref) |
|---|---|---|---|---|
| Accuracy | 0.808 | 0.878 | 0.830 | 0.814 |
| Macro-F1 | 0.769 | 0.841 | 0.781 | 0.769 |
| Fall recall | 0.933 | 0.911 | 0.822 | 0.889 |
| Fall precision | 0.737 | 0.932 | 0.881 | 0.851 |
| Missed-fall rate | 0.067 | 0.089 | 0.178 | 0.111 |
| False-fall alarms (FP) | 15 | 3 | 5 | 7 |
| TP/FN/FP/TN | 42/3/15/440 | 41/4/3/452 | 37/8/5/450 | 40/5/7/448 |

Per-class recall (seed 45): lie down 0.727, fall 0.933, walk 0.857, pickup 0.620,
run 0.893, sit down 0.750, stand up 0.613. Validation at the selected checkpoint:
macro-F1 0.817, accuracy 0.837, loss 0.502.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.933 — 42/45 falls caught), not 0.
- Macro-F1 is meaningful (0.769), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.61–0.93); the model is **not** a single-class / walk-only / trivial predictor.
- Training is healthy: early-stopped at epoch 188 (best 168), validation loss
  0.502, no numerical divergence.

Seed 45 has the **lowest clean accuracy** of the BiLSTM seeds (0.808) and the
**most clean false-fall alarms** (15; clean fall precision 0.737), consistent with
BiLSTM being the weakest family, but it is a clearly non-trivial converged
classifier and is **clean-qualified** by the same rule applied to seeds 42–44 and
the GRU/ResNet seeds. (For reference, this same seed value diverged for ResNet18
but trains cleanly here and for the GRU — the ResNet18 seed-45 divergence was a
ResNet18/optimizer interaction, not a property of the seed.)

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.111 | 0.090 | 0.108 | 5/40/63/392 | 63 |
| PGD ε=0.03  | 0.022 | 0.032 | 0.045 | 1/44/77/378 | 77 |

At matched ε=0.03, seed 45 is **severely but not totally degraded**: FGSM fall
recall 0.111 (5/45 falls caught), PGD 0.022 (1/45). This is the **only** seed in
the GRU/BiLSTM cross-architecture series so far that does **not** reach exactly
0.000 fall recall at ε=0.03 — its weaker, higher-false-alarm clean classifier
appears to retain one or a few stubbornly-classified fall windows under the matched
budget. Multiclass accuracy still collapses from 0.808 clean to 0.090 (FGSM) /
0.032 (PGD), and false-fall alarms inflate to 63 / 77.

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 45) | 0.0075 | 0.0125 | **none in grid** (bottoms at 0.022) |
| PGD  (seed 45) | 0.0075 | 0.010 | 0.035 |
| FGSM (seed 44, ref) | 0.005 | 0.0075 | 0.030 |
| PGD  (seed 44, ref) | 0.0025 | 0.0075 | 0.025 |
| FGSM (seed 43, ref) | 0.005 | 0.0075 | 0.0175 |
| PGD  (seed 43, ref) | 0.005 | 0.0075 | 0.015 |
| FGSM (seed 42, ref) | 0.0075 | 0.0175 | 0.0175 |
| PGD  (seed 42, ref) | 0.0075 | 0.015 | 0.0175 |

(Clean fall recall used for the drop threshold = 0.933.) Seed 45 still loses
≥0.10 fall recall by ε=0.0075 and drops below 0.50 by ε≈0.0125 under both attacks,
but it is the most attack-tolerant BiLSTM seed: **FGSM never reaches exactly 0.000
within the grid** (minimum 0.022 fall recall at ε≥0.045 — one persistent TP), and
**PGD reaches 0.000 only at ε=0.035**, slightly above the matched ε=0.03 point.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/bilstm/bilstm_seed45_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/bilstm/bilstm_seed_convergence_status.csv`
  (BiLSTM cross-architecture seed status; seeds 42 + 43 + 44 + 45, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/bilstm/bilstm_seed45_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for BiLSTM seeds 42–44 and the GRU seeds, and is
  comparison-only. The BiLSTM clean references actually used in every metric row
  (clean_accuracy 0.808, clean_fall_recall 0.933) are computed live from the
  loaded BiLSTM checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.
- The seed-45 sweep metadata records `first_epsilon_recall_zero = null` for both
  FGSM splits — this is correct (FGSM fall recall never reaches exactly 0 within
  the 0.0–0.075 grid), not a missing value.

## Limitations & wording
- This adds a **fourth clean-qualified BiLSTM seed (45)** to seeds 42/43/44;
  **BiLSTM now has 4 clean-qualified seeds (42, 43, 44, 45)**. Seed 46 remains
  before a full five-seed BiLSTM result.
- **Do NOT state that all four BiLSTM seeds collapse to 0.000 at ε=0.03.** That
  holds for seeds 42–44; **seed 45 retains FGSM 0.111 / PGD 0.022 fall recall at
  ε=0.03** and only reaches total PGD collapse by ε=0.035 (FGSM never reaches
  exactly 0 in-grid). The safe statement is: all four clean-qualified BiLSTM seeds
  show severe adversarial fall-recall degradation at ε=0.03 (fall recall ≤ 0.111;
  three of four reach exactly 0.000), and all reach <0.50 fall recall by ε≈0.0125.
- Only LeNet and GRU currently have full five-seed evidence; ResNet18 has a
  four-seed clean-qualified result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the BiLSTM
  seed-43/44 notes for the full protocol.
