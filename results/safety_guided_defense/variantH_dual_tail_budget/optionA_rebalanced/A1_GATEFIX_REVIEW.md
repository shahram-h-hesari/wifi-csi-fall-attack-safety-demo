# A1 gate-fix code-review audit (pre-pilot)

> **REVIEW ONLY.** Static code inspection + read-only git/grep checks. No training, no attacks, no
> evaluation, no full pilot; no A2/A0, no H2/H3, no seed 44/45/46; no code change, no `.tex` edit, no
> artifact overwrite, no commit until reviewed. Audits commit `9d0a907 Fix A1 pilot gate and fall-rescue
> floor threading` on branch `feature/safety-proxy-guided-defense`. Window-level, digital-domain, white-box,
> processed CSI; **no product / clinical / deployment / certified / over-the-air claim.**

## Scope

Confirms the prior blocking finding in [A1_CODE_REVIEW.md](A1_CODE_REVIEW.md) (Decision B) is resolved and
the A1 seed-42 pilot is safe to approve. Files inspected (read-only):
`scripts/train_variantH_dual_tail_budget.py`, the committed `_smoke/A1_gatefix/seed42/` artifacts, and
`OPTION_A_REBALANCED_PREREGISTRATION.md`.

## 1. Prior blocking issue — FIXED ✅

`run_pilot` now resolves and threads the Option-A floor into the training epoch:

- line 495: `kabs = cfg.get("k_abs_min")` (A1 → `4`; H1 → `None`).
- lines 528–531: `train_one_epoch_variantH(..., max_batches=None, fall_k_abs_min=kabs)`.
- chain verified end-to-end: `train_one_epoch_variantH(fall_k_abs_min)` (line 170) →
  `variantH_margin_terms(fall_k_abs_min)` (line 211) → `fall_rescue_loss(k_abs_min)` (line 163) →
  `_resolve_k_floor(n, k_frac, k_abs_min)` (line 146).

The prior bug — a future A1 pilot silently running the fall-rescue term at k ≈ 1 without the floor — **can no
longer occur**.

## 2. A1 pilot gate is narrow ✅

Defense-in-depth, in `main()`:

- **seed gate** (line 644): any `seed != 42` → `SystemExit` (blocks seed 44/45/46 and all other seeds),
  *before* foundation load.
- **setting whitelist** (line 647): unknown settings rejected by `--setting choices` + this guard.
- **OPTIONA_RUNNABLE gate** (line 649): `A2`/`A0` → `SystemExit` *before* foundation load
  (`OPTIONA_RUNNABLE = {"A1"}`, line 70).
- **pilot gate** (line 678): `--pilot` allowed only for setting in `("H1","A1")`; `H2`/`H3` → `SystemExit`.
- **run_pilot assert** (line 493): redundant hard guard `args.setting in ("H1","A1") and args.seed == 42`.

Allowed: `--pilot --setting A1 --seed 42`. Blocked: A2, A0, H2, H3, seed44/45/46, any other seed/setting —
each by at least one guard, A2/A0/seed-gate by two.

## 3. H1 behavior unchanged ✅

- `SETTINGS["H1"]` has `k_abs_min: None` (line 61) → `kabs = None` → `_resolve_k_floor` floor branch
  inactive (line 97 `k = base`) → committed Variant H fall-rescue selection preserved.
- `optionA = args.setting in OPTIONA_SETTINGS` is `False` for H1 → namespace stays
  `variantH_dual_tail_budget/H1/seed42` (results + checkpoints), run name `seed42_variantH_H1` unchanged
  (lines 497, 503–505) → H1 checkpoint filenames identical.
- Only additive changes to H1's record: extra per-epoch logging columns
  (`nonfall_selected_count`, `fall_selected_count`, `fall_k_abs_floor_active_frac`,
  `budget_to_rescue_loss_ratio`) and extra metadata keys. No change to loss, selection rule, guard,
  early-stop, or evaluation.

## 4. A1 namespace correct ✅

For `optionA` settings (line 500–502):
- results → `results/safety_guided_defense/variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/`
- checkpoints → `checkpoints/safety_guided_defense/variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/`

Matches `OPTION_A_REBALANCED_PREREGISTRATION.md` §5. This is distinct from both the H1 namespace and the
smoke namespace (`optionA_rebalanced/_smoke/...`), so a future A1 pilot cannot collide with H1/G1 or with the
committed smoke artifacts.

## 5. Gate-fix smoke artifacts support the fix ✅

From committed `_smoke/A1_gatefix/seed42/` (self-check JSON, smoke log/summary, report):

- **Self-check PASS:** class indices; A1 params exact (`lam_b=0.25`, `lam_r=1.0`, `k_abs_min=4`,
  `k_frac=0.25`, `gamma=0.5`); targeted-sign increased; TopK correctness; finite/nonzero one-batch losses;
  directionality (budget ↓ `z_f−z_y`, rescue ↑ `z_f−max_{c≠f}z_c`).
- **`k_abs_min=4` floor PASS:** synthetic `n=10 → 4`, `n=3 → 3`, `n=0 → 0` (loss 0, no error). Consistent
  with `_resolve_k_floor`: n=10 base=⌈2.5⌉=3 → max(3,4)=4; n=3 base=⌈0.75⌉=1 → min(max(1,4),3)=3; n=0 → 0.
- **Smoke PASS (2×6, seed 42):** all loss terms finite; `nonfall_budget` and `fall_rescue` nonzero both
  epochs; `fall_k_abs_floor_active_frac = 1.0` (floor active every batch); `fall_selected_count` 2.83→2.50 =
  `min(4, n_adv_falls)` for these small batches; `budget_to_rescue_loss_ratio` logged (0.503 → 0.180).
- **No scientific claim:** epoch-1/2 recall 0 is the expected cold-start; summary JSON `note` and report both
  state smoke-only, no pilot/convergence conclusion. `test_set_used: false`, no `.pt` persisted.
- Reproduces committed A1 smoke to sub-0.1% drift (loss 4.578/4.290 vs 4.575/4.291).

## 6. No disallowed files committed ✅

Commit `9d0a907` contains exactly 5 files: `scripts/train_variantH_dual_tail_budget.py` + 4 `A1_gatefix`
smoke artifacts (`.md`, `_selfcheck_summary.json`, `_smoke_log.csv`, `_smoke_summary.json`). Verified:
- no `.pt`, no `.tex` (grep over commit name-only = none);
- no Variant G files changed since `db30d54` (`git diff --name-only db30d54 HEAD --` Variant G files empty);
- no A1 full-pilot artifacts, no A2/A0, no H2/H3, no seed44/45/46;
- committed real-A1 smoke folder `_smoke/A1/seed42/` intact (4 files, untouched).

## 7. Risk assessment

| risk | status | basis |
|---|---|---|
| A1 pilot runs **without** the floor | **Eliminated** | `kabs` threaded through the full call chain (§1); self-check + smoke prove floor active |
| A2/A0 run accidentally | **Eliminated** | `OPTIONA_RUNNABLE` guard (line 649) *and* pilot gate (line 678) |
| H2/H3 run accidentally | **Eliminated** | pilot gate (line 678) + run_pilot assert (line 493) |
| seed44/45/46 run accidentally | **Eliminated** | seed gate (line 644) *before* foundation load + run_pilot assert |
| overwrite H1/G1 artifacts | **Eliminated** | A1 writes to disjoint `optionA_rebalanced/A1/seed42` namespace (§4); H1 namespace unchanged |
| smoke overwrote committed A1 smoke | **Eliminated** | `--smoke-tag` routed gate-fix run to `A1_gatefix/`; `_smoke/A1/` intact (§6) |

Residual note (non-blocking): the A1 pilot has **not** been run; the pre-registered seed-42 success/reject
criteria in `OPTION_A_REBALANCED_PREREGISTRATION.md` §8–§9 still govern interpretation, and the joint target
(> 80% PGD recall AND < 10% FP) remains **unmet**. This audit clears the *code path*, not the scientific
outcome.

## 8. Final decision

**A — APPROVE A1 seed42 pilot.**

The blocking issue is fixed, the gate is narrow with defense-in-depth, H1 is unchanged, the namespace is
correct and disjoint, and the smoke/self-check evidence confirms the floor behaves as designed.

Approval scope:
- **A1 only** (no other Option-A or Variant H setting);
- **seed 42 only**;
- **no A2/A0**;
- **no H2/H3**;
- **no seed 44** (a separate committed pre-registration is required first);
- **no architecture change** (LeNet only);
- **no thesis / scientific / product / clinical / deployment / certified / OTA claim** until the full A1
  evaluation (clean / FGSM / PGD / PGD-20 / ε-sweeps / probability+logit exports / confidence-inversion /
  Wilson) is complete and reviewed against the pre-registered criteria.

### Scope reminder
Review only — no training/attacks/evaluation/A2/A0/H2/H3/seed44-46/code change/`.tex` edit/artifact
overwrite. Approves the A1 seed-42 pilot code path; starts no run.
