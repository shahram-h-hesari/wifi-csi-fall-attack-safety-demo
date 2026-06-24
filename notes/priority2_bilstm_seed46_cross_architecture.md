# Priority 2 — BiLSTM Seed 46 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **BiLSTM** architecture, **seed 46** — the
fifth and final seed of the planned BiLSTM cross-architecture set (42–46). Run
under the **same fixed protocol** as BiLSTM seeds 42–45 and the GRU
cross-architecture seeds — same UT-HAR/SenseFi pipeline, same 500-window test
split (45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping,
same 18-point epsilon grid, same FGSM/PGD settings, same safety-proxy metric
scripts, same `--model bilstm` factory entry. No methodology, hyperparameter, or
protocol change was made for this seed.

With seed 46 clean-qualified, **the BiLSTM five-seed set (42–46) is complete.**
ResNet18 seed 47 remains intentionally deferred and is unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model bilstm
  --seed 46 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name bilstm_seed46 --results-dir results/cross_architecture/bilstm
  --checkpoint-dir checkpoints/cross_architecture/bilstm`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model bilstm
  --seed 46 --epsilon 0.03 --attacks both --run-name bilstm_seed46
  --checkpoint checkpoints/cross_architecture/bilstm/bilstm_seed46_best.pt
  --results-dir results/cross_architecture/bilstm`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `d445a02` (BiLSTM seed-45 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
BiLSTM seed-42/43/44/45 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 163 (best epoch 143).

| Metric | seed 46 | seed 45 | seed 44 | seed 43 | seed 42 |
|---|---|---|---|---|---|
| Accuracy | 0.836 | 0.808 | 0.878 | 0.830 | 0.814 |
| Macro-F1 | 0.803 | 0.769 | 0.841 | 0.781 | 0.769 |
| Fall recall | 0.867 | 0.933 | 0.911 | 0.822 | 0.889 |
| Fall precision | 0.886 | 0.737 | 0.932 | 0.881 | 0.851 |
| Missed-fall rate | 0.133 | 0.067 | 0.089 | 0.178 | 0.111 |
| False-fall alarms (FP) | 5 | 15 | 3 | 5 | 7 |
| TP/FN/FP/TN | 39/6/5/450 | 42/3/15/440 | 41/4/3/452 | 37/8/5/450 | 40/5/7/448 |

Per-class recall (seed 46): lie down 0.712, fall 0.867, walk 0.891, pickup 0.760,
run 0.926, sit down 0.750, stand up 0.677. Validation at the selected checkpoint:
macro-F1 0.867, accuracy 0.879, loss 0.382.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.867 — 39/45 falls caught), not 0.
- Macro-F1 is meaningful (0.803), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.68–0.93); the model is **not** a single-class / walk-only / trivial predictor.
- Training is healthy: early-stopped at epoch 163 (best 143), validation loss
  0.382, no numerical divergence.

Seed 46 is a solid mid-range BiLSTM clean classifier and is **clean-qualified** by
the same rule applied to seeds 42–45 and the GRU/ResNet seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.118 | 0.098 | 0/45/44/411 | 44 |
| PGD ε=0.03  | 0.000 | 0.028 | 0.029 | 0/45/54/401 | 54 |

Under matched attacks at ε=0.03, BiLSTM seed 46 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000) — i.e. it **does reach
exactly 0.000 at ε=0.03**, like seeds 42–44 and unlike the attack-tolerant seed
45. Multiclass accuracy falls from 0.836 clean to 0.118 (FGSM) / 0.028 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 46) | 0.0075 | 0.010 | 0.020 |
| PGD  (seed 46) | 0.005 | 0.0075 | 0.015 |

(Clean fall recall used for the drop threshold = 0.867.) Both thresholds are
concrete (not null): FGSM reaches exactly 0.000 by ε=0.020 and PGD by ε=0.015,
and both are 0.000 at the matched ε=0.03 point — verified against the matched
single-ε run, which independently reports FGSM/PGD fall recall 0.000.

## Five-seed BiLSTM summary (42–46, all clean-qualified)
| Seed | Clean acc | Clean fall recall | FGSM@0.03 recall | PGD@0.03 recall | FGSM recall=0 ε | PGD recall=0 ε |
|---|---|---|---|---|---|---|
| 42 | 0.814 | 0.889 | 0.000 | 0.000 | 0.0175 | 0.0175 |
| 43 | 0.830 | 0.822 | 0.000 | 0.000 | 0.0175 | 0.015 |
| 44 | 0.878 | 0.911 | 0.000 | 0.000 | 0.030 | 0.025 |
| 45 | 0.808 | 0.933 | **0.111** | **0.022** | none in grid | 0.035 |
| 46 | 0.836 | 0.867 | 0.000 | 0.000 | 0.020 | 0.015 |

**Precise wording (use this, do not over-round):**
- **4 of 5** clean-qualified BiLSTM seeds (42, 43, 44, 46) reach **exactly 0.000**
  fall recall under **both** FGSM and PGD at ε=0.03.
- **Seed 45 is the exception**: at ε=0.03 it retains FGSM 0.111 / PGD 0.022 fall
  recall; FGSM never reaches exactly 0.000 within the 0.0–0.075 grid (bottoms at
  0.022), and PGD reaches 0.000 only at ε=0.035.
- **All 5** clean-qualified seeds reach **exactly 0.000 PGD fall recall by ε ≤
  0.035** (four of them by ε ≤ 0.025), and all 5 fall below 0.50 fall recall by
  ε ≈ 0.0075–0.0125.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/bilstm/bilstm_seed46_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/bilstm/bilstm_seed_convergence_status.csv`
  (BiLSTM cross-architecture seed status; seeds 42–46, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/bilstm/bilstm_seed46_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for BiLSTM seeds 42–45 and the GRU seeds, and is
  comparison-only. The BiLSTM clean references actually used in every metric row
  (clean_accuracy 0.836, clean_fall_recall 0.867) are computed live from the
  loaded BiLSTM checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This completes a **full five-seed clean-qualified BiLSTM set (42–46)**. However,
  BiLSTM's adversarial behavior at ε=0.03 is **not** uniformly total: **4/5 seeds
  reach exactly 0.000 fall recall under both attacks at ε=0.03; seed 45 does not**
  (FGSM 0.111, PGD 0.022). The thesis-safe statement is: *all five clean-qualified
  BiLSTM seeds show severe adversarial fall-recall degradation at ε=0.03, with 4/5
  reaching exactly 0.000 under both attacks; all five reach 0.000 PGD fall recall
  by ε ≤ 0.035.* Do **not** state "all five collapse to 0.000 at ε=0.03."
- LeNet and GRU have full five-seed evidence with zero-variance 0.000 PGD collapse
  at ε=0.03; ResNet18 has a four-seed clean-qualified result. BiLSTM is now also a
  full five-seed set but with the seed-45 attack-tolerance caveat above.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the BiLSTM
  seed-43/44/45 notes for the full protocol.
