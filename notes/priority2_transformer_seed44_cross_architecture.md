# Priority 2 — Transformer Seed 44 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the attention-based **Transformer (ViT)** architecture,
**seed 44**, extending the Priority 2 cross-architecture study from Transformer
seeds 42/43 to a third seed. Run under the **same fixed protocol** as Transformer
seeds 42/43 and the other cross-architecture seeds — same UT-HAR/SenseFi pipeline,
same 500-window test split (45 fall / 455 non-fall), same preprocessing, same
fall/non-fall mapping, same 18-point epsilon grid, same FGSM/PGD settings, same
safety-proxy metric scripts, same `--model transformer` factory entry
(`UT_HAR_ViT`). No methodology, hyperparameter, or protocol change was made for
this seed.

This is the second of the remaining Transformer seeds being completed one by one
(43, 44 done; 45 and 46 remain). ResNet18 seed 47 is intentionally deferred and is
unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model transformer
  --seed 44 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name transformer_seed44 --results-dir results/cross_architecture/transformer
  --checkpoint-dir checkpoints/cross_architecture/transformer`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model transformer
  --seed 44 --epsilon 0.03 --attacks both --run-name transformer_seed44
  --checkpoint checkpoints/cross_architecture/transformer/transformer_seed44_best.pt
  --results-dir results/cross_architecture/transformer`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `3f0c0b2` (Transformer seed-43 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
Transformer seed-42 and seed-43 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 133 (best epoch 113).

| Metric | seed 44 | seed 43 (ref) | seed 42 (ref) |
|---|---|---|---|
| Accuracy | 0.940 | 0.788 | 0.918 |
| Macro-F1 | 0.920 | 0.756 | 0.895 |
| Fall recall | 0.978 | 0.933 | 0.978 |
| Fall precision | 0.957 | 0.808 | 0.978 |
| Missed-fall rate | 0.022 | 0.067 | 0.022 |
| False-fall alarms (FP) | 2 | 10 | 1 |
| TP/FN/FP/TN | 44/1/2/453 | 42/3/10/445 | 44/1/1/454 |

Per-class recall (seed 44): lie down 0.848, fall 0.978, walk 0.966, pickup 0.960,
run 0.983, sit down 0.750, stand up 1.000. Validation at the selected checkpoint:
macro-F1 0.957, accuracy 0.966, loss 0.122.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.978 — 44/45 falls caught), not 0.
- Macro-F1 is meaningful (0.920), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.75–1.00); the model is **not** a single-class / walk-only / trivial predictor.
- Training converged cleanly: early-stopped at epoch 133 (best 113), validation
  loss 0.122, no numerical divergence.

Seed 44 is the **strongest Transformer clean classifier so far** (accuracy 0.940,
macro-F1 0.920) and is **clean-qualified** by the same rule applied to seeds 42/43
and the GRU/BiLSTM/ResNet seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.010 | 0.005 | 0/45/30/425 | 30 |
| PGD ε=0.03  | 0.000 | 0.004 | 0.002 | 0/45/31/424 | 31 |

Under matched attacks at ε=0.03, Transformer seed 44 **misses every one of the 45
fall windows** under both FGSM and PGD (fall recall 0.000) — i.e. it **does reach
exactly 0.000 at ε=0.03**, like seeds 42/43. Multiclass accuracy falls from 0.940
clean to 0.010 (FGSM) / 0.004 (PGD) — the most severe accuracy collapse of the
three Transformer seeds, consistent with its higher clean accuracy.

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 44) | 0.005 | 0.0075 | 0.030 |
| PGD  (seed 44) | 0.005 | 0.0075 | 0.025 |
| FGSM (seed 43, ref) | 0.0025 | 0.010 | 0.025 |
| PGD  (seed 43, ref) | 0.0025 | 0.010 | 0.025 |

(Clean fall recall used for the drop threshold = 0.978.) Both thresholds are
concrete (not null): FGSM reaches exactly 0.000 by ε=0.030 and PGD by ε=0.025, and
both are 0.000 at the matched ε=0.03 point — verified against the matched single-ε
run, which independently reports FGSM/PGD fall recall 0.000.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/transformer/transformer_seed44_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/transformer/transformer_seed_convergence_status.csv`
  (Transformer cross-architecture seed status; seeds 42 + 43 + 44, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/transformer/transformer_seed44_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for Transformer seeds 42/43 and the GRU/BiLSTM seeds, and
  is comparison-only. The Transformer clean references actually used in every
  metric row (clean_accuracy 0.940, clean_fall_recall 0.978) are computed live from
  the loaded ViT checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.
- The ViT is substantially slower than the other architectures (Stage 1 ≈ 44 min,
  Stage 2 sweep ≈ 20 min on CPU); this is a wall-clock property only and does not
  affect correctness.

## Limitations & wording
- This adds a **third clean-qualified Transformer seed (44)** to seeds 42/43;
  **Transformer now has 3 clean-qualified seeds (42, 43, 44)**, all reaching
  exactly 0.000 fall recall under both FGSM and PGD at ε=0.03. This is **not yet** a
  full five-seed Transformer result — seeds 45 and 46 remain. Only LeNet, GRU, and
  BiLSTM currently have full five-seed evidence; ResNet18 has a four-seed
  clean-qualified result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations. The attention/ViT model is an attention-based temporal robustness
  baseline, **not** a clinical or biomarker model; attention weights are not
  exposed or interpreted.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the Transformer
  seed-43 note (`notes/priority2_transformer_seed43_cross_architecture.md`) for
  the full protocol.
