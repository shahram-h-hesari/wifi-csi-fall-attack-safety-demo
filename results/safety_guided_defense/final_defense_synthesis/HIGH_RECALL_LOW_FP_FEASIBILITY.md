# High-recall / low-false-alarm feasibility investigation

> **Analysis / documentation only.** No training, no attacks, no evaluation, no new seeds, no script
> change, no `.tex` edit, no artifact overwrite. Built from committed per-window probability/logit CSVs
> (Variant G G1 seed-44 and Variant F seed-44 v2safety; clean / PGD-10 / PGD-20) through commit `6d4bd56`,
> using the same method as the committed diagnostics. Window-level, digital-domain, white-box; seed-44 test
> **45 fall windows, 455 non-fall windows**, ε=0.030. **No solved / certified / clinical / over-the-air
> claim.**

## Question

Can we realistically move from the current best **Variant G G1 seed-44** result to **PGD fall recall > 80 %
AND attacked non-fall false-fall rate < 10 %** (FP ≤ 45 of 455)?

## Headline answer (recommendation B)

**No — current G1 cannot reach recall > 80 % AND FP ≤ 45 by operating-point selection, and it is a
*two-tail* problem, not a single-knob one.** Post-hoc gating is a one-directional filter (it can only
*remove* fall alerts, never *create* them), so **the maximum recall achievable over every gate on G1 is
0.600 = the raw value** — recall > 80 % (and even > 70 %) is categorically unreachable post-hoc. The 18
missed falls are **robustly** pushed into run/walk (negative fall margin, same windows missed under
PGD-20), and the 65 false alarms are **upper-tail walk/run** windows. **Reaching the target requires a new
training objective that simultaneously raises the lower tail of the fall margin and lowers the upper tail
of the non-fall fall-risk** — the **dual-tail Variant H** (§6).

---

## 1. Target feasibility gap

**Current Variant G G1 seed-44 PGD confusion (n=500):**

| | TP | FN | FP | TN | recall | FA rate (FP/455) |
|---|---|---|---|---|---|---|
| **Variant G G1 seed44** | **27** | **18** | **65** | 390 | **0.600** (27/45) | **14.3 %** |
| Variant F seed44 | 28 | 17 | 112 | 343 | 0.622 (28/45) | 24.6 % |
| Variant D seed44 | 17 | 28 | 167 | 288 | 0.378 (17/45) | 36.7 % |

**Targets and gaps from G1:**
- recall > 80 % ⇒ **TP ≥ 37** ⇒ **+10 detected fall windows** (27 → ≥37).
- FA rate < 10 % ⇒ **FP ≤ 45** ⇒ **−20 false positives** (65 → ≤45).

**Key statement (explicit):** the next target is **not merely lower FP**. It requires **simultaneously
increasing recall (+10 true falls) AND reducing false alarms (−20)** — moving *both* tails at once. Variant
G already improved the false-alarm side (vs F: FP 65 vs 112) at roughly matched recall; the new target adds
a **recall-raising** requirement that no previous variant has met under attack, on top of a tighter FP bar.

---

## 2. Current recall / false-alarm frontier (post-hoc, diagnostic only)

Sweeping the committed G1 seed-44 outputs over P(fall), entropy, fall-vs-rest margin, and P(fall)+entropy
gates. **A gate can only remove argmax-fall alerts**, so for any gate $g$: $\text{recall}(g)\le 0.600$ and
$\text{FP}(g)\le 65$. Confirmed empirically: **max recall over all gates = 0.600**.

| target | achieved? | reason |
|---|---|---|
| recall ≥ 0.80 & FP ≤ 45 | **NO** | gating cannot raise recall above raw 0.600 |
| recall ≥ 0.70 & FP ≤ 45 | **NO** | gating cannot raise recall above 0.600 |
| recall ≥ 0.60 & FP ≤ 45 | **NO** | FP ≤ 45 forces recall to 0.356 (committed FA investigation) |
| recall ≥ 0.80 & FP ≤ 65 | **NO** | recall cannot reach 0.80 post-hoc |
| recall ≥ 0.70 & FP ≤ 55 | **NO** | recall cannot reach 0.70 post-hoc |
| recall ≥ 0.60 & FP ≤ 55 | **NO** | min FP while retaining all 27 TP is **59** (not ≤ 55) |

**None of the six targets is reachable.** The raw and validation-selected G1 operating points
(recall 0.600 / FP 65) are already the recall-maximal points; gating only trades recall *down* for FP
*down* (best recall-preserving point ≈ FP 59). The recall > 80 % requirement is **structurally impossible**
by any post-hoc rule — it requires the model to *detect more falls*, which only training can do.

---

## 3. Missed-fall diagnosis (18 missed vs 27 detected, G1 seed-44 PGD)

Median [IQR]:

| quantity | detected falls (n=27) | **missed falls (n=18)** |
|---|---|---|
| P(fall) | 0.340 [0.289, 0.387] | **0.179 [0.139, 0.231]** |
| fall margin $m_f = z_f-\max_{c\neq f}z_c$ | +0.436 [0.311, 0.553] | **−0.770 [−1.363, −0.325]** |
| entropy | 1.693 [1.433, 1.776] | **1.365 [1.212, 1.590]** |
| confidence margin | 0.116 | 0.087 |
| top predicted class | fall | **run 11, walk 5, lie-down 2** (16/18 motion) |

**Answers:**
- **Recoverable by thresholding?** **No.** The 18 missed falls have argmax = run/walk (not fall), so a gate
  of the form "alert iff argmax = fall AND …" **cannot recover them** — gating never *adds* a fall
  prediction. Their fall margin is **negative** ($m_f$ median −0.77; **0/18 have $m_f \ge 0$**), so even a
  lenient fall-decision rule would need to overturn a confident run/walk argmax.
- **Confidently pushed into a specific class?** **Yes — run (11/18), then walk (5/18)** = 16/18 motion.
  PGD drives true falls *into the motion classes*, with lower entropy (1.365) than detected falls — a
  **confident** misclassification, not a near-tie.
- **Near boundary or confident?** **Mixed, mostly confident:** of the 18, **7 are near-boundary**
  (−0.5 < $m_f$ < 0) and **11 are strongly negative** ($m_f \le −0.5$, down to −2.45). The ~7 near-boundary
  windows are the realistic "rescue" targets; the 11 strong ones need substantial margin change.
- **Same windows under PGD-20?** **Yes — all 18 missed falls are also missed under PGD-20 (18/18).** These
  are **robust** misses, not weak-attack artifacts.
- **Need stronger fall-preservation pressure?** **Yes — specifically on the lower tail.** The missed falls
  occupy the negative tail of $m_f(x^{adv})$; the existing $\mathcal{L}_{fall}$ (a mean hinge) does not
  prioritize these hardest fall windows.

---

## 4. False-alarm diagnosis (65 FAs, connected to the recall target)

From the committed FA investigation, re-stated against the new target:

| true (source) class | n FA | % of FP |
|---|---|---|
| run | 28 | 43.1 % |
| walk | 20 | 30.8 % |
| **walk + run** | **48** | **73.8 %** |
| stand-up / lie / pickup / sit | 17 | 26.2 % |

- **fall-vs-true-class margin $r_y = z_f - z_y$ (FAs):** median **0.798** [0.558, 1.096] — fall beats the
  true non-fall class by ~0.8; these are the **upper tail** of non-fall fall-risk.
- **To reach FP ≤ 45:** at least **20 of the 65 false-alarm windows must have their $r_y$ pushed below 0**
  (fall no longer the argmax).

**Answers:**
- **Mostly upper-tail walk/run confusion?** **Yes** — 73.8 % motion (run-dominant 43.1 %), all carrying a
  positive $r_y \approx 0.8$.
- **Will reducing FP by 20 hurt the recall region?** **Risk: yes, if done by shifting the boundary.** The
  missed falls are pushed *into* run/walk and the false alarms are walk/run pushed *into* fall — **both live
  at the same fall↔motion boundary**. A crude global push of $z_f$ down (to cut FP) would deepen the missed
  falls' negative $m_f$; a crude push of $z_f$ up (to rescue falls) would inflate the FAs' $r_y$. This is
  why the next objective must **separate**, not shift.
- **Do true falls and false alarms overlap in score space?** **Yes** — detected-fall P(fall) median 0.340
  vs FA median 0.383 (FAs slightly higher; residual inversion +0.043); only 28 % of FAs sit below the
  detected-fall median. Post-hoc separation fails (§2).

---

## 5. Two-tail mathematical interpretation

Define, on adversarial inputs $x^{adv}$:
$$m_f(x) = z_f(x) - \max_{c\neq f} z_c(x)\quad\text{(fall windows)},\qquad r_y(x) = z_f(x) - z_y(x)\quad\text{(non-fall windows, }y\in\mathcal{N}).$$

The seed-44 evidence is a **two-tail separation failure** at the fall↔motion boundary:

- **Lower tail of $m_f(x^{adv})$ (fall windows):** the 18 missed falls have $m_f < 0$ (median −0.77, down to
  −2.45) — fall pushed *below* run/walk. **To raise recall above 80 %, the objective must raise the lower
  tail of $m_f$** for the hardest ~10+ fall windows.
- **Upper tail of $r_y(x^{adv})$ (non-fall windows):** the 65 false alarms have $r_y > 0$ (median +0.80) —
  walk/run pushed *above* their true class into fall. **To reduce FP below 10 %, the objective must lower
  the upper tail of $r_y$** for ≥ 20 non-fall windows.
- **Both, not one at the other's expense.** Because missed falls and false alarms share the fall↔motion
  boundary, a successful next defense must **simultaneously** raise the fall lower tail *and* lower the
  non-fall upper tail — i.e. **increase separation** between the true-fall score distribution and the
  high-risk-non-fall score distribution, rather than translate the boundary (which trades one tail for the
  other). Variant G's *mean* hinges moved the bulk but not the tails; a **tail-aware (TopK)** objective is
  indicated.

---

## 6. Proposed next mathematical direction (design only; NOT run)

§2 shows recall > 80 % & FP ≤ 45 is unreachable by post-hoc gating, and §5 shows why — so a new objective
is warranted.

### Variant H — dual-tail safety-budget defense

$$\mathcal{L}_H = \mathcal{L}_{FWCE} + \lambda_f\,\mathcal{L}_{fall} + \lambda_s\,\mathcal{L}_{src} + \lambda_t\,\mathcal{L}_{tgt} + \lambda_b\,\mathcal{L}_{\text{nonfall-budget}} + \lambda_r\,\mathcal{L}_{\text{fall-rescue}}$$

with the two **TopK (tail-aware)** terms:

$$\mathcal{L}_{\text{nonfall-budget}} = \operatorname{TopKMean}_{y\in\mathcal{N}}\Big[\max\!\big(0,\ z_f(x^{adv}) - z_y(x^{adv}) + \gamma_b\big)\Big]$$

$$\mathcal{L}_{\text{fall-rescue}} = \operatorname{TopKMean}_{y=f}\Big[\max\!\big(0,\ \gamma_r + \max_{c\neq f} z_c(x^{adv}) - z_f(x^{adv})\big)\Big]$$

**Explanation:**
- $\mathcal{L}_{\text{nonfall-budget}}$ penalizes the **top-K most-violating non-fall windows** (largest
  $r_y$) — the upper tail that becomes false alarms — where K tracks the **per-batch false-alert budget**.
- $\mathcal{L}_{\text{fall-rescue}}$ penalizes the **top-K hardest fall windows** (smallest $m_f$, most
  negative) — the lower tail that becomes missed falls.
- **Goal = separation, not suppression:** true fall windows should *remain* fall (rescue the lower tail);
  high-risk walk/run windows should *stop* becoming fall (budget the upper tail). The two TopK terms act on
  opposite tails of the same boundary, which is exactly the §5 diagnosis.

This is a **specification**, not a run; implementing/running it is a separate, reviewed step.

---

## 7. Pilot criteria for the new target (seed-42 only; pre-registered; NOT run)

- **Minimum useful:** PGD recall ≥ 0.60 ∧ PGD FP < current G1 seed-42 FP (104) ∧ clean fall recall ≥ 0.90 ∧
  clean guard holds (acc ≥ 0.70, mF1 ≥ 0.65) ∧ PGD-20 recall > 0.
- **High-recall target:** PGD recall ≥ 0.70 ∧ FP ≤ 55 ∧ PGD-20 recall ≥ 50 % of PGD-10.
- **Strong target:** PGD recall ≥ 0.80 ∧ FP ≤ 45 ∧ clean fall recall ≥ 0.90 ∧ PGD-20 durability holds ∧
  confidence inversion not worsened.
- **Ideal target:** PGD recall ≥ 0.80 ∧ FP ≤ 45 on **seed 42**, then an **independent seed-44 validation
  under a separate pre-registration**.
- **Reject:** FP ≤ 45 only by dropping recall < 0.60; or recall improves only by pushing FP back above G1
  levels; or clean fall recall < 0.90; or clean guard fails; or PGD-20 collapses; or confidence inversion
  worsens.

---

## 8. Does architecture affect this target?

- The current best result is **LeNet + Variant G G1**. Architecture *may* affect separability of the
  fall↔motion boundary, but **architecture should not be changed randomly** alongside a new loss — that
  would confound the objective's effect.
- **Before** switching architecture, inspect whether missed falls and false alarms are separable in the
  *current* logit space. The evidence here says they are **not post-hoc separable** (overlap; §2–§4), and
  the missed falls are *confidently* in run/walk ($m_f$ to −2.45) — which suggests a **training-objective**
  fix (Variant H) before an architecture change.
- If, after Variant H, separability is still poor, a **separate pre-registered, architecture-controlled
  study** (ResNet18 / GRU / BiLSTM with the *same* loss, holding everything else fixed) could test whether
  a richer representation lifts the frontier. That is future work, not part of this investigation.

---

## 9. What should not be claimed

- **60 % attacked recall is a meaningful adversarial-robustness research result, but not enough for
  deployment.**
- **14.3 % attacked false-alarm rate is improved (from F's 24.6 %) but still not acceptable for
  deployment.**
- **> 80 % recall AND < 10 % false alarms is a new *aspirational research target*, not already achieved.**
- **No clinical validation, no product readiness, no certified robustness, no over-the-air claim.**
  Everything here is window-level, digital-domain, white-box on processed CSI tensors.

---

## 10. Final recommendation

**B — current G1 cannot reach the target; specify a dual-tail Variant H next (do not run until reviewed).**
Post-hoc operating-point selection cannot exceed recall 0.600 (let alone 0.80), and FP ≤ 45 forces recall
to 0.356; the missed falls are robust, confident motion misclassifications and the false alarms are
upper-tail motion confusions — a two-tail problem. The next step is to **create the dual-tail Variant H
implementation specification** ($\mathcal{L}_{\text{nonfall-budget}} + \mathcal{L}_{\text{fall-rescue}}$,
§6) with pre-registered seed-42 criteria (§7), and **not run it until reviewed**.

*(Secondary notes: **C** — an architecture-controlled study — is a *later* option only if Variant H stalls
(§8); **D** — temporal/event-level aggregation — is an orthogonal, non-window-level route to a lower
operational false-alert rate, out of the current window-level scope. Neither replaces the Variant H training
fix as the immediate next step.)*

### Scope reminder
Analysis only — no training/attacks/evaluation/new seeds/script change/`.tex` edit/artifact overwrite.
Window-level, processed CSI tensor, digital-domain, white-box; **not** solved, **not** certified, **not**
clinical, **not** over-the-air. Variant H is a **specification only — not run**.
