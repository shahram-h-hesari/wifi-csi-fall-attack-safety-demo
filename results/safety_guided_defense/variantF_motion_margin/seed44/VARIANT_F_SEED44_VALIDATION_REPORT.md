# Variant F — seed-44 independent validation report

> **Independent validation of the frozen Variant F candidate** (λ_m=1.0, λ_f=1.0, γ_m=γ_f=0.5), scored
> against `seed44_preregistration/VARIANT_F_SEED44_PREREGISTRATION.md` (criteria fixed *before* the run).
> Seed 44 **only**; seeds 43/45/46 not run; no λ/margin/loss/guard change. The **only** code change was
> relaxing the seed-eligibility check in `train_variantF_motion_margin.py` to permit seed 44 (loss,
> λ, margins, guard unchanged). LeNet, same UT-HAR/SenseFi split. Frozen Variant D / Variant E /
> selection-v2 / seed-42 Variant F artifacts not modified. Window-level, digital-domain, white-box; test
> n=500 (45 fall windows), ε=0.030. **No solved / certified / clinical / over-the-air claim.**

## Decision: **STRONG SUPPORT** (primary candidate v2safety)

The frozen Variant F (1.0,1.0) v2safety checkpoint passes **all** STRONG-SUPPORT conditions on the
independent seed, with an operating point remarkably consistent with the seed-42 pilot.

## Results (test, ε=0.030)

| Model | Clean acc | Clean macro-F1 | Clean fall recall | **PGD recall** [95% Wilson] | PGD FP | walk/run→fall | walk/run logit margin | **PGD-20 recall** | collapse ε |
|---|---|---|---|---|---|---|---|---|---|
| FGSM defense seed44 (floor) | 0.928 | — | 1.000 | 0.044 [0.012, 0.148] | 42 | 25 | — | — | — |
| Variant D safety seed44 (FP ref) | 0.722 | — | 0.978 | 0.378 [0.251, 0.524] | 167 | 116 | 1.733 | — | — |
| **Variant F (1.0,1.0) v2safety** | **0.700** | **0.658** | **0.978** | **0.622 [0.476, 0.749]** | **112** | **73** | **0.961** | **0.511** | **0.035** |
| Variant F (1.0,1.0) v2lowFA | 0.690 | — | 0.911 | 0.133 [0.063, 0.262] | 44 | 30 | 0.847 | 0.067 | — |

Cross-seed consistency (Variant F v2safety): seed 42 → recall 0.667 / FP 115 / clean acc 0.734 / margin
0.986 / PGD-20 0.644; **seed 44 → recall 0.622 / FP 112 / clean acc 0.700 / margin 0.961 / PGD-20 0.511**.
The mechanism and operating point **replicated**.

## Criterion-by-criterion (v2safety; pre-registration §3, tiered)

| # | Criterion | Result | Verdict |
|---|---|---|---|
| 1 | Clean accuracy ≥ 0.70 | 0.700 | ✅ (at boundary) |
| 2 | Clean macro-F1 ≥ 0.65 | 0.658 | ✅ (at boundary) |
| 3 | Clean fall recall ≥ 0.90 | 0.978 | ✅ |
| 4 | PGD recall tier (>0.044 / ≥0.20 / ≥0.30) | 0.622 | ✅ **STRONG** (≥0.30) |
| 5 | PGD recall Wilson lower bound > 0 | 0.476 | ✅ |
| 6 | PGD FP ≤ same-seed Variant D (167) | 112 | ✅ (also ≤ 0.70×167) |
| 7 | walk/run → fall ≤ same-seed Variant D (116) | 73 | ✅ |
| 8 | walk/run logit margin < reference (prior-E 2.716) | 0.961 | ✅ (also < Variant D seed44's 1.733) |
| 9 | PGD-20 tier (non-collapse / ≥50% / ≥75% of PGD-10) | 0.511 (= 0.82 × 0.622) | ✅ **STRONG** (≥75%) |
| 10 | No gradient masking (recall non-increasing PGD-10→20) | 0.622 → 0.511 | ✅ |

All ten hold; criteria 4 and 9 reach the **STRONG** tier; FP and walk/run are **strictly below** (not
just comparable to) the same-seed Variant D baseline; geometry improved → **STRONG SUPPORT**.

## The report's required statements

- **Supports / strongly supports / weakly supports / rejects?** **STRONG SUPPORT.**
- **Did the clean guard hold?** **Yes**, on test out-of-sample (acc 0.700 ≥ 0.70, macro-F1 0.658 ≥ 0.65)
  — but **at the boundary**, lower than Variant D's clean accuracy (0.722): a real clean cost.
- **Clean fall recall ≥ 0.90?** **Yes** (0.978).
- **PGD recall met the tiered threshold?** **Yes — STRONG tier** (0.622 ≥ 0.30), Wilson [0.476, 0.749],
  far above the FGSM floor (0.044, fully CI-separated).
- **PGD-20 durability held?** **Yes — STRONG** (0.511 = 82% of PGD-10 recall; no collapse, no masking).
- **False alarms below/comparable to Variant D seed44?** **Below** (112 < 167).
- **walk/run false alarms below/comparable to Variant D seed44?** **Below** (73 < 116).
- **Logit-margin geometry improved?** **Yes** — residual walk/run `logit_fall − logit_true` median 0.961
  vs prior-E reference 2.716 (and < Variant D seed44's 1.733); the margin mechanism transferred.
- **Does Variant F remain the best candidate after independent validation?** **Yes.** On seed 44 it
  **Pareto-dominates** the same-seed Variant D baseline (recall ↑, FP ↓, walk/run ↓) and sits far above
  the FGSM-defense floor; it is the cost-preferred checkpoint at FN:FP ≥ 5:1 (`analysis/cost_curve.csv`).
  The v2lowFA candidate is **REJECT** (recall 0.133, fails the clean guard) — not the primary candidate.

## Honest caveats

- **Two seeds total** (42 design + 44 validation); n_f = 45 (wide CIs; recall vs Variant D overlaps
  slightly — the dominance rests on the large, CI-separated margin over the FGSM floor *and* the lower FP,
  not on a CI-separated recall gap vs Variant D).
- **Clean-accuracy cost:** clean acc 0.700 and macro-F1 0.658 sit at the guard boundary and below Variant
  D's clean accuracy — Variant F buys attacked recall + false-alarm control + geometry at a clean cost.
- λ=(0.5,1.0) was not re-run (it failed the guard on seed 42); only the frozen (1.0,1.0) was validated.
- Window-level, digital-domain, white-box only.

## Thesis-safe interpretation

Across an independent seed, the margin-aware Variant F defense **improves the attacked recall /
false-alarm trade-off versus Variant D and the FGSM defense, with the residual-motion-false-alarm
geometry measurably improved and recall durable under stronger PGD**, at a clean-accuracy cost. This now
constitutes **two-seed (42 + 44) evidence for a margin-aware safety-proxy defense trade-off** on
processed CSI tensors. It is **not** a solved defense, **not** certified robustness, **not** clinical
validation, and **not** an over-the-air result; the claim is a window-level, digital-domain, white-box
**trade-off operating point** with quantified uncertainty.

## Artifacts
- Comparison: `variantF_seed44_comparison.csv`; scorecard: `analysis/criteria_scorecard.csv`;
  decision: `analysis/decision.txt`; Wilson: `analysis/wilson_intervals.csv`;
  geometry: `analysis/logit_margin_geometry.csv`; cost: `analysis/cost_curve.csv`;
  figure: `figures/fig_pareto_seed44.png`.
- Variant F seed-44 training log/candidates/metadata under `logs/`, `analysis/`, `metadata/`;
  per-checkpoint test-eval (single-ε, 18-ε sweeps, probability/logit, PGD-20) under `test_eval/`.
- Same-seed Variant D baseline (trained once, frozen recipe) under
  `checkpoints/safety_guided_defense/seed44/` and `results/safety_guided_defense/seed44/`.
