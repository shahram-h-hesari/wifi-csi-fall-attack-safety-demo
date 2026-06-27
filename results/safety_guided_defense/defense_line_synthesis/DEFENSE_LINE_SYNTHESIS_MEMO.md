# Defense-line synthesis memo (Variant D → E → selection-v2 → Variant F)

> **Documentation/synthesis only.** No experiment run, no model trained, no seeds 45–46 run, no thesis
> `.tex` edited, no artifact modified. All numbers are from committed results: window-level,
> digital-domain, white-box evaluation on processed UT-HAR/SenseFi CSI tensors; test n=500 (45 fall
> windows), ε=0.030 unless noted. **No solved / certified / clinical / over-the-air claim.**

## 1. Executive thesis claim

Across two seeds (42 design + 44 pre-registered independent validation), a **margin-aware adversarial
defense (Variant F)** improves the attacked safety trade-off on processed WiFi-CSI windows: relative to a
strong adversarial-training baseline (Variant D) it **raises PGD@0.030 fall recall while reducing
false-fall alarms (including the dominant walk/run → fall errors), measurably improves the residual
false-alarm logit geometry, and keeps fall recall durable under a stronger PGD-20 attack** — at a
**clean-accuracy cost**. This is **window-level, digital-domain, white-box** evidence for a *safety-proxy
trade-off operating point*; it is **not** solved robustness, **not** certified robustness, **not**
clinical validation, and **not** an over-the-air result.

## 2. Defense progression table (test, PGD@0.030)

| Defense (candidate) | seed | Clean acc | Clean macroF1 | Clean fall recall | PGD recall | PGD FP | walk/run→fall | walk/run logit margin | PGD-20 recall | Interpretation |
|---|---|---|---|---|---|---|---|---|---|---|
| FGSM defense | 42 | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | — | — | weak-PGD baseline |
| FGSM defense | 44 | 0.928 | — | 1.000 | 0.044 | 42 | 25 | — | — | **same-seed recall floor** |
| Variant D safety | 42 | 0.746 | 0.700 | 1.000 | 0.444 | 157 | 120 | — | — | high recall, high FA |
| Variant D safety | 43 | 0.720 | 0.676 | 1.000 | 0.289 | 160 | 119 | — | — | high recall, high FA |
| Variant D safety | 44 | 0.722 | — | 0.978 | 0.378 | 167 | 116 | 1.733 | — | **same-seed FA reference** |
| prior Variant E safety | 42 | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | FA↓, clean↑ (lucky epoch) |
| prior Variant E safety | 43 | 0.630 | 0.600 | 0.978 | 0.378 | 151 | 108 | — | — | **clean collapse (epoch 18)** |
| selection-v2 v2safety | 42 | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | = prior E (harmless) |
| selection-v2 v2safety | 43 | 0.720 | 0.669 | 0.933 | 0.111 | 79 | 50 | — | 0.000 | clean fixed, **recall-fragile** |
| **Variant F (1.0,1.0) v2safety** | **42** | 0.734 | 0.690 | 0.978 | **0.667** | 115 | 80 | **0.986** | 0.644 | **Pareto win (design)** |
| **Variant F (1.0,1.0) v2safety** | **44** | 0.700 | 0.658 | 0.978 | **0.622** | 112 | 73 | **0.961** | 0.511 | **STRONG SUPPORT (validated)** |

(Lower walk/run logit margin = residual false alarms closer to the decision boundary = better geometry.)

## 3. Mechanistic story

1. **Variant D (recover recall, pay false alarms).** Fall-weighted FGSM+PGD multi-ε adversarial training
   pushes the boundary toward fall, recovering attacked recall (0.44 / 0.29 / 0.38 across seeds 42/43/44)
   but mapping adversarial high-motion windows to fall (FP ~157–167; walk/run ~116–120).
2. **Variant E (cut motion false alarms, but selection-sensitive).** A probability hard-negative penalty
   `mean P_fall(x_adv)` over adversarial walk/run lowers motion FA *count* (walk/run 120→80 on seed 42),
   but the recall-heavy safety score selects very different epochs per seed (seed 42 clean-strong epoch 56;
   seed 43 clean-weak epoch 18, clean acc 0.630) — **checkpoint-selection sensitivity**, not loss instability.
3. **selection-v2 (fix the selection, lose recall).** A stronger clean guard (val acc ≥0.70 ∧ macro-F1
   ≥0.65) defers selection to a clean-stable epoch: seed-43 clean acc recovers 0.630→0.720 and false alarms
   halve (151→79; walk/run 108→50), but attacked recall drops to 0.111 and **collapses to 0 under PGD-20**.
4. **Math-to-behavior audit (diagnose the real problem).** The residual walk/run false alarms are
   **high-confidence** (median fall-prob ~0.8 vs true-fall ~0.2; large positive `logit_fall − logit_true`,
   margin ~2.7), calibration poor (ECE ~0.5). So thresholding cannot help — it is a **logit-geometry**
   problem, and the recall numbers are few-window (n_f=45, wide CIs).
5. **Variant F (target the geometry, protect recall).** Two margin terms on the adversarial sub-batch:
   a **motion-margin** `max(0, γ_m + z_fall − z_true)` for walk/run (push the true motion class above fall)
   and a **fall-margin** `max(0, γ_f + max_{c≠fall} z_c − z_fall)` for true falls (keep fall on top).
   λ_m=λ_f=1.0, γ=0.5.
6. **seed 42 designed it; seed 44 independently validated it.** The seed-42 pilot found λ=(1.0,1.0) a
   Pareto win; the pre-registered seed-44 run reproduced the operating point and scored **STRONG SUPPORT**.

## 4. Quantitative headline

- **Seed 42 (design):** Variant F v2safety PGD recall **0.667 [0.521, 0.786]** at FP **115**, vs
  selection-v2 0.356 [0.232, 0.502] / FP 117 and Variant D 0.444 / FP 157 → **Pareto-dominates both**;
  Wilson interval **separated** from selection-v2.
- **Seed 44 (independent validation):** Variant F v2safety PGD recall **0.622 [0.476, 0.749]** at FP
  **112**, walk/run **73**, vs Variant D seed-44 0.378 / FP 167 / walk/run 116 (**Pareto-dominates**) and
  vs FGSM floor 0.044 [0.012, 0.148] (**CI-separated**).
- **PGD-20 durability:** seed 42 0.644 (97% of PGD-10) and seed 44 0.511 (82% of PGD-10) — no collapse,
  no gradient-masking signature; collapse-ε 0.035 (vs selection-v2 0.030).
- **Logit-margin improvement:** residual walk/run `logit_fall − logit_true` median **2.716 → 0.986
  (seed 42) / 0.961 (seed 44)** — the margin mechanism transferred.
- **Clean-accuracy cost:** clean acc 0.734 (seed 42) / **0.700 (seed 44, at the guard boundary)**, below
  Variant D's ~0.72–0.75 — the trade-off is real and reported.

## 5. What exactly Variant F contributed

Variant F's contribution is **not** simply higher recall, and **not** simply fewer false alarms — earlier
variants could move either one in isolation (Variant D maximizes recall at high FA; selection-v2 minimizes
FA at low recall). Variant F's specific, mechanistically-confirmed contribution is **a better-placed
decision geometry**: the motion-margin term pushes adversarial walk/run windows back toward their true
class (residual false-alarm margin 2.7 → ~1.0), while the fall-margin term *preserves* attacked fall
recall — so the model gets **higher recall AND fewer false alarms at the same time** (a Pareto move), and
the recovered recall is **durable under a stronger PGD-20 attack**. It converts the prior variants'
either/or trade-off into a strictly better operating point, validated out-of-sample.

## 6. Limitations

- **Two Variant F seeds only** (42 design + 44 validation); seeds 45/46 not run.
- **n_fall = 45** per test split → wide Wilson intervals; the recall gain over Variant D is large but its
  CI overlaps slightly (dominance rests on the lower FP + the CI-separated margin over the FGSM floor).
- **Clean-accuracy cost:** seed-44 clean acc 0.700 and macro-F1 0.658 sit **at the guard boundary** and
  below Variant D — Variant F buys recall/FA/geometry at a clean cost.
- **Digital-domain, white-box, processed-tensor** evaluation only; **UT-HAR/SenseFi**, **LeNet** only.
- No clinical, certified-robustness, or over-the-air claim; PGD-10/20 monotonicity is a masking *screen*,
  not a robustness proof.

## 7. Should we run seeds 45–46?

**Recommendation: D, then B** — *update the thesis first with the current two-seed evidence, then run
seeds 45–46 as confirmatory before final submission.* Reasoning (advisor lens):
- **Is the current evidence enough for a proposal/thesis?** Yes, for a **pre-registered two-seed
  trade-off-study claim** with honest caveats. The contribution (margin-aware geometry fix + recall
  preservation, validated out-of-sample with STRONG SUPPORT) is defensible now.
- **What would seeds 45–46 add?** n=4 Variant F seeds → narrower cross-seed spread and tighter aggregate
  CIs; turns "two-seed evidence" into "four-seed evidence," strengthening (not changing) the claim.
- **What risk do they introduce?** Operating-point variability (as selection-v2 showed across seeds) could
  surface a weaker seed; the **clean accuracy already sits at the guard boundary on seed 44**, so a seed
  that fails the guard is plausible and would require honest reporting (which the pre-registration handles).
- **Time cost:** ~1.5–2 h/seed (Variant F + Variant D baseline + eval) → ~3–4 h for both, CPU.
- **Would they change the thesis claim?** Unlikely to change the *direction*; they would **calibrate the
  confidence** and the reported variance. So they are valuable *confirmation*, not a blocker.

Net: write first (lock framing, expose exactly what to claim), then spend the cheap ~3–4 h on seeds 45–46
to harden the headline contribution before submission. (Not A — stopping forgoes cheap de-risking of the
novel contribution; not C alone — one extra seed is a half-measure when both are cheap.)

## 8. Thesis insertion plan

- **Chapter 6 (Robustness Enhancement / defenses):** present the progression Variant D → E → selection-v2
  → Variant F as the chapter's arc. Insert the defense-loss math from `results/thesis_math_documentation/
  thesis_math_snippets.tex`: fall-weighted CE (`eq:fwce`), Variant D mixed loss (`eq:variantD-loss`),
  Variant E motion penalty (`eq:variantE-loss`/`eq:variantE-motion`), selection-v2 guard + SafetyScore
  (`eq:v2-guard`/`eq:safetyscore`/`eq:nfab`), and the logit-margin definition (`eq:margin-def`).
  **Update needed:** the math doc currently labels the margin loss `eq:margin-loss-future` as *future
  work* — promote it to the **implemented Variant F objective** (two terms: motion margin + fall margin,
  λ_m=λ_f=1.0, γ=0.5) and add the fall-margin equation. Add the progression table (§2) and the seed-42/44
  Pareto figures.
- **Chapter 5 (safety-proxy interpretation):** reinforce that the metrics are safety-proxy (recall / FFA /
  specificity / class-normalized walk/run FA), cite the Wilson-interval treatment (`eq:wilson`) and the
  n_f=45 uncertainty caveat as a standing interpretation rule.
- **Chapter 7 (discussion / limitations):** state the two-seed STRONG-SUPPORT result, the
  clean-accuracy-cost trade-off, the FN:FP cost-curve framing (`eq:cost`), the stronger-PGD masking screen
  (`eq:stronger-pgd`), and the residual-geometry / future-work direction (deeper architectures, more
  seeds, OTA out of scope). Keep the §1 non-claims verbatim (see `math_overclaim_audit.md`).

## 9. Exact next prompt

```
Draft the thesis defense narrative from the committed evidence, ONE CHAPTER AT A TIME, starting with
Chapter 6, WITHOUT inserting into the live thesis yet -- produce a reviewable draft file first.

Constraints:
- Documentation/drafting only: do NOT run experiments, do NOT run seeds 45-46, do NOT train, do NOT edit
  any thesis-overleaf-local .tex file. Write the draft to a NEW file under
  results/safety_guided_defense/defense_line_synthesis/ (e.g. CH6_DEFENSE_DRAFT.md), as LaTeX-ready text.
- Use the progression table and numbers from DEFENSE_LINE_SYNTHESIS_MEMO.md and the equations/labels from
  results/thesis_math_documentation/thesis_math_snippets.tex (do NOT change notation). Promote the
  margin-loss equation from "future work" to the implemented Variant F objective (motion + fall margin);
  flag any "% citation needed" markers, do NOT invent citations.
- Apply every non-claim from results/thesis_math_documentation/math_overclaim_audit.md (no
  solved/certified/clinical/over-the-air; window-level digital-domain white-box; safety-proxy; n_f=45
  uncertainty). Show me the Chapter-6 draft for review and stop; do not commit until I approve.
```
