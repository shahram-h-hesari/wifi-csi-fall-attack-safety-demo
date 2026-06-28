# Option B: FAR-constrained adaptive-Lagrangian rescue — implementation spec & smoke-test plan

> **Specification only — NO code, NO training, NO evaluation, NO checkpoints, NO `.tex`, NO change to
> A1/G1/H1 result files, NO commit performed by this document.** This is the math-to-code plan + smoke/self-
> check design that must be reviewed (Gate 1) **before** any code is written. Source of truth =
> `ADAPTIVE_LAGRANGIAN_FAR_CONSTRAINED_PREREGISTRATION.md` (committed at `89f78a0d`). Window-level,
> digital-domain, white-box, processed CSI; test n=500 (45 fall / 455 non-fall), validation n=496 (44 falls),
> ε=0.030. **No product / clinical / deployment / certified / over-the-air claim.**

## 1. Source-of-truth pre-registration summary (pinned first-pilot)

| knob | pinned value |
|---|---|
| seed | **42 only** |
| architecture | **LeNet only** |
| dataset | **UT-HAR only** |
| train epsilons | **`{0.005, 0.015, 0.03}`** |
| `λ_r` (rescue weight, fixed) | **1.0** |
| `λ_b(0)` (initial budget weight) | **0.25** |
| `η` (step size) | **0.10** |
| `λ_b,max` (cap) | **1.0** |
| update cadence | **epoch-level only** (no per-mini-batch update) |
| constraint signal | **validation PGD-10 FAR only** (PGD@0.030, steps=10) |
| fall-rescue `k_abs_min` | **4** (retained) |
| base (frozen Variant G G1) | `λ_s=λ_f=λ_t=1.0`, `w_wr=2.0`, `γ_b=γ_r=0.5`, fall weight 3 |
| test-set use during train/selection | **none** (held out until a separate approval) |

Update rule (index `t` = epoch):
`λ_b(t+1) = clip(λ_b(t) + 0.10·(FAR_val_PGD10(t) − 0.10), 0, 1.0)`, `λ_b(0)=0.25`.

Selection score (validation only):
`Score = PGDRecall − 4.0·max(0, FAR−0.10) − 2.0·max(0, 0.90−CleanFallRecall) − 2.0·max(0, 0.70−CleanAcc)`.

## 2. Proposed code-change locations

**Create a NEW script** — do **not** modify `scripts/train_variantH_dual_tail_budget.py` (its A1/H1 pilot
gates and committed runs must stay byte-stable). Proposed:

`scripts/train_optionB_adaptive_lagrangian.py`

Rationale and reuse boundary:
- **Reuse by import (read-only), never by edit.** Import the frozen foundation + shared helpers:
  - from `scripts.training_safety_guided_*` (the `tvg`/`tsg` modules already used): `load_foundation`,
    `compute_validation_bundle`, `targeted_fall_pgd`, `safety_score` infra, `targeted_sign_check`,
    `V2_GUARD_ACC`/`V2_GUARD_F1`, source-weight + margin utilities.
  - from `scripts/train_variantH_dual_tail_budget.py`: `fall_rescue_loss`, `nonfall_budget_loss`,
    `variantH_margin_terms`, `_resolve_k_floor`, `train_one_epoch_variantH` (or a thin Option-B epoch wrapper
    that calls the same term functions). Importing does not modify the file.
  - **No automatic helper-copy fallback in the first implementation.** Reuse the Variant H/A1 helpers by
    **safe import** wherever possible (a module-level import that does not trigger training, argument
    parsing, or other side effects). **If the imports are not side-effect-safe, or the helper functions are
    too entangled to import cleanly, the implementation must STOP and request a code-review approval before
    copying or duplicating any helper logic.** Copy/duplication is **not** pre-authorized here and must not be
    done silently inside the first implementation; it requires an explicit separate decision at Gate 2.
- **New namespace, disjoint from all committed runs:**
  - results → `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/`
  - checkpoints → `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/`
  - smoke/self-check → `.../adaptive_lagrangian_far_constrained/_smoke/optionB/seed42/` (and a `--smoke-tag`
    override, mirroring the A1 gate-fix pattern, so re-smokes never overwrite committed artifacts).
- **No change to** `export_probability_predictions.py`, `run_variantG_eval.py`, Variant G files, or any A1/
  G1/H1 result/checkpoint. The Option-B test evaluation (later, separately approved) reuses
  `export_probability_predictions.py --split test` unmodified, exactly as the A1 kill-check did.

**Functions likely needed in the new script:**
- `SETTINGS = {"optionB": {...pinned...}}`; gates `OPTIONB_RUNNABLE = {"optionB"}`.
- `lambda_update(lam_cur, far_val, eta=0.10, lam_max=1.0, target=0.10)` → returns `clip(lam_cur + eta*(far_val-target), 0, lam_max)` (pure function, unit-tested in self-check).
- `selection_score(vb)` → the pinned §1 score from a validation bundle.
- `run_self_check(args, F)`, `run_smoke(args, F)`, `run_pilot(args, F)`, `main()` — same skeleton/discipline
  as the Variant H script, with the epoch-level adaptive update threaded between epochs.

## 3. Adaptive update implementation logic

```
# computed ONCE before the loop from the validation labels (no hard-coded denominator):
N_val_nonfall = count(y_val != fall_class)                                      # expected 452 for seed42 UT-HAR
assert N_val_nonfall == 452, "validation non-fall count mismatch -> STOP (split mismatch)"   # see note below

lambda_b_current = 0.25                        # λ_b(0)
for epoch in 1..N:
    train_one_epoch(..., lam_b = lambda_b_current, lam_r = 1.0, k_abs_min = 4)   # uses CURRENT λ_b
    vb = compute_validation_bundle(... PGD-10 @0.030 ...)                        # VALIDATION only
    far_val = vb["val_pgd_false_fall_alarms"] / N_val_nonfall                    # FAR_val_PGD10(t)
    lambda_b_next = clip(lambda_b_current + 0.10 * (far_val - 0.10), 0.0, 1.0)   # λ_b(t+1)
    log(epoch, lambda_b_current, lambda_b_next, far_val, N_val_nonfall, vb metrics, losses, diagnostics)
    do_checkpoint_selection(vb)                                                  # validation only
    lambda_b_current = lambda_b_next                                             # used NEXT epoch
```

- **FAR denominator is computed, not hard-coded.** `N_val_nonfall = count(y_val != fall_class)` is derived
  from the validation labels once before training, and `FAR_val_PGD10 = FP_val_PGD10 / N_val_nonfall`.
- **Split-integrity guard.** For the seed-42 UT-HAR pre-registered split the expected count is **452**
  non-fall windows (496 − 44 falls). The implementation must **assert/log** `N_val_nonfall == 452`; if the
  count differs, it **stops (or hard-flags) as a split mismatch before any pilot** rather than silently
  dividing by an unexpected denominator. `N_val_nonfall` is also logged every epoch and in metadata for
  auditability.
- The epoch trains with `lambda_b_current`; the update is computed **after** validation and applied to the
  **next** epoch only — exactly one update per epoch (no EMA, no per-batch update).
- **Never** compute or use a test-set FAR anywhere in the loop (asserted; see §7).
- Both `lambda_b_current` and `lambda_b_next` are logged every epoch so the trajectory is auditable.

## 4. Checkpoint-selection logic

1. **Hard clean guard (all three required):** clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65 ∧ clean fall recall ≥ 0.90.
   Checkpoints failing any are ineligible.
2. Among eligible checkpoints, maximize the pinned score (validation bundle, PGD-10 @0.030):
   `Score = PGDRecall − 4.0·max(0, FAR−0.10) − 2.0·max(0, 0.90−CleanFallRecall) − 2.0·max(0, 0.70−CleanAcc)`.
3. Save candidate checkpoints: **max-score** (primary), **max-recall-within-guard**, **min-FAR-within-guard**
   (transparency, like selection-v2). Selection uses **validation only**.
4. **Test evaluation is NOT part of training.** It runs only after training completes **and** a separate
   approval (Gate 5), reusing `export_probability_predictions.py --split test` unmodified.

## 5. Required logs / metadata

**Per-epoch training log (CSV) columns:**
- `epoch`, `lambda_b_current`, `lambda_b_next`, `far_val_pgd10`, `n_val_nonfall`
- `val_pgd_false_fall_alarms` (PGD FP), `val_pgd_fall_recall`
- `val_clean_accuracy`, `val_clean_macro_f1`, `val_clean_fall_recall`
- `mean_nonfall_budget`, `mean_fall_rescue` (and base/src/fall/tgt means for parity with Variant H log)
- `fall_k_abs_floor_active_frac`, `fall_selected_count`, `nonfall_selected_count`
- `clean_guard_eligible` (0/1), `selection_score`
- `sel_maxscore`, `sel_maxrec`, `sel_minFA` (which candidate(s) updated this epoch)

**Run metadata (JSON):** all §1 pinned values, the literal update-rule string, `target=0.10`, `n_nonfall_val`,
final `lambda_b` trajectory summary (min/max/last), selected epochs + candidate metrics, split sizes,
`test_set_used: false`, git commit, device/lib versions, claim boundary, and any stop condition that fired.

## 6. Smoke / self-check design

**No full training.** Self-check = pure-function + one-batch checks; smoke = a tiny run (e.g. 2 epochs ×
few batches), writing only to the `_smoke` namespace (with `--smoke-tag` override).

**Self-check (deterministic, no training):**
- **Gate check:** the script refuses any setting other than `optionB` and any seed other than 42; refuses
  A2/A0/H2/H3 and seed 44/45/46 (assert the gate raises `SystemExit`).
- **`lambda_update` math (synthetic FAR):**
  - FAR = 0.15 → `0.25 + 0.10·(0.15−0.10) = 0.255` (increase).
  - FAR = 0.05 → `0.25 + 0.10·(0.05−0.10) = 0.245` (decrease).
  - FAR = 1.00 (very high), iterate → monotone increase, **clips at 1.0**, never exceeds.
  - FAR = 0.00 (very low), iterate from a small λ_b → monotone decrease, **clips at 0.0**, never negative.
  - assert exact equality to 1e-9 on the two single-step cases.
- **Cadence:** assert the update is invoked **exactly once per epoch** (counter equals epoch count; no
  per-batch invocation) on a 2-epoch dry loop with a stubbed validation FAR.
- **Selection score:** assert `selection_score` returns the hand-computed value on a synthetic bundle (e.g.
  recall 0.6, FAR 0.15, cleanFR 0.95, acc 0.72 → `0.6 − 4.0·0.05 − 0 − 0 = 0.40`).
- **Term reuse parity:** one-batch `fall_rescue`/`nonfall_budget` finite and nonzero; `k_abs_min=4` floor
  active (n=10→4, n=3→3, n=0→0), matching the committed Variant H self-check.
- **No test access:** assert the validation bundle is built from the val loader and that no test loader is
  referenced anywhere in the train/selection path (static check + runtime guard).

**Smoke (tiny run):**
- 2 epochs × few batches, seed 42, `optionB` only; writes to `_smoke/optionB/seed42/` (or `--smoke-tag`).
- Verify: losses finite; budget+rescue nonzero; floor active fraction logged; `lambda_b_current` and
  `lambda_b_next` logged each epoch and consistent with the update rule given the observed smoke FAR;
  exactly one update per epoch; `test_set_used=false`; cold-start recall 0 is expected (no convergence claim).
- Verify selection score is computed and logged but **no** checkpoint is treated as a result (smoke = code
  correctness only).

## 7. Failure / stop conditions

Stop immediately and report if any occur:
- **NaN/inf** in total loss or any term.
- **Missing PGD validation metrics** (no `val_pgd_*` available to form the FAR signal).
- **`lambda_b` update lands outside [0, 1.0]** (clip invariant violated) — hard bug.
- **Validation non-fall count mismatch** (`N_val_nonfall != 452` for the seed-42 UT-HAR split) — stop/flag as
  a split mismatch before any pilot rather than dividing by an unexpected denominator.
- **Any test-set access during training or selection** (must never happen) — hard bug.
- **All-zero rescue or budget term** despite valid fall / non-fall examples.
- **Clean guard never eligible after the minimum epoch** (model cannot satisfy the clean floors).
- **Accidental unauthorized setting or seed** (anything ≠ optionB / seed 42) starts.
- Do **not** stop for epoch-1/2 cold-start alone (G/G1/H1/A1 all began at recall 0).

## 8. Approval gates (sequential; each reviewed before the next)

- **Gate 1 — implementation spec review** (this document). No code until approved.
- **Gate 2 — code implementation review** (the new script, math-to-code audit, gate/namespace check).
- **Gate 3 — smoke / self-check review** (run self-check + tiny smoke; verify §6 + §7; no pilot yet).
- **Gate 4 — seed-42 pilot approval** (single pinned config; explicit go-ahead).
- **Gate 5 — held-out test evaluation approval** (after the pilot, reuse `export_probability_predictions.py`
  unmodified; classify against pre-registered §8 criteria).

### Scope reminder
Specification only — no code/training/evaluation/checkpoints/`.tex`/A1-G1-H1 change. Defines where and how
Option B would be implemented and how it would be smoke-checked; the next deliverable is the Gate-2 code
implementation **after this spec is reviewed**. Starts nothing.
