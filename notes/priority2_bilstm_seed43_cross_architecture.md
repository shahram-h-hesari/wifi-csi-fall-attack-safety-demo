# Priority 2 — BiLSTM Seed 43 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the recurrent **BiLSTM** architecture, **seed 43**,
extending the Priority 2 cross-architecture study from the original BiLSTM seed-42
pilot to a second seed. Run under the **same fixed protocol** as BiLSTM seed 42
and the GRU cross-architecture seeds — same UT-HAR/SenseFi pipeline, same
500-window test split (45 fall / 455 non-fall), same preprocessing, same
fall/non-fall mapping, same 18-point epsilon grid, same FGSM/PGD settings, same
safety-proxy metric scripts, same `--model bilstm` factory entry. No methodology,
hyperparameter, or protocol change was made for this seed.

This is the **first of the remaining BiLSTM seeds (43, then 44, 45, 46)** being
completed one by one toward a future multi-seed BiLSTM set. ResNet18 seed 47 is
intentionally deferred and is unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model bilstm
  --seed 43 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name bilstm_seed43 --results-dir results/cross_architecture/bilstm
  --checkpoint-dir checkpoints/cross_architecture/bilstm`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model bilstm
  --seed 43 --epsilon 0.03 --attacks both --run-name bilstm_seed43
  --checkpoint checkpoints/cross_architecture/bilstm/bilstm_seed43_best.pt
  --results-dir results/cross_architecture/bilstm`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `5cb9cf9` (HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
BiLSTM seed-42 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; ran the full 200-epoch budget (best epoch 196, no early stop
— the same expected BiLSTM behavior as seed 42).

| Metric | BiLSTM seed 43 | BiLSTM seed 42 (ref) |
|---|---|---|
| Accuracy | 0.830 | 0.814 |
| Macro-F1 | 0.781 | 0.769 |
| Fall recall | 0.822 | 0.889 |
| Fall precision | 0.881 | 0.851 |
| Missed-fall rate | 0.178 | 0.111 |
| False-fall alarms (FP) | 5 | 7 |
| TP/FN/FP/TN | 37/8/5/450 | 40/5/7/448 |

Per-class recall (seed 43): lie down 0.712, fall 0.822, walk 0.905, pickup 0.760,
run 0.950, sit down 0.725, stand up 0.516. Validation at the selected checkpoint:
macro-F1 0.828, accuracy 0.855, loss 0.400.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.822 — 37/45 falls caught), not 0.
- Macro-F1 is meaningful (0.781), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.52–0.95); the model is **not** a single-class / walk-only / trivial predictor.
- Training is healthy: validation loss 0.400, no numerical divergence. BiLSTM uses
  the full 200-epoch budget without early-stopping (best epoch 196) — this is the
  **same expected behavior as the seed-42 pilot**, not a training failure.

Seed 43 is marginally stronger than the seed-42 pilot on accuracy/macro-F1 and is
**clean-qualified** by the same rule applied to the GRU/ResNet seeds. BiLSTM
remains the weakest clean classifier of the cross-architecture families, as
already noted in the pilot.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.130 | 0.103 | 0/45/38/417 | 38 |
| PGD ε=0.03  | 0.000 | 0.032 | 0.029 | 0/45/53/402 | 53 |

Under matched attacks at ε=0.03, BiLSTM seed 43 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000), reproducing the seed-42
BiLSTM result. Multiclass accuracy falls from 0.830 clean to 0.130 (FGSM) / 0.032
(PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 43) | 0.005 | 0.0075 | 0.0175 |
| PGD  (seed 43) | 0.005 | 0.0075 | 0.015 |
| FGSM (seed 42, ref) | 0.0075 | 0.0175 | 0.0175 |
| PGD  (seed 42, ref) | 0.0075 | 0.015 | 0.0175 |

(Clean fall recall used for the drop threshold = 0.822.) Both attacks reach 0.000
fall recall by ε ≤ 0.0175. BiLSTM collapses at a slightly smaller budget than the
seed-42 pilot — consistent with its weaker clean margin.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/bilstm/bilstm_seed43_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (new): `results/cross_architecture/bilstm/bilstm_seed_convergence_status.csv`
  (BiLSTM cross-architecture seed status; seeds 42 + 43, both clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/bilstm/bilstm_seed43_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for BiLSTM seed 42 and the GRU seeds, and is
  comparison-only. The BiLSTM clean references actually used in every metric row
  (clean_accuracy 0.830, clean_fall_recall 0.822) are computed live from the
  loaded BiLSTM checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.

## Limitations & wording
- This adds a **second clean-qualified BiLSTM seed (43)** to the seed-42 pilot;
  **BiLSTM now has 2 clean-qualified seeds (42, 43)**, both collapsing to 0.000
  fall recall under matched PGD (and FGSM) at ε=0.03. This is **not yet** a full
  multi-seed BiLSTM result — seeds 44, 45, 46 remain to be run before BiLSTM can
  be reported as a multi-seed (let alone five-seed) family. Only LeNet and GRU
  currently have full five-seed evidence; ResNet18 has a four-seed clean-qualified
  result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the GRU per-seed
  notes for the full protocol.
