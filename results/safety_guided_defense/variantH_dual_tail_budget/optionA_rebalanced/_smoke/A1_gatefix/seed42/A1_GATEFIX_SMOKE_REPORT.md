# Option A / A1 — gate-fix re-smoke report

> **SMOKE ONLY — code-correctness check, NOT a pilot, convergence, or scientific result.** No full pilot,
> no A2/A0, no H2/H3, no seed 44/45/46, no architecture change, no `.tex` edit. No `.pt` persisted. **No
> thesis / product / clinical / deployment / certified / over-the-air claim.** The epoch-1/2 recall-collapse
> is the expected cold-start (Variant G/G1/H1 began identically), **not** a convergence conclusion.

## Why this gate-fix was needed

The committed A1 code-review audit ([A1_CODE_REVIEW.md](../../A1_CODE_REVIEW.md), Decision B) found a **real
blocking bug** in `run_pilot`: the pilot training path did **not** thread the Option-A fall-rescue floor and
was hard-coded to setting `H1`. Consequently, a future A1 full pilot would have silently run **without** the
`k_abs_min` floor (fall-rescue TopK collapsing to k ≈ 1 fall/batch), invalidating the entire A1 design
intent. The audit was approved precisely because it caught this before any A1 pilot was launched.

## What the fix changes (`scripts/train_variantH_dual_tail_budget.py` only)

- **`run_pilot` now threads the floor:** the per-epoch training call passes
  `fall_k_abs_min=cfg.get("k_abs_min")` (A1 → 4; H1 → `None`, i.e. committed behavior unchanged).
- **A1 pilot gate opened narrowly:** the `--pilot` path is permitted **only** for
  `--pilot --setting A1 --seed 42` (alongside the pre-existing H1 seed-42 pilot).
- **A2 / A0 remain blocked** by the `OPTIONA_RUNNABLE` guard (only A1 approved).
- **H2 / H3 remain blocked** at the pilot gate (re-review required).
- **seed 44 / 45 / 46 remain blocked** by the seed gate (separate committed pre-registration required).
- A1 pilot artifacts are routed to the Option-A namespace
  `results/.../variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/` (and matching checkpoints dir).
- Per-epoch logging now records `nonfall_selected_count`, `fall_selected_count`,
  `fall_k_abs_floor_active_frac`, and `budget_to_rescue_loss_ratio`; metadata records `k_abs_min`.
- A `--smoke-tag` option lets the re-smoke write to this `A1_gatefix` folder **without overwriting** the
  committed `_smoke/A1/seed42/` artifacts. `--smoke-tag` does **not** affect the `--pilot` path.

## Self-check (PASS)

- class-index assertions PASS (FALL=1, NUM=7, WALK=2, RUN=4, nonfall {0,2,3,4,5,6}).
- **A1 params PASS** (`lam_b=0.25`, `lam_r=1.0`, `k_abs_min=4`, `nonfall_k_frac=0.25`,
  `fall_rescue_k_frac=0.25`, `gamma_b=0.5`, `gamma_r=0.5`).
- **`k_abs_min=4` floor PASS:** synthetic `n=10 → selected 4`; `n=3 → selected 3`;
  `n=0 → selected 0`, loss 0.0 (no error); selected rows = largest hinges; gradients flow only through
  selected rows.
- targeted-PGD sign PASS (median fall logit 0.0097 → 0.0279; increased).
- TopK correctness PASS (top-2 mean 4.0; grad only selected; empty→0; k≥1).
- one-batch losses finite; nonfall_budget 0.980 > 0, fall_rescue 0.573 > 0; rescue_diag valid=3 → selected 3
  with `floor_active=True` (n<4 clamps to n, not an error).
- directionality PASS (minimizing budget reduces z_f−z_y; minimizing rescue increases z_f−max_{c≠f}z_c).

## A1 gate-fix smoke (2 epochs × 6 batches, seed 42) — PASS

| epoch | loss | base | budget | rescue | nonfall_sel | fall_sel | floor_active_frac | b/r_ratio | acc | cleanFR | pgd_fr | pgd_FP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 4.578 | 1.973 | 0.456 | 0.907 | 7.50 | 2.83 | 1.00 | 0.503 | 0.244 | 0.000 | 0.000 | 0 |
| 2 | 4.290 | 1.970 | 0.180 | 1.004 | 8.00 | 2.50 | 1.00 | 0.180 | 0.244 | 0.000 | 0.000 | 0 |

- All loss components **finite**; **nonfall_budget and fall_rescue nonzero** each epoch.
- **Fall-rescue floor active every batch** (`fall_k_abs_floor_active_frac = 1.00`).
- **Fall selected count uses `min(4, n_adv_falls)`:** per-batch fall-selected ≈ 2.5–2.83 = all available
  adversarial falls in these tiny smoke batches (each batch had < 4 adv falls, so the floor clamps to n);
  whenever a batch has ≥ 4 adv falls it selects exactly 4 (proven by the synthetic `n=10 → 4` self-check).
  This is the intended fix vs H1's effective k ≈ 1 fall/batch.
- **`budget_to_rescue_loss_ratio` logged** each epoch (0.503 → 0.180); with `lam_b=0.25` the budget term is
  smaller relative to rescue than in H1 (the intended rebalance).
- Cold-start at 2 epochs (clean acc 0.244, recall 0) — **expected**, identical to G/G1/H1 starts.

This run reproduces the committed A1 smoke to sub-0.1% drift (epoch-1 loss 4.578 vs 4.575; epoch-2 4.290 vs
4.291), confirming the gate-fix path preserves A1 behavior.

## Status

A1 gate-fix code is correctness-validated. **The A1 full pilot was NOT run** and must be launched explicitly
after this fix is reviewed. **No convergence, pilot, or scientific claim is made here** — this is a
smoke-only code-correctness check.
