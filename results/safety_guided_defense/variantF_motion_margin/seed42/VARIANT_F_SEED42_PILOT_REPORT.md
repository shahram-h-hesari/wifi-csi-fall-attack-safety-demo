# Variant F (margin-aware) — seed-42 pilot report

> **Scope:** seed 42 **only**, LeNet only, same UT-HAR/SenseFi split. Only the three pre-registered λ
> settings were run `(λ_m,λ_f) ∈ {(1.0,0.5),(1.0,1.0),(0.5,1.0)}`; γ_m=γ_f=0.5 fixed. New namespace;
> frozen Variant D / Variant E / selection-v2 scripts and artifacts not modified; no thesis `.tex` edited.
> **Seed 43/44/45/46 untouched.** Window-level, digital-domain, white-box; test n=500 (45 fall windows),
> ε=0.030 unless noted. **No solved / certified / clinical / over-the-air claim.**

**Headline:** **Variant F succeeds and produces a Pareto win.** The best setting, **λ=(1.0,1.0)
v2safety**, **Pareto-dominates both selection-v2 and Variant D** on the recall/false-alarm frontier
(PGD recall **0.667** vs 0.356 / 0.444 at **FP 115** vs 117 / 157), the recall gain is **statistically
meaningful** (Wilson CIs separated), the **logit geometry improved as designed** (residual walk/run
`logit_fall−logit_true` median 2.716 → **0.986**), and recall is **durable under PGD-20** (0.644).

## Objective and method

`L_F = L_FWCE + λ_m·mean_{adv walk/run} max(0, γ_m + z_fall − z_true) + λ_f·mean_{adv fall} max(0, γ_f + max_{c≠fall} z_c − z_fall)`,
fixed γ_m=γ_f=0.5, on the frozen Variant E batch-split mixture (50% clean / 25% FGSM / 25% PGD,
multi-ε {0.005,0.015,0.030}, fall weight 3). Selection reuses the frozen selection-v2 guard
(val clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65) and candidate set (v2safety/v2maxrec/v2lowFA/v2macroF1).
New script `scripts/train_variantF_motion_margin.py` (enforces seed-42-only and the 3 allowed λ
settings). Runtime: ~39 min/setting (CPU), ~2 h total; eval ~44 min.

## Results (test, ε=0.030)

| Model / candidate | Clean acc | Clean macro-F1 | Clean fall recall | **PGD recall** | PGD FP | walk+run→fall | walk/run logit margin | **PGD-20 recall** | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|---|
| FGSM defense | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | — | — | 0.018 |
| Variant D safety | 0.746 | 0.700 | 1.000 | 0.444 | 157 | 120 | — | — | 0.030 |
| prior Variant E safety | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | 0.030 |
| selection-v2 v2safety | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | 0.030 |
| selection-v2 v2lowFA | 0.818 | — | 0.956 | 0.133 | 61 | 36 | — | — | 0.025 |
| **F (1.0,1.0) v2safety** | 0.734 | 0.690 | 0.978 | **0.667** | **115** | 80 | **0.986** | **0.644** | **0.035** |
| F (1.0,0.5) v2safety | 0.780 | 0.808 | 0.956 | 0.644 | 128 | 88 | 1.312 | 0.600 | — |
| F (1.0,1.0) v2lowFA | 0.678 | — | 0.911 | 0.178 | 56 | 46 | 0.901 | 0.133 | — |
| F (1.0,0.5) v2lowFA | 0.776 | — | 0.933 | 0.022 | 30 | 16 | 0.648 | 0.000 | — |
| F (0.5,1.0) | — | — | — | — | — | — | — | — | **failed clean guard** |

Wilson 95% CIs (PGD recall): **F(1.0,1.0) v2safety 0.667 [0.521, 0.786]** (30/45) vs selection-v2 v2safety
0.356 [0.232, 0.502] (16/45) vs Variant D 0.444 [0.309, 0.588] (20/45). The F(1.0,1.0) interval is
**separated** from selection-v2's (0.521 > 0.502) — a statistically meaningful recall gain, not a
few-window artifact.

## Which λ setting performed best

**λ=(1.0,1.0) — clearly.** It gives the highest test recall (0.667) at the lowest false alarms among the
high-recall points (FP 115 < selection-v2's 117), the most-improved geometry (margin 0.986), the most
durable PGD-20 recall (0.644), and the widest collapse-ε (0.035). λ=(1.0,0.5) reaches similar recall
(0.644) but at higher FP (128, walk/run 88) — a more false-alarm-heavy point. λ=(0.5,1.0) **failed the
clean guard** on every epoch (weaker motion penalty → clean accuracy never reached 0.70), so it produced
no eligible v2safety/v2lowFA candidate — a documented negative result.

## Did Variant F succeed, fail, or produce a trade-off point?

**Succeeded — and it is a Pareto win.** Per the pre-registered §6 criteria, **F(1.0,1.0) v2safety passes
8 of 9**: clean acc 0.734 ≥ 0.70 ✓; clean macro-F1 0.690 ≥ 0.65 ✓; clean fall recall 0.978 ≥ 0.90 ✓;
PGD recall 0.667 ≥ selection-v2 0.356 ✓; **FP 115 ≤ selection-v2 117 ✓**; walk/run 80 ≤ 80 ✓; geometry
improved (0.986 < 2.716) ✓; PGD-20 recall 0.644 > 0 ✓; Wilson lower bound 0.521 > 0 ✓. The **only** miss
is the stricter false-alarm target `FP ≤ 0.70 × Variant D = 110` (FP = 115, i.e. 5 alarms over the bound).

## Is it a Pareto win over selection-v2?

**Yes.** F(1.0,1.0) v2safety has recall 0.667 ≥ 0.356 **and** FP 115 ≤ 117 with the clean guard satisfied
⇒ it **dominates** selection-v2 v2safety. It also dominates **Variant D safety** (recall 0.667 > 0.444 and
FP 115 < 157). On the FN:FP cost curve it is the cost-preferred checkpoint at **FN:FP ≥ 5:1** (the
safety-leaning regime); at 1:1–2:1 the low-false-alarm point (F v2lowFA) is preferred.

## Did the logit geometry actually improve?

**Yes — this is the mechanistic confirmation.** The median residual walk/run `logit_fall − logit_true`
dropped from **2.716 (prior Variant E)** to **0.986 (F 1.0,1.0)** and **1.312 (F 1.0,0.5)** — the
motion-margin term pushed the residual false alarms much closer to the decision boundary (from
confidently-fall toward the margin). The fall-margin term simultaneously kept fall logits up, recovering
recall. The margin loss did exactly what it was designed to do.

## Did recall remain durable under PGD-20?

**Yes.** F(1.0,1.0) v2safety PGD-20 recall = 0.644 (from PGD-10 0.667 — minimal drop), versus selection-v2
seed-43 v2safety which collapsed to 0.000 under PGD-20. So the Variant F recall is durable under the
stronger attack, consistent with the wider collapse-ε (0.035 vs 0.030). No gradient-masking signature
(recall does not stay artificially high).

## Should seed 44 later validate selection-v2 or Variant F?

**Variant F (λ_m=1.0, λ_f=1.0, γ=0.5) is now the single best frozen candidate on the design seed** — it
Pareto-dominates selection-v2 (and Variant D) with a statistically meaningful, mechanistically-explained,
PGD-20-durable recall gain. Therefore **seed 44 should validate the frozen Variant F (1.0,1.0)** rather
than selection-v2, under the same pre-registration rigor (clean guard out-of-sample; recall above the
FGSM-defense floor with Wilson lower bound > 0; false-alarm and geometry targets; PGD-20 non-collapse).
**Caveats (honest):** this is **one design seed** (n_f = 45); Variant F trades **clean accuracy**
(0.734 vs selection-v2's 0.806 — a real clean cost, though guard-passing); and it met the
selection-v2-relative false-alarm target (≤117) but not the stricter Variant-D-relative one (≤110).
Independent validation on seed 44 is required before any cross-seed claim.

## Limitations
- Seed 42 only (design seed); not validated; n_f = 45 (wide CIs, though the headline gain is CI-separated).
- Clean accuracy cost (0.734) and the stricter ≤110 false-alarm target not met (FP = 115).
- λ=(0.5,1.0) failed the clean guard — the motion penalty cannot be too weak relative to the fall margin.
- Window-level, digital-domain, white-box only; no clinical / certified / over-the-air claim.

## Artifacts
- Comparison: `variantF_seed42_comparison.csv`; scorecard: `analysis/criteria_scorecard.csv`;
  Wilson: `analysis/wilson_intervals.csv`; geometry: `analysis/logit_margin_geometry.csv`;
  cost: `analysis/cost_curve.csv`; figure: `figures/fig_pareto_variantF.png`.
- Per-setting training logs / candidates / metadata under `logs/`, `analysis/`, `metadata/`;
  per-checkpoint test-eval (single-ε, 18-ε sweeps, probability/logit, PGD-20) under `test_eval/`.
- Checkpoints (local-only, gitignored `*.pt`) under `checkpoints/.../variantF_motion_margin/seed42/`.
