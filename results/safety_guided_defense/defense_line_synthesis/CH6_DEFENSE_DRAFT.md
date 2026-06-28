# Chapter 6 — Robustness Enhancement: A Safety-Proxy Defense Trade-off (reviewable draft)

> **Reviewable draft only — NOT inserted into the live thesis `.tex`.** This file drafts the Chapter 6
> defense narrative from committed evidence so it can be reviewed before any Overleaf edit. All numbers
> trace to committed artifacts under `results/safety_guided_defense/` and the math to
> `results/thesis_math_documentation/thesis_math_snippets.tex`. Equation labels (`eq:...`) refer to that
> committed snippet file; notation is kept identical. **Scope of every claim in this chapter:**
> window-level, digital-domain (perturbations on the processed CSI tensor, Eq.~\ref{eq:perturb-domain}),
> white-box, on UT-HAR/SenseFi processed CSI windows (Eq.~\ref{eq:processed-window}), LeNet classifier,
> test split $n=500$ with $n_f=45$ fall windows, headline budget $\epsilon=0.030$. **No certified-robustness,
> no clinical-validation, no over-the-air, and no deployment-readiness claim is made anywhere in this
> chapter.** The result is reported as a *safety-proxy defense trade-off*, not as solved robustness.

---

## 6.1 Overview and chapter claim

Chapter 5 established that an undefended WiFi-CSI fall/activity classifier, while accurate on clean
windows, loses fall recall catastrophically under small white-box $\ell_\infty$ perturbations of the
processed CSI tensor, and that the safety-relevant failure is two-sided: missed falls (false negatives)
*and* confident false fall alerts (false positives) from motion classes (walk, run). This chapter develops
and evaluates a sequence of training-time defenses that target that safety-proxy failure, culminating in
an implemented **margin-aware defense (Variant F)** that is independently validated on a held-out seed.

**Chapter claim (thesis-safe).** Relative to a strong adversarial-training baseline, the implemented
margin-aware defense **improves the attacked safety-proxy trade-off** on processed WiFi-CSI windows: it
**raises PGD@0.030 fall recall while simultaneously reducing false fall alerts**, and it does so with a
**measurably improved residual false-alarm logit geometry** and recall that is **durable under stronger
PGD**. This is demonstrated as a **two-seed result** (one design seed, one pre-registered independent
validation seed). The improvement is a *trade-off operating point with quantified uncertainty* — it is
**not** a solved defense and is reported with its costs (a clean-accuracy reduction) and its limitations
(residual false alarms that, as a dedicated diagnostic shows, are **not** removable by post-hoc
thresholding). A principled next objective (Variant G) was **subsequently executed** — and extended through
Variant H, Option A/A1, and Option B (an adaptive false-alarm-rate controller); §6.9 reports that extended
line as a **diagnostic negative result** that reached a *representation-level frontier limit* rather than the
joint safety target. The implemented **positive** contribution of this chapter therefore remains **Variant
F**, while the extended line's contribution is the **delineation of the safety-proxy recall / false-alarm
frontier** itself.

The chapter proceeds along the defense arc: preliminaries and the threat model (§6.2); the FGSM baseline,
Variant D, Variant E, and selection-v2 (§6.3); the implemented margin-aware **Variant F** (§6.4), with its
seed-42 design (§6.4.2) and seed-44 pre-registered validation (§6.4.3); supporting tables (§6.5) and figure
placeholders (§6.6); the residual false-alarm diagnostic and its confidence-inversion limitation (§6.7);
Variant G as future work (§6.8, **superseded**); the discussion of the executed defense line and its
representation-level frontier limit (§6.9); and conclusions (§6.10).

---

## 6.2 Preliminaries: threat model, classifier, and safety-proxy metrics

The classifier produces logits $z_\theta(x)\in\mathbb{R}^{7}$ and class probabilities by softmax
(Eq.~\ref{eq:logits}–\ref{eq:argmax}). Attacks are white-box $\ell_\infty$ perturbations of the processed
CSI tensor: FGSM (Eq.~\ref{eq:fgsm}) and projected gradient descent (PGD, Eq.~\ref{eq:pgd}). Unless stated
otherwise, **evaluation** PGD uses $M=10$ steps, $\alpha=\epsilon/6$, at $\epsilon=0.030$; an 18-point
budget sweep (Eq.~\ref{eq:eps-sweep}) and collapse-$\epsilon$ thresholds (Eq.~\ref{eq:collapse-half}–\ref{eq:collapse-drop})
characterize budget sensitivity. The perturbation is digital-domain on the processed tensor
(Eq.~\ref{eq:perturb-domain}) — not physical RF injection, channel spoofing, or over-the-air transmission.

Because the safety question is "are falls detected, and are false alerts controlled," the chapter reports
**safety-proxy metrics** over the binary fall-alert reduction (Eq.~\ref{eq:fall-binary}): fall recall and
miss rate (Eq.~\ref{eq:recall-miss}), false fall alerts $FP_f$ (Eq.~\ref{eq:ffa}), specificity and PPV
(Eq.~\ref{eq:spec-ppv}), binary $\mathrm{F1}_f$ and macro-F1 (Eq.~\ref{eq:f1-macro}), and the
class-normalized motion false alarms $FA_{\mathrm{walk/run}\to f}$ (Eq.~\ref{eq:class-fa}–\ref{eq:motion-fa}).
All recall estimates are reported with 95% Wilson intervals (Eq.~\ref{eq:wilson}); with $n_f=45$ these
intervals are wide and overlapping, so differences of a few fall windows are **not** overclaimed, whereas
false-alarm counts over $455$ non-fall windows are comparatively stable.

---

## 6.3 The defense arc, step by step

### 6.3.1 FGSM adversarial-training baseline (§6.2 step 1)

The baseline is standard FGSM adversarial training: the classifier is trained on FGSM-perturbed windows
(Eq.~\ref{eq:fgsm}) under cross-entropy (Eq.~\ref{eq:ce}). It hardens the model against the weak,
single-step attack it trains on but **does not** withstand the stronger iterative PGD attack used for
evaluation: PGD@0.030 fall recall is **0.089** (seed 42) and **0.044** (seed 44). The seed-44 figure,
$R_f=0.044$ with Wilson interval $[0.012,0.148]$, serves throughout the chapter as the **same-seed recall
floor**: any defense claiming attacked robustness must clear this floor with a Wilson lower bound above it.

### 6.3.2 Variant D — fall-weighted FGSM+PGD multi-$\epsilon$ defense (step 2)

Variant D recovers attacked fall recall by combining three ingredients: (i) a **fall-weighted
cross-entropy** $\mathcal{L}_{\mathrm{FWCE}}$ with fall-class weight $w_{c_f}=3$ (Eq.~\ref{eq:fwce}) that
penalizes missed falls more heavily; (ii) a **batch-split mixture** of 50% clean, 25% FGSM, 25% PGD
windows; and (iii) **multi-$\epsilon$** training perturbations sampled from $\{0.005,0.015,0.030\}$. The
objective is Eq.~\ref{eq:variantD-loss}. This is an *experimental adversarial-training recipe, not a
certified defense.*

Variant D succeeds at its goal and exposes the central tension of the chapter: it **recovers recall but
pays heavily in false alarms.** On seed 42 PGD recall rises to **0.444** but false alerts climb to
**157** (walk/run 120); the pattern replicates on seeds 43 and 44 (Table 6.1). Variant D **seed 44** —
$R_f=0.378\,[0.251,0.524]$, $FP_f=167$, walk/run $116$, residual motion margin $1.733$ — is used as the
**same-seed false-alarm reference** against which later variants are measured.

### 6.3.3 Variant E — motion hard-negative penalty (step 3)

Variant E attacks the false-alarm side directly with a **motion hard-negative penalty** added to the
fall-weighted objective (Eq.~\ref{eq:variantE-loss}): it penalizes the **fall probability** assigned to
adversarial walk/run windows (Eq.~\ref{eq:variantE-motion}, over the adversarial-motion set
Eq.~\ref{eq:variantE-set}), with $\lambda_{\mathrm{motion}}=1.0$. On the favorable seed-42 epoch it cuts
false alerts from Variant D's 157 to **117** (walk/run 80) while lifting clean accuracy.

Variant E also surfaces two problems that motivate the remaining arc. First, it is **selection-sensitive**:
on seed 43 the chosen checkpoint suffered a **clean collapse** (clean accuracy 0.630), revealing that the
default checkpoint rule could select a clean-weak model. Second, and decisively, the penalty is on the
fall *probability*, not a *margin*: as Eq.~\ref{eq:variantE-motion}'s limitation note states, it can reduce
the **number** of motion false alarms but does **not** guarantee that residual false alarms become
low-confidence. The residual walk/run false alarms retain a large positive logit margin $m_{f,y}$
(Eq.~\ref{eq:margin-def}) — they are confidently wrong.

### 6.3.4 Selection-v2 — clean-stability-aware checkpoint selection (step 4)

Selection-v2 addresses the *selection* failure without touching the loss. It strengthens the eligibility
**guard** to $\mathrm{Acc}^{\mathrm{val}}_{\mathrm{clean}}\ge 0.70 \wedge \mathrm{MacroF1}^{\mathrm{val}}_{\mathrm{clean}}\ge 0.65$
(Eq.~\ref{eq:v2-guard}, up from the original 0.60/0.50), ranks eligible checkpoints by a validation-only
**SafetyScore** (Eq.~\ref{eq:safetyscore}) with normalized false-alarm burden NFAB (Eq.~\ref{eq:nfab}), and
saves four candidate checkpoints per run (`v2safety`, `v2maxrec`, `v2lowFA`, `v2macroF1`). The motivation is
the empirical validation-to-test reliability gap (Eq.~\ref{eq:valtest-gap}): validation recall transferred
poorly on one seed while false-alarm counts transferred reliably, so selecting on **clean guards + false
alarms** (and saving multiple candidates) is more robust than selecting on validation recall.

Selection-v2 **fixes the clean instability but reveals recall fragility.** On seed 43 the guard-clean
checkpoint is recovered (clean accuracy 0.720) but PGD recall drops to **0.111** at $FP_f=79$, and the
recall collapses to $0$ under stronger PGD (collapse-$\epsilon$ 0.000). Selection alone, on the Variant
D/E loss, therefore rides an unfavourable frontier: it can lower false alarms only by sacrificing attacked
recall. This is the precise gap that Variant F's loss is designed to close.

---

## 6.4 Variant F — the implemented margin-aware defense (step 5)

### 6.4.1 Objective

Variant F keeps the Variant D adversarial-training scaffolding (fall-weighted CE, batch-split clean/FGSM/PGD
mix, multi-$\epsilon$) and the selection-v2 guard, and replaces the *probability* penalty of Variant E with
**two logit-margin terms on the adversarial sub-batch** — the **implemented Variant F objective**:

$$
\mathcal{L}_{F} \;=\; \mathcal{L}_{\mathrm{FWCE}}
\;+\; \lambda_m\, \mathcal{L}_{\mathrm{motion}}^{\mathrm{margin}}
\;+\; \lambda_f\, \mathcal{L}_{\mathrm{fall}}^{\mathrm{margin}},
$$

with the **motion margin** (push the true walk/run logit above the fall logit on adversarial motion
windows)

$$
\mathcal{L}_{\mathrm{motion}}^{\mathrm{margin}}
=\frac{1}{\lvert\mathcal{B}^{\mathrm{adv}}_{\mathrm{motion}}\rvert}
\sum_{i\in\mathcal{B}^{\mathrm{adv}}_{\mathrm{motion}}}
\max\!\big(0,\ \gamma_m + z_f(x_i^{\mathrm{adv}}) - z_{y_i}(x_i^{\mathrm{adv}})\big),
$$

and the **fall-preservation margin** (keep the fall logit above the largest non-fall logit on adversarial
true falls)

$$
\mathcal{L}_{\mathrm{fall}}^{\mathrm{margin}}
=\frac{1}{\lvert\mathcal{B}^{\mathrm{adv}}_{\mathrm{fall}}\rvert}
\sum_{i\in\mathcal{B}^{\mathrm{adv}}_{\mathrm{fall}}}
\max\!\big(0,\ \gamma_f + \max_{c\neq c_f} z_c(x_i^{\mathrm{adv}}) - z_f(x_i^{\mathrm{adv}})\big).
$$

The frozen configuration is $\lambda_m=\lambda_f=1.0$, $\gamma_m=\gamma_f=0.5$, fall weight 3.

> **Note for thesis integration / math package.** The committed math snippet
> `eq:margin-loss-future` (`thesis_math_snippets.tex`) currently labels a single margin term as *future
> work*. In the thesis this must be **promoted to the implemented Variant F objective** shown above: it is
> implemented (`scripts/train_variantF_motion_margin.py`), trained, evaluated, and independently validated.
> The motion margin generalizes `eq:margin-loss-future` to the adversarial-motion sub-batch, and a second
> **fall-preservation** margin is added to protect attacked true-fall recall. (Variant G, originally framed
> as future work in §6.8, was subsequently executed; its outcome and that of the variants after it are
> recorded in §6.9.)

The two terms are complementary and directly target the §6.3.3 limitation: the motion margin removes the
positive false-alarm margin $m_{f,y}$ (Eq.~\ref{eq:margin-def}) that the probability penalty left intact,
while the fall-preservation margin defends the recall that selection-v2 showed was fragile.

### 6.4.2 Seed-42 design result

On the design seed (42), Variant F `v2safety` attains PGD@0.030 fall recall **0.667 [0.521, 0.786]** at
$FP_f=115$ (walk/run 80), clean accuracy 0.734, residual walk/run logit margin **0.986** (down from prior
Variant E's 2.716), and PGD-20 recall **0.644**, with collapse-$\epsilon$ 0.035. Against the same-seed
references it **Pareto-dominates** (Eq.~\ref{eq:pareto}) both selection-v2 ($0.356\,[0.232,0.502]$ / FP 117)
and Variant D ($0.444$ / FP 157), and its Wilson interval is **separated** from selection-v2's. The
$\lambda=(0.5,1.0)$ setting failed the clean guard and is reported as a documented negative. Variant F
seed-42 is the **design** operating point; it is not, by itself, the validated result — that requires an
independent seed.

### 6.4.3 Seed-44 pre-registered independent validation

The seed-42 design was frozen and a seed-44 validation was **pre-registered** before running (tiered
success/failure criteria fixed in advance; the only code change permitted was relaxing the seed-eligibility
check, with loss, $\lambda$, margins, and guard unchanged). On the independent seed, Variant F `v2safety`
reproduces the operating point: PGD recall **0.622 [0.476, 0.749]** at $FP_f=112$ (walk/run 73), clean
accuracy 0.700 (macro-F1 0.658, clean fall recall 0.978), residual motion margin **0.961**, PGD-20 recall
**0.511** (82% of PGD-10, no gradient-masking signature, Eq.~\ref{eq:stronger-pgd}). It **Pareto-dominates**
the same-seed Variant D baseline ($0.378$ / FP 167 / walk/run 116) and is **CI-separated** from the FGSM
floor ($0.044\,[0.012,0.148]$). All ten pre-registered criteria pass, with the two tiered criteria (PGD
recall, PGD-20 durability) reaching the **STRONG** tier — a **STRONG SUPPORT** decision. The `v2lowFA`
candidate (recall 0.133, fails the clean guard) is reported as a rejected alternative, not the primary
result.

**Honest cost.** Variant F's clean accuracy (0.734 seed 42; 0.700 seed 44, at the guard boundary) is
**below** Variant D's $\approx0.72$–$0.75$. Variant F buys attacked recall, false-alarm control, and
improved geometry **at a clean-accuracy cost** — this trade is stated, not hidden.

---

## 6.5 Tables

### Table 6.1 — Defense progression (test, $\epsilon=0.030$)

Clean acc / clean macro-F1 / clean fall recall / **PGD fall recall** / PGD false alerts $FP_f$ /
walk/run$\to$fall / residual walk/run logit margin / PGD-20 recall. (`—` = not computed for that row.)

| Model | Seed | Clean acc | Clean mF1 | Clean fall R | **PGD $R_f$** | $FP_f$ | wr$\to$f | wr margin | PGD-20 | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| FGSM defense | 42 | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | — | — | weak-PGD baseline |
| FGSM defense | 44 | 0.928 | — | 1.000 | 0.044 | 42 | 25 | — | — | **same-seed recall floor** |
| Variant D | 42 | 0.746 | 0.700 | 1.000 | 0.444 | 157 | 120 | — | — | high recall, high FA |
| Variant D | 43 | 0.720 | 0.676 | 1.000 | 0.289 | 160 | 119 | — | — | high recall, high FA |
| Variant D | 44 | 0.722 | — | 0.978 | 0.378 | 167 | 116 | 1.733 | — | **same-seed FA reference** |
| prior Variant E | 42 | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | FA$\downarrow$, clean$\uparrow$ |
| prior Variant E | 43 | 0.630 | 0.600 | 0.978 | 0.378 | 151 | 108 | — | — | **clean collapse** |
| selection-v2 | 42 | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 2.716 | — | = prior E (harmless) |
| selection-v2 | 43 | 0.720 | 0.669 | 0.933 | 0.111 | 79 | 50 | — | 0.000 | clean fixed, **recall-fragile** |
| **Variant F (1.0,1.0)** | **42** | 0.734 | 0.690 | 0.978 | **0.667** | 115 | 80 | **0.986** | 0.644 | **Pareto win (design)** |
| **Variant F (1.0,1.0)** | **44** | 0.700 | 0.658 | 0.978 | **0.622** | 112 | 73 | **0.961** | 0.511 | **STRONG SUPPORT (validated)** |

### Table 6.2 — Variant F seed-44 validation (test, $\epsilon=0.030$)

| Model (seed 44) | Clean acc | Clean fall R | **PGD $R_f$** [95% Wilson] | $FP_f$ | wr$\to$f | wr margin | PGD-20 |
|---|---|---|---|---|---|---|---|
| FGSM defense (floor) | 0.928 | 1.000 | 0.044 [0.012, 0.148] | 42 | 25 | — | — |
| Variant D (FA ref) | 0.722 | 0.978 | 0.378 [0.251, 0.524] | 167 | 116 | 1.733 | — |
| **Variant F v2safety** | **0.700** | **0.978** | **0.622 [0.476, 0.749]** | **112** | **73** | **0.961** | **0.511** |
| Variant F v2lowFA | 0.690 | 0.911 | 0.133 [0.063, 0.262] | 44 | 30 | 0.847 | 0.067 |

Variant F `v2safety` Pareto-dominates Variant D and is CI-separated from the FGSM floor; `v2lowFA` is a
rejected low-recall alternative.

### Table 6.3 — Residual false-alarm diagnostic: confidence inversion (PGD@0.030, Variant F `v2safety`)

Medians over **A** = true falls detected under PGD vs **B** = non-fall windows falsely alerted as fall.
Margin column is fall-vs-rest logit margin $z_f-\max_{c\neq c_f}z_c$ (for detected true falls this is the
positive fall margin; for false alarms it is the residual margin over the next class).

| Seed | Group | $n$ | median P(fall) | fall-vs-rest margin | entropy | confidence margin |
|---|---|---|---|---|---|---|
| 42 | A true-fall detected | 30 | **0.415** | 0.456 | **1.414** | **0.141** |
| 42 | B false alarms | 115 | **0.518** | 0.881 | **1.296** | **0.306** |
| 44 | A true-fall detected | 28 | **0.392** | 0.420 | **1.401** | **0.111** |
| 44 | B false alarms | 112 | **0.513** | 0.901 | **1.298** | **0.304** |

**Confidence inversion (both seeds):** the false alarms have **higher** median fall probability, **larger**
fall-vs-rest and confidence margins, and **lower** entropy (i.e. they are *more confident*) than the true
falls the model detects. The ordering required for a post-hoc gate is **reversed**.

### Table 6.4 — What improved, what remains unresolved

| Dimension | Status after Variant F | Evidence |
|---|---|---|
| Attacked fall recall vs Variant D | **Improved** (0.667 / 0.622 vs 0.444 / 0.378) | Tables 6.1–6.2 |
| False fall alerts vs Variant D | **Improved** (115 / 112 vs 157 / 167) | Tables 6.1–6.2 |
| walk/run false alarms vs Variant D | **Improved** (80 / 73 vs 120 / 116) | Tables 6.1–6.2 |
| Residual motion logit geometry | **Improved** (margin 0.99 / 0.96 vs prior-E 2.716, D 1.733) | Table 6.1 |
| PGD-20 durability / masking screen | **Held** (0.644 / 0.511; monotone PGD-10$\to$20) | Table 6.2, Eq.~\ref{eq:stronger-pgd} |
| Independent-seed reproducibility | **Held** (pre-registered STRONG SUPPORT on seed 44) | §6.4.3 |
| Clean accuracy | **Cost** (0.73 / 0.70, below Variant D's 0.72–0.75) | Tables 6.1–6.2 |
| **Absolute false-alarm level** | **Unresolved** (still $\sim$112–115 of 455 non-fall windows) | Table 6.1 |
| **Post-hoc filterability of residual FAs** | **Unresolved — not filterable** (confidence inversion) | §6.7, Table 6.3 |
| Seed breadth | **Limited** (two seeds: 42 design + 44 validation) | §6.7 limitations |

---

## 6.6 Figures (placeholders for thesis integration)

> Figures are committed under `results/safety_guided_defense/.../figures/`; insert as thesis floats.

- **Figure 6.1 — Defense-progression Pareto plot.** PGD@0.030 fall recall vs false alerts $FP_f$ for FGSM
  baseline, Variant D, prior E, selection-v2, and Variant F (seeds 42/44), with the clean guard annotated;
  shows Variant F advancing the recall/false-alarm frontier. *(Placeholder — compose from Table 6.1.)*
- **Figure 6.2 — Variant F seed-42 vs seed-44 Pareto comparison.** Variant F `v2safety` operating points
  against the same-seed Variant D baseline and FGSM floor on each seed, illustrating reproducibility of the
  operating point. *(Source: `variantF_motion_margin/seed44/figures/fig_pareto_seed44.png` + seed-42
  counterpart.)*
- **Figure 6.3 — Confidence-inversion plot.** Fall-probability and entropy distributions of detected true
  falls vs residual false alarms (and the fall-prob–vs–margin / fall-prob–vs–entropy scatters), showing the
  inverted ordering. *(Source: `variantF_false_alarm_diagnostic/figures/fig_separability_seed{42,44}.png`,
  `fig_hist_fallprob_margin_seed{42,44}.png`.)*
- **Figure 6.4 — PGD-20 durability comparison.** PGD-10 vs PGD-20 fall recall for Variant F (seeds 42/44),
  confirming durable recall and no gradient-masking signature (Eq.~\ref{eq:stronger-pgd}). *(Placeholder —
  compose from Table 6.2.)*

---

## 6.7 Limitation: residual false alarms are not post-hoc filterable

A natural question is whether the residual $\sim$112–115 false alarms can simply be removed by a more
conservative decision rule — a probability, margin, or entropy threshold on top of the argmax. A dedicated
diagnostic (`variantF_false_alarm_diagnostic/`) answers this **no**, and the reason is the **confidence
inversion** of Table 6.3.

The diagnostic computes, for every non-fall window falsely alerted as fall under PGD@0.030, its fall
probability, fall-vs-true and fall-vs-rest logit margins, entropy, and confidence margin, on both seeds. It
then sweeps five post-hoc decision rules — (A) fall-probability threshold, (B) top-vs-second logit-margin
threshold, (C) entropy threshold, and the combinations (D) probability$\wedge$entropy and (E)
margin$\wedge$entropy — searching for an operating point meeting false-alarm-control targets. The findings:

1. **Confidence inversion (Table 6.3).** Residual false alarms are *more confident* than detected true
   falls on every axis. Any gate strict enough to remove false alarms removes true falls first. For
   example, requiring $P(\mathrm{fall})\ge 0.50$ drops fall recall to **0.089 / 0.067** while false alarms
   fall only to 68 / 62.
2. **No useful, stable operating point.** Across all five rules, the best F1 is always the *ungated* point;
   meaningful false-alarm reduction forces large recall loss; and of the pre-set (recall, $FP_f$) targets,
   only one is met on **one** seed, none on both. No single threshold is cross-seed stable.
3. **Cost framing.** Under the cost model $\mathrm{Cost}=\lambda_{FN}\,FN_f+\lambda_{FP}\,FP_f$
   (Eq.~\ref{eq:cost}), the raw Variant F point is preferred at every $\lambda_{FN}{:}\lambda_{FP}\ge 2{:}1$
   — the regime relevant to fall monitoring, where a missed fall costs at least as much as a false alert —
   because recall-preserving gates remove at most $\sim$4 false alarms.

**Diagnosis (committed): "Not filterable."** The residual false alarms are high-confidence logit-geometry
errors, not near-boundary noise. They cannot be removed by changing **where** the decision threshold sits;
removing them requires changing **what** is learned — i.e. a new training objective. This is the bridge to
§6.8, and it is reported here as a **limitation of the implemented defense**, not omitted.

This limitation does not weaken the chapter claim; it sharpens it. Variant F demonstrably **compressed** the
motion false-alarm geometry (residual margin 2.716 $\to$ 0.96–0.99) and improved the recall/false-alarm
trade-off, but it did not reduce the residual false alarms to a *filterable* regime. The improvement is a
**safety-proxy defense trade-off**, with a clearly characterized residual failure mode.

---

## 6.8 Variant G — the principled next objective (original design; subsequently executed, see §6.9)

> **Reading note.** This section preserves the *original pre-registered design rationale* for Variant G as it
> stood when first drafted (it motivates the objective from the Variant F diagnostic). Variant G was
> **subsequently implemented, trained, and evaluated**, and the line was extended through Variant H, Option A
> (A1), and Option B. The **executed outcome** — a representation-level frontier limit, a diagnostic
> negative — is in §6.9; read this section as design context, not as a statement that Variant G is unrun.

The diagnostic specifies exactly what a further improvement must do: reduce **confident** adversarial
nonfall$\to$fall errors (concentrated in walk/run, which are 65–70% of residual false alarms) **without**
breaking the clean guard (already at its 0.70 boundary) or the attacked fall recall. A pre-registered
design memo (`variantG_design_memo/`) proposed **Variant G** as the direct response. *(At the time of this
section's drafting Variant G was not yet run; it was **subsequently implemented, trained, and evaluated** —
see §6.9. The design rationale below is retained for context.)*

Variant G keeps the Variant F objective and adds (A) **targeted nonfall$\to$fall adversarial hard
negatives** — examples generated by attacking walk/run/non-fall windows *toward* the fall class, with a
margin pushing the true non-fall logit back above fall — and (B) a **source-class-weighted motion margin**
that concentrates corrective pressure on walk/run; an (C) **false-alert-budget constraint** is applied at
**checkpoint selection**, not as the primary loss, and an (D) **auxiliary binary fall-alert head** is held
as the deeper future direction if (A)+(B) underdeliver. The memo pre-registers seed-42-only pilot settings,
constrained checkpoint selection, and explicit success/failure criteria (including a requirement that the
confidence inversion measurably *reduce*), with seeds 44/45/46 gated behind a genuine seed-42 improvement.
The originally recommended research sequencing was **thesis first, the Variant G seed-42 pilot thereafter, and
additional confirmation seeds last**. *(This sequencing was subsequently carried out — the Variant G seed-42
pilot and its successors were run; §6.9 records the executed outcome as a diagnostic negative.)*

> **Update (superseded by §6.9).** Subsequent to this Variant-F-centric narrative, the Variant G line **and**
> its successors were in fact executed: Variant G (targeted non-fall→fall hard negatives + source-weighted
> motion margin), Variant H (static dual-tail rescue/budget), Option A / A1 (rebalanced static dual-tail with
> a fall-rescue floor), and Option B (an adaptive-Lagrangian false-alarm-rate controller). Their combined
> outcome — a **representation/frontier-level limit**, not a loss-tuning gap — is recorded in §6.9. The
> "future work" framing of §6.8 above is therefore **superseded**: the question it posed was answered, and
> the answer is a diagnostic negative.

---

## 6.9 Discussion: the safety-proxy frontier limit after the full defense line

This section records the outcome of executing the defense line beyond Variant F — Variant G, Variant H,
Option A (A1), and Option B (adaptive-Lagrangian FAR control) — and interprets what the combined evidence
means. Every number below traces to committed artifacts under
`results/safety_guided_defense/variantH_dual_tail_budget/` and is window-level, white-box, digital-domain
($\ell_\infty$ PGD@$\epsilon{=}0.030$ on the processed CSI tensor), on the same UT-HAR/LeNet test split
($n{=}500$, $n_f{=}45$ falls, $455$ non-fall windows).

**Safety-frontier definitions and the joint target (math).** On the binary fall-alert reduction, with
$TP_f, FN_f, FP_f$ the fall true positives, false negatives, and false positives under attack, the two
safety-proxy quantities are the **fall recall** (sensitivity) and the **false-alarm rate** over non-fall
windows:
$$
\mathrm{Recall}_f = \frac{TP_f}{TP_f + FN_f}, \qquad
\mathrm{FAR}_f = \frac{FP_f}{N_{\mathrm{nonfall}}},
$$
with, for this held-out split, $N_{\mathrm{fall}} = TP_f + FN_f = 45$ and $N_{\mathrm{nonfall}} = 455$. The
joint safety target is $\mathrm{Recall}_f > 0.80$ **and** $\mathrm{FAR}_f < 0.10$. Translated to integer
counts on this split:
- $\mathrm{Recall}_f > 0.80$ requires $TP_f \ge 37$, since $36/45 = 0.800$ exactly and the target is strict
  ($37/45 = 0.822$ is the smallest integer recall above $0.80$);
- $\mathrm{FAR}_f < 0.10$ requires $FP_f \le 45$, since $45/455 = 0.0989 < 0.10$ while $46/455 = 0.1011$.

So the joint target is the integer feasible region $\{\,TP_f \ge 37 \ \wedge\ FP_f \le 45\,\}$. None of the
committed operating points (best prior G1 seed44: $TP_f = 27$, $FP_f = 65$; Variant F seed44: $TP_f = 28$,
$FP_f = 112$) lies in it.

### 6.9.1 The correct comparison point: the best prior frontier (Variant G, G1, seed 44)

The strongest *validated* operating point produced by the line is **Variant G setting G1 on seed 44**:
**PGD fall recall $0.600$ ($27/45$), $FP_f=65/455$ (false-alarm rate $14.3\%$), clean guard held (clean
accuracy $0.746$).** This — not the rejected A1 point — is the correct baseline against which later variants
must be judged. It is itself a *partial* operating point: the attacked false-alarm rate is still above $10\%$
and recall is well below $0.80$, so the joint safety target (PGD recall $>0.80$ **and** attacked false-alarm
rate $<10\%$) is **not** met even by the best prior result.

### 6.9.2 Option B (adaptive-Lagrangian FAR control): held-out test result

Option B made the false-alarm-budget weight $\lambda_b$ an **adaptive Lagrange-style multiplier** updated once
per epoch from the validation attacked false-alarm rate, retaining the fall-rescue floor:
$$
\lambda_b(t{+}1) = \mathrm{clip}\!\big(\lambda_b(t) + \eta\,[\,\mathrm{FAR}^{\mathrm{val}}(t) - 0.10\,],\ 0,\ \lambda_{b,\max}\big),
\qquad \lambda_b(0){=}0.25,\ \eta{=}0.10,\ \lambda_{b,\max}{=}1.0,
$$
where $\mathrm{FAR}^{\mathrm{val}}(t)$ is the validation PGD false-alarm rate at epoch $t$ (never the test
set). The bracket is positive when the constraint is violated ($\mathrm{FAR}^{\mathrm{val}} > 0.10$), so
$\lambda_b$ **rises** to apply more false-alarm pressure, and negative when it is satisfied, so $\lambda_b$
**relaxes** toward $0$. Such a controller can drive the operating point *toward* the $\mathrm{FAR} \le 0.10$
boundary, but — as §6.9.3–6.9.4 show — it **cannot manufacture separability** if the attacked fall and
non-fall fall-score distributions overlap. On the held-out test split, the three validation-selected
checkpoints are:

| Option B checkpoint | PGD recall | $FP_f$ | FAR | clean acc | clean guard |
|---|---|---|---|---|---|
| maxscore | 0.422 (19/45) | 59 | 13.0% | 0.694 | **failed** |
| maxrec | 0.667 (30/45) | 85 | 18.7% | 0.668 | **failed** |
| minFA | 0.133 (6/45) | 36 | 7.9% | 0.698 | **failed** |

**Verdict: REJECT / informative negative.** The clean guard ($\mathrm{Acc}_{\mathrm{clean}}\ge 0.70$) that
held on *validation* fails on *test* for all three checkpoints, and none matches the G1-seed44 frontier with
the guard intact: maxrec's higher recall ($0.667$) is bought with worse false alarms ($85$ vs $65$) and a
broken guard — a dominated trade, not a frontier gain.

### 6.9.3 Threshold diagnostic: the failure is representation-level, not selection-level

A natural objection is that a different checkpoint or a different decision threshold would recover the target.
Formally, a one-vs-rest fall threshold $\tau$ on the fall score $s_f(x)$ (predict *fall* iff
$s_f(x)\ge\tau$) traces an operating point
$$
\big(TP_f(\tau),\ FP_f(\tau)\big), \qquad
TP_f(\tau)=\big|\{x{:}\,y{=}\mathrm{fall},\ s_f(x)\ge\tau\}\big|, \quad
FP_f(\tau)=\big|\{x{:}\,y{\ne}\mathrm{fall},\ s_f(x)\ge\tau\}\big|,
$$
and the target is met iff some $\tau$ lands in the feasible region $TP_f(\tau)\ge 37 \wedge FP_f(\tau)\le 45$.
A post-hoc sweep of $\tau$ over the committed PGD test exports (analysis only — no retraining, no new
attacks) shows that region is empty for every checkpoint:

- **No threshold $\tau$ on any Option B checkpoint reaches $TP_f(\tau)\ge 37$ and $FP_f(\tau)\le 45$
  simultaneously.**
- The smallest $\tau$ achieving $TP_f=37$ already incurs **$FP_f\ge 95$** (maxscore 95, maxrec 107, minFA
  122) — roughly $2$–$3\times$ the $45$-false-alarm budget.
- Conversely, holding $FP_f(\tau)\le 45$ caps recall at only **$\sim 0.24$–$0.33$** ($TP_f \approx 11$–$15$).

Because *no* $\tau$ enters the feasible region, the failure is **not** a poorly chosen threshold or
checkpoint; it is a **frontier / separability** failure of the learned representation.

### 6.9.4 Why: attacked score overlap at the fall–vs–walk/run boundary

The mechanism is a **distribution overlap** in the fall score $s_f(x)$. Write the attacked fall-score
distributions for the two groups as $s_f(x^{\mathrm{adv}}\mid y{=}\mathrm{fall})$ and
$s_f(x^{\mathrm{adv}}\mid y{\ne}\mathrm{fall})$. A single threshold $\tau$ can separate the classes only if
these distributions are (near-)disjoint; when they overlap, any $\tau$ in the overlap simultaneously admits
true falls and false alarms, so no $\tau$ achieves high $TP_f$ and low $FP_f$ at once. Empirically the overlap
is severe: under PGD the fall-score on genuine attacked **fall** windows is pushed **down** (median
$\approx 0.13$–$0.27$) into the **upper tail of the fall-score on attacked non-fall windows** (non-fall upper
quartile $\approx 0.07$–$0.15$). This is exactly why the trade is forced — **lowering $\tau$ raises
$TP_f$ but also $FP_f$; raising $\tau$ lowers $FP_f$ but collapses $TP_f$** — and it makes the feasible region
of §6.9.3 empty. This is the same
trade — reduce false alarms $\Rightarrow$ recall collapses; raise recall $\Rightarrow$ false alarms climb —
seen numerically across every variant. Error-routing confirms the locus: under attack, missed falls are
predicted mostly as **walk/run**, and false alarms originate mostly from **walk/run**. The **fall $\leftrightarrow$
walk/run boundary** is the persistent hard-confusion region; the perturbation collapses falls and locomotion
into one another, and a safety-proxy loss reshaping the LeNet decision surface cannot pull them back apart.
This is the same confidence-inversion / not-filterable phenomenon first diagnosed for Variant F (§6.7),
now shown to persist through targeted hard negatives, dual-tail rescue, and adaptive FAR control.

### 6.9.5 Thesis-safe interpretation

These are **safety-proxy, window-level, white-box, digital-perturbation** results on processed CSI tensors,
reported at research stage with quantified uncertainty. They are **not** claims of clinical validation,
deployment readiness, product performance, certified robustness, or over-the-air resistance. Option B and the
broader G/H/A line are best presented as a **diagnostic negative result**: they clarify that, on this
shallow-CNN representation, *loss-reweighting alone* — whether static motion margins, targeted hard
negatives, static dual-tail rescue/budget terms, or an adaptive Lagrangian controller — **cannot** separate
the attacked fall and non-fall score distributions enough to meet the joint recall/false-alarm target. The
contribution is the **delineation of a safety-proxy recall / false-alarm frontier that conventional accuracy
or single-operating-point reporting would obscure**, together with a mechanistic localization of the residual
obstacle to the fall/locomotion boundary.

### 6.9.6 Future-work bridge

- **Stop further LeNet loss-reweighting.** The threshold diagnostic settles this question for the shallow CNN:
  the barrier is representation-level, so additional $\lambda$ variants on the same backbone are not
  scientifically justified.
- **One narrow, pre-registered architecture test — only if time allows.** The committed cross-architecture
  pilots show that *undefended* GRU, BiLSTM, Transformer, and ResNet-18 all collapse to $\approx 0\%$ attacked
  fall recall under PGD@0.030 — so capacity alone is **not** robustness. However, those backbones carry
  substantially higher *clean* headroom (clean fall recall $0.89$–$0.98$, clean accuracy $\approx 0.81$ for
  BiLSTM) than defended-LeNet ($\approx 0.70$), which is precisely the axis on which A1 and Option B failed to
  generalize. A *single* defended **BiLSTM or Transformer**, seed 42 only, under the **frozen Variant G1
  objective** (no new loss tuning), evaluated on the same held-out protocol, would test one specific
  hypothesis: whether a stronger clean backbone keeps the clean guard above $0.70$ on test while the safety
  objective still recovers attacked recall. This is a bounded test of one hypothesis, not a likely solution —
  the score-overlap barrier may persist with better features.
- **Temporal / event-level aggregation is future work.** Declaring a fall only when several neighboring
  windows agree could suppress *isolated* false alarms, but it (a) cannot be tested post-hoc on the current
  per-window exports, which lack verified temporal contiguity/event identity, and (b) **changes the
  evaluation unit** from window to event — so any gain must be reported as event-level post-processing, not a
  window-level robustness improvement, and must not be framed as deployment readiness (a white-box adaptive
  adversary can target a run of windows).

---

## 6.10 Conclusions

- **Variant F is the strongest implemented defense result of this thesis.** Built on fall-weighted
  adversarial training with two logit-margin terms (the implemented Variant F objective of §6.4.1), it is
  the endpoint of a disciplined arc — FGSM baseline → Variant D → Variant E → selection-v2 → Variant F.
- **It provides two-seed evidence for an improved attacked recall / false-alarm trade-off.** On a design
  seed and a **pre-registered independent validation seed**, Variant F raises PGD@0.030 fall recall (0.667
  / 0.622) while reducing false fall alerts (115 / 112) and walk/run false alarms (80 / 73) relative to the
  Variant D baseline, with improved residual logit geometry and PGD-durable recall — a **STRONG SUPPORT**
  pre-registered outcome. This is reported as a **safety-proxy defense trade-off**, achieved at a stated
  clean-accuracy cost.
- **It still leaves high false alarms.** Roughly 112–115 of 455 non-fall windows remain falsely alerted
  under PGD@0.030; the absolute false-alarm level is **not** resolved.
- **Those false alarms are not threshold-filterable, because of confidence inversion.** A dedicated
  diagnostic shows the residual false alarms are *more confident* than the detected true falls on every
  axis, so no probability/margin/entropy gate yields a stable, useful operating point across both seeds.
  The residual failure is one of learned decision geometry, not of threshold placement.
- **The defense line beyond Variant F was executed and reached a representation-level limit (§6.9).** Variant
  G's best validated point (G1, seed 44: PGD recall $0.600$, $FP_f=65$, clean guard held) is the strongest
  partial operating point but does **not** meet the joint target; Variant H, Option A (A1), and Option B
  (adaptive-Lagrangian FAR control) are all **rejected**. A post-hoc threshold diagnostic shows **no decision
  threshold on any Option B checkpoint reaches $TP\ge 37$ with $FP_f\le 45$** (reaching $TP=37$ costs
  $FP_f\ge 95$), so the residual failure is **representation/frontier-level**, not checkpoint- or
  threshold-selection — the attacked fall and non-fall fall-scores overlap at the fall$\leftrightarrow$walk/run
  boundary.
- **Consequently, further LeNet loss-reweighting is not pursued.** The diagnostic value of the extended line
  is to delineate a safety-proxy recall / false-alarm frontier and localize its obstacle; a single
  pre-registered defended **BiLSTM/Transformer** run under the frozen G1 objective, and (separately)
  event-level aggregation, are framed as **bounded future work**, not results of this thesis.

**Scope reminder.** Every claim above is window-level, digital-domain, white-box, on processed CSI tensors.
None of it constitutes certified robustness, clinical validation, an over-the-air result, or a
deployment-readiness claim.
