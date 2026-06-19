# Priority 2 — Seed-42 Cross-Architecture Pilot

## Goal
Test whether the adversarial **window-level safety-proxy failure** established for
the LeNet baseline also appears **when the model architecture changes**, holding
everything else fixed (dataset, split, preprocessing, fall mapping, epsilon grid,
attack settings, metrics). This is a **seed-42 pilot across architecture
families**, not a full multi-seed cross-architecture study.

Priority 1 already established **five-seed (42–46) reliability for LeNet**: the
collapse there is reproducible, not a single-seed artifact. This pilot asks the
complementary question — does the same failure mode appear under a deeper
convolutional network and under a recurrent network — using **seed 42 only** for
each new architecture.

## Models used (all from the SenseFi UT-HAR family, same input `(N,1,250,90)`)
| Model | Family | Source class | Params | Commit |
|---|---|---|---|---|
| LeNet | CNN (LeNet) | `UT_HAR_LeNet` | 296K | Priority 1 (aggregate `3200a89`, package `14a1e6f`) |
| ResNet18 | Deep CNN (ResNet-18) | `UT_HAR_ResNet18` | 11.18M | `3578136` |
| GRU | Recurrent (GRU) | `UT_HAR_GRU` | 30K | `40bd655` |

Selected via the `--model` factory (`scripts/model_factory.py`). The ResNet and
GRU models already existed in the SenseFi clone
(`third_party/WiFi-CSI-Sensing-Benchmark/UT_HAR_model.py`); no new architecture
code was written. ResNet carries its own input reshape head; GRU reshapes
internally via `x.view(-1,250,90)` — both consume the same processed tensors as
LeNet, so preprocessing, FGSM/PGD attack math, and metric scripts are unchanged.

## Protocol (identical to Priority 1)
- Seed: **42** (each new architecture)
- Dataset / split: UT-HAR (SenseFi), held-out **test split n = 500** windows,
  **45 fall** / 455 non-fall; fall = class index 1.
- Epsilon grid (sweep): 18 points 0.0 … 0.075
  `[0.0, 0.0025, 0.005, 0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020, 0.025,
  0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060, 0.075]`; matched point 0.030.
- FGSM: single-step L∞, no [0,1] clamp (processed tensors).
- PGD: L∞, 10 steps, α = ε/6 (= 0.005 at ε=0.03), projected.
- Metrics: window-level safety proxies (fall recall, missed-fall, false-fall
  alarms, precision/F1, MCC, Cohen's κ, confusion counts) + collapse thresholds.

## Clean results (no attack)
| Model | Accuracy | Macro-F1 | Fall recall | Missed-fall | False-fall alarms | MCC | TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|
| LeNet | 0.970 | 0.952 | 0.956 | 0.044 | 0 | 0.975 | 43/2/0/455 |
| ResNet18 | 0.942 | 0.900 | 0.978 | 0.022 | 1 | 0.976 | 44/1/1/454 |
| GRU | 0.904 | 0.882 | 0.933 | 0.067 | 2 | 0.938 | 42/3/2/453 |

All three are strong clean classifiers (clean fall recall 0.93–0.98).

## FGSM / PGD at epsilon = 0.03
| Model | FGSM recall | FGSM FP | FGSM MCC | PGD recall | PGD FP | PGD MCC | FGSM TP/FN/FP/TN | PGD TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| LeNet | 0.000 | 47 | −0.101 | 0.000 | 48 | −0.102 | 0/45/47/408 | 0/45/48/407 |
| ResNet18 | 0.022 | 14 | −0.014 | 0.000 | 43 | −0.096 | 1/44/14/441 | 0/45/43/412 |
| GRU | 0.000 | 53 | −0.108 | 0.000 | 65 | −0.122 | 0/45/53/402 | 0/45/65/390 |

Under PGD at ε=0.03, **all three architectures miss every one of the 45 fall
windows** (fall recall 0.000). FGSM at ε=0.03 collapses LeNet and GRU to 0.000
and ResNet18 to 0.022. MCC at ε=0.03 is ≤ 0 for every model/attack — worse than
chance on the fall-vs-nonfall proxy.

## Collapse thresholds (smallest ε on the grid)
| Model | Attack | recall < 0.50 | recall < 0.10 | recall = 0 |
|---|---|---|---|---|
| LeNet | FGSM | 0.005 | 0.010 | 0.010 |
| LeNet | PGD | 0.005 | 0.0075 | 0.0075 |
| ResNet18 | FGSM | 0.005 | 0.0125 | 0.035 |
| ResNet18 | PGD | 0.0025 | 0.005 | 0.0075 |
| GRU | FGSM | 0.010 | 0.0175 | 0.020 |
| GRU | PGD | 0.0075 | 0.0125 | 0.015 |

PGD reaches zero fall recall at a small budget (ε ≤ 0.015) for all three models.
ResNet18 is the most FGSM-tolerant (FGSM recall hits 0 only at ε=0.035) but is
still fully broken by PGD by ε=0.0075.

## Generated package files
- Summary table: `results/cross_architecture/cross_architecture_seed42_pilot_summary.csv`
- Thresholds table: `results/cross_architecture/cross_architecture_seed42_pilot_thresholds.csv`
- Figures:
  - `results/cross_architecture/figures/cross_architecture_seed42_fall_recall_vs_epsilon.png` (FGSM & PGD panels)
  - `results/cross_architecture/figures/cross_architecture_seed42_pgd_false_alarms_at_003.png`
- LaTeX: `tables/chapter_cross_architecture_seed42_table.tex`, `tables/chapter_cross_architecture_seed42_figure_caption.tex`
- Per-model raw results: `results/converged_*` (LeNet), `results/cross_architecture/resnet/`, `results/cross_architecture/gru/`

## Limitations
- **Seed-42 pilot only** for ResNet18 and GRU (single seed each). Multi-seed
  reliability is established **only for LeNet** (Priority 1, seeds 42–46). This
  pilot does **not** establish multi-seed cross-architecture reliability.
- Three architectures (one each: LeNet/ResNet18/GRU) — not an exhaustive sweep
  of model families.
- ResNet18 seed-42 clean training was run under heavy machine contention
  (recorded `elapsed ≈ 7.9 h`); this is a non-representative wall-clock time, not
  a property of the model, and does not affect correctness (deterministic seed,
  normal early-stopping).
- All quantities are window-level safety-proxy metrics on digital-domain,
  processed-tensor perturbations.

## Careful thesis wording
- This is a **seed-42 cross-architecture pilot**. Priority 1 already established
  **five-seed reliability for the LeNet baseline**; this pilot tests whether the
  same safety-proxy failure **also appears when the architecture changes**
  (deeper CNN, recurrent network), using seed 42 for each new architecture.
- The pilot indicates the failure is **not specific to LeNet**: under matched
  PGD at ε=0.03, LeNet, ResNet18, and GRU all collapse to 0.000 window-level
  fall recall on seed 42.
- Do **not** claim full multi-seed cross-architecture reliability (only LeNet has
  multi-seed evidence so far).
- Do **not** claim real-world clinical unsafe behavior, over-the-air validation,
  or certified robustness. These are digital-domain, software-only, window-level
  safety-proxy results.
