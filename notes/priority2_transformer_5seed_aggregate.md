# Priority 2 — Transformer (ViT) Five-Seed Aggregate (Clean-Qualified)

Thesis-ready aggregate for the attention-based **Transformer (ViT)** multi-seed
extension of the Priority 2 cross-architecture study. Built **only** from the
already-committed Transformer seed-42–46 raw result files in
`results/cross_architecture/transformer/` (no experiment rerun; no raw result file
modified). Analogous in style to the GRU and BiLSTM five-seed aggregates, with
**precise wording for the seed-45 FGSM deviation**.

## Headline (read the nuance — do NOT over-round)
- **5/5 Transformer seeds (42–46) are clean-qualified** — each a non-trivial,
  converged 7-class classifier (no divergence, no single-class predictor).
- **All five show severe adversarial window-level fall-recall degradation at
  ε=0.03.**
- **PGD at ε=0.03 reaches exactly 0.000 fall recall in 5/5 seeds** (zero variance).
- **FGSM at ε=0.03 reaches exactly 0.000 fall recall in 4/5 seeds** (42, 43, 44,
  46). **Seed 45 is the FGSM exception:** FGSM@0.03 fall recall = **0.022** (one
  residual true positive); its FGSM fall recall reaches exactly 0.000 only at
  **ε=0.040**. Seed 45 PGD@0.03 = **0.000** (PGD recall=0 at ε=0.030).
- **All 5/5 seeds reach exactly 0.000 fall recall under FGSM by ε ≤ 0.040 and under
  PGD by ε ≤ 0.030.**
- **PGD is the consistent worst-case attack** (5/5 exact at ε=0.03; tighter
  recall=0 thresholds). **Do NOT write that all five seeds reach 0.000 under FGSM
  at ε=0.03.**

This matches the BiLSTM pattern (PGD consistent across seeds; a seed-45
FGSM-tolerance exception). LeNet and GRU each show zero-variance 0.000 PGD collapse
at ε=0.03 across all five seeds.

## Methods (identical fixed protocol across all five seeds)
- Model: `UT_HAR_ViT` via the `--model transformer` factory (`scripts/model_factory.py`).
- Data: UT-HAR (SenseFi), held-out **test split n = 500** windows (**45 fall /
  455 non-fall**); fall = class index 1. Same preprocessing and fall/non-fall
  mapping as the LeNet baseline.
- Training (Stage 1): Adam, lr 1e-3, batch 64, max 200 epochs, early-stopping
  patience 20 on validation macro-F1; best checkpoint = validation-selected. (All
  five seeds early-stopped; best epochs ranged 39–113.)
- Attacks (Stage 2, frozen checkpoint): FGSM (single-step L∞) and PGD (L∞, 10
  steps, α = ε/6), no [0,1] clamp (processed CSI tensors); matched point ε=0.030;
  18-point sweep ε ∈ [0.0 … 0.075].
- Metrics: window-level fall-vs-non-fall safety proxies + multiclass accuracy/
  macro-F1 + collapse thresholds. Same metric scripts as all prior seeds/architectures.
- Aggregation: mean ± sample SD (ddof=1); 95% CI via Student-t, df=4 (t=2.776).
  All five FGSM and PGD recall=0 thresholds are in-grid (non-null), so summary
  means use all 5 seeds.

## Clean performance (per seed, test split n=500)
| Seed | Accuracy | Macro-F1 | Fall recall | Fall precision | TP/FN/FP/TN | Status |
|---|---|---|---|---|---|---|
| 42 | 0.918 | 0.895 | 0.978 | 0.978 | 44/1/1/454 | clean-qualified |
| 43 | 0.788 | 0.756 | 0.933 | 0.808 | 42/3/10/445 | clean-qualified |
| 44 | 0.940 | 0.920 | 0.978 | 0.957 | 44/1/2/453 | clean-qualified |
| 45 | 0.936 | 0.915 | 0.978 | 0.917 | 44/1/4/451 | clean-qualified |
| 46 | 0.820 | 0.786 | 0.867 | 0.907 | 39/6/4/451 | clean-qualified |
| **mean ± SD** | **0.880 ± 0.071** | **0.854 ± 0.078** | **0.947 ± 0.049** | **0.913 ± 0.066** | — | 5/5 |

## Fixed ε=0.03 attack performance (per seed, test split n=500)
| Seed | FGSM recall | FGSM acc | FGSM macF1 | FGSM TP/FN/FP/TN | PGD recall | PGD acc | PGD macF1 | PGD TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| 42 | 0.000 | 0.008 | 0.008 | 0/45/45/410 | 0.000 | 0.000 | 0.000 | 0/45/47/408 |
| 43 | 0.000 | 0.060 | 0.040 | 0/45/72/383 | 0.000 | 0.008 | 0.005 | 0/45/76/379 |
| 44 | 0.000 | 0.010 | 0.005 | 0/45/30/425 | 0.000 | 0.004 | 0.002 | 0/45/31/424 |
| **45** | **0.022** | 0.002 | 0.003 | 1/44/48/407 | 0.000 | 0.000 | 0.000 | 0/45/49/406 |
| 46 | 0.000 | 0.030 | 0.032 | 0/45/48/407 | 0.000 | 0.006 | 0.005 | 0/45/49/406 |
| **mean ± SD** | **0.004 ± 0.010** | **0.022 ± 0.024** | **0.018 ± 0.017** | — | **0.000 ± 0.000** | **0.004 ± 0.004** | **0.002 ± 0.003** | — |

Mean false-fall alarms: clean 4.2 ± 3.5, FGSM@0.03 48.6 ± 15.1, PGD@0.03 50.4 ± 16.2.
(Per-seed FGSM/PGD accuracy, macro-F1, and confusion counts are read from each
seed's committed `*_attacks_metadata.json` / safety-metric CSVs.)

**Collapse count at ε=0.03 (state exactly):** PGD fall recall = 0.000 in **5/5**
seeds; FGSM fall recall = 0.000 in **4/5** seeds (42, 43, 44, 46). Seed 45 is the
lone FGSM exception (FGSM@0.03 = 0.022; PGD@0.03 = 0.000).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Seed | FGSM drop≥0.10 | FGSM <0.50 | FGSM =0 | PGD drop≥0.10 | PGD <0.50 | PGD =0 |
|---|---|---|---|---|---|---|
| 42 | 0.005 | 0.010 | 0.030 | 0.005 | 0.0075 | 0.025 |
| 43 | 0.0025 | 0.010 | 0.025 | 0.0025 | 0.010 | 0.025 |
| 44 | 0.005 | 0.0075 | 0.030 | 0.005 | 0.0075 | 0.025 |
| 45 | 0.005 | 0.0125 | **0.040** | 0.005 | 0.010 | 0.030 |
| 46 | 0.0025 | 0.0075 | 0.0175 | 0.0025 | 0.0075 | 0.015 |
| **mean ± SD** | 0.0040 ± 0.0014 | 0.0095 ± 0.0021 | 0.0285 ± 0.0082 | 0.0040 ± 0.0014 | 0.0085 ± 0.0014 | 0.0240 ± 0.0055 |

(Clean fall recall per seed used for the drop threshold; all thresholds are in-grid
/ non-null.) **FGSM `recall=0` mean/SD use all 5 seeds** (max 0.040, at seed 45);
**PGD `recall=0` mean/SD use all 5 seeds** (max 0.030, at seed 45). PGD reaches
exactly 0.000 by a tighter budget than FGSM in every seed.

## Generated package files
- `results/cross_architecture/transformer/transformer_clean_qualified_seedwise_metrics.csv`
- `results/cross_architecture/transformer/transformer_clean_qualified_summary.csv`
- `results/cross_architecture/transformer/transformer_clean_qualified_thresholds.csv`
- `results/cross_architecture/transformer/figures/transformer_clean_qualified_fall_recall_clean_vs_fgsm_vs_pgd.png`
  (clean vs FGSM@0.03 vs PGD@0.03 per seed; seed 45's FGSM residual is labelled and
  annotated, not hidden)
- Seed status tracker: `results/cross_architecture/transformer/transformer_seed_convergence_status.csv`
- Per-seed raw results: `results/cross_architecture/transformer/transformer_seed{42..46}_*`
  (commits: seed 42 `d18dd99`; seed 43 `3f0c0b2`; seed 44 `60cdea2`;
  seed 45 `5ef971b`; seed 46 `6fa0285`).
- Per-seed notes: `notes/priority2_transformer_seed{43,44,45,46}_cross_architecture.md`
  and the seed-42 pilot note.

Every seedwise/threshold row carries `*_source` columns pointing at the exact raw
CSV it was read from, so the aggregate is fully traceable to committed files.

## Metric / provenance note (carried from the per-seed runs)
The `stage1_clean_references` block inside each seed's attack metadata reports the
committed **LeNet** Stage-1 reference values (the attack script reads
`results/converged_baseline/converged_seed42_*` for that field); this is
comparison-only. The Transformer clean references actually used in every metric row
(and aggregated here) are computed live from the loaded ViT checkpoints and are
correct. The "legacy" (val+test, 996-window) pool is comparison-only and never
used for training or selection.

## Thesis-safe interpretation
Across a full five-seed sweep (seeds 42–46), attention-based Transformer (ViT)
classifiers trained on UT-HAR reach high but seed-variable clean fall-detection
performance (clean fall recall 0.947 ± 0.049; clean accuracy 0.788–0.940), and all
five seeds suffer severe adversarial window-level fall-recall degradation at
ε=0.03. The collapse is **total under PGD in every seed** — PGD at ε=0.03 drives
fall recall to exactly 0.000 in all 5/5 seeds (zero variance) — and **near-total
under FGSM** — FGSM at ε=0.03 reaches exactly 0.000 in four of five seeds, with
seed 45 retaining a small residual (0.022) that reaches exact zero by ε=0.040.
Every seed reaches exactly 0.000 fall recall under both attacks within the sweep
grid (FGSM by ε ≤ 0.040, PGD by ε ≤ 0.030), while false-fall alarms inflate from
~4 (clean) to ~49 (FGSM) / ~50 (PGD) of 455 non-fall windows. The Transformer
evidence thus reproduces the adversarial safety-proxy failure across an
attention-based family and five seeds, with PGD the consistent worst-case attack
and a minor FGSM-tolerance exception at seed 45.

## Boundary language (must accompany any use of these numbers)
These are **UT-HAR**, **processed-CSI-tensor**, **digital white-box** adversarial
results — **window-level safety-proxy** metrics computed on software feature
tensors. They are **not** clinical fall-risk prediction, **not** clinical
deployment evidence, **not** over-the-air / physical-layer / packet-level attacks,
and **not** certified robustness. "Fall recall" is a window-level
activity-recognition proxy on the UT-HAR protocol, not a validated clinical
fall-detection outcome. The attention/ViT model is an attention-based temporal
robustness baseline, **not** a clinical or biomarker model; attention weights are
not exposed or interpreted. Full five-seed multi-seed evidence now exists for
LeNet, GRU, BiLSTM, and Transformer (BiLSTM and Transformer each with a seed-45
FGSM-tolerance caveat); ResNet18 is a four-seed clean-qualified result with seed 47
deferred. See [[project_overview]] and the per-seed Transformer notes for full
detail.
