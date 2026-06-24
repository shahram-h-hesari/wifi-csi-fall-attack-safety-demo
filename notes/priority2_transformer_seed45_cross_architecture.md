# Priority 2 — Transformer Seed 45 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for the attention-based **Transformer (ViT)** architecture,
**seed 45**, extending the Priority 2 cross-architecture study from Transformer
seeds 42/43/44 to a fourth seed. Run under the **same fixed protocol** as
Transformer seeds 42–44 and the other cross-architecture seeds — same
UT-HAR/SenseFi pipeline, same 500-window test split (45 fall / 455 non-fall), same
preprocessing, same fall/non-fall mapping, same 18-point epsilon grid, same
FGSM/PGD settings, same safety-proxy metric scripts, same `--model transformer`
factory entry (`UT_HAR_ViT`). No methodology, hyperparameter, or protocol change
was made for this seed.

This is the third of the remaining Transformer seeds being completed one by one
(43, 44 done; **45 done here**; 46 remains). ResNet18 seed 47 is intentionally
deferred and is unrelated to this run.

> **Headline nuance (read before quoting):** unlike Transformer seeds 42–44 (which
> all reach exactly 0.000 fall recall under both attacks at ε=0.03), **seed 45 does
> NOT reach 0.000 under FGSM at ε=0.03** — FGSM@0.03 fall recall = 0.022 (1/45
> retained). **PGD@0.03 does reach exactly 0.000.** Seed 45's FGSM fall recall
> reaches exactly 0.000 only at ε=0.040. This mirrors the BiLSTM seed-45
> FGSM-tolerance pattern and must be reported precisely.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model transformer
  --seed 45 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name transformer_seed45 --results-dir results/cross_architecture/transformer
  --checkpoint-dir checkpoints/cross_architecture/transformer`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model transformer
  --seed 45 --epsilon 0.03 --attacks both --run-name transformer_seed45
  --checkpoint checkpoints/cross_architecture/transformer/transformer_seed45_best.pt
  --results-dir results/cross_architecture/transformer`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep` instead of
  `--epsilon 0.03`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit
`15fd8724`, repo commit `60cdea2` (Transformer seed-44 HEAD at run time), branch
`feature/converged-clean-baseline`. Checkpoints are git-ignored (local only);
Transformer seed-42/43/44 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 117 (best epoch 97).

| Metric | seed 45 | seed 44 (ref) | seed 43 (ref) | seed 42 (ref) |
|---|---|---|---|---|
| Accuracy | 0.936 | 0.940 | 0.788 | 0.918 |
| Macro-F1 | 0.915 | 0.920 | 0.756 | 0.895 |
| Fall recall | 0.978 | 0.978 | 0.933 | 0.978 |
| Fall precision | 0.917 | 0.957 | 0.808 | 0.978 |
| Missed-fall rate | 0.022 | 0.022 | 0.067 | 0.022 |
| False-fall alarms (FP) | 4 | 2 | 10 | 1 |
| TP/FN/FP/TN | 44/1/4/451 | 44/1/2/453 | 42/3/10/445 | 44/1/1/454 |

Per-class recall (seed 45): lie down 0.864, fall 0.978, walk 0.959, pickup 0.960,
run 0.975, sit down 0.775, stand up 0.935. Validation at the selected checkpoint:
macro-F1 0.951, accuracy 0.964, loss 0.124.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful (0.978 — 44/45 falls caught), not 0.
- Macro-F1 is meaningful (0.915), not a degenerate value.
- Predictions are distributed across **all seven classes** (per-class recall
  0.78–0.98); the model is **not** a single-class / walk-only / trivial predictor.
- Training converged cleanly: early-stopped at epoch 117 (best 97), validation
  loss 0.124, no numerical divergence.

Seed 45 is a strong Transformer clean classifier (accuracy 0.936, second only to
seed 44) and is **clean-qualified** by the same rule applied to seeds 42–44 and the
GRU/BiLSTM/ResNet seeds. The seed-value-45 divergence seen for ResNet18 does **not**
reproduce here (nor for GRU/BiLSTM).

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.022 | 0.002 | 0.003 | 1/44/48/407 | 48 |
| PGD ε=0.03  | 0.000 | 0.000 | 0.000 | 0/45/49/406 | 49 |

At matched ε=0.03, **PGD drives fall recall to exactly 0.000** (and multiclass
accuracy to 0.000), but **FGSM retains a residual 0.022 fall recall** (1/45 falls
caught) — seed 45 does **not** reach exactly 0.000 under FGSM at ε=0.03. Multiclass
accuracy is near-zero under both (FGSM 0.002, PGD 0.000); false-fall alarms inflate
to 48 / 49.

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | drop ≥ 0.10 from clean | recall < 0.50 | recall = 0 |
|---|---|---|---|
| FGSM (seed 45) | 0.005 | 0.0125 | 0.040 |
| PGD  (seed 45) | 0.005 | 0.010 | 0.030 |
| FGSM (seed 44, ref) | 0.005 | 0.0075 | 0.030 |
| PGD  (seed 44, ref) | 0.005 | 0.0075 | 0.025 |

(Clean fall recall used for the drop threshold = 0.978.) Both thresholds are
concrete (not null), but seed 45 is more FGSM-tolerant than seeds 42–44: its FGSM
fall recall holds one stubborn true positive (recall 0.022) across ε=0.025–0.035
and reaches exactly 0.000 only at **ε=0.040** (verified from the full FGSM sweep:
fall recall decreases monotonically and stays 0.000 for ε ≥ 0.040). PGD reaches
exactly 0.000 by **ε=0.030**. Both attacks drop fall recall below 0.50 by ε ≈
0.010–0.0125.

## Generated package files
Raw per-seed results (28 files), `results/cross_architecture/transformer/transformer_seed45_*`:
- Clean: `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json` (+ `..._legacy_eval_*`).
- Matched ε=0.03: `..._fgsm_safety_metrics_test_epsilon_0_03.csv`,
  `..._pgd_safety_metrics_test_epsilon_0_03.csv`, paired prediction CSVs,
  `..._attacks_metadata.json` (+ legacy splits).
- Sweep: `..._fgsm_epsilon_sweep_test.csv`, `..._pgd_epsilon_sweep_test.csv`,
  sweep prediction CSVs, `..._sweep_metadata.json` (+ legacy splits).
- Tracker (updated): `results/cross_architecture/transformer/transformer_seed_convergence_status.csv`
  (Transformer cross-architecture seed status; seeds 42 + 43 + 44 + 45, all clean-qualified).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/transformer/transformer_seed45_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (the attack script reads
  `results/converged_baseline/converged_seed42_*` for that field); this is the
  same behavior recorded for Transformer seeds 42–44 and the GRU/BiLSTM seeds, and
  is comparison-only. The Transformer clean references actually used in every
  metric row (clean_accuracy 0.936, clean_fall_recall 0.978) are computed live from
  the loaded ViT checkpoint and are correct.
- "legacy" (val+test, 996-window) rows are a comparison-only pool for prior
  thesis artifacts; they are never used for training or selection.
- The ViT is substantially slower than the other architectures (Stage 1 ≈ 39 min,
  Stage 2 sweep ≈ 22 min on CPU); this is a wall-clock property only and does not
  affect correctness.

## Limitations & wording
- This adds a **fourth clean-qualified Transformer seed (45)** to seeds 42/43/44;
  **Transformer now has 4 clean-qualified seeds (42, 43, 44, 45)**. Seed 46 remains
  before a full five-seed Transformer result.
- **Do NOT state that all four Transformer seeds reach 0.000 at ε=0.03.** Precise:
  at ε=0.03, **PGD reaches exactly 0.000 in all 4/4** clean-qualified seeds, but
  **FGSM reaches exactly 0.000 in only 3/4** (seeds 42, 43, 44); **seed 45 retains
  FGSM@0.03 fall recall 0.022** and reaches exact FGSM zero only at ε=0.040. All
  four seeds reach exactly 0.000 fall recall under both attacks by ε ≤ 0.040.
- Only LeNet, GRU, and BiLSTM currently have full five-seed evidence; ResNet18 has
  a four-seed clean-qualified result.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations. The attention/ViT model is an attention-based temporal robustness
  baseline, **not** a clinical or biomarker model; attention weights are not
  exposed or interpreted.
- See [[project_overview]], the seed-42 pilot note
  (`notes/priority2_seed42_cross_architecture_pilot.md`), and the Transformer
  seed-43/44 notes for the full protocol.
