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
convolutional network, recurrent networks, and an attention-based network — using
**seed 42 only** for each new architecture.

## Temporal / attention framing (thesis-safe)
- **BiLSTM** is included as a stronger bidirectional temporal-sequence robustness
  baseline; **Transformer (ViT)** is included as an attention-based temporal
  robustness baseline. Both are motivated by future WiFi-based gait/fall-risk
  monitoring (attention models can, in principle, weight different time regions or
  CSI features), but **neither is presented as clinical fall-risk prediction**.
- UT-HAR contains no longitudinal older-adult fall-risk labels, clinical risk
  scores, future-fall outcomes, or multi-day gait trajectories. These models are
  used only to test whether temporal/attention CSI models exhibit similar
  adversarial safety-proxy degradation under the available UT-HAR
  activity-recognition protocol. See `external clinical-safety bridge note removed from public artifact package`.

## Models used (all from the SenseFi UT-HAR family, same input `(N,1,250,90)`)
| Model | Family | Source class | Params | Commit |
|---|---|---|---|---|
| LeNet | CNN (LeNet) | `UT_HAR_LeNet` | 295,655 | Priority 1 (`3200a89`, pkg `14a1e6f`) |
| ResNet18 | Deep CNN (ResNet-18) | `UT_HAR_ResNet18` | 11,182,142 | `3578136` |
| GRU | Recurrent (GRU) | `UT_HAR_GRU` | 30,407 | `40bd655` |
| BiLSTM | Recurrent (BiLSTM) | `UT_HAR_BiLSTM` | 80,327 | `c298471` |
| Transformer | Attention (ViT) | `UT_HAR_ViT` | 10,575,007 | `5202608` |

Selected via the `--model` factory (`scripts/model_factory.py`). All five models
already existed in the SenseFi clone
(`third_party/WiFi-CSI-Sensing-Benchmark/UT_HAR_model.py`); no new architecture
code was written (the ViT needed only a one-line factory alias). ResNet and ViT
carry their own input head (conv / patch-embedding); GRU/BiLSTM reshape internally
via `x.view(-1,250,90)` — all consume the same processed tensors as LeNet, so
preprocessing, FGSM/PGD attack math, and metric scripts are unchanged.

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
| BiLSTM | 0.814 | 0.769 | 0.889 | 0.111 | 7 | 0.857 | 40/5/7/448 |
| Transformer | 0.918 | 0.895 | 0.978 | 0.022 | 1 | 0.976 | 44/1/1/454 |

LeNet, ResNet18, GRU, and Transformer are strong clean classifiers (clean fall
recall 0.93–0.98); the Transformer matches the best clean fall recall (0.978) and
early-stopped normally. BiLSTM is the weakest clean classifier (accuracy 0.814,
fall recall 0.889) and ran the full 200-epoch cap without early-stopping; its
weaker clean baseline is reported alongside its collapse.

## FGSM / PGD at epsilon = 0.03
| Model | FGSM recall | FGSM FP | FGSM MCC | PGD recall | PGD FP | PGD MCC | FGSM TP/FN/FP/TN | PGD TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| LeNet | 0.000 | 47 | −0.101 | 0.000 | 48 | −0.102 | 0/45/47/408 | 0/45/48/407 |
| ResNet18 | 0.022 | 14 | −0.014 | 0.000 | 43 | −0.096 | 1/44/14/441 | 0/45/43/412 |
| GRU | 0.000 | 53 | −0.108 | 0.000 | 65 | −0.122 | 0/45/53/402 | 0/45/65/390 |
| BiLSTM | 0.000 | 30 | −0.080 | 0.000 | 55 | −0.111 | 0/45/30/425 | 0/45/55/400 |
| Transformer | 0.000 | 45 | −0.099 | 0.000 | 47 | −0.101 | 0/45/45/410 | 0/45/47/408 |

Under PGD at ε=0.03, **all five architectures miss every one of the 45 fall
windows** (fall recall 0.000). FGSM at ε=0.03 collapses LeNet, GRU, BiLSTM, and
Transformer to 0.000 and ResNet18 to 0.022. MCC at ε=0.03 is ≤ 0 for every
model/attack — worse than chance on the fall-vs-nonfall proxy. The Transformer
result is the cleanest demonstration: a well-trained attention model (clean fall
recall 0.978, properly early-stopped) is still driven to 0.000 fall recall.

## Collapse thresholds (smallest ε on the grid)
| Model | Attack | recall < 0.50 | recall < 0.10 | recall = 0 |
|---|---|---|---|---|
| LeNet | FGSM | 0.005 | 0.010 | 0.010 |
| LeNet | PGD | 0.005 | 0.0075 | 0.0075 |
| ResNet18 | FGSM | 0.005 | 0.0125 | 0.035 |
| ResNet18 | PGD | 0.0025 | 0.005 | 0.0075 |
| GRU | FGSM | 0.010 | 0.0175 | 0.020 |
| GRU | PGD | 0.0075 | 0.0125 | 0.015 |
| BiLSTM | FGSM | 0.0075 | 0.0175 | 0.0175 |
| BiLSTM | PGD | 0.0075 | 0.015 | 0.0175 |
| Transformer | FGSM | 0.010 | 0.0125 | 0.030 |
| Transformer | PGD | 0.0075 | 0.0125 | 0.025 |

PGD reaches zero fall recall at a small budget (ε ≤ 0.025) for all five models.
ResNet18 and the Transformer are the most FGSM-tolerant (FGSM recall hits 0 only
at ε=0.035 / 0.030) but are still fully broken by PGD by ε ≤ 0.0075.

## Generated package files
- Summary table: `results/cross_architecture/cross_architecture_seed42_pilot_summary.csv`
- Thresholds table: `results/cross_architecture/cross_architecture_seed42_pilot_thresholds.csv`
- Figures:
  - `results/cross_architecture/figures/cross_architecture_seed42_fall_recall_vs_epsilon.png` (FGSM & PGD panels)
  - `results/cross_architecture/figures/cross_architecture_seed42_pgd_false_alarms_at_003.png`
- LaTeX: `tables/chapter_cross_architecture_seed42_table.tex`, `tables/chapter_cross_architecture_seed42_figure_caption.tex`
- external clinical-safety research group bridge note: `external clinical-safety bridge note removed from public artifact package`
- Per-model raw results: `results/converged_*` (LeNet), `results/cross_architecture/{resnet,gru,bilstm,transformer}/`

## Attention diagnostic (Stage E) — not performed
`UT_HAR_ViT`'s `MultiHeadAttention` computes attention internally but does not
return or store the attention weights. Exposing them would require modifying the
SenseFi attention module, which is out of scope for this pilot, so no attention
visualization was produced. If pursued later, it must be framed only as a model
diagnostic — **not** a clinical biomarker and **not** evidence of gait
instability or fall risk.

## Limitations
- **Seed-42 pilot only** for ResNet18, GRU, BiLSTM, and Transformer (single seed
  each). Multi-seed reliability is established **only for LeNet** (Priority 1,
  seeds 42–46). This pilot does **not** establish multi-seed cross-architecture
  reliability.
- Five architectures (one each) — not an exhaustive sweep of model families or
  Transformer variants/depths.
- BiLSTM did not converge as strongly as the others (no early stop; clean
  accuracy 0.814); its weaker clean baseline is reported alongside its collapse.
- ResNet18 seed-42 clean training was run under heavy machine contention
  (`elapsed ≈ 7.9 h`); a non-representative wall-clock time, not a model property,
  not affecting correctness (deterministic seed, normal early-stopping).
- All quantities are window-level safety-proxy metrics on digital-domain,
  processed-tensor perturbations.

## Careful thesis wording
- This is a **seed-42 cross-architecture pilot**. Priority 1 established
  **five-seed reliability for the LeNet baseline**; this pilot tests whether the
  same safety-proxy failure **also appears when the architecture changes** (deeper
  CNN, recurrent GRU/BiLSTM, attention-based Transformer), using seed 42 for each.
- **Transformer extends the pilot to an attention-based model family**, framed
  only as an attention-based temporal robustness baseline motivated by future
  WiFi gait/fall-risk monitoring — **not** as clinical fall-risk prediction.
- The pilot indicates the failure is **not specific to LeNet**: under matched PGD
  at ε=0.03, all five architectures collapse to 0.000 window-level fall recall on
  seed 42.
- Do **not** claim full multi-seed cross-architecture reliability (only LeNet has
  multi-seed evidence so far).
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, certified robustness, or that attention maps
  are medical explanations. These are digital-domain, software-only, window-level
  safety-proxy results.
