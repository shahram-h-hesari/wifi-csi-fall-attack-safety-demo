# Priority 2 — GRU Seed 46 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **GRU** architecture, **seed 46** — the
fifth and final seed of the GRU cross-architecture set (42–46). Run under the
**same fixed protocol** as the prior GRU seeds and the other architectures — same
UT-HAR/SenseFi pipeline, same 500-window test split (45 fall / 455 non-fall), same
preprocessing, same fall/non-fall mapping, same 18-point epsilon grid, same
FGSM/PGD settings, same safety-proxy metric scripts, same `--model gru` factory
entry. No methodology, hyperparameter, or protocol change was made for this seed.

With seed 46 clean-qualified, **GRU now has a full five-seed (42–46) result,
matching the LeNet baseline seed count.**

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model gru
  --seed 46 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name gru_seed46 --results-dir results/cross_architecture/gru
  --checkpoint-dir checkpoints/cross_architecture/gru`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model gru
  --seed 46 --epsilon 0.03 --attacks both --run-name gru_seed46
  --checkpoint checkpoints/cross_architecture/gru/gru_seed46_best.pt
  --results-dir results/cross_architecture/gru`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `cbca55b` (seed-45 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
seed-42/43/44/45 GRU files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 110 (best epoch 90).

| Metric | seed 46 | seed 45 | seed 44 | seed 43 | seed 42 |
|---|---|---|---|---|---|
| Accuracy | 0.872 | 0.920 | 0.932 | 0.904 | 0.904 |
| Macro-F1 | 0.845 | 0.892 | 0.910 | 0.875 | 0.882 |
| Fall recall | 0.911 | 0.933 | 0.911 | 0.911 | 0.933 |
| Fall precision | 0.891 | 0.875 | 0.932 | 0.911 | 0.955 |
| Missed-fall rate | 0.089 | 0.067 | 0.089 | 0.089 | 0.067 |
| False-fall alarms (FP) | 5 | 6 | 3 | 4 | 2 |
| TP/FN/FP/TN | 41/4/5/450 | 42/3/6/449 | 41/4/3/452 | 41/4/4/451 | 42/3/2/453 |

Per-class recall (seed 46): lie down 0.848, fall 0.911, walk 0.905, pickup 0.860,
run 0.917, sit down 0.775, stand up 0.677. Validation at the selected checkpoint:
macro-F1 0.905, accuracy 0.911, loss 0.295.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.911), not 0.
- Macro-F1 is meaningful (0.845), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.68–0.92); the model is **not** a single-class / trivial predictor.
- Training converged normally: early-stopped at epoch 110 (best epoch 90),
  healthy validation loss (0.295), no numerical divergence.

Seed 46 has the lowest clean accuracy of the five GRU seeds (0.872) but is still a
clearly converged, non-trivial classifier — **clean-qualified** by the same rule
applied to seeds 42–45.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.168 | 0.141 | 0/45/53/402 | 53 |
| PGD ε=0.03  | 0.000 | 0.058 | 0.053 | 0/45/60/395 | 60 |

Under matched attacks at ε=0.03, GRU seed 46 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000), consistent with seeds
42–45. Multiclass accuracy falls from 0.872 clean to 0.168 (FGSM) / 0.058 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 46) | 0.0075 | 0.010 | 0.030 |
| PGD  (seed 46) | 0.005 | 0.0075 | 0.025 |

(Clean fall recall used for the drop threshold = 0.911.) PGD drives fall recall to
exactly 0.000 by ε ≤ 0.025; FGSM by ε ≤ 0.030. Thresholds are within ordinary
seed-to-seed variation of seeds 42–45.

## Five-seed GRU summary (42–46, all clean-qualified)
| Seed | Clean acc | Clean fall recall | FGSM@0.03 recall | PGD@0.03 recall | FGSM recall=0 ε | PGD recall=0 ε |
|---|---|---|---|---|---|---|
| 42 | 0.904 | 0.933 | 0.000 | 0.000 | 0.020 | 0.015 |
| 43 | 0.904 | 0.911 | 0.022 | 0.000 | 0.035 | 0.025 |
| 44 | 0.932 | 0.911 | 0.000 | 0.000 | 0.020 | 0.015 |
| 45 | 0.920 | 0.933 | 0.022 | 0.000 | 0.045 | 0.025 |
| 46 | 0.872 | 0.911 | 0.000 | 0.000 | 0.030 | 0.025 |

**All 5/5 clean-qualified GRU seeds collapse to 0.000 PGD fall recall at ε=0.03**
(every one of the 45 fall windows missed, zero variance). FGSM at ε=0.03 reaches
0.000 in 3/5 seeds and 0.022 in the other two. PGD reaches zero fall recall by
ε ≤ 0.025 in all five seeds.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/gru/gru_seed46_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/gru/gru_seed_convergence_status.csv`
  (GRU cross-architecture seed status; seeds 42–46, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/gru/gru_seed46_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for GRU seeds 42–45 and is comparison-only. The GRU clean
  references actually used in every metric row (clean_accuracy 0.872,
  clean_fall_recall 0.911) are computed live from the loaded GRU checkpoint and
  are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- GRU now has a **full five-seed (42–46) clean-qualified result**, matching the
  LeNet baseline seed count. **5/5 clean-qualified GRU seeds collapse to 0.000 PGD
  fall recall at ε=0.03.** This is a multi-seed result for a *recurrent* model
  family; it is **not** a claim of reliability for every architecture family
  (BiLSTM and Transformer remain seed-42 pilots), and it is **not** full
  five-seed evidence for those families.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the seed-43/44/45
  notes for the full protocol.
