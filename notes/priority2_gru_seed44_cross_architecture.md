# Priority 2 — GRU Seed 44 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **GRU** architecture, **seed 44**, extending
the Priority 2 cross-architecture study from the seed-42 pilot and seed-43 run to
a third seed. Run under the **same fixed protocol** as GRU seeds 42/43 and the
other architectures — same UT-HAR/SenseFi pipeline, same 500-window test split
(45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping, same
18-point epsilon grid, same FGSM/PGD settings, same safety-proxy metric scripts,
same `--model gru` factory entry. No methodology, hyperparameter, or protocol
change was made for this seed.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model gru
  --seed 44 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name gru_seed44 --results-dir results/cross_architecture/gru
  --checkpoint-dir checkpoints/cross_architecture/gru`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model gru
  --seed 44 --epsilon 0.03 --attacks both --run-name gru_seed44
  --checkpoint checkpoints/cross_architecture/gru/gru_seed44_best.pt
  --results-dir results/cross_architecture/gru`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `a3ec075` (seed-43 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
seed-42 and seed-43 GRU files were not modified.

## Clean results (no attack) — PASS clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 170 (best epoch 150).

| Metric | GRU seed 44 | GRU seed 43 (ref) | GRU seed 42 (ref) |
|---|---|---|---|
| Accuracy | 0.932 | 0.904 | 0.904 |
| Macro-F1 | 0.910 | 0.875 | 0.882 |
| Fall recall | 0.911 | 0.911 | 0.933 |
| Fall precision | 0.932 | 0.911 | 0.955 |
| Missed-fall rate | 0.089 | 0.089 | 0.067 |
| False-fall alarms (FP) | 3 | 4 | 2 |
| TP/FN/FP/TN | 41/4/3/452 | 41/4/4/451 | 42/3/2/453 |

**Clean-gate decision: PASS.** GRU seed 44 converged to a non-trivial 7-class
classifier (normal early-stopping, best epoch 150; per-class recall spread across
all seven classes 0.77–0.98 — not a diverged or single-class predictor) with
clean fall recall 0.911. Clean accuracy 0.932 is the strongest of the three GRU
seeds. Far from the non-converged failure mode (cf. the excluded ResNet seed 45:
clean accuracy 0.294, clean fall recall 0.000, best epoch 1). Seed 44 is therefore
**clean-qualified** by the same rule applied to seeds 42/43 and the ResNet18
multi-seed seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.148 | 0.098 | 0/45/36/419 | 36 |
| PGD ε=0.03  | 0.000 | 0.018 | 0.009 | 0/45/45/410 | 45 |

Under matched attacks at ε=0.03, GRU seed 44 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000) — the strongest collapse of
the three GRU seeds (seed 42 / seed 43 FGSM@0.03 fall recall were 0.000 / 0.022;
all three GRU seeds reach 0.000 PGD@0.03). Multiclass accuracy falls from 0.932
clean to 0.148 (FGSM) / 0.018 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 44) | 0.005 | 0.0075 | 0.020 |
| PGD  (seed 44) | 0.0025 | 0.0075 | 0.015 |
| FGSM (seed 43, ref) | 0.0025 | 0.0075 | 0.035 |
| PGD  (seed 43, ref) | 0.0025 | 0.0075 | 0.025 |
| FGSM (seed 42, ref) | 0.005 | 0.010 | 0.020 |
| PGD  (seed 42, ref) | 0.005 | 0.0075 | 0.015 |

(Clean fall recall used for the drop threshold = 0.911.) PGD drives fall recall to
exactly 0.000 by ε ≤ 0.015; FGSM by ε ≤ 0.020. Thresholds are within ordinary
seed-to-seed variation of seeds 42/43.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/gru/gru_seed44_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/gru/gru_seed_convergence_status.csv`
  (GRU cross-architecture seed status; seeds 42 + 43 + 44, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/gru/gru_seed44_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for GRU seeds 42/43 and is comparison-only. The GRU clean
  references actually used in every metric row (clean_accuracy 0.932,
  clean_fall_recall 0.911) are computed live from the loaded GRU checkpoint and
  are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This adds a **third clean-qualified GRU seed (44)** to seeds 42/43. GRU now has
  **3/3 clean-qualified seeds collapsing to 0.000 PGD fall recall at ε=0.03**
  (seed 44 additionally reaches 0.000 FGSM fall recall at ε=0.03). This is *not
  yet* full five-seed reliability — only LeNet has that (Priority 1, seeds 42–46).
  BiLSTM and Transformer remain seed-42 pilots.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the seed-43 note
  (`notes/priority2_gru_seed43_cross_architecture.md`) for the full protocol.
