# Priority 2 — GRU Seed 45 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **GRU** architecture, **seed 45**, extending
the Priority 2 cross-architecture study from seeds 42/43/44 to a fourth seed. Run
under the **same fixed protocol** as the prior GRU seeds and the other
architectures — same UT-HAR/SenseFi pipeline, same 500-window test split
(45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping, same
18-point epsilon grid, same FGSM/PGD settings, same safety-proxy metric scripts,
same `--model gru` factory entry. No methodology, hyperparameter, or protocol
change was made for this seed.

> **Seed-45 caution resolved.** Seed 45 was the seed that *diverged* for ResNet18
> (val loss ~10¹⁵, walk-only predictor, clean fall recall 0.000 — excluded as
> non-converged; see `notes/priority2_resnet_seed45_nonconverged.md`). The clean
> gate was therefore applied **strictly** here. **GRU seed 45 trained cleanly and
> PASSES** — the ResNet18 seed-45 divergence does not reproduce for the GRU.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model gru
  --seed 45 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name gru_seed45 --results-dir results/cross_architecture/gru
  --checkpoint-dir checkpoints/cross_architecture/gru`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model gru
  --seed 45 --epsilon 0.03 --attacks both --run-name gru_seed45
  --checkpoint checkpoints/cross_architecture/gru/gru_seed45_best.pt
  --results-dir results/cross_architecture/gru`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `ad7fcb7` (seed-44 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
seed-42/43/44 GRU files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 144 (best epoch 124).

| Metric | GRU seed 45 | seed 44 (ref) | seed 43 (ref) | seed 42 (ref) |
|---|---|---|---|---|
| Accuracy | 0.920 | 0.932 | 0.904 | 0.904 |
| Macro-F1 | 0.892 | 0.910 | 0.875 | 0.882 |
| Fall recall | 0.933 | 0.911 | 0.911 | 0.933 |
| Fall precision | 0.875 | 0.932 | 0.911 | 0.955 |
| Missed-fall rate | 0.067 | 0.089 | 0.089 | 0.067 |
| False-fall alarms (FP) | 6 | 3 | 4 | 2 |
| TP/FN/FP/TN | 42/3/6/449 | 41/4/3/452 | 41/4/4/451 | 42/3/2/453 |

Per-class recall (seed 45): lie down 0.879, fall 0.933, walk 0.980, pickup 0.940,
run 0.950, sit down 0.800, stand up 0.710. Validation at the selected checkpoint:
macro-F1 0.927, accuracy 0.935, loss 0.190.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.933 — joint-highest among the GRU seeds), not 0.
- Macro-F1 is meaningful (0.892), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.71–0.98); the model is **not** a single-class / trivial predictor.
- Training converged normally: early-stopped at epoch 144 (best epoch 124),
  healthy validation loss (0.190), no numerical divergence.

Contrast with the excluded ResNet18 seed 45 (clean accuracy 0.294, clean fall
recall 0.000, best epoch 1, val loss ~10¹⁵). GRU seed 45 is therefore
**clean-qualified** by the same rule applied to seeds 42/43/44.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.022 | 0.166 | 0.106 | 1/44/34/421 | 34 |
| PGD ε=0.03  | 0.000 | 0.006 | 0.004 | 0/45/45/410 | 45 |

Under matched PGD at ε=0.03, GRU seed 45 **misses every one of the 45 fall
windows** (fall recall 0.000), consistent with seeds 42/43/44. FGSM at ε=0.03
collapses fall recall to 0.022 (1/45 falls caught). Multiclass accuracy falls from
0.920 clean to 0.166 (FGSM) / 0.006 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 45) | 0.0075 | 0.0125 | 0.045 |
| PGD  (seed 45) | 0.005 | 0.0075 | 0.025 |
| FGSM (seed 44, ref) | 0.005 | 0.0075 | 0.020 |
| PGD  (seed 44, ref) | 0.0025 | 0.0075 | 0.015 |
| FGSM (seed 43, ref) | 0.0025 | 0.0075 | 0.035 |
| PGD  (seed 43, ref) | 0.0025 | 0.0075 | 0.025 |
| FGSM (seed 42, ref) | 0.005 | 0.010 | 0.020 |
| PGD  (seed 42, ref) | 0.005 | 0.0075 | 0.015 |

(Clean fall recall used for the drop threshold = 0.933.) PGD drives fall recall to
exactly 0.000 by ε ≤ 0.025; FGSM by ε ≤ 0.045. Seed 45 is the most FGSM-tolerant
of the four GRU seeds (FGSM reaches 0.000 only at ε=0.045) but is still fully
broken by PGD by ε ≤ 0.025. Thresholds are within ordinary seed-to-seed variation.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/gru/gru_seed45_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/gru/gru_seed_convergence_status.csv`
  (GRU cross-architecture seed status; seeds 42 + 43 + 44 + 45, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/gru/gru_seed45_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for GRU seeds 42/43/44 and is comparison-only. The GRU
  clean references actually used in every metric row (clean_accuracy 0.920,
  clean_fall_recall 0.933) are computed live from the loaded GRU checkpoint and
  are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This adds a **fourth clean-qualified GRU seed (45)** to seeds 42/43/44. GRU now
  has **4/4 clean-qualified seeds collapsing to 0.000 PGD fall recall at ε=0.03**.
  This is *not yet* full five-seed reliability — only LeNet has that (Priority 1,
  seeds 42–46). BiLSTM and Transformer remain seed-42 pilots.
- Note that "seed 45" is architecture-specific: it diverged for ResNet18
  (excluded) but converges cleanly for the GRU. The non-convergence was a
  ResNet18/optimizer interaction, not a property of the seed value itself.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the seed-43/44 notes
  for the full protocol.
