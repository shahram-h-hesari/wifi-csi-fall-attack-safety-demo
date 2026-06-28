# Option A / A1 — smoke-only validation report

> **SMOKE ONLY — code-correctness check, NOT a pilot or convergence result.** No full pilot, no A2/A0, no
> H2/H3, no seed 44/45/46, no architecture change, no `.tex` edit. No `.pt` persisted. **No
> thesis / product / clinical / deployment / certified / over-the-air claim.** The epoch-2 recall-collapse
> flags are the expected cold-start (Variant G/G1/H1 began identically), **not** a convergence conclusion.

## Commands run
- Self-check: `python scripts/train_variantH_dual_tail_budget.py --setting A1 --self-check`
- Smoke: `python scripts/train_variantH_dual_tail_budget.py --setting A1 --smoke --epochs 2 --smoke-batches 6`

## Git
- HEAD at run time: `89ac238133beb60f695b83d6f06d318dbed04eab`
- Diff: **only** `scripts/train_variantH_dual_tail_budget.py` (+128 / −34); Variant G files unmodified.

## A1 parameters (match OPTION_A_REBALANCED_PREREGISTRATION.md)
`lam_b = 0.25`, `lam_r = 1.0`, `nonfall k_frac = 0.25`, `fall_rescue k_frac = 0.25`,
**`fall_rescue k_abs_min = 4`**, `gamma_b = 0.5`, `gamma_r = 0.5`; base (Variant G G1) `lam_s=lam_f=lam_t=1.0`,
`w_wr=2.0`, fall weight 3 — unchanged.

## Self-check (PASS)
- class-index assertions PASS (FALL=1, NUM=7, WALK=2, RUN=4, nonfall {0,2,3,4,5,6}).
- **A1 params PASS** (exact match to pre-registration).
- **k_abs_min floor PASS:** synthetic n=10 → selected **4**; n=3 → selected **3**; n=0 → selected **0**, loss 0;
  selected = largest hinges; gradients flow only through selected rows.
- targeted-PGD sign PASS (median fall logit 0.0097 → 0.0279; P(fall) 0.1414 → 0.1441; increased).
- TopK correctness PASS (top-2 mean 4.0; grad only selected; empty→0; k≥1).
- one-batch losses finite; **nonfall_budget 0.980 > 0**, **fall_rescue 0.573 > 0**; rescue_diag valid=3 →
  selected 3 with `floor_active=True` (n<4 clamps to n, not an error).
- directionality PASS: minimizing nonfall-budget reduces $z_f-z_y$ (−0.113 → −0.238); minimizing
  fall-rescue increases $z_f-\max_{c\neq f}z_c$ (−1.123 → −0.998).

## Smoke (2 epochs × 6 batches, seed 42)
| epoch | loss | base | src | fall | tgt | budget | rescue | nonfall_sel | fall_sel | floor_active_frac | b/r_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 4.575 | 1.973 | 0.333 | 0.905 | 0.346 | 0.456 | 0.905 | 7.5 | 2.83 | 1.00 | 0.504 |
| 2 | 4.291 | 1.970 | 0.127 | 1.008 | 0.134 | 0.180 | 1.008 | 8.0 | 2.50 | 1.00 | 0.178 |

- All loss components **finite**; **nonfall_budget and fall_rescue nonzero** each epoch.
- **Fall-rescue floor active every batch** (`floor_active_frac = 1.0`). Per-batch fall-selected ≈ 2.5–2.83 =
  **all available adversarial falls** (the floor selects `min(4, n_fall)`); whenever a batch has ≥ 4 adv
  falls it selects exactly 4 (proven by the synthetic n=10 → 4 self-check). This is materially higher than
  H1's effective k ≈ 1 fall/batch — the intended fix.
- `budget_to_rescue_loss_ratio` logged (0.504 → 0.178); with `lam_b=0.25` the budget term is now smaller
  relative to rescue than in H1 (the intended rebalance).
- Cold-start at 2 epochs (clean acc 0.244, recall 0) — **expected**, identical to G/G1/H1 starts; **no
  convergence/pilot conclusion drawn.**

## Warning fields (smoke = not applicable)
`clean_fall_recall_collapse_after_warmup`, `pgd_fall_recall_collapse_after_warmup`,
`fall_class_suppression_warning` = `not_applicable_smoke` (no warmup in a 2-epoch smoke).

## Status
A1 smoke-only code is correctness-validated. **A1 full pilot remains BLOCKED** (the `--pilot` path is
H1-only; A1 pilot refuses). A2/A0 are defined but **hard-blocked**; seed 44/45/46 blocked. The A1 seed-42
pilot must be launched explicitly after this implementation is reviewed.
