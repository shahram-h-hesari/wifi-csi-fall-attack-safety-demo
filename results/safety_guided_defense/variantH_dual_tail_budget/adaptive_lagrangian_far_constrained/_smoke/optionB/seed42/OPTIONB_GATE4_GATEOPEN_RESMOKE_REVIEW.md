# Option B — Gate-4 gate-opening patch re-smoke review

> **SMOKE / SELF-CHECK ONLY — code-correctness, NOT a pilot or convergence result.** No full pilot, no full
> training, no held-out test evaluation, no `.pt` checkpoints, no A2/A0/H2/H3/A1, no seed 44/45/46, no `.tex`
> edit, no A1/G1/H1 change. The valid seed-42 pilot command was **NOT** run. Cold-start recall 0 over 2
> epochs is expected. **No product / clinical / deployment / certified / over-the-air claim.** Re-smokes the
> Gate-4 gate-opening patch to `train_optionB_adaptive_lagrangian.py` (opens `--pilot` for optionB+seed42
> only; `run_pilot` = fixed 70 epochs, no early stopping, validation-only selection).

## Commands and exit codes

| step | command | exit |
|---|---|---|
| self-check | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --self-check` | **0** |
| smoke | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --smoke --epochs 2 --smoke-batches 6` | **0** |
| seed44 smoke refusal | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --seed 44 --smoke` | **1** |
| seed44 pilot refusal | `python scripts/train_optionB_adaptive_lagrangian.py --setting optionB --seed 44 --pilot` | **1** |

The valid pilot command `--setting optionB --seed 42 --pilot` was **NOT executed**.

## Gate semantics after the patch (self-check `_check_gate`, all PASS)

- **Blocked (raise):** `H2/42`, `A1/42`, `A0/42`, `optionB/44` (smoke) **and** `H2/42`, `A1/42`, `optionB/44`
  (pilot). seed44 refusals confirmed at runtime with **exit 1**, before any data load.
- **Allowed (no raise):** `optionB/42` smoke **and** `optionB/42` pilot.

So the gate now permits exactly `optionB + seed 42` (smoke or pilot) and nothing else.

## Key smoke / self-check outputs

- **Synthetic λ-update checks:** `FAR=0.15 → 0.255` ✓, `FAR=0.05 → 0.245` ✓, high-FAR clips at 1.0 ✓,
  low-FAR clips at 0.0 ✓.
- **Live λ trajectory (smoke):** `0.250 → 0.240 → 0.230` (FAR=0 < target 0.10 ⇒ relax by 0.01/epoch) —
  unchanged by the refactor.
- **`N_val_nonfall = 452`** (computed from validation labels; split guard armed).
- **Selection-score checks:** no-violation `0.60` ✓, FAR-only `0.40` ✓, all-three `0.10` ✓.
- **Once-per-epoch cadence:** 3/3 synthetic ✓; smoke loop `assert updates == n_epochs` held.
- **No test-loader access:** val loader only; `_test_loader` never referenced.
- **budget/rescue nonzero:** budget 0.416 / 0.453, rescue 0.997 / 0.683 across the two epochs.
- **Floor active:** `fall_k_abs_floor_active_frac` = 1.00 / 0.83.
- Cold-start clean acc 0.244, recall 0 — expected; no claim.

## Artifacts

All re-smoke artifacts stayed under
`results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/_smoke/optionB/seed42/`:
- `optionB_smoke_log.csv` (deterministic; unchanged from Gate-3),
- `optionB_smoke_summary.json` (updated: new timestamp/elapsed),
- `optionB_selfcheck_summary.json` (updated: gate block now reflects opened-pilot semantics —
  `optionB_seed42_pilot_ok` replaces the old `pilot_refused`),
- `OPTIONB_GATE3_SMOKE_REVIEW.md` (prior), `OPTIONB_GATE4_GATEOPEN_RESMOKE_REVIEW.md` (this file).

**No `.pt` checkpoint created. No `optionB/seed42/{logs,metadata,analysis}` pilot directories created.**

## Fixed-70 / no-early-stopping pilot logic (ready for review)

`run_pilot` (now implemented) runs `_adaptive_train(mode="pilot", n_epochs=PILOT_EPOCHS=70)` with **no
patience/min-epochs branch**, saves only validation-selected checkpoints (maxscore / maxrec-within-guard /
minFA-within-guard, plus `last`) to the `optionB/seed42` checkpoint namespace, writes results to the
`optionB/seed42` results namespace, and records metadata with `fixed_epochs=70`, `early_stopping=false`,
`patience`/`min_epochs` = "inactive_not_used_for_optionB_pilot", `test_set_used=false`. This logic is staged
for review but **not executed**.

## Verdict

**Gate-4 gate-opening patch re-smoke: PASS.**
- Valid seed-42 pilot command was **not** run.
- Unauthorized seed44 smoke and pilot were **refused** (exit 1, before data load).
- Fixed-70 / no-early-stopping pilot logic is implemented and **ready for review**.

**Next step:** commit review of the gate-opening patch, then push, then a **separate explicit approval** to
launch the seed-42 pilot (`--setting optionB --seed 42 --pilot`). No pilot is launched by this re-smoke.

### Scope reminder
Re-smoke review only — no full pilot/training/test evaluation/checkpoints; no A2/A0/H2/H3/A1/seed44-46;
no `.tex`/A1/G1/H1 change. Records the Gate-4 gate-opening re-smoke PASS; the seed-42 pilot remains pending a
separate explicit launch approval.
