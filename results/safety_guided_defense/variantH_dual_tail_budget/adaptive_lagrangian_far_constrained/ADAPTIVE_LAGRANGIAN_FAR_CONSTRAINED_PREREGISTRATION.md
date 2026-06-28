# Option B: FAR-constrained adaptive-Lagrangian rescue — pre-registration

> **Pre-registration only — NOT implemented, NOT run.** No training, attacks, evaluation, A2/A0/H2/H3,
> seed 44/45/46; no model-code change, no `.tex` edit, no Variant G/G1 or A1 artifact change, no commit until
> reviewed. Designs the next defense attempt from committed evidence through `3f95410` (A1 informative
> negative). Criteria, objective, settings, and stop conditions are fixed here **before** any run.
> Window-level, digital-domain, white-box, processed CSI tensors; test n=500 (45 fall / 455 non-fall),
> validation n=496 (44 falls), ε=0.030. **No product / clinical / deployment / certified / over-the-air
> claim.** This is a **new line**, not A1/H2/H3.

## 1. Motivation from prior results

The committed defense line establishes two validated partial operating points and two rejected dual-tail
attempts; all share one structural problem — they cannot hold attacked recall **and** false-alarm rate
together.

| model (committed) | clean acc | PGD-10 recall | PGD FP | FAR (/455) | status |
|---|---|---|---|---|---|
| Variant G G1 seed42 | 0.716 | **0.689** | 104 | 22.9% | validated higher-recall, **high FP** |
| Variant G G1 seed44 | 0.746 | 0.600 (27/45) | **65** | **14.3%** | validated lower-FP, **recall ~0.60, FAR > 10%** |
| Variant H H1 seed42 | 0.662 | 0.489 | 94 | 20.7% | **REJECT** — clean-guard failure + recall suppression |
| Option A A1 seed42 | 0.678 | 0.556 (25/45) | 68 | 15.0% | **REJECT** — informative negative (clean acc 0.678, mF1 0.635, clean fall recall 0.933) |

- **G1** is the strongest committed point but is high-FP at the higher-recall operating point.
- **H1** added a *static* nonfall-budget term and *over-suppressed* recall while breaking the clean guard.
- **A1** fixed H1's fall-rescue under-power (the `k_abs_min=4` floor worked — ~2.6 falls/batch vs k≈1) and
  improved slightly over H1 (recall 0.556 vs 0.489; FP 68 vs 94), but is **dominated by G1** on recall and
  clean performance, **still > 10% FAR**, and again breaks the clean guard on test. **Rejected as an
  informative negative.**

**Lesson:** a *fixed* budget weight `λ_b` either under-cuts false alarms or over-suppresses recall — it
cannot adapt to where the model currently is on the recall/FAR trade-off.

## 2. Scientific problem

- **Static dual-tail weighting trades one failure mode for the other.** A constant `λ_b` applies the same
  false-alarm pressure regardless of the model's current FAR, so it overshoots (kills recall) or undershoots
  (leaves FAR high).
- **Reframe as a constrained objective:** *maximize attacked fall recall **subject to** FAR ≤ 10%*, rather
  than minimizing a fixed-weight sum of recall and FAR penalties. The constraint should be enforced by a
  **dual variable that adapts** — pressure rises only while the constraint is violated and relaxes once it is
  satisfied. This is the core hypothesis of Option B.

## 3. Target operating region

- **Test split:** 45 fall windows, 455 non-fall windows (unchanged).
- **Desired joint target:** **TP ≥ 37/45** (recall ≥ 0.80) **and FP ≤ 45/455** (FAR ≤ 10%), simultaneously.
- Anchor gap from the closest committed point (G1 seed44, 27/45 TP, 65 FP): **+10 true positives and
  −20 false positives at once** — the same two-tail-separation problem that remains open.

## 4. Mathematical objective

Same per-window safety-margin structure as Variant G/H (frozen base), with the **budget weight made an
adaptive dual variable** instead of a constant.

**Per-batch loss:**

$$\mathcal{L}(t) = \underbrace{\mathcal{L}_{FWCE}}_{\text{base clean+adv}} + \lambda_s\mathcal{L}_{src} + \lambda_f\mathcal{L}_{fall} + \lambda_t\mathcal{L}_{tgt} + \lambda_r\,\mathcal{L}_{\text{rescue}} + \lambda_b(t)\,\mathcal{L}_{\text{budget}}$$

- **Base clean/adversarial loss** $\mathcal{L}_{FWCE}$: the committed fall-weighted CE over clean+FGSM+PGD
  windows (unchanged).
- **Rescue term** (attacked fall windows): $\mathcal{L}_{\text{rescue}} = \operatorname{TopKMean}_{y=f}\big[\max\!\big(0,\ \gamma_r + \max_{c\neq f}z_c(x^{adv}) - z_f(x^{adv})\big)\big]$, with the **`k_abs_min` floor retained** (≥ 4 falls/batch) — the one mechanically-correct piece of A1.
- **False-alarm budget term** (attacked non-fall windows): $\mathcal{L}_{\text{budget}} = \operatorname{TopKMean}_{y\in\mathcal{N}}\big[\max\!\big(0,\ z_f(x^{adv}) - z_y(x^{adv}) + \gamma_b\big)\big]$ (unchanged selection).
- Base coefficients frozen at Variant G G1: $\lambda_s=\lambda_f=\lambda_t=1.0$, $w_{wr}=2.0$,
  $\gamma_b=\gamma_r=0.5$, fall weight 3. $\lambda_r$ fixed (see §6).

**Adaptive Lagrangian update on the budget weight** (the only new dynamic). The first pilot uses the
**fixed, pinned** form below — index $t$ denotes the **epoch**:

$$\lambda_b(t+1) = \operatorname{clip}\!\Big(\lambda_b(t) + 0.10\,\big(\mathrm{FAR}^{\text{val}}_{\text{PGD10}}(t) - 0.10\big),\ \ 0,\ \ 1.0\Big), \qquad \lambda_b(0) = 0.25$$

**FAR-estimator cadence (pinned for the first pilot):**
- **Once-per-epoch update.** $\lambda_b$ is updated **exactly once per epoch, after the epoch's validation
  metrics are computed**, and the new value is used for the *next* epoch's training. There is **no
  per-mini-batch update** in the first pilot — batch-level FAR is too noisy to drive the dual variable.
- **Constraint signal = validation PGD-10 false-alarm rate.** $\mathrm{FAR}^{\text{val}}_{\text{PGD10}}(t) =
  \text{FP}/n_{\text{nonfall}}^{\text{val}}$ on the **validation** split under PGD@0.030, steps=10 (the same
  bundle used for selection) — **never test**. Logged every epoch.

**Behaviour of the pinned update:**
- **Increase only on violation, relax when safe:** if $\mathrm{FAR}^{\text{val}}_{\text{PGD10}}(t) > 0.10$ the
  bracket is positive so $\lambda_b$ rises (more false-alarm pressure); if it is $< 0.10$ the bracket is
  negative so $\lambda_b$ decays toward 0 (recall is no longer penalized once FAR is within budget).
- **Non-negativity** is enforced by the lower clip at 0 (the budget term must never *reward* false alarms).
- **Cap $\lambda_{b,\max} = 1.0$** bounds the maximum pressure so a transient FAR spike cannot collapse recall
  (an explicit guard against the H1/A1 over-suppression failure).
- **Step size $\eta = 0.10$.** With FAR expressed as a fraction in $[0,1]$, one epoch of maximal violation
  (FAR=1.0) moves $\lambda_b$ by at most $0.10\cdot0.90 = 0.09$, so the dual variable changes gradually and
  cannot jump to the cap in a single epoch.

**Intended mechanism:** $\lambda_b(t)$ self-tunes to sit at the FAR≤10% boundary — applying just enough
false-alarm pressure to satisfy the constraint and no more — so the rescue term can keep lifting the weakest
fall margins instead of being dominated by a static budget penalty. Option B is successful only if FAR is
driven to ≤ 10% **without** recall collapse (the two tails separate rather than trade).

## 5. Checkpoint selection rule (aligned to the target; validation only, never test)

1. **Hard clean guard (pinned).** Reject any checkpoint that does not satisfy **all** of:
   - clean accuracy ≥ **0.70**,
   - clean macro-F1 ≥ **0.65**,
   - clean fall recall ≥ **0.90**.

   (A1 passed the first two on validation but failed acc on test; adding the clean-fall-recall floor at
   selection makes the guard explicit and three-pronged.)
2. Among clean-valid checkpoints, maximize the **pinned target-aligned score** (validation bundle):

$$\text{Score} = \mathrm{PGDRecall} - 4.0\,\max(0,\ \mathrm{FAR}-0.10) - 2.0\,\max(0,\ 0.90-\mathrm{CleanFallRecall}) - 2.0\,\max(0,\ 0.70-\mathrm{CleanAcc})$$

- All terms on the **validation** bundle (PGD-10 @0.030). The three penalties are one-sided hinges: zero when
  the constraint/floor is met, growing only on violation.
- The weights are **pinned for the first pilot at $\alpha=4.0$, $\beta=2.0$, $\gamma=2.0$** — fixed here
  before any run, so selection cannot be reverse-engineered from outcomes. Any other weights are **not
  approved** (see §6).
- Report **all** candidate checkpoints (max-score, max-recall-within-guard, min-FAR-within-guard) for
  transparency, as in selection-v2.

## 6. First-pilot settings (pinned; NO random search, NO sweep)

**These are the only approved values for the first pilot:**

| knob | pinned value |
|---|---|
| seed | **42 only** |
| architecture | **LeNet only** |
| dataset | **UT-HAR only** |
| train epsilons | **`{0.005, 0.015, 0.03}`** |
| eval | clean / FGSM@0.030 / PGD-10@0.030, validation for selection (test held out) |
| `λ_b(0)` (initial budget weight) | **0.25** |
| `η` (step size) | **0.10** |
| `λ_b,max` (cap) | **1.0** |
| `λ_r` (rescue weight, fixed) | **1.0** |
| fall-rescue `k_abs_min` | **4** (retained) |
| base (frozen Variant G G1) | `λ_s=λ_f=λ_t=1.0`, `w_wr=2.0`, `γ_b=γ_r=0.5`, fall weight 3 |
| update rule | `λ_b(t+1) = clip(λ_b(t) + 0.10·(FAR_val_PGD10(t) − 0.10), 0, 1.0)`, once per epoch |

**Not approved for the first pilot.** Any other value of `η` (e.g. 0.05), `λ_b,max` (e.g. 2.0), or score
weights `(α, β, γ)` — and any grid/sweep over them — is **out of scope** and would require a **separate
pre-registration and code review**. The first pilot is a **single configuration**, not a search.

## 7. Explicit gate

- **Only this pre-registration is approved.**
- **No training is approved.**
- **No code implementation is approved** until a separate implementation spec + code review.
- A2/A0/H2/H3, seed 44/45/46, architecture changes, and event-level aggregation are **out of scope** for
  Option B.

## 8. Success criteria (pre-registered; evaluated on seed-42 test)

- **Strong success:** PGD recall ≥ 0.80 ∧ PGD FP ≤ 45 ∧ clean fall recall ≥ 0.90 ∧ clean acc ≥ 0.70 ∧
  macro-F1 ≥ 0.65 ∧ PGD-20 durability holds (if produced).
- **Promising improvement:** PGD recall ≥ 0.70 ∧ PGD FP ≤ 65 ∧ clean guard holds (acc ≥ 0.70, mF1 ≥ 0.65).
- **Minimum useful (pinned):** PGD recall ≥ **0.60** ∧ PGD FP ≤ **65** ∧ clean acc ≥ **0.70** ∧
  macro-F1 ≥ **0.65** ∧ clean fall recall ≥ **0.90**. (FP ≤ 65 matches G1 seed44 and is below A1's 68; this
  bar requires Option B to be at least non-dominated on FP while clearing the recall floor and the full clean
  guard.)
- **Reject:** clean-guard failure; or PGD recall < 0.60; or FP controlled **only** by recall collapse; or the
  result is dominated by G1 (seed42 0.689/104 or seed44 0.600/65) or by A1 (0.556/68).

## 9. Safety / scope language

- **No clinical claim.**
- **No deployment / product claim.**
- **No certified-robustness claim.**
- **No over-the-air (OTA) claim.**
- Research-stage, **window-level, digital-domain, white-box** evaluation on processed CSI tensors only.
- The joint > 80%-recall / < 10%-FAR target is currently **unmet**; Option B is an attempt, not a result.

## 10. Required next steps after this pre-registration

1. **Implementation spec + code-review plan** (math-to-code mapping for the adaptive update, the FAR
   estimator, the cap/clip, logging of `λ_b(t)` and `FAR_t` every update) — **before** any code is written.
2. **Smoke test + self-check** (finite losses; budget/rescue nonzero; the pinned once-per-epoch update where
   `λ_b` rises on synthetic FAR>0.10 and decays on FAR<0.10; clip to [0, 1.0] respected; no per-batch update;
   floor active) — **before** any pilot.
3. **Pilot gate** (seed 42 only, the single pinned configuration in §6) **only after the code review is
   approved.**
4. No automatic follow-up; each stage reviewed before the next.

### Scope reminder
Pre-registration only — no training/attacks/evaluation/code/`.tex`/A2/A0/H2/H3/seed44-46/Variant-G/A1
change. Defines a **new** adaptive-Lagrangian FAR-constrained line; recommends an implementation spec +
code review as the next deliverable; **starts nothing.**
