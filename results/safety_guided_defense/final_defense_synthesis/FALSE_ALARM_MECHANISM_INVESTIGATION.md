# False-alarm mechanism investigation — why Variant G G1 still raises 65 PGD false alarms on seed 44

> **Analysis / documentation only.** No training, no attacks, no new seeds, no script change, no `.tex`
> edit, no artifact overwrite. Built from committed per-window probability/logit CSVs (Variant G G1 seed-44
> and Variant F seed-44 v2safety; clean / PGD-10 / PGD-20) through commits `656cd50` and `03743b9`,
> using the same method as the committed diagnostics (`diagnose_variantG1_filterability.py`,
> `analyze_variantG_g1_seed44.py`). Window-level, digital-domain, white-box; seed-44 test n=500, **455
> non-fall windows**, 45 fall windows, ε=0.030. **No solved / certified / clinical / over-the-air claim.**

## Question

Why does Variant G G1 still produce **65 PGD false-fall alarms** on seed 44, and what **mathematical
factor** should the next objective target to push **below a 10 % attacked non-fall false-alarm rate**
(FP ≤ 45 of 455) while keeping attacked fall recall **≥ 0.50**?

## Headline answer (decision C)

**A < 10 % attacked false-alarm rate is not reachable by post-hoc gating of G1 without collapsing recall —
it likely requires a new training objective.** Forcing FP ≤ 45 on the committed G1 seed-44 outputs drops
PGD recall to **0.356** (below the 0.50 floor); the best recall-preserving gate reaches only ~FP 55–59. The
residual 65 false alarms are **upper-tail walk/run confusions** (73.8 % motion) that remain **more
confident than the detected true falls** and **durable under stronger PGD** — a learned-geometry /
upper-tail-risk problem, not a thresholding one. The mathematical lever for the next objective is the
**upper tail of the non-fall fall-vs-true-class margin** $z_f(x^{adv})-z_y(x^{adv})$, $y\in\mathcal{N}$.

---

## 1. Current best result and remaining gap

| metric (seed-44 test, ε=0.030) | Variant F v2safety | **Variant G G1 v2safety** | direction |
|---|---|---|---|
| PGD fall recall [Wilson] | 0.622 [0.476, 0.749] | **0.600 [0.455, 0.730]** | ≈ (−1 fall window) |
| PGD false alarms (FP) | 112 | **65** | ↓ −47 |
| **FA rate among non-fall** (FP/455) | 24.6 % | **14.3 %** | ↓ |
| walk/run→fall | 73 | **48** | ↓ −25 |
| clean accuracy | 0.700 | **0.746** | ↑ |
| clean fall recall | 0.978 | 0.956 | ✓ ≥0.90 |
| PGD-20 recall | 0.511 | **0.600** | ↑ (durable) |
| confidence-inversion gap (B−A median P(fall)) | +0.121 | **+0.043** | ↓ (less inverted) |

- **FP reduction already achieved by G1:** 112 → 65 = **47 fewer false alarms (−42 %)**; rate 24.6 % →
  14.3 %.
- **Remaining reduction needed for FP ≤ 45 (<10 %):** 65 → 45 = **≥ 20 fewer FP windows** (rate 14.3 % →
  9.9 %).
- **Recall cost that would be unacceptable:** any drop below **0.50** (the pre-registered floor). Gating G1
  to FP ≤ 45 forces recall to **0.356** — a loss of ~0.24 (≈ 11 of 45 true falls missed). That is an
  **unacceptable** recall cost; it trades the safety objective (catch falls) for the false-alarm objective.

---

## 2. False-alarm source anatomy (65 G1 seed-44 PGD false alarms)

| true (source) class | n FA | % of FP |
|---|---|---|
| run | 28 | 43.1 % |
| walk | 20 | 30.8 % |
| stand up | 10 | 15.4 % |
| lie down | 3 | 4.6 % |
| pickup | 3 | 4.6 % |
| sit down | 1 | 1.5 % |
| **walk + run (motion)** | **48** | **73.8 %** |
| other non-fall | 17 | 26.2 % |

**Diagnosis: A — mostly walk/run motion confusion**, and within that **run-dominant** (43.1 %, the single
largest source). Motion classes account for **73.8 %** of the residual false alarms; the non-motion tail
(stand-up 15 %, lie/pickup/sit ~11 %) is secondary. This matches the source-weighted-margin design intent
($s_{\mathcal{M}}=2$) — the term reduced motion FAs (73 → 48 walk/run vs Variant F) but did **not**
eliminate the hardest motion windows.

---

## 3. Score-distribution diagnosis (A = detected true falls, n=27; B = false alarms, n=65)

Median [IQR] on the G1 seed-44 PGD outputs:

| quantity | A: true falls detected | B: false alarms | overlap indicator |
|---|---|---|---|
| P(fall) | 0.340 [0.289, 0.387] | **0.383 [0.337, 0.442]** | only **28 %** of FAs fall below A's median |
| fall-vs-rest margin $z_f-\max_{c\neq f}z_c$ | 0.436 [0.311, 0.553] | **0.634 [0.289, 0.841]** | FAs larger (more confident) |
| entropy | 1.693 [1.433, 1.776] | **1.530 [1.468, 1.728]** | FAs lower (more confident) |
| confidence margin (top1−top2) | 0.116 [0.085, 0.142] | **0.182 [0.078, 0.232]** | FAs larger |
| fall-vs-true-class margin $z_f-z_y$ (FAs only) | — | **0.798 [0.558, 1.096]** | fall beats true class by ~0.8 |
| top-2 class of FAs | — | run 35, pickup 16, walk 11, stand-up 2, lie 1 | motion-adjacent |

**Answers:**
- **Are false alarms still more confident than detected true falls?** **Yes — mildly.** Median P(fall)
  0.383 (FA) vs 0.340 (true): the **+0.043 residual inversion** persists (down from Variant F's +0.121 but
  still > 0). FAs also have larger fall-vs-rest and confidence margins and lower entropy.
- **Separable by probability / margin / entropy / confidence?** **No, not cleanly.** The IQRs overlap
  heavily and the inversion runs the *wrong* way (FAs score ≥ true falls), so any gate strict enough to
  remove FAs removes true falls first — only 28 % of FAs sit below the true-fall median P(fall).
- **Boundary geometry or calibration?** **Predominantly boundary geometry.** The residual FAs carry a real
  **fall-vs-true-class logit margin of ~0.8** — fall genuinely beats the true non-fall class by a
  substantial margin on adversarial motion windows. That is a *learned-margin* problem (the boundary is in
  the wrong place for the hardest windows), with a *secondary* calibration component (the mild residual
  inversion). It is not fixable by rescaling confidence alone.

---

## 4. Post-hoc < 10 % feasibility (diagnostic only — thresholds NOT for deployment)

Sweeping the committed G1 seed-44 outputs over gate families — P(fall), entropy, fall-vs-rest margin,
combined P(fall)+entropy, combined margin+entropy (the fall-vs-true-class margin is not gateable at
inference since the true class is unknown). Raw G1 = recall 0.600 / FP 65 (14.3 %).

| target | achieved? | best rule | τ | PGD recall | FP | walk/run→fall | clean fall recall | clean FP | PGD-20 |
|---|---|---|---|---|---|---|---|---|---|
| recall ≥ 0.50 & **FP ≤ 45** | **NO** | — | — | — | — | — | — | — | — |
| recall ≥ 0.40 & **FP ≤ 45** | **NO** | — | — | — | — | — | — | — | — |
| recall ≥ 0.30 & **FP ≤ 45** | YES | margin+entropy | (0.25, 1.75) | 0.356 | 41 | 33 | 0.911 | 4 | 0.222 |
| recall ≥ 0.50 & FP ≤ 50 | **NO** | — | — | — | — | — | — | — | — |
| recall ≥ 0.50 & FP ≤ 55 | YES | margin | 0.20 | 0.556 | 55 | 40 | 0.911 | 14 | 0.444 |
| recall ≥ 0.50 & FP ≤ 60 | YES | margin | 0.10 | 0.600 | 59 | 43 | 0.956 | 19 | 0.511 |

**Key facts:**
- **The < 10 % target (FP ≤ 45) is infeasible at recall ≥ 0.50** — and even at recall ≥ 0.40. The **maximum
  recall achievable at FP ≤ 45 is only 0.356** (FP 43, margin τ=0.4), confirming that the last ~20 FP cannot
  be removed by thresholding without sacrificing ~0.24 of recall.
- Gating *can* tighten G1 to **FP ≈ 55 at recall 0.556** (12.1 %) or **FP ≈ 59 at recall 0.600** (13.0 %) —
  an incremental improvement, but **still above 10 %**, and PGD-20 durability degrades under the tighter
  margin gate (0.600 → 0.444).
- This is the same wall the Variant F diagnostic hit, only shifted: G1's reduced inversion bought a lower
  *raw* FP, but the residual upper-tail FAs are again not post-hoc separable.

---

## 5. Mathematical interpretation — the dominant failure mode

The evidence selects **A + B + C + D** (and a confirming E):

- **A. Residual walk/run source confusion** — 73.8 % of FAs are motion (run 43 %, walk 31 %).
- **B. False alarms are concentrated in the high-score upper tail of non-fall windows** — the residual FAs
  carry a **fall-vs-true-class margin $z_f(x^{adv})-z_y(x^{adv})\approx 0.8$** (IQR [0.56, 1.10]); they are
  the *worst* non-fall windows, not average ones.
- **C. True falls and false alarms overlap too much for post-hoc gating** — only 28 % of FAs lie below the
  true-fall median P(fall); §4 shows FP ≤ 45 is unreachable at recall ≥ 0.50.
- **D. Confidence inversion is reduced but not enough** — the B−A median P(fall) gap fell +0.121 → **+0.043**
  but remains positive (FAs still more fall-confident).
- **E. PGD-20 indicates remaining *robust* false alarms** — the FAs persist under stronger PGD (raw G1
  PGD-20 recall 0.600 = PGD-10; the false alarms are not weak-attack artifacts).

**In math terms.** Let $r_y(x^{adv}) = z_f(x^{adv}) - z_y(x^{adv})$ be the **fall-over-true-class margin**
on an adversarial non-fall window $y\in\mathcal{N}$. A false alarm is exactly $r_y > 0$. Variant G's
$\mathcal{L}_{src}$ and $\mathcal{L}_{tgt}$ penalize the **mean** of $\max(0,\gamma+r_y)$ over the non-fall
(and targeted) sub-batch, so they push the **average** non-fall window's margin down — which is why the FA
*count* fell 112 → 65. But the residual 65 FAs are the **upper tail** of $r_y$ (median residual $r_y\approx
0.8$): a mean penalty under-weights the worst windows once most of the mass is already on the safe side.
The **false-alert budget constraint** (FP ≤ 45) is a constraint on the **count of $r_y>0$ windows**, i.e.
on the **upper quantiles** of the $r_y$ distribution, not its mean; and the **recall constraint**
(≥ 0.50) forbids paying for that count with the true-fall margin $z_f - \max_{c\neq f}z_c$ on $y=f$. The
two distributions (true-fall scores vs upper-tail non-fall scores) overlap, so a single inference-time
threshold cannot satisfy both constraints. **The next objective must reduce the upper tail of $r_y$
directly** — not its mean — while protecting $\mathcal{L}_{fall}$.

*(F — "representation lacks separability" — is partially implicated by the overlap, but the ~0.8 residual
margin shows the dominant issue is where the boundary sits for the hardest windows, addressable by an
upper-tail training term, before concluding the representation itself is insufficient.)*

---

## 6. Recommended next experiment (justified: < 10 % is not gate-reachable)

Because §4 shows FP ≤ 45 is **not** achievable by G1 gating at recall ≥ 0.50, a new objective is warranted.

### Variant H — false-alert-budget-aware hard-negative defense (design only; NOT run)

$$\mathcal{L}_H = \mathcal{L}_{FWCE} + \lambda_f\,\mathcal{L}_{fall} + \lambda_s\,\mathcal{L}_{src} + \lambda_t\,\mathcal{L}_{tgt} + \lambda_b\,\mathcal{L}_{budget}$$

$$\mathcal{L}_{budget} = \operatorname{TopKMean}_{y\in\mathcal{N}}\Big[\max\!\big(0,\ z_f(x^{adv}) - z_y(x^{adv}) + \gamma_b\big)\Big]$$

i.e. the mean of the hinge over the **top-K most-violating** adversarial non-fall windows in the batch
(largest $r_y+\gamma_b$), where K is set to the **per-batch false-alert budget** (e.g. K ≈ batch-nonfall ×
target-rate).

**Purpose / why this term and not more of $\mathcal{L}_{src}$:**
- Variant G ($\mathcal{L}_{src},\mathcal{L}_{tgt}$) reduces the **average / targeted** non-fall
  vulnerability — it moved the FA count 112 → 65 but leaves the **upper tail**.
- $\mathcal{L}_{budget}$ is a **TopK (quantile-style) penalty** that concentrates gradient on the **worst
  non-fall windows most responsible for false alerts** — directly attacking the upper tail of $r_y$ that
  §5 identifies, which is what a count-based FP ≤ 45 budget actually constrains.
- The goal is **not generic accuracy**; it is **FP ≤ 45 (< 10 %) while PGD recall ≥ 0.50**, with
  $\mathcal{L}_{fall}$ preserved so the recall constraint is not violated.

### Seed-42-only pilot (pre-registered; NOT a full run)
- **One or two settings only**, no random hyperparameter search: e.g. **H1** $(\lambda_b, K, \gamma_b) =
  (1.0,\ K{=}\lceil n^{batch}_{\mathcal{N}}\times 0.10\rceil,\ 0.5)$ on the frozen Variant G G1 base; optional
  **H2** with a larger $\lambda_b{=}2.0$ as the single sensitivity point.
- **Pre-register thresholds before the run** (clean guard 0.70/0.65; clean fall recall ≥ 0.90; success =
  seed-42 PGD FP ≤ 45 at recall ≥ 0.50, or "near" = FP ≤ 50 at recall ≥ 0.50 without recall collapse).
- **Validate on seed 44 only if** seed-42 reaches FP ≤ 45 (or near it) **without recall collapse** — same
  promotion discipline as Variant G (validation-selected gate, test once).
- Reuse all committed eval tooling; the only new code would be the `TopKMean` term in a new
  `train_variantH_*` script + its math-to-code spec — **not** part of this investigation.

---

## 7. What should NOT be done

- **No random hyperparameter search** — Variant H is one or two pre-registered settings, motivated by §5.
- **Do not report any test-tuned threshold as final** — §4 numbers are diagnostic; a real gate must be
  validation-selected and tested once (as in the seed-44 validation).
- **Do not claim < 10 % if recall collapses** — FP 41 at recall 0.356 is *not* a < 10 % success; the recall
  floor (≥ 0.50) is part of the claim.
- **Do not claim deployment readiness** — 14.3 % attacked FP, window-level, no temporal aggregation.
- **Do not move to Chapter 6 drafting before deciding whether the residual false-alarm rate is acceptable
  for the thesis story** — this investigation is that decision input.
- **Do not claim clinical meaning** — "safety-relevant," never "clinically meaningful."

---

## 8. Final decision

**C — < 10 % likely requires a new training objective.** Post-hoc gating of G1 cannot reach FP ≤ 45 at
recall ≥ 0.50 (max recall at FP ≤ 45 is 0.356); the residual upper-tail walk/run false alarms are confident
and PGD-durable, so the count must be reduced at **training time** (the budget-aware Variant H, §6).
*(Secondary note: **D — temporal/event-level aggregation** is a complementary, non-window-level route to a
lower operational false-alert rate; it is out of the current window-level scope and would be an orthogonal
contribution, not a substitute for the training fix.)*

**Two labels:**
- **Research / thesis label: MAJOR MILESTONE.** A diagnosed failure mode (confidence inversion) was
  formalized, implemented, and **two-seed validated**, cutting attacked false alarms ~42 % at matched recall
  with better clean accuracy and durability — a complete, honest math→code→evidence contribution.
- **Deployment / product label: NOT READY.** A 14.3 % attacked non-fall false-alarm rate (and ~24.6 % for
  the higher-recall Variant F) is well above a 10 % operational target; the false alarms are adversarially
  robust; results are window-level, digital-domain, white-box, with no temporal aggregation and no
  over-the-air validation.

*(These labels are intentionally asymmetric: the result is a genuine research milestone yet not
deployment-ready — both statements are true and should be reported together.)*

---

## 9. Math → code → evidence discipline for the next step

The next step, **if taken**, follows the same thesis discipline as Variants F and G — never reverse-engineered:

1. **Observed result** — G1 leaves 65 PGD FAs (14.3 %); gating cannot reach < 10 % at recall ≥ 0.50 (§1–§4).
2. **Mathematical diagnosis** — the residual FAs are the **upper tail** of the non-fall fall-vs-true-class
   margin $r_y = z_f(x^{adv})-z_y(x^{adv})$; a mean penalty under-constrains a count/quantile budget (§5).
3. **Objective design** — add a **TopK/budget-aware** term $\mathcal{L}_{budget}$ targeting that upper tail,
   keeping $\mathcal{L}_{fall}$ for the recall constraint (§6) — *defined/motivated/constrained*, not
   *proved*.
4. **Code mapping** — implement $\mathcal{L}_{budget}$ as a TopK hinge in a new `train_variantH_*` script
   with a committed math-to-code spec and the mandatory sign/assert checks (mirrors Variant G).
5. **Empirical validation** — seed-42 pre-registered pilot → (only if it reaches/nears FP ≤ 45 without
   recall collapse) a pre-registered seed-44 validation with a validation-selected gate; the experiments
   then **support or fail to support** the upper-tail mechanism.

### Scope reminder
Analysis only — no training/attacks/new seeds/script change/`.tex` edit/artifact overwrite. Window-level,
processed CSI tensor, digital-domain, white-box; **not** solved, **not** certified, **not** clinical,
**not** over-the-air.
