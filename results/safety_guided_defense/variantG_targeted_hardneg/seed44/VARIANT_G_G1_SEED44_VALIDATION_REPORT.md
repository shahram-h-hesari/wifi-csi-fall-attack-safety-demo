# Variant G G1 — seed-44 validation report

> **Independent seed-44 validation of frozen Variant G G1**, executed per the committed pre-registration (`seed44_preregistration/VARIANT_G_G1_SEED44_PREREGISTRATION.md`; criteria + gate families + validation-only threshold rule fixed *before* the run). Seed 44 ONLY; G1 ONLY; no G2/G3; no seeds 45/46. Loss / class indices / targeted-PGD sign / source weighting / selection-v2 unchanged (only the seed gate was relaxed to allow 44, and a validation-split per-window export was added, eval-only). The seed-44 **test set was not used to select the gate threshold** (τ chosen on validation only). Window-level, digital-domain, white-box; test n=500 (45 fall windows), ε=0.030. **No solved / certified / clinical / over-the-air claim.**

## Final category: **STRONG VALIDATION**

Reason: all strong-tier conditions met.

## 1. Training & checkpoint metadata

- Setting **G1** (λ_s=1.0, λ_f=1.0, λ_t=1.0, w_wr=2.0, γ=0.5, fall weight 3); seed **44**; LeNet; UT-HAR/SenseFi split (val 44 fall / 452 nonfall, test 45 fall / 455 nonfall).
- v2safety checkpoint selected by the frozen selection-v2 rule (validation-only). Full metadata: `metadata/seed44_variantG_G1_metadata.json`; selection candidates: `analysis/seed44_variantG_G1_selection_candidates.csv`.

## 2. Validation threshold-selection (validation data ONLY)

Raw-G1 validation clean FP (no gate) = 15. Feasible set requires: val PGD recall ≥ 0.50, val PGD FP ≤ 90, val clean fall recall ≥ 0.90, val clean FP ≤ raw+5. Full sweep: `analysis/validation_threshold_selection.csv`.

| family | chosen τ | val PGD recall | val PGD FP | val PGD F1 | val clean fall recall | val clean FP |
|---|---|---|---|---|---|---|
| entropy | 1.94 | 0.614 | 74 | 0.372 | 0.955 | 15 |
| pfall (carried) | 0.19 | 0.614 | 73 | 0.375 | 0.955 | 15 |

**Carried gate to test:** `pfall` at τ = 0.19 (higher validation F1).

## 3-6. Seed-44 TEST metrics (evaluated once)

| Model | clean acc | clean mF1 | clean fall R | PGD recall [Wilson] | PGD FP | walk/run→fall | spec | prec | F1 | PGD-20 |
|---|---|---|---|---|---|---|---|---|---|---|
| **raw G1 v2safety** | 0.746 | 0.692 | 0.956 | 0.600 [0.455, 0.730] | 65 | 48 | 0.857 | 0.293 | 0.394 | 0.600 |
| **gated G1 (pfall τ=0.19)** | 0.746 | 0.692 | 0.956 | 0.600 [0.455, 0.730] | 65 | 48 | 0.857 | 0.293 | 0.394 | 0.578 |
| Variant F seed44 v2safety | 0.700 | 0.658 | 0.978 | 0.622 [0.476, 0.749] | 112 | 73 | — | — | — | 0.511 |
| Variant D seed44 (FP ref) | 0.722 | — | — | 0.378 | 167 | 116 | — | — | — | — |
| FGSM defense seed44 (floor) | 0.928 | — | — | 0.044 | 42 | 25 | — | — | — | — |

- **PGD-20 durability:** raw 0.600 (= 100% of raw PGD-10); gated 0.578.
- **Clean false-alarm burden:** raw clean FP 20; gated clean FP 20.

## 9. Confidence inversion (vs Variant F seed44)

| Model | A P(fall) | B P(fall) | gap (B−A) | A entropy | B entropy |
|---|---|---|---|---|---|
| Variant F seed44 | 0.392 | 0.513 | +0.121 | 1.401 | 1.298 |
| Variant G G1 seed44 | 0.340 | 0.383 | +0.043 | 1.693 | 1.530 |

- Inversion **reduced** vs Variant F seed44.

## 10. False-alarm source anatomy (raw G1, PGD@0.030)

| source class | n FA | % | median P(fall) | median entropy |
|---|---|---|---|---|
| lie down | 3 | 4.6 | 0.299 | 1.693 |
| walk | 20 | 30.8 | 0.386 | 1.598 |
| pickup | 3 | 4.6 | 0.395 | 1.730 |
| run | 28 | 43.1 | 0.420 | 1.478 |
| sit down | 1 | 1.5 | 0.228 | 1.891 |
| stand up | 10 | 15.4 | 0.355 | 1.669 |
| **TOTAL** | 65 | 100.0 | — | — |

## 11. Wilson intervals (PGD-10 fall recall, n_f=45)

| Model | recall | 95% Wilson |
|---|---|---|
| raw G1 | 0.600 | [0.455, 0.730] |
| gated G1 | 0.600 | [0.455, 0.730] |
| Variant F seed44 | 0.622 | [0.476, 0.749] |

## 7-8 / 12. Figures
- `figures/fig_G1_seed44_pareto.png` (recall vs FP: raw/gated G1 vs F/D/FGSM)
- `figures/fig_G1_seed44_epsilon_sweep.png` (18-ε PGD + FGSM sweeps)

## 13. Final category & promotion

**STRONG VALIDATION.**

On the independent seed, the frozen G1 operating point **matches Variant F's attacked recall** (raw 0.600 vs 0.622 — within overlapping Wilson CIs) **while cutting false alarms ~42% (65 vs 112)** and walk/run→fall (48 vs 73), with **higher clean accuracy** (0.746 vs 0.700), **more durable PGD-20** (0.600 vs 0.511), and **reduced confidence inversion**. The validation-defined gate (P(fall) ≥ τ chosen on validation) left this essentially unchanged — the inversion reduction already made the *raw* operating point low-FP, so no aggressive post-hoc gating was needed. All pre-registered STRONG-VALIDATION conditions hold; the result is **not** a strict Pareto dominance (recall is ~1 fall window below Variant F, not a significant gap) but a **large false-alarm reduction at matched recall with better clean accuracy and durability**. Per the promotion rule, Variant G G1 **now has two-seed evidence** and may be reported as a validated alternative operating point to Variant F — still a window-level, digital-domain, white-box trade-off, **not** solved/certified/clinical/over-the-air robustness. Variant F remains a co-equal final defense (higher recall); G1 is the **lower-false-alarm** validated point.

## Artifacts
- `analysis/validation_threshold_selection.csv`, `analysis/seed44_variantG_G1_selection_candidates.csv`
- `metadata/seed44_variantG_G1_metadata.json`, `logs/seed44_variantG_G1_training_log.csv`
- `figures/fig_G1_seed44_pareto.png`, `figures/fig_G1_seed44_epsilon_sweep.png`
- per-window val + test probability/logit + 18-ε sweep CSVs under `test_eval/`
