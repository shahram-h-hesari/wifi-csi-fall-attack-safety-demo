# Provenance — D13 Step 0A/0B Validation-Only Complementarity + Transfer Audit

Generated: 2026-07-04. Repo commit at time of run: `1bcf6b8f35493a73269171c6b0678ca52b0a7580`,
branch `feature/safety-proxy-guided-defense`. Python 3.10.11, torch 2.12.0+cpu (`.venv`). No
training. No fusion-weight fitting. No thesis/Overleaf files touched. No existing result artifacts
or global ledgers modified. Nothing committed. Nothing pushed.

## Scope

This is a diagnostic-only audit deciding whether AFAC-score (D8b checkpoint), D10
(GAIRAT GR1_v2macroF1), and D11b (SAT SA1_v2lowFA) have enough validation-only complementarity to
justify a later, separately pre-registered Stage 1 score-fusion experiment. It cannot claim F20. It
can only authorize, reject, or mark inconclusive a later experiment (see gate result in the main
report). PGD epsilon = 0.030 throughout; no other epsilon was used.

## Input artifacts (Step 0A — validation PGD saved scores; no test path opened)

| Model | Checkpoint (thesis name) | Validation score file |
|---|---|---|
| AFAC | AFAC-score / `optionB_maxscore` (D8b reference) | `results/afac_score_frozen_threshold_followup/val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv` |
| D10 | GAIRAT-style boundary reweighting / `GR1_v2macroF1` | `results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/val_eval/GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv` |
| D11b | SAT-style selective filtering / `SA1_v2lowFA` | `results/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/val_eval/SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv` |

All three verified before use: 496 windows, 44 fall, 452 non-fall, and identical window ordering
(matching `true_label` sequence across all three files, confirming safe alignment by `sample_id`).
No test-split file (`test_eval/...`) was opened, read, or referenced anywhere in either script used
for this audit — verified by direct grep of both scripts before execution (see `COMMANDS_RUN.txt`).

## Checkpoints used (Step 0B — shared-input transfer audit; validation-only PGD regenerated)

| Model | Checkpoint path |
|---|---|
| AFAC | `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt` |
| D10 | `checkpoints/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt` |
| D11b | `checkpoints/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/seed42_basat_sat_SA1_v2lowFA_best.pt` |

All three are `lenet` architecture (confirmed via the `--model lenet` flag used in every prior
export command for these checkpoints, in `results/d10_d11_locked_test_followup/COMMANDS_RUN.txt`
and `results/afac_score_frozen_threshold_followup/COMMANDS_RUN.txt`).

Attack settings for regeneration: PGD, epsilon = 0.030, 10 steps, alpha = epsilon/6 = 0.005 —
identical to every other committed validation/test export in this repo, delegated to
`run_converged_attacks.generate_attacked_batch` (the same function used by
`export_probability_predictions.py`). Validation data loaded via
`train_converged_clean_baseline.load_raw_ut_har` + `build_loaders(data, 64)`, using the
`shuffle=False, drop_last=False` validation loader — the same deterministic order used to produce
every previously saved validation score export in this repo, so `sample_id` alignment holds.
`set_seed(1337)` called before data loading (deterministic; PGD attack generation itself is
gradient-based and deterministic given fixed inputs/model weights, so the seed's role here is
loader/data-path determinism, not stochastic attack sampling).

## Validation-only regenerated artifacts

Step 0B regenerates PGD adversarial validation examples against each of the three source models
(in-memory only; per-window fall probabilities under all 9 eval/source combinations are written to
`d13_stage0_transfer_matrix.csv`, not the raw adversarial tensors themselves, to keep the output
folder lightweight — the matrix fully specifies the audit's evidentiary content). No existing
artifact was overwritten; all outputs are new files under this folder only.

## Diagonal validity check (required before trusting any transfer-dependent gate)

The transfer script's diagonal cells (each model evaluated on adversarial examples crafted against
itself) were required to reproduce Step 0A's saved-score confusion counts at FAR<=0.18 within ±2
per cell. Actual result: **all three diagonal cells reproduced Step 0A's counts exactly (diff=0 in
every TP/FN/FP/TN cell)** — see `d13_stage0_transfer_validity_summary.json`. `step0b_valid = true`.
Step 0B's transfer-dependent gates are therefore treated as valid, not `STEP0B_INVALID`.

## Threshold-selection rule used in this audit (Step 0A/0B only)

Grid = midpoints between consecutive sorted unique validation scores (plus two epsilon-shifted
boundary points below the minimum and above the maximum score). Threshold selected to maximize
validation fall recall subject to FAR <= cap; tie-break 1 = lower FAR; tie-break 2 = higher
threshold. **This is a diagnostic-only rule distinct from, and not intended to override,** the
already-frozen, thesis-committed AFAC-score Stage-1 threshold (`0.170908` at FAR cap 0.18, archived
in `results/afac_score_frozen_threshold_followup/` and the Overleaf-linked appendix). The two
thresholds differ slightly (`0.168743` here vs `0.170908` there) purely because of the midpoint-grid
convention specified for this D13 audit; neither value has been changed in the other's artifacts.

## Explicit non-actions

- No test-split file was opened, read, summarized, or referenced by either script (grep-verified).
- No model was trained or fine-tuned.
- No fusion weights were fit (P0 uses fixed equal 1/3 weights on ECDF-transformed scores; Oracle-A
  and Oracle-B are set-theoretic/combinatorial bounds, not learned classifiers).
- No existing result artifact, global ledger, or thesis file was edited.
- No git commit or push was performed in this repository as part of this audit.
- No files in the pre-existing untracked working-tree folders were deleted, staged, or reorganized.
