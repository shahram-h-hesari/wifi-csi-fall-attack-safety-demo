# Priority 2 — BiLSTM Five-Seed Aggregate (Clean-Qualified)

Thesis-ready aggregate for the **BiLSTM** (recurrent) multi-seed extension of the
Priority 2 cross-architecture study. Built **only** from the already-committed
BiLSTM seed-42–46 raw result files in `results/cross_architecture/bilstm/` (no
experiment rerun; no raw result file modified). Analogous in style to the GRU
five-seed aggregate (`notes/priority2_gru_5seed_aggregate.md`), with **precise
wording for the seed-45 deviation**.

## Headline (read the nuance — do NOT over-round)
- **5/5 BiLSTM seeds (42–46) are clean-qualified** — each a non-trivial, converged
  7-class classifier (no divergence, no single-class predictor).
- **All five show severe adversarial window-level fall-recall degradation at
  ε=0.03.**
- **4 of 5 seeds (42, 43, 44, 46) reach exactly 0.000 fall recall under *both*
  FGSM and PGD at ε=0.03.**
- **Seed 45 is the exception:** at ε=0.03 it retains **FGSM fall recall 0.111** and
  **PGD fall recall 0.022**. Its FGSM fall recall **never reaches exactly 0.000
  within the 0.0–0.075 sweep grid** (bottoms at 0.022); its PGD fall recall reaches
  exactly 0.000 only at **ε=0.035**.
- **All 5/5 seeds reach exactly 0.000 PGD fall recall by ε ≤ 0.035** (four of them
  by ε ≤ 0.025).
- **Do NOT write "all five BiLSTM seeds reach 0.000 at ε=0.03."** That is false for
  seed 45.

This differs from LeNet and GRU, which each show a **zero-variance 0.000 PGD
collapse at ε=0.03 across all five seeds**; BiLSTM is a full five-seed
clean-qualified set but with the seed-45 attack-tolerance caveat above.

## Methods (identical fixed protocol across all five seeds)
- Model: `UT_HAR_BiLSTM` via the `--model bilstm` factory (`scripts/model_factory.py`).
- Data: UT-HAR (SenseFi), held-out **test split n = 500** windows (**45 fall /
  455 non-fall**); fall = class index 1. Same preprocessing and fall/non-fall
  mapping as the LeNet baseline.
- Training (Stage 1): Adam, lr 1e-3, batch 64, max 200 epochs, early-stopping
  patience 20 on validation macro-F1; best checkpoint = validation-selected.
  (Seeds 42/43 ran the full 200-epoch budget without early-stopping; seeds 44/45/46
  early-stopped — both are healthy BiLSTM behavior.)
- Attacks (Stage 2, frozen checkpoint): FGSM (single-step L∞) and PGD (L∞, 10
  steps, α = ε/6), no [0,1] clamp (processed CSI tensors); matched point ε=0.030;
  18-point sweep ε ∈ [0.0 … 0.075].
- Metrics: window-level fall-vs-non-fall safety proxies + multiclass accuracy/
  macro-F1 + collapse thresholds. Same metric scripts as all prior seeds/architectures.
- Aggregation: mean ± sample SD (ddof=1); 95% CI via Student-t, df=4 (t=2.776).
  The FGSM `recall=0` threshold mean/SD are computed over the **4 seeds that reach
  zero in-grid** (seed 45 excluded; **null is not averaged as zero**).

## Clean performance (per seed, test split n=500)
| Seed | Accuracy | Macro-F1 | Fall recall | Fall precision | TP/FN/FP/TN | Status |
|---|---|---|---|---|---|---|
| 42 | 0.814 | 0.769 | 0.889 | 0.851 | 40/5/7/448 | clean-qualified |
| 43 | 0.830 | 0.781 | 0.822 | 0.881 | 37/8/5/450 | clean-qualified |
| 44 | 0.878 | 0.841 | 0.911 | 0.932 | 41/4/3/452 | clean-qualified |
| 45 | 0.808 | 0.769 | 0.933 | 0.737 | 42/3/15/440 | clean-qualified |
| 46 | 0.836 | 0.803 | 0.867 | 0.886 | 39/6/5/450 | clean-qualified |
| **mean ± SD** | **0.833 ± 0.028** | **0.793 ± 0.030** | **0.884 ± 0.043** | **0.857 ± 0.073** | — | 5/5 |

## Fixed ε=0.03 attack performance (per seed, test split n=500)
| Seed | FGSM recall | FGSM acc | FGSM macF1 | FGSM TP/FN/FP/TN | PGD recall | PGD acc | PGD macF1 | PGD TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| 42 | 0.000 | 0.090 | 0.075 | 0/45/30/425 | 0.000 | 0.014 | 0.018 | 0/45/55/400 |
| 43 | 0.000 | 0.130 | 0.103 | 0/45/38/417 | 0.000 | 0.032 | 0.029 | 0/45/53/402 |
| 44 | 0.000 | 0.088 | 0.072 | 0/45/33/422 | 0.000 | 0.018 | 0.010 | 0/45/46/409 |
| **45** | **0.111** | 0.090 | 0.108 | 5/40/63/392 | **0.022** | 0.032 | 0.045 | 1/44/77/378 |
| 46 | 0.000 | 0.118 | 0.098 | 0/45/44/411 | 0.000 | 0.028 | 0.029 | 0/45/54/401 |
| **mean ± SD** | **0.022 ± 0.050** | **0.103 ± 0.019** | **0.091 ± 0.017** | — | **0.004 ± 0.010** | **0.025 ± 0.008** | **0.026 ± 0.013** | — |

Mean false-fall alarms: clean 7.0 ± 4.7, FGSM@0.03 41.6 ± 13.1, PGD@0.03 57.0 ± 11.7.
(Per-seed FGSM/PGD accuracy, macro-F1, and confusion counts are read from each
seed's committed `*_attacks_metadata.json` / safety-metric CSVs.)

**Collapse count at ε=0.03 (state exactly):** FGSM fall recall = 0.000 in **4/5**
seeds (42, 43, 44, 46); PGD fall recall = 0.000 in **4/5** seeds (42, 43, 44, 46).
Seed 45 is the lone exception (FGSM 0.111, PGD 0.022).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Seed | FGSM drop≥0.10 | FGSM <0.50 | FGSM =0 | PGD drop≥0.10 | PGD <0.50 | PGD =0 |
|---|---|---|---|---|---|---|
| 42 | 0.005 | 0.0075 | 0.0175 | 0.005 | 0.0075 | 0.0175 |
| 43 | 0.005 | 0.0075 | 0.0175 | 0.005 | 0.0075 | 0.015 |
| 44 | 0.005 | 0.0075 | 0.030 | 0.0025 | 0.0075 | 0.025 |
| 45 | 0.0075 | 0.0125 | **none in grid** | 0.0075 | 0.010 | 0.035 |
| 46 | 0.0075 | 0.010 | 0.020 | 0.005 | 0.0075 | 0.015 |
| **mean ± SD** | 0.0060 ± 0.0014 | 0.0090 ± 0.0022 | **0.0213 ± 0.0060** † | 0.0050 ± 0.0018 | 0.0080 ± 0.0011 | **0.0215 ± 0.0086** |

† **FGSM `recall=0` mean/SD computed over the 4 seeds that reach exactly 0 in-grid
(42, 43, 44, 46); seed 45 is excluded because its FGSM fall recall never reaches
exactly 0 within the 0.0–0.075 grid — it is NOT averaged as 0.** PGD `recall=0`
mean/SD use all 5 seeds (all reach 0 by ε ≤ 0.035).

## Generated package files
- `results/cross_architecture/bilstm/bilstm_clean_qualified_seedwise_metrics.csv`
- `results/cross_architecture/bilstm/bilstm_clean_qualified_summary.csv`
- `results/cross_architecture/bilstm/bilstm_clean_qualified_thresholds.csv`
- `results/cross_architecture/bilstm/figures/bilstm_clean_qualified_fall_recall_clean_vs_fgsm_vs_pgd.png`
  (clean vs FGSM@0.03 vs PGD@0.03 per seed; seed 45's residual recall is labelled
  and annotated, not hidden)
- Seed status tracker: `results/cross_architecture/bilstm/bilstm_seed_convergence_status.csv`
- Per-seed raw results: `results/cross_architecture/bilstm/bilstm_seed{42..46}_*`
  (commits: seed 42 `62a4c05`; seed 43 `107b7e6`; seed 44 `301adfe`;
  seed 45 `d445a02`; seed 46 `7d2f5ed`).
- Per-seed notes: `notes/priority2_bilstm_seed{43,44,45,46}_cross_architecture.md`
  and the seed-42 pilot note.

Every seedwise/threshold row carries `*_source` columns pointing at the exact raw
CSV it was read from, so the aggregate is fully traceable to committed files.

## Metric / provenance note (carried from the per-seed runs)
The `stage1_clean_references` block inside each seed's attack metadata reports the
committed **LeNet** Stage-1 reference values (the attack script reads
`results/converged_baseline/converged_seed42_*` for that field); this is
comparison-only. The BiLSTM clean references actually used in every metric row
(and aggregated here) are computed live from the loaded BiLSTM checkpoints and are
correct. The "legacy" (val+test, 996-window) pool is comparison-only and never
used for training or selection. Seed-45's FGSM `recall=0` threshold is recorded as
`null`/`none` in the source sweep metadata — this is correct, not a missing value.

## Thesis-safe interpretation
Across a full five-seed sweep (seeds 42–46), BiLSTM recurrent classifiers trained
on UT-HAR reach moderate, consistent clean fall-detection performance (clean fall
recall 0.884 ± 0.043) — BiLSTM is the weakest clean family in the study — and all
five seeds suffer severe adversarial window-level fall-recall degradation at
ε=0.03. The collapse is **near-total but not uniformly total at the matched
budget**: four of the five seeds (42, 43, 44, 46) reach exactly 0.000 fall recall
under both FGSM and PGD at ε=0.03, while seed 45 — a weaker, higher-false-alarm
clean classifier — retains a small residual fall recall at ε=0.03 (FGSM 0.111, PGD
0.022) and reaches total PGD collapse only by ε=0.035 (its FGSM fall recall never
reaches exactly 0 within the grid, bottoming at 0.022). All five seeds nonetheless
fall below 0.50 fall recall by ε ≈ 0.0075–0.0125 and reach exactly 0.000 PGD fall
recall by ε ≤ 0.035, while false-fall alarms inflate from ~7 (clean) to ~42 (FGSM)
/ ~57 (PGD) of 455 non-fall windows. The BiLSTM evidence thus reproduces the
adversarial safety-proxy failure across a recurrent-network family and five seeds,
but with quantitatively less uniform total collapse at ε=0.03 than LeNet or GRU.

## Boundary language (must accompany any use of these numbers)
These are **UT-HAR**, **processed-CSI-tensor**, **digital white-box** adversarial
results — **window-level safety-proxy** metrics computed on software feature
tensors. They are **not** clinical fall-risk prediction, **not** clinical
deployment evidence, **not** over-the-air / physical-layer / packet-level attacks,
and **not** certified robustness. "Fall recall" is a window-level
activity-recognition proxy on the UT-HAR protocol, not a validated clinical
fall-detection outcome. Full five-seed multi-seed evidence now exists for LeNet,
GRU, and BiLSTM (BiLSTM with the seed-45 caveat above); ResNet18 is a four-seed
clean-qualified result; the Transformer remains a seed-42 pilot. See
[[project_overview]] and the per-seed BiLSTM notes for full detail.
