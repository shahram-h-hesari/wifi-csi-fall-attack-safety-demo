# Option B (adaptive-Lagrangian FAR-constrained) — Gate-3 smoke review

> **SMOKE / SELF-CHECK ONLY — code-correctness, NOT a pilot or convergence result.** No full training, no
> pilot, no held-out test evaluation, no `.pt` persisted, no A2/A0/H2/H3, no seed 44/45/46, no `.tex` edit,
> no A1/G1/H1 change. Cold-start recall 0 over 2 epochs is expected (G/G1/H1/A1 began identically). **No
> product / clinical / deployment / certified / over-the-air claim.** Implements
> `train_optionB_adaptive_lagrangian.py` against `ADAPTIVE_LAGRANGIAN_FAR_CONSTRAINED_PREREGISTRATION.md` +
> `IMPLEMENTATION_SPEC_AND_SMOKE_PLAN.md` (committed at `df338705`).

## Commands and exit codes

| step | command | exit |
|---|---|---|
| self-check | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --self-check` | **0** |
| smoke | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --smoke --epochs 2 --smoke-batches 6` | **0** |

**Gate-demo refusals (real Python exit codes, no pipe masking):**

| command | message | exit |
|---|---|---|
| `... --setting optionB --pilot` | "The Option B FULL PILOT is NOT approved in this Gate-2 implementation … requires explicit Gate-4 approval." | **1** |
| `... --setting optionB --seed 44 --smoke` | "Option B is seed-42 ONLY for now (got seed 44); seeds 44/45/46 are blocked …" | **1** |

(`--setting` is additionally restricted to `optionB` by argparse `choices`; A2/A0/H2/H3 cannot be passed.)

## Files created (all under the approved `_smoke` namespace)

`results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/_smoke/optionB/seed42/`
- `optionB_selfcheck_summary.json`
- `optionB_smoke_log.csv`
- `optionB_smoke_summary.json`
- `OPTIONB_GATE3_SMOKE_REVIEW.md` (this file)

## Confirmations

- **No `.pt` checkpoint created** (smoke persists no weights; `git status` shows no `.pt`).
- **No pilot / full training / test evaluation ran** — 2 epochs × 6 batches only; `--pilot` refused;
  `test_set_used: false`.
- **No unauthorized setting/seed ran** — seed 44 refused (exit 1); pilot refused (exit 1); self-check gate
  block confirmed H2/A1/A0/seed44/pilot rejected and optionB+seed42 accepted.
- **No test loader accessed** — selection/training use `val_loader` only; `N_val_nonfall` is computed from
  validation labels; `F["_test_loader"]` is never referenced in the train/selection path.

## Key smoke outputs

- **Synthetic λ-update checks (self-check):** `FAR=0.15 → 0.25→0.255` ✓, `FAR=0.05 → 0.25→0.245` ✓,
  `high FAR clips at 1.0` ✓, `low FAR clips at 0.0` ✓.
- **Live λ trajectory (smoke):** `0.250 → 0.240 → 0.230` — with cold-start FAR=0 < target 0.10, the update
  relaxes λ_b by `0.10·(0−0.10) = −0.01` per epoch, exactly as designed (constraint satisfied ⇒ pressure
  released).
- **`N_val_nonfall = 452`** (expected 452; logged each epoch; split-integrity guard would stop on mismatch).
- **Selection-score checks (self-check):** no-violation `0.60` ✓, FAR-only `0.40` ✓, all-three `0.10` ✓.
- **Gate-rejection checks (self-check):** H2/A1/A0 rejected ✓, seed44 rejected ✓, pilot refused ✓,
  optionB+seed42 allowed ✓.
- **Once-per-epoch cadence:** 3 updates over 3 synthetic epochs ✓; the smoke loop's `assert updates ==
  epochs` held.
- **Floor active + terms nonzero:** `fall_k_abs_floor_active_frac` = 1.00 / 0.83 across the two epochs;
  `mean_nonfall_budget` (0.416 / 0.453) and `mean_fall_rescue` (0.997 / 0.683) both nonzero each epoch.
- Cold-start clean acc 0.244, recall 0 — **expected**, no convergence/pilot conclusion drawn.

## Verdict

**Gate-3: PASS.** Self-check and smoke both clean; gate, no-test-leakage, FAR-denominator, once-per-epoch
update, clip bounds, and selection-score invariants all verified at runtime; no `.pt`; artifacts confined to
the `_smoke` namespace.

**Next gate: Gate 4 — seed-42 pilot approval is required before any full run.** The pilot path remains gated
off in this implementation (`--pilot` exits 1) and must be explicitly authorized.

### Scope reminder
Smoke/self-check review only — no full training/pilot/test evaluation/checkpoints; no A2/A0/H2/H3/seed44-46;
no `.tex`/A1/G1/H1 change. Records the Gate-3 PASS; the seed-42 pilot stays gated pending Gate-4 approval.
