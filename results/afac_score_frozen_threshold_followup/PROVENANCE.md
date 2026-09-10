# Provenance — AFAC-Score Frozen Validation-Threshold Follow-Up (Stage 1 + Stage 2)

Generated: 2026-07-04. Repo commit at time of Stage 1: `1bcf6b8f35493a73269171c6b0678ca52b0a7580`,
branch `feature/safety-proxy-guided-defense`. Python 3.10.11, torch 2.12.0+cpu (`.venv`).
No thesis/Overleaf files edited. Nothing committed in this repo as part of Stage 1 or Stage 2
unless explicitly requested. Stage 1 was archived and committed in the Overleaf-linked thesis repo
(commit `65418ef2112ad6c465c0a01a4377e395c1079717`) before Stage 2 was run, preserving evidence that
the thresholds were fixed prior to any test contact.

## Scope of this stage

**Stage 1 only: validation-only threshold selection.** No held-out test file was read, opened, or
referenced by any script run in this stage. No training was performed. No threshold was applied to
the test split. This document covers Stage 1 exclusively; Stage 2 (test application) requires
separate approval and a separate PROVENANCE update.

## Checkpoint

- Internal name: `optionB_maxscore`. Thesis name: **AFAC-score**, the D8b appendix reference.
- Path: `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt`
- Trained: seed 42, 70 fixed epochs (checkpoint selected at epoch 68), CPU, torch 2.12.0+cpu,
  `test_set_used: false` per training metadata
  (`results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/metadata/seed42_optionB_metadata.json`).
- Historical status: this checkpoint's held-out test scores already exist (Gate-5 exports, below)
  and were used for the D8b post-hoc appendix row. Gate 5's own argmax evaluation REJECTED this
  checkpoint under its pre-registered clean-accuracy guard (test clean acc 0.694 < 0.70) — this is
  disclosed for the record and must accompany any frozen-threshold result in Stage 2 reporting.

## Data and splits

UT-HAR via SenseFi benchmark loader (`third_party/WiFi-CSI-Sensing-Benchmark`). Validation split:
496 windows (44 fall / 452 non-fall) — assert-checked in
`scripts/analysis/afac_score_stage1_validation_selection.py`. Held-out test split (500 windows, 45
fall / 455 non-fall) exists from the prior Gate-5 evaluation but was **not accessed** in Stage 1.

## New artifact generated in this stage

Validation per-window score export (inference only), via
`scripts/export_probability_predictions.py --split val`:

| File | Condition | Windows |
|---|---|---|
| `val_eval/optionB_maxscore_clean_probabilities_val_epsilon_0_03.csv` | clean | 496 |
| `val_eval/optionB_maxscore_fgsm_probabilities_val_epsilon_0_03.csv` | FGSM, eps=0.03 | 496 |
| `val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv` | **PGD, eps=0.03 (primary evidence for Stage 1)** | 496 |

Settings: epsilon 0.030, PGD 10 steps, alpha = eps/6 (defaults), attack generation delegated to
`run_converged_attacks.generate_attacked_batch` — byte-identical to every other committed eval in
this repo (D8b Gate-5 test exports, D10/D11 exports).

## Pre-existing artifacts referenced for context (not re-read as data in Stage 1)

- Gate-5 test exports (existing, untouched):
  `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_{clean,fgsm,pgd}_probabilities_test_epsilon_0_03.csv`.
- D8b post-hoc reference (existing, untouched):
  `results/operating_region_characterization/operating_region_summary.csv`
  (optionB_maxscore seed42, threshold 0.153246, TP/FN/FP/TN 36/9/91/364, AUROC 0.8439).
- Pre-run strategy (existing, untouched):
  `results/afac_score_frozen_threshold_followup/AFAC_PRE_RUN_STRATEGY.md`.

## Threshold selection protocol (Stage 1)

Script: `scripts/analysis/afac_score_stage1_validation_selection.py`. For each FAR cap in
{0.18 (primary), 0.20 (comparison), 0.15 (diagnostic), 0.10 (R90F10 diagnostic)}: select the
threshold maximizing validation PGD fall recall subject to validation FAR <= cap; tie-break 1 =
lower validation FAR; tie-break 2 = higher threshold. A stratified bootstrap (2000 resamples per
cap, fixed seed 20260704, resampling fall and non-fall windows separately) re-runs the same
selection rule to characterize threshold and recall stability given only 44 validation fall
windows.

**No-test-tuning verification:** the selection script was grep-checked before execution for any
reference to `test_eval` or a test-split path; none exists. The frozen thresholds recorded in
`afac_score_threshold_selection_validation.csv` are final for Stage 1 and were not adjusted based
on proximity to the known D8b post-hoc threshold (~0.1532) or any other test-derived quantity.

## Outputs of this stage

- `afac_score_threshold_selection_validation.csv` — frozen thresholds + validation metrics per cap.
- `afac_score_bootstrap_stability_validation.csv` — bootstrap threshold/recall stability per cap.
- `afac_score_validation_frontier.csv` — full validation recall/FAR frontier (455 distinct
  thresholds) for inspection.
- `afac_score_stage1_validation_summary.md` — human-readable summary and buffer assessment.
- `val_eval/*.csv` — the three per-window validation score exports.
- This file and `COMMANDS_RUN.txt`.

## Explicit non-actions in Stage 1

- No threshold was applied to any test-split file during Stage 1.
- No comparison between the frozen validation thresholds and any test-derived number was performed
  during selection.
- No `.tex` file, thesis chapter, or Overleaf-linked repo file was edited.
- No git commit was made in this repository as part of Stage 1 (per instructions, only if
  explicitly requested).

---

## Stage 2 — held-out test application (run 2026-07-04, after Stage 1 archived/committed)

**Scope: single-shot application of the four Stage 1 frozen thresholds to the existing held-out
test scores. No threshold selection, adjustment, or reselection logic exists in the Stage 2
script.**

### Test data used (existing, reused, not regenerated)

- `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv`
  (primary evidence; PGD eps=0.030, eval PGD-10, alpha=eps/6 — the Gate-5 export).
- `.../optionB_maxscore_clean_probabilities_test_epsilon_0_03.csv` (clean-condition check at the
  primary threshold only, pre-registered in the Stage 1 strategy).
- Both files verified: **500 windows, 45 fall, 455 non-fall.**
- Neither file was regenerated; both were produced by the pre-existing Gate-5 evaluation and are
  untouched by this stage.

### Frozen thresholds applied (exactly as selected in Stage 1; not modified here)

| FAR cap | Role | Threshold |
|---|---|---|
| 0.18 | Primary | 0.170908 |
| 0.20 | Comparison | 0.147881 |
| 0.15 | Diagnostic | 0.181992 |
| 0.10 | R90F10 diagnostic | 0.234373 |

### Script

`scripts/analysis/afac_score_stage2_test_application.py` — hard-codes the four frozen thresholds
as constants (`FROZEN_THRESHOLDS`), contains no selection/optimization logic, reads only the two
existing test-score files above, applies each threshold once, and writes the outputs below.

### Outputs of Stage 2

- `afac_score_test_metrics_by_far_cap.csv` — full locked-test metrics per frozen threshold.
- `afac_score_clean_condition_at_primary_threshold.csv` — clean-condition recall/FAR at the primary
  threshold only.
- `afac_score_false_alarm_source_breakdown.csv`, `afac_score_missed_fall_destination_breakdown.csv`
  — error-structure breakdowns per threshold.
- `afac_score_frozen_threshold_summary.csv` — comparison table (AFAC rows + D8b reference +
  D10/D11a/D11b locked rows, the latter three copied as constants from
  `results/d10_d11_locked_test_followup/` for reference; not recomputed here).
- `afac_score_frozen_threshold_summary.md` — human-readable Stage 2 headline and verdict.

### Explicit non-actions in Stage 2

- No threshold was changed after seeing test results (verified: `FROZEN_THRESHOLDS` in the script
  matches the Stage 1 selection CSV exactly).
- The primary rule (FAR cap 0.18) was not switched to the comparison (0.20) row despite the latter
  numerically tying the D8b reference recall — this is stated explicitly in the summary.
- No `.tex` file, thesis chapter, or Overleaf-linked repo file was edited.
- No git commit was made in this repository as part of Stage 2 (per instructions, only if
  explicitly requested).
