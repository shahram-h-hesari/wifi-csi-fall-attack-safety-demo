# Variant H — dual-tail safety-budget defense: implementation specification

> **Implementation specification only — Variant H is NOT implemented, NOT run.** No code written, no
> script change, no training/attacks/evaluation, no new seeds, no `.tex` edit, no artifact overwrite.
> Translates the committed two-tail objective (`HIGH_RECALL_LOW_FP_FEASIBILITY.md`, commit `ea9af77`) into a
> precise code-level plan + sanity-check plan + smoke-test plan + pilot-readiness checklist. Preserves the
> thesis discipline: **observed result → mathematical diagnosis → objective design → math-to-code mapping →
> sanity checks → smoke validation → pilot only after approval.** Window-level, digital-domain, white-box;
> **no solved / certified / clinical / over-the-air claim.**

## 1. Starting point and target

**Observed result (committed).** Current best *validated* model: **Variant G G1 seed-44**. Seed-44 PGD
confusion (test n=500; 45 fall / 455 non-fall):

| TP | FN | FP | TN | PGD recall | attacked FA rate (FP/455) |
|---|---|---|---|---|---|
| 27 | 18 | 65 | 390 | **0.600** | **65/455 = 14.3 %** |

**Target.**
- PGD fall recall **> 80 %** ⇒ at least **37/45** detected fall windows.
- attacked non-fall false-alarm rate **< 10 %** ⇒ **FP ≤ 45** of 455.

**Required improvement:** **≥ +10 detected fall windows** (27 → ≥ 37) **and ≥ −20 false positives** (65 →
≤ 45) — *simultaneously*.

**Why a new objective is needed (mathematical diagnosis).** Post-hoc gating **cannot** reach this target:
a gate of the form "alert iff argmax = fall AND …" can only **remove** fall alerts, never **create** new
true-positive fall detections, so the maximum recall over every gate equals the raw 0.600 (committed
feasibility §2: all six recall/FP targets fail; FP ≤ 45 forces recall to 0.356). The 18 missed falls are
**robust** motion misclassifications (16/18 predicted run/walk, 18/18 also missed under PGD-20, fall margin
median −0.77), and the 65 false alarms are **upper-tail** walk/run windows (73.8 % motion, $r_y$ median
+0.80). **The next objective must change the learned decision geometry on both tails of the fall↔motion
boundary.**

## 2. Mathematical objective

Notation: input window $x$; true label $y$; fall class $f=1$; non-fall classes
$\mathcal{N}=\{0,2,3,4,5,6\}$; walk/run subset $\mathcal{M}=\{2,4\}$; logits $z_\theta(x)$; untargeted
FGSM/PGD adversarial example $x^{adv}$ (ascent on the true label); targeted-to-fall adversarial example
$x^{tgt}$ (descent on CE-to-fall). Margins:

$$m_f(x) = z_f(x) - \max_{c\neq f} z_c(x)\ \ \text{(fall windows)},\qquad r_y(x) = z_f(x) - z_y(x),\ y\in\mathcal{N}\ \ \text{(non-fall windows)}.$$

**Variant H (dual-tail safety-budget objective):**

$$\mathcal{L}_H = \mathcal{L}_{FWCE} + \lambda_f\,\mathcal{L}_{fall} + \lambda_s\,\mathcal{L}_{src} + \lambda_t\,\mathcal{L}_{tgt} + \lambda_b\,\mathcal{L}_{\text{nonfall-budget}} + \lambda_r\,\mathcal{L}_{\text{fall-rescue}}$$

$$\mathcal{L}_{\text{nonfall-budget}} = \operatorname{TopKMean}_{y\in\mathcal{N}}\Big[\max\!\big(0,\ z_f(x^{adv}) - z_y(x^{adv}) + \gamma_b\big)\Big]$$

$$\mathcal{L}_{\text{fall-rescue}} = \operatorname{TopKMean}_{y=f}\Big[\max\!\big(0,\ \gamma_r + \max_{c\neq f} z_c(x^{adv}) - z_f(x^{adv})\big)\Big]$$

The first four terms ($\mathcal{L}_{FWCE},\mathcal{L}_{fall},\mathcal{L}_{src},\mathcal{L}_{tgt}$) are the
**frozen Variant G objective** (reused unchanged); Variant H adds the two **TopK (tail-aware)** terms.

**Two-tail mechanism:**
- $\mathcal{L}_{\text{nonfall-budget}}$ **lowers the upper tail of $r_y$** — it concentrates gradient on the
  **top-K highest-risk non-fall windows** (largest $z_f-z_y$), exactly the walk/run windows that become
  false fall alarms.
- $\mathcal{L}_{\text{fall-rescue}}$ **raises the lower tail of $m_f$** — it concentrates gradient on the
  **top-K hardest fall windows** (most negative $m_f$), exactly the falls that become missed detections.
- **Goal = separation, not suppression:** true fall windows should *retain positive* $m_f$; high-risk
  walk/run windows should be pushed *below* the fall-alert boundary ($r_y < 0$).

**Explicit failure framing:** **Variant H is not successful if it reduces false alarms by sacrificing fall
recall.** A drop in PGD recall below the pilot floor (§7) is a *failure*, regardless of how low FP goes.

## 3. Exact math-to-code mapping

**Future script (NOT created here):** `scripts/train_variantH_dual_tail_budget.py`. Reuses the committed
Variant G foundation: `import_variantG()` → `targeted_fall_pgd()`, `source_weights()`,
`variantG_margin_terms()` (for $\mathcal{L}_{src},\mathcal{L}_{fall},\mathcal{L}_{tgt}$), the selection-v2
`run_full` machinery, the PGD-20 / probability-logit eval tooling, and the class-index asserts
(`FALL_CLASS_INDEX=1`, `WALK,RUN=2,4`, `NONFALL_EXPECTED={0,2,3,4,5,6}`).

| math term | intended mechanism | future script / function | inputs | output | key hyperparameters | required sanity check |
|---|---|---|---|---|---|---|
| TopK reducer | select & average worst windows | `topk_mean(values, k_frac, k_abs)` | hinge vector (≥0) | scalar mean of top-K | `k_frac=0.25` | selects largest values; empty→0; deterministic |
| $\mathcal{L}_{\text{nonfall-budget}}$ | lower upper tail of $r_y$ | `nonfall_budget_loss(logits_adv, y, fall_idx, gamma_b, k_frac, source_weights=None)` | adv logits + labels (non-fall mask) | scalar ≥0 | $\gamma_b=0.5$, `k_frac`, opt. $s_{\mathcal{M}}$ | >0 when risky non-fall present; minimizing ↓ $z_f-z_y$ |
| $\mathcal{L}_{\text{fall-rescue}}$ | raise lower tail of $m_f$ | `fall_rescue_loss(logits_adv, y, fall_idx, gamma_r, k_frac)` | adv logits + labels (fall mask) | scalar ≥0 | $\gamma_r=0.5$, `k_frac` | >0 when hard falls present; minimizing ↑ $m_f$ |
| $\mathcal{L}_{src},\mathcal{L}_{fall},\mathcal{L}_{tgt}$ | Variant G terms (unchanged) | `variantG_margin_terms()` (reused) | adv + targeted logits | three scalars | $\gamma_m=\gamma_f=\gamma_t=0.5$, $w_{wr}=2$ | identical to committed Variant G |
| all components | full Variant H loss | `variantH_margin_terms(...)` | adv + targeted outputs, labels | dict: `src_motion, fall_margin, targeted, nonfall_budget, fall_rescue` | $\lambda_{f,s,t,b,r}$ | each finite; correct subset masks |
| $x^{tgt}$ targeted attack | worst nonfall→fall dirs | `targeted_fall_pgd()` (reused) | clean non-fall windows | targeted adv | ε=0.030, M=7, α=ε/4 | pre-train sign check (median $z_f$↑) |
| checkpoint pick | clean-stable, FA-aware | selection-v2 `run_full` (reused) | val bundle | v2safety/maxrec/lowFA/macroF1 | guard 0.70/0.65 | **validation-only** |
| durability | masking screen | PGD-20 eval (reused) | test windows | PGD-20 recall | M=20 | recall non-increasing PGD-10→20 |

**Function contracts (future):**
1. `topk_mean(values, k_frac=None, k_abs=None)` — vector of (already-hinged, ≥0) losses → mean of the K
   largest. K = `k_abs` if given else `ceil(k_frac · len(values))`, clamped to `[1, len]`. **Empty input →
   `torch.zeros((), …)`** (safe). Deterministic (`torch.topk`, stable on ties by index). Gradients flow
   **only** through the selected top-K entries.
2. `nonfall_budget_loss(logits_adv, y, fall_idx, gamma_b, k_frac, source_weights=None)` — restrict to
   `y ∈ 𝒩`; compute `r = z_f − z_y`; hinge `relu(r + gamma_b)`; **optionally** multiply by walk/run
   `source_weights`; return `topk_mean(hinge, k_frac)`. Empty non-fall mask → 0.
3. `fall_rescue_loss(logits_adv, y, fall_idx, gamma_r, k_frac)` — restrict to `y = fall_idx`; compute
   `mneg = max_{c≠f} z_c − z_f`; hinge `relu(gamma_r + mneg)`; return `topk_mean(hinge, k_frac)` over the
   **hardest** fall windows. Empty fall mask → 0.
4. `variantH_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx, gamma_b, gamma_r, k_frac, device)`
   — calls `variantG_margin_terms()` for `(src_motion, fall_margin, targeted)` and the two new functions for
   `(nonfall_budget, fall_rescue)`; returns all five. Total loss assembled in the epoch loop:
   `loss = base_FWCE + λ_s·src + λ_f·fall + λ_t·tgt + λ_b·nonfall_budget + λ_r·fall_rescue`.
5. **Reuse from Variant G (do not re-implement):** `targeted_fall_pgd()`, source weighting, selection-v2
   guard, PGD-20 diagnostic, probability/logit exports.

**Which adversarial source each budget term uses (first implementation — keep it simple):**
- `L_nonfall-budget` uses the **untargeted PGD** adversarial non-fall examples (`x^{adv}`) — the same
  sub-batch that produces the residual false alarms in evaluation.
- `L_fall-rescue` uses the **untargeted PGD** adversarial **fall** examples (`x^{adv}`, `y=f`) — the same
  sub-batch that produces the missed falls.
- **Targeted-to-fall examples (`x^{tgt}`) remain covered by the existing `L_tgt` only** — do **not** also
  route them into the budget terms in the first implementation.
- **Do not mix multiple adversarial sources into one term in the first implementation.** (A later, separate
  ablation may add targeted examples to `L_nonfall-budget`.)

## 4. Hyperparameter plan (pre-registered; NO random search)

Fixed across all: $\lambda_f=\lambda_s=\lambda_t=1.0$, $w_{wr}=2.0$, $\gamma_m=\gamma_t=0.5$, fall weight 3,
train ε{0.005,0.015,0.030}, M=7 α=ε/4, selection-v2 guard 0.70/0.65 — **identical to frozen Variant G**.
Only $(\lambda_b,\lambda_r)$ vary; `k_frac=0.25`, $\gamma_b=\gamma_r=0.5$ fixed.

| setting | $\lambda_b$ | $\lambda_r$ | k_frac | $\gamma_b$ | $\gamma_r$ | hypothesis |
|---|---|---|---|---|---|---|
| **H1** balanced dual-tail | 0.5 | 0.5 | 0.25 | 0.5 | 0.5 | both tails improve together |
| **H2** stronger nonfall budget | 1.0 | 0.5 | 0.25 | 0.5 | 0.5 | isolates FP-reduction pressure |
| **H3** stronger fall rescue | 0.5 | 1.0 | 0.25 | 0.5 | 0.5 | isolates recall-raising pressure |

**Recommended minimal pilot:** **H1 + one ablation.** If compute is constrained, run **H1 (balanced) plus
H3 (fall-rescue-heavy)** — H1 tests the joint hypothesis, H3 tests whether recall can be raised at all (the
harder, novel direction); H2 can be deferred. **Do not propose a broad search.**

**Expected behavior (stated before any run):**
- Increasing $\lambda_b$ should **reduce FP** but may **reduce recall** (over-suppressing $z_f$).
- Increasing $\lambda_r$ should **increase recall** but may **increase FP** (inflating $z_f$ on motion).
- The **balanced** setting (H1) tests whether both tails can move **together** (separation), which is the
  whole premise; if only the trade-off (one up, one down) appears, the dual-tail hypothesis is not supported.

## 5. Required implementation sanity checks (before ANY pilot)

**Class-index checks:** assert `tsg.FALL_CLASS_INDEX == 1`, `tsg.NUM_CLASSES == 7`, `(WALK,RUN)==(2,4)`,
`{c for c≠fall}==NONFALL_EXPECTED`. Halt on mismatch.

**Loss nonzero checks (deterministic batch):** `nonfall_budget_loss > 0` when risky non-fall examples
exist; `fall_rescue_loss > 0` when hard fall examples exist; **all five components finite**.

**TopK checks:** `topk_mean` selects the **largest** hinge values (not random — assert against a manual
`sort()[-k:]`); K ≥ 1 when valid samples exist; **empty fall/non-fall masks return 0 safely**; gradients
flow **only** through the selected top-K entries (assert non-selected entries have zero grad contribution).

**Directionality checks:** on a frozen checkpoint, one gradient step that minimizes `L_nonfall-budget`
should **decrease** median $z_f-z_y$ on the targeted non-fall windows; one step minimizing `L_fall-rescue`
should **increase** median $m_f$ on the hardest fall windows. If a sign is wrong, halt and fix.

**No fall-suppression check (during smoke):** clean fall recall must **not** collapse; PGD fall recall must
**not** remain zero after early recovery; **if FP drops but fall recall collapses, mark as FAILURE.**

**No test-leakage check:** validation **may** be used for checkpoint selection; **test may NOT** be used
for threshold or checkpoint selection; **seed 44 may NOT be run** without a separate pre-registration (§8).

## 6. Smoke-test plan only (NOT a pilot)

- **seed 42 only**, **one setting only** (preferably **H1**), **1–2 epochs** or a small batch-limited run
  (e.g. `--smoke --smoke-batches 5`, mirroring the committed Variant G smoke mode).
- **Purpose:** verify code, loss components, gradients, logs, and the selection path — **no claims from
  smoke results.**
- **Smoke must report:** all loss components finite; `nonfall_budget` **nonzero**; `fall_rescue`
  **nonzero**; top-K selected counts (per term); clean acc / macro-F1 trend; clean fall recall if available;
  PGD recall / FP if available; **no `.pt` checkpoint committed**; **no seed 44/45/46**.

## 7. Future seed-42 pilot criteria (pre-registered)

- **Minimum useful:** clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65 ∧ clean fall recall ≥ 0.90 ∧ PGD recall ≥ 0.60 ∧
  PGD FP < **G1 seed-42 FP (104)** ∧ PGD-20 recall > 0 ∧ confidence inversion **not worse** than G1.
- **High-recall target:** PGD recall ≥ 0.70 ∧ FP ≤ 55 ∧ PGD-20 recall ≥ 50 % of PGD-10.
- **Strong target:** PGD recall ≥ 0.80 ∧ FP ≤ 45 ∧ clean fall recall ≥ 0.90 ∧ PGD-20 durability holds ∧
  confidence inversion not worsened.
- **Reject:** FP ≤ 45 only by recall collapse; or PGD recall < 0.60; or clean fall recall < 0.90; or clean
  guard fails; or PGD-20 collapses; or confidence inversion worsens; or false alarms remain above G1 with
  no recall gain.

**Recall collapse is a failure outcome** (not a success with low FP) — restated from §2.

## 8. Future seed-44 validation rule

- **No seed-44 Variant H run** is allowed until a seed-42 pilot **succeeds or nearly reaches** the
  high-recall/low-FP target.
- A **separate seed-44 pre-registration** must be **written and committed before** any seed-44 run.
- The **seed-44 test set must be used once**; **no tuning after seed-44 results**.
- **Any threshold/gate must be selected on validation data only** (as in the Variant G G1 seed-44
  validation).

## 9. Architecture note

Architecture may affect the achievable frontier, but an **architecture change must be a separate controlled
study**. **Do not mix** a new objective + a new architecture + new hyperparameters + new thresholding all at
once. **Variant H should first test whether the objective alone improves the LeNet frontier.** If Variant H
stalls on LeNet, a **separate pre-registered architecture-controlled study** (ResNet18 / GRU / BiLSTM with
the *same* loss, everything else fixed) may be designed later.

## 10. What not to claim

- Variant H is **not implemented** yet. — **not validated** yet. — **not a product claim.**
- **> 80 % recall and < 10 % false alarms is an aspirational research target, not achieved.**
- **No** clinical validation. **No** certified robustness. **No** deployment readiness. **No** over-the-air
  claim. Everything is window-level, digital-domain, white-box on processed CSI tensors.

## 11. Final recommendation

**Recommended:** **Implement Variant H smoke-only code next, but do not run a full pilot until smoke checks
pass and the code is reviewed.** The objective, function contracts, hyperparameters, sanity checks, and
pilot/validation criteria are unambiguous and reuse the committed Variant G foundation; the next step is a
single, reviewable smoke-only implementation (the two TopK functions + `variantH_margin_terms` +
`--self-check`/`--smoke` modes), gated exactly as Variant G was.

*(Alternative — only if ambiguity is found: clarify implementation details before coding. No blocking
ambiguity is identified in this spec.)*

### Scope reminder
Specification only — Variant H is **not** implemented, trained, attacked, or evaluated. No script changed,
no `.tex` edited, no new seeds, no artifact overwritten. Window-level, processed CSI tensor, digital-domain,
white-box; **not** solved, **not** certified, **not** clinical, **not** over-the-air.
