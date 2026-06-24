# Priority 2 — BiLSTM Seed 44 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **BiLSTM** architecture, **seed 44**,
extending the Priority 2 cross-architecture study from BiLSTM seeds 42/43 to a
third seed. Run under the **same fixed protocol** as BiLSTM seeds 42/43 and the
GRU cross-architecture seeds — same UT-HAR/SenseFi pipeline, same 500-window test
split (45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping,
same 18-point epsilon grid, same FGSM/PGD settings, same safety-proxy metric
scripts, same `--model bilstm` factory entry. No methodology, hyperparameter, or
protocol change was made for this seed.

This is the second of the remaining BiLSTM seeds being completed one by one
(43 done; **44 done here**; 45 and 46 remain). ResNet18 seed 47 is intentionally
deferred and is unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model bilstm
  --seed 44 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name bilstm_seed44 --results-dir results/cross_architecture/bilstm
  --checkpoint-dir checkpoints/cross_architecture/bilstm`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model bilstm
  --seed 44 --epsilon 0.03 --attacks both --run-name bilstm_seed44
  --checkpoint checkpoints/cross_architecture/bilstm/bilstm_seed44_best.pt
  --results-dir results/cross_architecture/bilstm`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `107b7e6` (BiLSTM seed-43 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
BiLSTM seed-42 and seed-43 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; **early-stopped at epoch 171 (best epoch 151)** — unlike
seeds 42/43, this seed early-stopped, which is also healthy behavior.

| Metric | BiLSTM seed 44 | seed 43 (ref) | seed 42 (ref) |
|---|---|---|---|
| Accuracy | 0.878 | 0.830 | 0.814 |
| Macro-F1 | 0.841 | 0.781 | 0.769 |
| Fall recall | 0.911 | 0.822 | 0.889 |
| Fall precision | 0.932 | 0.881 | 0.851 |
| Missed-fall rate | 0.089 | 0.178 | 0.111 |
| False-fall alarms (FP) | 3 | 5 | 7 |
| TP/FN/FP/TN | 41/4/3/452 | 37/8/5/450 | 40/5/7/448 |

Per-class recall (seed 44): lie down 0.758, fall 0.911, walk 0.925, pickup 0.840,
run 0.983, sit down 0.800, stand up 0.613. Validation at the selected checkpoint:
macro-F1 0.876, accuracy 0.895, loss 0.335.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.911 — 41/45 falls caught), not 0.
- Macro-F1 is meaningful (0.841), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.61–0.98); the model is **not** a single-class / walk-only / trivial predictor.
- Training is healthy: early-stopped at epoch 171 (best 151), validation loss
  0.335, no numerical divergence.

Seed 44 is the **strongest BiLSTM clean classifier so far** (accuracy 0.878,
macro-F1 0.841) and is **clean-qualified** by the same rule applied to seeds
42/43 and the GRU/ResNet seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.088 | 0.072 | 0/45/33/422 | 33 |
| PGD ε=0.03  | 0.000 | 0.018 | 0.010 | 0/45/46/409 | 46 |

Under matched attacks at ε=0.03, BiLSTM seed 44 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000), reproducing the seed-42/43
BiLSTM result. Multiclass accuracy falls from 0.878 clean to 0.088 (FGSM) / 0.018
(PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 44) | 0.005 | 0.0075 | 0.030 |
| PGD  (seed 44) | 0.0025 | 0.0075 | 0.025 |
| FGSM (seed 43, ref) | 0.005 | 0.0075 | 0.0175 |
| PGD  (seed 43, ref) | 0.005 | 0.0075 | 0.015 |
| FGSM (seed 42, ref) | 0.0075 | 0.0175 | 0.0175 |
| PGD  (seed 42, ref) | 0.0075 | 0.015 | 0.0175 |

(Clean fall recall used for the drop threshold = 0.911.) Both attacks reach 0.000
fall recall by ε ≤ 0.030. Seed 44's stronger clean margin pushes its FGSM zero
threshold slightly higher (0.030) than seeds 42/43; PGD still reaches 0.000 by
ε ≤ 0.025. All within ordinary seed-to-seed variation.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/bilstm/bilstm_seed44_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/bilstm/bilstm_seed_convergence_status.csv`
  (BiLSTM cross-architecture seed status; seeds 42 + 43 + 44, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/bilstm/bilstm_seed44_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for BiLSTM seeds 42/43 and the GRU seeds, and is
  comparison-only. The BiLSTM clean references actually used in every metric row
  (clean_accuracy 0.878, clean_fall_recall 0.911) are computed live from the
  loaded BiLSTM checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This adds a **third clean-qualified BiLSTM seed (44)** to seeds 42/43;
  **BiLSTM now has 3 clean-qualified seeds (42, 43, 44)**, all collapsing to 0.000
  fall recall under matched PGD (and FGSM) at ε=0.03. This is **not yet** a full
  five-seed BiLSTM result — seeds 45 and 46 remain. Only LeNet and GRU currently
  have full five-seed evidence; ResNet18 has a four-seed clean-qualified result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the BiLSTM seed-43
  note (`notes/priority2_bilstm_seed43_cross_architecture.md`) for the full protocol.
