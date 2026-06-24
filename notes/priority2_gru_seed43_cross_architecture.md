# Priority 2 — GRU Seed 43 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **GRU** architecture, **seed 43**, extending
the Priority 2 cross-architecture study from the original seed-42 pilot to a
second seed. Run under the **same fixed protocol** as GRU seed 42 and the other
architectures — same UT-HAR/SenseFi pipeline, same 500-window test split
(45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping, same
18-point epsilon grid, same FGSM/PGD settings, same safety-proxy metric scripts,
same `--model gru` factory entry. No methodology, hyperparameter, or protocol
change was made for this seed.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model gru
  --seed 43 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name gru_seed43 --results-dir results/cross_architecture/gru
  --checkpoint-dir checkpoints/cross_architecture/gru`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model gru
  --seed 43 --epsilon 0.03 --attacks both --run-name gru_seed43
  --checkpoint checkpoints/cross_architecture/gru/gru_seed43_best.pt
  --results-dir results/cross_architecture/gru`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `f8d57bb`, branch `feature/converged-clean-baseline`.
Checkpoints are git-ignored (local only); seed-42 GRU files were not modified.

## Clean results (no attack) — PASS clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 171 (best epoch 151).

| Metric | GRU seed 43 | GRU seed 42 (reference) |
|---|---|---|
| Accuracy | 0.904 | 0.904 |
| Macro-F1 | 0.875 | 0.882 |
| Fall recall | 0.911 | 0.933 |
| Fall precision | 0.911 | 0.955 |
| Missed-fall rate | 0.089 | 0.067 |
| False-fall alarms (FP) | 4 | 2 |
| TP/FN/FP/TN | 41/4/4/451 | 42/3/2/453 |

**Clean-gate decision: PASS.** GRU seed 43 converged to a non-trivial 7-class
classifier (normal early-stopping, best epoch 151; not a diverged or single-class
predictor) with clean fall recall 0.911 — comparable to seed 42 (0.933) and far
from the non-converged failure mode (cf. the excluded ResNet seed 45: clean
accuracy 0.294, clean fall recall 0.000, best epoch 1). Seed 43 is therefore
**clean-qualified** by the same rule applied to the ResNet18 multi-seed seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.022 | 0.174 | 0.159 | 1/44/38/417 | 38 |
| PGD ε=0.03  | 0.000 | 0.020 | 0.020 | 0/45/49/406 | 49 |

Under matched PGD at ε=0.03, GRU seed 43 **misses every one of the 45 fall
windows** (fall recall 0.000), reproducing the seed-42 GRU result (PGD ε=0.03 fall
recall 0.000). FGSM at ε=0.03 collapses fall recall to 0.022 (1/45 falls caught).
Multiclass accuracy falls from 0.904 clean to 0.174 (FGSM) / 0.020 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 43) | 0.0025 | 0.0075 | 0.035 |
| PGD  (seed 43) | 0.0025 | 0.0075 | 0.025 |
| FGSM (seed 42, ref) | 0.005 | 0.010 | 0.020 |
| PGD  (seed 42, ref) | 0.005 | 0.0075 | 0.015 |

(Clean fall recall used for the drop threshold = 0.911.) PGD drives fall recall to
exactly 0.000 by ε ≤ 0.025 in both GRU seeds; FGSM reaches 0.000 by ε ≤ 0.035.
Thresholds are within ordinary seed-to-seed variation of the seed-42 pilot.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/gru/gru_seed43_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker: `results/cross_architecture/gru/gru_seed_convergence_status.csv`
  (GRU cross-architecture seed status; seeds 42 + 43, both clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/gru/gru_seed43_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for GRU seed 42 and is comparison-only. The GRU clean
  references actually used in every metric row (clean_accuracy 0.904,
  clean_fall_recall 0.911) are computed live from the loaded GRU checkpoint and
  are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This adds a **second clean-qualified GRU seed (43)** to the seed-42 GRU pilot;
  GRU now has **2/2 clean-qualified seeds collapsing to 0.000 PGD fall recall at
  ε=0.03**. This is *not yet* full five-seed reliability — only LeNet has that
  (Priority 1, seeds 42–46). BiLSTM and Transformer remain seed-42 pilots.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]] and the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`) for the full protocol.
