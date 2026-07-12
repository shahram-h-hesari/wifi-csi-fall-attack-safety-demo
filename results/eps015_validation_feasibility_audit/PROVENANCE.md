# Provenance — Task 3: Validation-Only PGD eps=0.015 False-Positive Audit and Feasibility Sweep

Generated: 2026-07-12. Analysis performed at repo commit `0d9ff96b15b7caf23b95b54a9feb6405251674c3`
on branch `feature/safety-proxy-guided-defense`. No thesis/Overleaf file was edited. No checkpoint
was loaded. No training or attack generation was run. No held-out-test file was opened.

## Scope

Authoritative target established in `research-os` commit `5fef192`: **Rfall > 0.90 AND FAR < 0.10
under PGD eps=0.015.** This task determines whether any existing saved validation-split PGD
eps=0.015 score axis reaches that target, and characterizes validation-side false alarms in
aggregate. It is analysis of existing validation evidence only -- not a new experiment, not a
threshold selection, not a protocol freeze, and not permission to read the held-out test.

## Inputs read (all pre-existing, committed artifacts; read-only)

- `results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep/eps0015/*_pgd_probabilities_val_epsilon_0_015.csv`
  (5 model/defense axes: AFAC_maxscore, D14B_seed44, GR1_macroF1, SA1_lowFA, ST1b6_lowFA) --
  the analyzed validation score exports. Each verified: 496 rows, 44 `fall_true_binary`, filename
  contains `_val_` and never `_test_`/`TESTREAD` (see `eps015_feasibility_lib.check_split_is_validation`).
- `results/defense_attempt_inventory/pgd_epsilon_frontier/h15_frozen_test_gate_numbers_eps0015.csv`
  -- source of the pre-registered/frozen validation thresholds for AFAC_maxscore, ST1b6_lowFA,
  SA1_lowFA (`tau_frozen_far012` column).
- `results/defense_attempt_inventory/PGD_EPSILON_RECALL_FAR_FRONTIER_PLAN.md` -- documents that
  `results/epsilon_sweep_predictions/pgd_predictions_short_epsilon_0_015.csv` (and its FGSM
  counterpart) is a mixed validation+test split (996 windows) with argmax-only labels; this
  artifact was excluded from this task's analysis for both reasons.
- `results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/FROZEN_H15_TEST_RESULT.md`
  -- source of the already-published test aggregate cited as fixed context only (TP 41, FN 4,
  FP 60, TN 395, recall 0.911111, FAR 0.131868). No per-window content from this file's sibling
  CSV was ever opened.
- `scripts/run_converged_attacks.py` (lines ~83-113) -- read only, to resolve the attack-norm
  question (Step 2). Not modified.

## What was NOT opened

- No file under `results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/*.csv`
  (the frozen test-read per-window probability exports).
- No file whose filename contains `_test_` or `TESTREAD`.
- No checkpoint file.
- No thesis/Overleaf file.

## Analysis code (new; this task)

- `scripts/analysis/eps015_feasibility_lib.py` -- pure functions (split-safety check, confusion
  metrics, threshold sweep, feasibility summary, false-positive source aggregation, score-margin
  buckets, axis-overlap comparison). No file I/O.
- `scripts/analysis/eps015_validation_feasibility_audit.py` -- driver; reads the validation
  artifacts listed above, verifies each via `check_split_is_validation` before use, writes the
  outputs listed below. New files only; nothing existing was overwritten.
- `scripts/analysis/test_eps015_feasibility_lib.py` -- 18 tests, synthetic fixtures only.

## Outputs (all new; this task)

- `results/eps015_validation_feasibility_audit/inventory.csv`
- `results/eps015_validation_feasibility_audit/operating_point_sweep.csv`
- `results/eps015_validation_feasibility_audit/per_axis_summary.csv`
- `results/eps015_validation_feasibility_audit/false_positive_source_summary.csv`
- `results/eps015_validation_feasibility_audit/score_axis_overlap.csv`
- `results/eps015_validation_feasibility_audit/provenance_manifest.csv` (paths + SHA256 hashes of every input and output artifact)
- `results/eps015_validation_feasibility_audit/REPORT.md`
- `results/eps015_validation_feasibility_audit/PROVENANCE.md` (this file)
- `results/eps015_validation_feasibility_audit/INTAKE_SUMMARY.md`

## Environment

Python 3.10.11, pandas 2.3.3, `.venv` (repo-local virtual environment). No GPU/CPU model
inference was performed -- this task only reads and aggregates already-saved CSV scores.

## Commands run

```
.venv/Scripts/python.exe scripts/analysis/eps015_validation_feasibility_audit.py
.venv/Scripts/python.exe -m pytest scripts/analysis/test_eps015_feasibility_lib.py -q
```
