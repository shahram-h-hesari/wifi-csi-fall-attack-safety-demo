# Priority 2 — GRU Five-Seed Aggregate (Clean-Qualified)

Thesis-ready aggregate for the **GRU** (recurrent) multi-seed extension of the
Priority 2 cross-architecture study. Built **only** from the already-committed GRU
seed-42–46 raw result files in `results/cross_architecture/gru/` (no experiment
was rerun; no raw result file was modified). Analogous in style to the ResNet18
clean-qualified aggregate (`notes/priority2_resnet18_multiseed_summary.md`).

## Headline
- **5/5 clean-qualified GRU seeds (42, 43, 44, 45, 46) collapse to exactly 0.000
  window-level PGD fall recall at ε=0.03** — every one of the 45 fall windows
  missed in every seed (zero variance).
- All five seeds are clean-qualified: each is a non-trivial, converged 7-class
  classifier (no divergence, no single-class predictor). The GRU now has a **full
  five-seed result, matching the LeNet baseline seed count.**
- This is a multi-seed result for a **recurrent** model family. It does **not**
  imply full multi-seed reliability for every architecture family — BiLSTM and
  Transformer remain seed-42 pilots; only LeNet (Priority 1) and now GRU have full
  five-seed evidence.

## Methods (identical fixed protocol across all five seeds)
- Model: `UT_HAR_GRU` via the `--model gru` factory (`scripts/model_factory.py`).
- Data: UT-HAR (SenseFi), held-out **test split n = 500** windows (**45 fall /
  455 non-fall**); fall = class index 1. Same preprocessing and fall/non-fall
  mapping as the LeNet baseline.
- Training (Stage 1): Adam, lr 1e-3, batch 64, max 200 epochs, early-stopping
  patience 20 on validation macro-F1; best checkpoint = validation-selected.
- Attacks (Stage 2, frozen checkpoint): FGSM (single-step L∞) and PGD (L∞, 10
  steps, α = ε/6), no [0,1] clamp (processed CSI tensors); matched point ε=0.030;
  18-point sweep ε ∈ [0.0 … 0.075].
- Metrics: window-level fall-vs-non-fall safety proxies (recall, precision,
  missed-fall, false-fall alarms, confusion counts) + multiclass accuracy/macro-F1
  + collapse thresholds. Same metric scripts as all prior seeds/architectures.
- Aggregation: mean ± sample SD (ddof=1); 95% CI via Student-t, df=4 (t=2.776).

## Clean performance (per seed, test split n=500)
| Seed | Accuracy | Macro-F1 | Fall recall | Fall precision | TP/FN/FP/TN | Status |
|---|---|---|---|---|---|---|
| 42 | 0.904 | 0.882 | 0.933 | 0.955 | 42/3/2/453 | clean-qualified |
| 43 | 0.904 | 0.875 | 0.911 | 0.911 | 41/4/4/451 | clean-qualified |
| 44 | 0.932 | 0.910 | 0.911 | 0.932 | 41/4/3/452 | clean-qualified |
| 45 | 0.920 | 0.892 | 0.933 | 0.875 | 42/3/6/449 | clean-qualified |
| 46 | 0.872 | 0.845 | 0.911 | 0.891 | 41/4/5/450 | clean-qualified |
| **mean ± SD** | **0.906 ± 0.023** | **0.881 ± 0.024** | **0.920 ± 0.012** | **0.913 ± 0.032** | — | 5/5 |

## Fixed ε=0.03 attack performance (per seed, test split n=500)
| Seed | FGSM recall | FGSM acc | FGSM macF1 | FGSM TP/FN/FP/TN | PGD recall | PGD acc | PGD macF1 | PGD TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| 42 | 0.000 | 0.142 | 0.099 | 0/45/53/402 | 0.000 | 0.018 | 0.015 | 0/45/65/390 |
| 43 | 0.022 | 0.174 | 0.159 | 1/44/38/417 | 0.000 | 0.020 | 0.020 | 0/45/49/406 |
| 44 | 0.000 | 0.148 | 0.098 | 0/45/36/419 | 0.000 | 0.018 | 0.009 | 0/45/45/410 |
| 45 | 0.022 | 0.166 | 0.106 | 1/44/34/421 | 0.000 | 0.006 | 0.004 | 0/45/45/410 |
| 46 | 0.000 | 0.168 | 0.141 | 0/45/53/402 | 0.000 | 0.058 | 0.053 | 0/45/60/395 |
| **mean ± SD** | **0.009 ± 0.012** | **0.160 ± 0.014** | **0.121 ± 0.028** | — | **0.000 ± 0.000** | **0.024 ± 0.020** | **0.020 ± 0.019** | — |

Mean false-fall alarms: clean 4.0 ± 1.6, FGSM@0.03 42.8 ± 9.4, PGD@0.03 52.8 ± 9.2.

The defining result: clean fall recall is high and tight (0.920 ± 0.012), yet
**PGD at ε=0.03 drives fall recall to exactly 0.000 in every seed (zero
variance)**, while multiclass accuracy collapses from ~0.91 to ~0.02. FGSM at
ε=0.03 is near-total (mean fall recall 0.009; 0.000 in 3/5 seeds, 0.022 in the
other two). Both attacks simultaneously inflate false-fall alarms by ~10–13×.

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Seed | FGSM drop≥0.10 | FGSM <0.50 | FGSM =0 | PGD drop≥0.10 | PGD <0.50 | PGD =0 |
|---|---|---|---|---|---|---|
| 42 | 0.005 | 0.010 | 0.020 | 0.005 | 0.0075 | 0.015 |
| 43 | 0.0025 | 0.0075 | 0.035 | 0.0025 | 0.0075 | 0.025 |
| 44 | 0.005 | 0.0075 | 0.020 | 0.0025 | 0.0075 | 0.015 |
| 45 | 0.0075 | 0.0125 | 0.045 | 0.005 | 0.0075 | 0.025 |
| 46 | 0.0075 | 0.010 | 0.030 | 0.005 | 0.0075 | 0.025 |
| **mean ± SD** | **0.0055 ± 0.0021** | **0.0095 ± 0.0021** | **0.0300 ± 0.0106** | **0.0040 ± 0.0014** | **0.0075 ± 0.0000** | **0.0210 ± 0.0055** |

PGD reaches zero fall recall at a small, tight budget (ε ≤ 0.025 in all five
seeds; mean ≈ 0.021). FGSM is more seed-variable but still reaches zero by
ε ≤ 0.045 in every seed. PGD crosses the <0.50 mark at ε=0.0075 in all five seeds
(zero variance).

## Generated package files
- `results/cross_architecture/gru/gru_clean_qualified_seedwise_metrics.csv`
- `results/cross_architecture/gru/gru_clean_qualified_summary.csv`
- `results/cross_architecture/gru/gru_clean_qualified_thresholds.csv`
- `results/cross_architecture/gru/figures/gru_clean_qualified_fall_recall_clean_vs_fgsm_vs_pgd.png`
- Seed status tracker: `results/cross_architecture/gru/gru_seed_convergence_status.csv`
- Per-seed raw results: `results/cross_architecture/gru/gru_seed{42..46}_*`
  (commits: seed 42 `40bd655`; seed 43 `a3ec075`; seed 44 `ad7fcb7`;
  seed 45 `cbca55b`; seed 46 `16e92f0`).
- Per-seed notes: `notes/priority2_seed42_cross_architecture_pilot.md`,
  `notes/priority2_gru_seed{43,44,45,46}_cross_architecture.md`.

Every seedwise/threshold row carries `*_source` columns pointing at the exact raw
CSV it was read from, so the aggregate is fully traceable to committed files.

## Metric / provenance note (carried from the per-seed runs)
The `stage1_clean_references` block inside each seed's attack metadata reports the
committed **LeNet** Stage-1 reference values (the attack script reads
`results/converged_baseline/converged_seed42_*` for that field); this is
comparison-only. The GRU clean references actually used in every metric row
(and aggregated here) are computed live from the loaded GRU checkpoints and are
correct. The "legacy" (val+test, 996-window) pool is comparison-only and never
used for training or selection.

## Thesis-safe interpretation
Across a full five-seed sweep (seeds 42–46), GRU recurrent classifiers trained on
UT-HAR reach strong, consistent clean fall-detection performance (clean fall
recall 0.920 ± 0.012), yet **every one of the five seeds is driven to exactly
0.000 window-level fall recall under matched PGD at ε=0.03** — all 45 fall windows
missed, with zero variance — while simultaneously emitting ~13× more false-fall
alarms. This elevates the recurrent-model finding from the original seed-42 pilot
to a reproducible multi-seed result and shows the adversarial safety-proxy failure
is not a single-seed artifact and not specific to the LeNet CNN baseline; the GRU
and LeNet now each have full five-seed evidence of the same collapse.

## Boundary language (must accompany any use of these numbers)
These are **UT-HAR**, **processed-tensor**, **digital white-box** adversarial
results — **window-level safety-proxy** metrics computed on software CSI feature
tensors. They are **not** clinical fall-risk prediction, **not** clinical
deployment evidence, **not** over-the-air / physical-layer / packet-level attacks,
and **not** certified robustness. The "fall recall" quantity is a window-level
activity-recognition proxy on the UT-HAR protocol, not a validated clinical
fall-detection outcome. Multi-seed evidence exists for **LeNet and GRU only**;
BiLSTM and Transformer remain seed-42 pilots. See [[project_overview]] and the
per-seed notes for full protocol and limitations.
