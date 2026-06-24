# Priority 2 — Transformer Seed 43 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the attention-based **Transformer (ViT)** architecture,
**seed 43**, extending the Priority 2 cross-architecture study from the original
Transformer seed-42 pilot to a second seed. Run under the **same fixed protocol**
as Transformer seed 42 and the other cross-architecture seeds — same
UT-HAR/SenseFi pipeline, same 500-window test split (45 fall / 455 non-fall), same
preprocessing, same fall/non-fall mapping, same 18-point epsilon grid, same
FGSM/PGD settings, same safety-proxy metric scripts, same `--model transformer`
factory entry (`UT_HAR_ViT`). No methodology, hyperparameter, or protocol change
was made for this seed.

This is the first of the remaining Transformer seeds being completed one by one
(43 done here; 44, 45, 46 remain). ResNet18 seed 47 is intentionally deferred and
is unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model transformer
  --seed 43 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name transformer_seed43 --results-dir results/cross_architecture/transformer
  --checkpoint-dir checkpoints/cross_architecture/transformer`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model transformer
  --seed 43 --epsilon 0.03 --attacks both --run-name transformer_seed43
  --checkpoint checkpoints/cross_architecture/transformer/transformer_seed43_best.pt
  --results-dir results/cross_architecture/transformer`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `41d9187` (HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
Transformer seed-42 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 47 (best epoch 27).

| Metric | Transformer seed 43 | Transformer seed 42 (ref) |
|---|---|---|
| Accuracy | 0.788 | 0.918 |
| Macro-F1 | 0.756 | 0.895 |
| Fall recall | 0.933 | 0.978 |
| Fall precision | 0.808 | 0.978 |
| Missed-fall rate | 0.067 | 0.022 |
| False-fall alarms (FP) | 10 | 1 |
| TP/FN/FP/TN | 42/3/10/445 | 44/1/1/454 |

Per-class recall (seed 43): lie down 0.773, fall 0.933, walk 0.830, pickup 0.760,
run 0.785, sit down 0.675, stand up 0.613. Validation at the selected checkpoint:
macro-F1 0.789, accuracy 0.813, loss 0.501.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.933 — 42/45 falls caught), not 0.
- Macro-F1 is meaningful (0.756), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.61–0.93); the model is **not** a single-class / walk-only / trivial predictor
  (a walk-only collapse would give ≈0.294 accuracy; this is 0.788).
- Training converged: early-stopped at epoch 47 (best 27), validation loss 0.501,
  no numerical divergence.

Seed 43 is markedly **weaker** than the seed-42 pilot (clean accuracy 0.788 vs
0.918; it early-stopped quickly at epoch 27 to a weaker optimum) and is the
weakest Transformer clean classifier so far, but it is a clearly non-trivial
converged classifier and is **clean-qualified** by the same rule applied to the
GRU/BiLSTM/ResNet seeds.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.060 | 0.040 | 0/45/72/383 | 72 |
| PGD ε=0.03  | 0.000 | 0.008 | 0.005 | 0/45/76/379 | 76 |

Under matched attacks at ε=0.03, Transformer seed 43 **misses every one of the 45
fall windows** under both FGSM and PGD (fall recall 0.000) — i.e. it **does reach
exactly 0.000 at ε=0.03**, like the seed-42 pilot. Multiclass accuracy falls from
0.788 clean to 0.060 (FGSM) / 0.008 (PGD), and false-fall alarms inflate to 72 / 76.

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 43) | 0.0025 | 0.010 | 0.025 |
| PGD  (seed 43) | 0.0025 | 0.010 | 0.025 |

(Clean fall recall used for the drop threshold = 0.933.) Both thresholds are
concrete (not null): FGSM and PGD each reach exactly 0.000 by ε=0.025, and both are
0.000 at the matched ε=0.03 point — verified against the matched single-ε run,
which independently reports FGSM/PGD fall recall 0.000.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/transformer/transformer_seed43_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (new): `results/cross_architecture/transformer/transformer_seed_convergence_status.csv`
  (Transformer cross-architecture seed status; seeds 42 + 43, both clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/transformer/transformer_seed43_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for the Transformer seed-42 pilot and the GRU/BiLSTM
  seeds, and is comparison-only. The Transformer clean references actually used in
  every metric row (clean_accuracy 0.788, clean_fall_recall 0.933) are computed
  live from the loaded ViT checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.
- The ViT is substantially slower than the other architectures (Stage 1 ≈ 17 min,
  Stage 2 sweep ≈ 24 min on CPU); this is a wall-clock property only and does not
  affect correctness.

## Limitations & wording
- This adds a **second clean-qualified Transformer seed (43)** to the seed-42
  pilot; **Transformer now has 2 clean-qualified seeds (42, 43)**, both reaching
  exactly 0.000 fall recall under both FGSM and PGD at ε=0.03. This is **not yet** a
  full multi-seed (let alone five-seed) Transformer result — seeds 44, 45, 46
  remain. Only LeNet, GRU, and BiLSTM currently have full five-seed evidence;
  ResNet18 has a four-seed clean-qualified result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations. The attention/ViT model is an attention-based temporal robustness
  baseline, **not** a clinical or biomarker model; attention weights are not
  exposed or interpreted.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the GRU/BiLSTM
  per-seed notes for the full protocol.
