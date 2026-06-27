# Variant G — seed-42 pilot report

> **Analysis of the committed seed-42 Variant G pilot** (targeted nonfall→fall hard-negative + source-class-weighted motion margin, on the frozen Variant F base). Three pre-registered settings **G1/G2/G3**, seed 42 ONLY; seeds 44/45/46 not run; loss / class indices / targeted-PGD sign / selection-v2 rule unchanged. Window-level, digital-domain, white-box; test n=500 (45 fall windows), ε=0.030. **No solved / certified / clinical / over-the-air claim.** All metrics computed from the committed per-window probability/logit exports (same method as the Variant F false-alarm diagnostic).

## Decision: **MINIMUM USEFUL**  (best setting: G1 — balanced A+B)

Reason: minimum-useful thresholds met; below pilot tier.

## 1. Clean metrics

| Model | clean acc | clean macro-F1 | clean fall recall | clean FP | clean walk/run→fall | clean precision | clean specificity |
|---|---|---|---|---|---|---|---|
| Variant F seed42 v2safety | 0.734 | 0.690 | 0.978 | — | — | — | — |
| Variant D seed42 (high-recall/high-FP ref) | 0.746 | 0.700 | 1.000 | — | — | — | — |
| FGSM defense seed42 (weak-PGD baseline) | 0.834 | 0.814 | 0.911 | — | — | — | — |
| **Variant G G1 v2safety** | 0.716 | 0.670 | 0.978 | 24 | 3 | 0.647 | 0.947 |
| **Variant G G2 v2safety** | 0.690 | 0.654 | 0.933 | 26 | 7 | 0.618 | 0.943 |
| **Variant G G3 v2safety** | 0.722 | 0.666 | 0.978 | 26 | 3 | 0.629 | 0.943 |

## 2. PGD@0.030 safety metrics

| Model | PGD recall [95% Wilson] | FP | walk/run→fall | specificity | precision | F1 | FGSM recall |
|---|---|---|---|---|---|---|---|
| Variant F seed42 v2safety | 0.667 | 115 | 80 | — | — | — | — |
| Variant D seed42 (high-recall/high-FP ref) | 0.444 | 157 | 120 | — | — | — | — |
| FGSM defense seed42 (weak-PGD baseline) | 0.089 | 54 | 39 | — | — | — | — |
| **Variant G G1 v2safety** | 0.689 [0.543, 0.805] | 104 | 74 | 0.771 | 0.230 | 0.344 | 0.844 |
| **Variant G G2 v2safety** | 0.644 [0.498, 0.768] | 106 | 79 | 0.767 | 0.215 | 0.322 | 0.778 |
| **Variant G G3 v2safety** | 0.489 [0.350, 0.630] | 108 | 76 | 0.763 | 0.169 | 0.251 | 0.733 |

*Context only (not a selection target):* Variant F seed44 v2safety (context) — recall 0.622, FP 112, walk/run 73, PGD-20 0.511.

## 3. False-alarm source anatomy (PGD@0.030)

| Setting | source class | n FA | % of FA | median P(fall) | median entropy |
|---|---|---|---|---|---|
| G1 | lie down | 10 | 9.6 | 0.270 | 1.840 |
| G1 | walk | 35 | 33.7 | 0.297 | 1.798 |
| G1 | pickup | 8 | 7.7 | 0.338 | 1.678 |
| G1 | run | 39 | 37.5 | 0.330 | 1.659 |
| G1 | sit down | 2 | 1.9 | 0.238 | 1.773 |
| G1 | stand up | 10 | 9.6 | 0.320 | 1.704 |
| G1 | **TOTAL** | 104 | 100.0 | — | — |
| G2 | lie down | 10 | 9.4 | 0.312 | 1.806 |
| G2 | walk | 34 | 32.1 | 0.323 | 1.799 |
| G2 | pickup | 6 | 5.7 | 0.303 | 1.832 |
| G2 | run | 45 | 42.5 | 0.352 | 1.624 |
| G2 | sit down | 1 | 0.9 | 0.275 | 1.859 |
| G2 | stand up | 10 | 9.4 | 0.313 | 1.753 |
| G2 | **TOTAL** | 106 | 100.0 | — | — |
| G3 | lie down | 10 | 9.3 | 0.372 | 1.679 |
| G3 | walk | 39 | 36.1 | 0.376 | 1.640 |
| G3 | pickup | 8 | 7.4 | 0.416 | 1.650 |
| G3 | run | 37 | 34.3 | 0.412 | 1.526 |
| G3 | sit down | 2 | 1.9 | 0.412 | 1.612 |
| G3 | stand up | 12 | 11.1 | 0.331 | 1.624 |
| G3 | **TOTAL** | 108 | 100.0 | — | — |

## 4. Confidence inversion before (Variant F) vs after (Variant G)

Medians: **A** = detected true falls, **B** = false alarms. Inversion present when B median P(fall) > A.

| Model | A P(fall) | B P(fall) | gap (B−A) | A margin | B margin | A entropy | B entropy | A conf | B conf |
|---|---|---|---|---|---|---|---|---|---|
| Variant F seed42 (before) | 0.415 | 0.518 | +0.103 | 0.456 | 0.881 | 1.414 | 1.296 | 0.141 | 0.306 |
| Variant G G1 (after) | 0.301 | 0.313 | +0.012 | 0.371 | 0.421 | 1.771 | 1.694 | 0.085 | 0.106 |
| Variant G G2 (after) | 0.322 | 0.329 | +0.007 | 0.513 | 0.576 | 1.792 | 1.719 | 0.130 | 0.138 |
| Variant G G3 (after) | 0.314 | 0.380 | +0.066 | 0.267 | 0.621 | 1.609 | 1.594 | 0.071 | 0.171 |

*Inversion reduced* ⇔ the (B−A) P(fall) gap shrinks substantially vs Variant F's +0.103; *removed* ⇔ gap ≤ 0.

## 5. PGD-20 durability

| Model | PGD-10 recall | PGD-20 recall | PGD-20 / PGD-10 |
|---|---|---|---|
| Variant F seed42 v2safety | 0.667 | 0.644 | 0.97 |
| **Variant G G1 v2safety** | 0.689 | 0.622 | 0.90 |
| **Variant G G2 v2safety** | 0.644 | 0.578 | 0.90 |
| **Variant G G3 v2safety** | 0.489 | 0.356 | 0.73 |

## 6. Wilson intervals (PGD-10 fall recall, n_f=45)

| Model | recall | 95% Wilson |
|---|---|---|
| Variant F seed42 v2safety | 0.667 | [0.521, 0.786] |
| Variant G G1 v2safety | 0.689 | [0.543, 0.805] |
| Variant G G2 v2safety | 0.644 | [0.498, 0.768] |
| Variant G G3 v2safety | 0.489 | [0.350, 0.630] |

## 7. Pareto plot
`figures/fig_variantG_pareto_seed42.png` — recall vs FP for Variant G G1/G2/G3 against Variant F seed42 (★), Variant D (■), FGSM defense (▼); reference lines at recall 0.50 and FP 115.

## 8. PGD epsilon-sweep figure
`figures/fig_variantG_pgd_epsilon_sweep_seed42.png` — 18-point PGD fall recall and false-alarm sweeps for each Variant G v2safety.

## 9. Decision scorecard

| Setting | clean acc≥0.70 | mF1≥0.65 | clean fall R≥0.90 | PGD R≥0.50 | FP<115 | FP≤90 | FP≤80 | wr<80 | wr≤60 | PGD20>0 | PGD20≥50% | PGD20≥75% | inversion | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | reduced | **MINIMUM USEFUL** |
| G2 | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | reduced | **FAIL** |
| G3 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | reduced | **FAIL** |

**Overall decision: MINIMUM USEFUL** (best setting G1).

## Interpretation (thesis-safe)

Variant G G1 **Pareto-improves** Variant F on the attacked frontier (PGD recall 0.689 ≥ 0.667, FP 104 ≤ 115, walk/run 74 ≤ 80) — higher recall *and* lower false alarms — and **substantially reduces the confidence inversion** the diagnostic isolated: the detected-fall-vs-false-alarm median P(fall) gap shrinks from Variant F's +0.103 to +0.012 (~89% smaller), with PGD-20 durability retained (90% of PGD-10). The ablation is consistent: the **targeted hard-negative term (A) is the active ingredient** — G3 (source-weighted only, no targeted term) has the lowest PGD recall and the largest residual inversion. **However**, the result lands at the **minimum-useful** tier, not pilot success: the absolute false-alarm count (104) misses the pre-registered pilot bar (FP ≤ 90 and walk/run ≤ 60), and clean accuracy (0.716) sits below Variant F's 0.734. Per the strict promotion rule (spec §14.9, which requires *at least* pilot success), **Variant F remains the final implemented defense** and Variant G remains future work — but the genuine Pareto move plus the confirmed mechanism (inversion reduced, the central hypothesis of the pilot) is a substantive positive result and a reasonable basis to *consider* a pre-registered seed-44 validation if the false-alarm bar is treated as a stretch rather than a gate. This is a window-level, digital-domain, white-box trade-off operating point, not solved/certified robustness.

## Artifacts
- `analysis/variantG_safety_metrics.csv`, `analysis/variantG_confidence_inversion.csv`
- `figures/fig_variantG_pareto_seed42.png`, `figures/fig_variantG_pgd_epsilon_sweep_seed42.png`
- per-candidate test_eval probability/logit + 18-eps sweep CSVs under `test_eval/`
- training logs/metadata under `logs/`, `metadata/`, `analysis/` (selection candidates)
