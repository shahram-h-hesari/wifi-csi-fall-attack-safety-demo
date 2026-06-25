# Priority 2 — Transformer Seed 46 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the attention-based **Transformer (ViT)** architecture,
**seed 46** — the fifth and final seed of the planned Transformer cross-architecture
set (42–46). Run under the **same fixed protocol** as Transformer seeds 42–45 and
the other cross-architecture seeds — same UT-HAR/SenseFi pipeline, same 500-window
test split (45 fall / 455 non-fall), same preprocessing, same fall/non-fall
mapping, same 18-point epsilon grid, same FGSM/PGD settings, same safety-proxy
metric scripts, same `--model transformer` factory entry (`UT_HAR_ViT`). No
methodology, hyperparameter, or protocol change was made for this seed.

With seed 46 clean-qualified, **the Transformer five-seed set (42–46) is complete.**
ResNet18 seed 47 remains intentionally deferred and is unrelated to this run.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model transformer
  --seed 46 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name transformer_seed46 --results-dir results/cross_architecture/transformer
  --checkpoint-dir checkpoints/cross_architecture/transformer`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model transformer
  --seed 46 --epsilon 0.03 --attacks both --run-name transformer_seed46
  --checkpoint checkpoints/cross_architecture/transformer/transformer_seed46_best.pt
  --results-dir results/cross_architecture/transformer`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `5ef971b` (Transformer seed-45 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
Transformer seed-42/43/44/45 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 59 (best epoch 39).

| Metric | seed 46 | seed 45 | seed 44 | seed 43 | seed 42 |
|---|---|---|---|---|---|
| Accuracy | 0.820 | 0.936 | 0.940 | 0.788 | 0.918 |
| Macro-F1 | 0.786 | 0.915 | 0.920 | 0.756 | 0.895 |
| Fall recall | 0.867 | 0.978 | 0.978 | 0.933 | 0.978 |
| Fall precision | 0.907 | 0.917 | 0.957 | 0.808 | 0.978 |
| Missed-fall rate | 0.133 | 0.022 | 0.022 | 0.067 | 0.022 |
| False-fall alarms (FP) | 4 | 4 | 2 | 10 | 1 |
| TP/FN/FP/TN | 39/6/4/451 | 44/1/4/451 | 44/1/2/453 | 42/3/10/445 | 44/1/1/454 |

Per-class recall (seed 46): lie down 0.667, fall 0.867, walk 0.884, pickup 0.760,
run 0.893, sit down 0.750, stand up 0.677. Validation at the selected checkpoint:
macro-F1 0.849, accuracy 0.863, loss 0.426.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.867 — 39/45 falls caught), not 0.
- Macro-F1 is meaningful (0.786), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.67–0.89); the model is **not** a single-class / walk-only / trivial predictor.
- Training converged: early-stopped at epoch 59 (best 39), validation loss 0.426,
  no numerical divergence.

Seed 46 is one of the weaker Transformer clean classifiers (accuracy 0.820, similar
to seed 43) but a clearly non-trivial converged classifier, and is
**clean-qualified** by the same rule applied to seeds 42–45.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.030 | 0.032 | 0/45/48/407 | 48 |
| PGD ε=0.03  | 0.000 | 0.006 | 0.005 | 0/45/49/406 | 49 |

Under matched attacks at ε=0.03, Transformer seed 46 **misses every one of the 45
fall windows** under both FGSM and PGD (fall recall 0.000) — i.e. it **does reach
exactly 0.000 at ε=0.03** under both attacks, like seeds 42/43/44 (and unlike the
FGSM-tolerant seed 45). Multiclass accuracy falls from 0.820 clean to 0.030 (FGSM)
/ 0.006 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 46) | 0.0025 | 0.0075 | 0.0175 |
| PGD  (seed 46) | 0.0025 | 0.0075 | 0.015 |

(Clean fall recall used for the drop threshold = 0.867.) Both thresholds are
concrete (not null): FGSM reaches exactly 0.000 by ε=0.0175 and PGD by ε=0.015, and
both are 0.000 at the matched ε=0.03 point — verified against the matched single-ε
run, which independently reports FGSM/PGD fall recall 0.000. Seed 46 is the
**fastest-collapsing** Transformer seed (lowest recall=0 thresholds), consistent
with its weaker clean margin.

## Five-seed Transformer summary (42–46, all clean-qualified)
| Seed | Clean acc | Clean fall recall | FGSM@0.03 recall | PGD@0.03 recall | FGSM recall=0 ε | PGD recall=0 ε |
|---|---|---|---|---|---|---|
| 42 | 0.918 | 0.978 | 0.000 | 0.000 | 0.030 | 0.025 |
| 43 | 0.788 | 0.933 | 0.000 | 0.000 | 0.025 | 0.025 |
| 44 | 0.940 | 0.978 | 0.000 | 0.000 | 0.030 | 0.025 |
| 45 | 0.936 | 0.978 | **0.022** | 0.000 | 0.040 | 0.030 |
| 46 | 0.820 | 0.867 | 0.000 | 0.000 | 0.0175 | 0.015 |

**Precise wording (use this, do not over-round):**
- **PGD reaches exactly 0.000 fall recall at ε=0.03 in all 5/5** clean-qualified
  Transformer seeds.
- **FGSM reaches exactly 0.000 fall recall at ε=0.03 in 4/5** seeds (42, 43, 44,
  46); **seed 45 is the exception** (FGSM@0.03 = 0.022, one residual true positive)
  and reaches exact FGSM zero only at ε=0.040.
- **All 5/5 seeds reach exactly 0.000 fall recall under both attacks within the
  grid** (FGSM by ε ≤ 0.040, PGD by ε ≤ 0.030). PGD is the more consistent
  worst-case attack (5/5 exact at ε=0.03; tighter recall=0 thresholds).

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/transformer/transformer_seed46_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/transformer/transformer_seed_convergence_status.csv`
  (Transformer cross-architecture seed status; seeds 42–46, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/transformer/transformer_seed46_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for Transformer seeds 42–45 and the GRU/BiLSTM seeds, and
  is comparison-only. The Transformer clean references actually used in every
  metric row (clean_accuracy 0.820, clean_fall_recall 0.867) are computed live from
  the loaded ViT checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.
- The ViT is substantially slower than the other architectures (Stage 1 ≈ 23 min,
  Stage 2 sweep ≈ 25 min on CPU); this is a wall-clock property only and does not
  affect correctness.

## Limitations & wording
- This completes a **full five-seed clean-qualified Transformer set (42–46)**.
  However, Transformer's adversarial behavior at ε=0.03 is **not** uniformly total
  under FGSM: **PGD reaches exactly 0.000 fall recall at ε=0.03 in 5/5 seeds, but
  FGSM in only 4/5** (seed 45 retains 0.022). The thesis-safe statement is: *all
  five clean-qualified Transformer seeds show severe adversarial fall-recall
  degradation at ε=0.03, with PGD reaching exactly 0.000 in 5/5 seeds and FGSM in
  4/5; all five reach exactly 0.000 under both attacks within the sweep grid (FGSM
  by ε ≤ 0.040, PGD by ε ≤ 0.030).* Do **not** state "all five collapse to 0.000
  at ε=0.03" without the FGSM/PGD distinction.
- LeNet, GRU, and BiLSTM also have full five-seed evidence; ResNet18 has a
  four-seed clean-qualified result. Both BiLSTM and Transformer have a seed-45
  FGSM-tolerance exception at ε=0.03 (PGD remains the consistent worst case for
  both).
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations. The attention/ViT model is an attention-based temporal robustness
  baseline, **not** a clinical or biomarker model; attention weights are not
  exposed or interpreted.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the Transformer
  seed-43/44/45 notes for the full protocol.
