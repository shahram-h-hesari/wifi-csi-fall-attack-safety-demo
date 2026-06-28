# Option A — rebalanced dual-tail defense: pre-registration

> **Pre-registration only — NOT implemented, NOT run.** No training, attacks, evaluation, H2/H3, seed
> 44/45/46; no script change, no `.tex` edit, no artifact overwrite, no commit until reviewed. Designs the
> next defense attempt from committed evidence through `85de6c9`. Criteria, settings, and stop conditions
> are fixed here **before** any run. Window-level, digital-domain, white-box, processed CSI tensors; test
> n=500 (45 fall / 455 non-fall), validation 496 (44 falls), ε=0.030. **No product / clinical / deployment
> / certified / over-the-air claim.**

## 1. Executive summary

**Option A is NOT the committed H2/H3.** It is a **new, rebalanced dual-tail design** motivated by the
committed **H1 failure** (REJECT): H1's source-weighted nonfall-budget term over-suppressed fall recall
(0.689→0.489 same-seed), while its fall-rescue term was **under-powered** (effective TopK k ≈ 1 fall/batch),
and the clean guard failed on test (acc 0.662, macro-F1 0.591).

**Goal:** preserve or improve PGD fall recall **while still reducing false alarms**, toward the unmet joint
target (PGD recall > 80% **and** false-alarm rate < 10%). The committed gap from the closest point
(Variant G G1 seed44, recall 0.600 = 27/45, FP 65 = 14.3%): **+10 true positives and −20 false positives,
simultaneously.**

The new design must:
- **lower** nonfall-budget pressure (`λ_b` below H1's 0.5),
- **strengthen** fall-rescue pressure (`λ_r` above H1's 0.5),
- **add a `k_abs` floor for fall-rescue** so it acts on more than ~1 fall window per batch,
- **avoid increasing** budget pressure (never above H1),
- **not run seed 44** until a seed-42 pilot succeeds,
- **remain LeNet-only** for now.

## 2. Why the committed H2/H3 should not be run

- **H2** (λ_b=1.0, λ_r=0.5): **stronger** nonfall-budget pressure — directly amplifies the recall
  suppression already seen in H1. Expected to make recall *worse*. **Do not run.**
- **H3** (λ_b=0.5, λ_r=1.0): stronger fall-rescue, **but keeps λ_b=0.5** (same budget pressure as H1) **and**
  inherits the **k ≈ 1 fall-rescue under-power** (no `k_abs` floor in the committed code). Likely still
  recall-limited. **Do not run as-is.**
- Therefore **neither committed setting addresses the H1 failure mode**; Option A is a *redesign*, not H2/H3.

## 3. Rebalanced objective

Same Variant H objective (unchanged form):

$$\mathcal{L}_H = \mathcal{L}_{FWCE} + \lambda_f\mathcal{L}_{fall} + \lambda_s\mathcal{L}_{src} + \lambda_t\mathcal{L}_{tgt} + \lambda_b\mathcal{L}_{\text{nonfall-budget}} + \lambda_r\mathcal{L}_{\text{fall-rescue}}$$

with $\mathcal{L}_{\text{nonfall-budget}} = \operatorname{TopKMean}_{y\in\mathcal{N}}[\max(0, z_f(x^{adv})-z_y(x^{adv})+\gamma_b)]$
and $\mathcal{L}_{\text{fall-rescue}} = \operatorname{TopKMean}_{y=f}[\max(0, \gamma_r + \max_{c\neq f}z_c(x^{adv})-z_f(x^{adv}))]$.

Base (frozen Variant G G1): $\lambda_s=\lambda_f=\lambda_t=1.0$, $w_{wr}=2.0$, $\gamma_m=\gamma_t=0.5$, fall
weight 3 — **unchanged**. **Option A re-parameterizes only the two new terms:**
- **lower $\lambda_b$** than H1 (H1=0.5),
- **higher $\lambda_r$** than H1 (H1=0.5),
- **fall-rescue uses a `k_abs` floor** (≥ 4 fall windows/batch, not k≈1),
- **nonfall-budget must not dominate early training** (kept small),
- **selection still uses the safety-aware validation rule (selection-v2), never test.**

Intended mechanism: $\mathcal{L}_{\text{nonfall-budget}}$ lowers the **highest-risk non-fall** fall-scores
(upper tail of $r_y=z_f-z_y$); $\mathcal{L}_{\text{fall-rescue}}$ raises the **weakest fall margins** (lower
tail of $m_f=z_f-\max_{c\neq f}z_c$). **Option A is successful only if false alarms decrease *without* recall
collapse** — i.e., the two tails separate rather than trade.

## 4. Proposed settings (pre-registered; NO random search)

### A1 — recall-preserving rebalanced dual-tail *(preferred first run)*
`λ_b = 0.25`, `λ_r = 1.0`, `nonfall k_frac = 0.25`, `fall_rescue k_frac = 0.25`, **`fall_rescue k_abs_min = 4`**,
`γ_b = 0.5`, `γ_r = 0.5`. *Purpose:* reduce recall suppression (half H1's budget pressure) and strengthen
fall rescue (2× H1) with a floor so rescue affects ≥ 4 falls/batch.

### A2 — stronger fall rescue, very light budget *(only after A1 reviewed)*
`λ_b = 0.10`, `λ_r = 1.5`, `nonfall k_frac = 0.25`, `fall_rescue k_frac = 0.25`, **`fall_rescue k_abs_min = 4`**,
`γ_b = 0.5`, `γ_r = 0.5`. *Purpose:* test whether stronger rescue recovers attacked recall **without**
returning to Variant F-level false alarms.

### A0 — fall-rescue floor only *(optional ablation; only if separately approved)*
`λ_b = 0.0`, `λ_r = 1.0`, **`fall_rescue k_abs_min = 4`**. *Purpose:* isolate whether recall can be raised
**before** reintroducing any budget pressure.

**Run order:** **A1 (seed 42) first.** A2 and A0 are **not** run unless A1 completes, is reviewed, and is
separately approved.

## 5. Required code changes for future implementation (specify only; do NOT implement now)

In a future, separately-reviewed commit to `scripts/train_variantH_dual_tail_budget.py` (or a new
`optionA` script):
- Add a **new setting namespace `optionA_rebalanced`** with keys A1/A2/A0; **do not reuse the names H2/H3**.
- Implement a **separate `k_abs_min` for fall-rescue**: extend `fall_rescue_loss(logits_adv, y, fall_idx,
  gamma_r, k_frac, k_abs_min=None)` so its effective K = `max(ceil(k_frac·n_fall), k_abs_min)` clamped to
  `n_fall` (i.e., at least `k_abs_min` falls when available).
- Keep `nonfall_budget_loss` TopK **as committed** (no change to the budget term's selection).
- Keep the **seed-42-only pilot gate**; **block seed 44/45/46**.
- **Block A2/A0 unless explicitly approved** (mirror the H1-only `--pilot` gate: a new `--pilot` must default
  to A1 and refuse A2/A0 without an explicit, separately-approved flag).
- **Logging:** record per epoch — **nonfall selected count**, **fall selected count**, **whether fall
  selected count hit `k_abs_min`**, and the **ratio of budget loss to rescue loss** across training.
- Add an **early-warning** flag if clean fall recall collapses *after warmup* (not epoch 1–2).
- Output namespace: `results/.../variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/`;
  checkpoints `checkpoints/.../variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/`.

These are **specifications**; implementation + a smoke/self-check + a code review must precede any A1 run
(same discipline as Variant H).

## 6. Seed-42 pilot plan (pre-register A1 only)

**Allowed:** A1 · seed 42 · LeNet · same UT-HAR/SenseFi split · ε=0.030 · selection-v2 style · same clean
guard (0.70/0.65) · same evaluation suite as H1 (clean / FGSM@0.030 / PGD@0.030 / PGD-20 / 18-ε sweeps /
probability+logit exports / confidence-inversion / Wilson).

**Not allowed:** A2 (until A1 completes + reviewed) · A0 (unless separately approved) · H2/H3 · seed 44 ·
seed 45/46 · architecture changes · threshold tuning on test · any automatic follow-up.

## 7. Stop conditions (during a future A1 run)

Stop immediately and report if any occur:
- NaN/inf in total loss or either new term;
- nonfall-budget or fall-rescue invalid (e.g., not finite, or always zero with valid samples);
- **fall selected count remains < 4 despite the `k_abs_min` floor** (floor not working);
- clean fall recall remains 0 **after warmup**;
- PGD fall recall remains 0 **after warmup**;
- clean guard cannot recover;
- the model is clearly suppressing the fall class to cut FP;
- an unsupported setting or seed starts;
- any automatic follow-up starts.

**Do not stop** for epoch-1/epoch-2 cold-start alone (the validated Variant G/G1/H1 baselines all began with
recall 0 before recovering ~epoch 27–61).

## 8. Success criteria (pre-registered; evaluated on seed-42 test)

**Strong success:** PGD recall ≥ 0.80 ∧ PGD FP ≤ 45 ∧ clean fall recall ≥ 0.90 ∧ clean acc ≥ 0.70 ∧
macro-F1 ≥ 0.65 ∧ PGD-20 durability holds ∧ confidence inversion not worsened vs G1 (gap ≤ +0.012).

**Promising improvement:** PGD recall ≥ 0.70 ∧ PGD FP ≤ 65 ∧ clean fall recall ≥ 0.90 ∧ clean guard holds ∧
PGD-20 recall ≥ 50% of PGD-10 ∧ inversion not worse than H1 (gap ≤ +0.061).

**Minimum useful:** PGD recall ≥ 0.60 ∧ PGD FP < G1 seed-42 FP (104) ∧ clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65 ∧
clean fall recall ≥ 0.90 ∧ PGD-20 recall > 0 ∧ inversion not worse than H1.

**Reject:** PGD recall < 0.60; or clean guard fails; or FP reduction occurs by recall collapse; or PGD FP
remains high with no recall gain; or PGD-20 collapses; or inversion worsens badly; or A1 is dominated by
Variant G G1 seed-42 (recall 0.689 / FP 104 / acc 0.716 / mF1 0.670 / PGD-20 0.622 / inversion +0.012).

## 9. Decision rules after A1

- **If A1 is REJECT:** do **not** run A2 automatically; write an **A1 mechanism report**; decide (with the
  user) whether to stop or redesign.
- **If A1 is MINIMUM USEFUL:** review before deciding A2 or seed-44; **no automatic follow-up**.
- **If A1 is PROMISING:** consider an A2 or a seed-44 pre-registration — **only after review**.
- **If A1 is STRONG:** write a **seed-44 pre-registration** (validation-only gate) **before** any seed-44 run.

## 10. Architecture and event-level boundary

- **No architecture changes in Option A** (LeNet only).
- **No event-level aggregation in Option A** (window-level only).
- Those are **separate future paths** with their own pre-registrations.
- **Do not mix** objective redesign + architecture change + temporal aggregation in one experiment.

## 11. No-claim boundary

- Option A is **not yet run** (and not yet implemented).
- Current work does **not** achieve > 80% recall with < 10% false alarms (joint target **unmet**).
- **No** clinical, deployment, product, certified, or over-the-air claim. Window-level, digital-domain,
  white-box, benchmark-level, research-stage only.

## 12. Final recommendation

**Recommended next action:** implement only the **A1** pre-registered code changes (with a smoke/self-check
and code review first), and run **A1 seed-42 only after explicit approval**. **Do not** run A2, A0, H2/H3,
seed 44, or Chapter 6 finalization automatically.

### Scope reminder
Pre-registration only — no training/attacks/evaluation/H2/H3/seed44-46/script change/`.tex` edit/artifact
overwrite. Recommends A1 (seed 42) as the next pilot after a separate implementation + review; starts
nothing.
