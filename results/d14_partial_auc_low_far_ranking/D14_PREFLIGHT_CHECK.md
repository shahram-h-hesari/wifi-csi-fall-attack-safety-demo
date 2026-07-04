# D14 Phase 0 — Checkpoint and Implementation Preflight Check

Date: 2026-07-04. **Preflight/inspection only. No training run. No validation evaluation run. No
test-split access. Nothing committed.** This report checks whether D14 can be implemented cleanly
from existing artifacts before any training starts, per the pre-registration memo committed in the
Overleaf-linked thesis repo (commit `7ee228369052461682741a372a1ac2c3209fecb1`,
`provenance/appendices/internal_defense_experiment_ledger/decision_memos/20260704_d14_partial_auc_low_far_preregistration.md`).

## 1. Git state

- Branch: `feature/safety-proxy-guided-defense`
- Latest commit: `ec65751` ("Add D13 validation complementarity audit")
- Working tree: no modifications; only the same pre-existing untracked analysis folders from this
  session (`.codex/`, `results/afac_score_frozen_threshold_followup/`,
  `results/d10_d11_locked_test_followup/`, `results/defense_attempt_inventory/`,
  `results/operating_region_characterization/`, `results/reconstructed_ch04_cross_arch_resnet/`,
  `scripts/analysis/`, one loose script). Confirmed clean before this preflight began.

## 2. AFAC-score checkpoint (primary D14 starting checkpoint)

| Item | Path |
|---|---|
| Checkpoint | `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt` |
| Metadata | `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/metadata/seed42_optionB_metadata.json` |
| Validation scores | `results/afac_score_frozen_threshold_followup/val_eval/optionB_maxscore_{clean,fgsm,pgd}_probabilities_val_epsilon_0_03.csv` |
| Test scores (existing, not to be touched by D14 training/validation) | `results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_{clean,fgsm,pgd}_probabilities_test_epsilon_0_03.csv` |
| Generating script | `scripts/train_optionB_adaptive_lagrangian.py` |
| Review docs | `OPTIONB_SEED42_PILOT_VALIDATION_REVIEW.md`, `OPTIONB_GATE5_TEST_EVAL_REVIEW.md`, `OPTIONB_GATE4_PILOT_READINESS_REVIEW.md` |

**Disambiguation evidence (maxscore vs. maxrec vs. minFA):** the metadata JSON explicitly lists
three named checkpoints under `"checkpoints"` — `maxscore`, `maxrec`, `minFA` — each with its own
full path, and the file selected here matches the `maxscore` entry exactly. `"selection": "validation-only:
maxscore / maxrec-within-guard / minFA-within-guard"` confirms `maxscore` is the AFAC-score row
naming convention used throughout the ledger (D8b). `test_set_used: false` is recorded at training
time, consistent with the D14 no-test-tuning requirement.

**Status: USABLE.**

## 3. D10 checkpoint (fallback only)

| Item | Path |
|---|---|
| Checkpoint | `checkpoints/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt` |
| Metadata | `results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/metadata/seed42_basat_gairat_GR1_metadata.json` |
| Validation scores | `results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/val_eval/GR1_v2macroF1_{clean,fgsm,pgd}_probabilities_val_epsilon_0_03.csv` |
| Test scores (existing) | `results/d10_d11_locked_test_followup/test_eval/GR1_v2macroF1_{clean,fgsm,pgd}_probabilities_test_epsilon_0_03.csv` |
| Generating script | `scripts/train_basat_gairat.py` |

**Disambiguation evidence:** the metadata JSON lists four named checkpoints (`v2safety`,
`v2maxrec`, `v2lowFA`, `v2macroF1`) with distinct selected epochs; the file used here matches the
`v2macroF1` entry, which is the exact variant whose validation AUROC (0.871229) matches the D10
row already recorded in Internal Appendix IA and used in the D13 audit. `test_set_used: false`
recorded. `git_commit: 7b9db40...` recorded in the metadata, providing an independent training-time
provenance anchor.

**Status: USABLE.**

**Recommendation: use the AFAC-score checkpoint as the D14 starting point.** No fallback is needed
— both are usable, but AFAC-score is the pre-registered primary and the D10 fallback rule is
declared here only for completeness, not because it is required.

**Test-artifact discipline note:** Some historical AFAC-score and D10 test-score artifacts were
identified only to verify checkpoint provenance and row identity. D14 Phase 0 did not perform a new
held-out test read, did not use held-out test metrics for D14 configuration, threshold, seed, or
checkpoint selection, and did not access the held-out test split for D14 evaluation. The selected
D14 starting checkpoint follows the pre-registered rule: AFAC-score is primary because its
checkpoint/provenance is usable; D10 remains fallback only and is not invoked.

## 4. Scalar score convention s(x)

- **Score type:** softmax probability of the fall class (not a raw logit, not a margin). Computed
  as `probs = torch.softmax(logits, dim=1)` and then `fall_probability = probs[:, fall_idx]`, in
  `scripts/export_probability_predictions.py` (lines ~143, ~161) and identically in
  `scripts/run_converged_attacks.py`'s `collect_paired_predictions`.
- **Fall class index:** 1. `CLASS_NAMES = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup",
  4: "run", 5: "sit down", 6: "stand up"}`, `FALL_CLASS_INDEX = 1`, both in
  `scripts/train_converged_clean_baseline.py`.
- **Direction:** higher score = more fall-like (it is a probability of the positive/fall class;
  all threshold-selection scripts select `si >= tau` as the fall-positive decision rule).
- **Validation thresholds selected from this same score:** yes, confirmed by direct inspection —
  `scripts/analysis/afac_score_stage1_validation_selection.py`, `d10_d11_locked_test_followup.py`,
  and `d13_stage0_complementarity_audit.py` all read `float(r["fall_probability"])` from the saved
  CSVs and sweep exactly that column.
- **Consistency across AFAC/D10/D11:** confirmed identical — the same `fall_probability` column
  name, same softmax-over-fall-index definition, same CSV schema, used by every one of the four
  scripts above and by the D13 audit that combined all three models' scores directly (their
  ECDF-mean P0 probe would not have been meaningful otherwise).

**D14 implication:** `s(x)` for the ranking loss must be `torch.softmax(model(x), dim=1)[:, 1]`
(fall class index 1), computed on the adversarial batch, matching this convention exactly. No new
evaluation score should be introduced.

## 5. PGD attack settings to reuse

From `scripts/run_converged_attacks.py::generate_attacked_batch` (evaluation-time; used to produce
every committed val/test score CSV in this ledger) and `scripts/train_safety_guided_defense.py::pgd_perturb`
(training-time; identical math, used by the safety-guided/BASAT defense family trainers):

| Setting | Value |
|---|---|
| Epsilon | 0.030 |
| PGD steps (evaluation convention) | 10 |
| PGD steps (training convention, prior defenses) | varies by family — e.g. GR1 (D10) trained with `train_pgd_steps=7`; evaluation of all checkpoints (including GR1) still uses 10-step PGD |
| Step size (alpha) | epsilon / 6 &asymp; 0.005 (evaluation default in `export_probability_predictions.py`) |
| Random start | **None** — `adv = original.clone().detach()`, no initial random perturbation before the first gradient step |
| Clipping / normalization | L-infinity projection each step: `perturbation = clamp(adv - original, -epsilon, epsilon)`; **no [0, 1] value clamp** (UT-HAR tensors are processed CSI features, not image pixels) |
| Attack loss | `nn.CrossEntropyLoss()` on the true label |
| Targeted or untargeted | **Untargeted** (loss computed against the ground-truth label, not a target label) |

**Recommendation for D14:** reuse the evaluation-time convention exactly for both attack generation
inside the training loop (adversarial examples the ranking loss and PGD-AT cross-entropy term are
computed on) and for validation/test scoring: epsilon=0.030, 10 PGD steps, alpha=epsilon/6, no
random start, L-infinity projection, untargeted cross-entropy loss. This is a deliberate choice to
avoid the mismatch some prior defenses had between a cheaper training-time attack (e.g., 7 steps)
and the 10-step evaluation attack; using 10 steps throughout keeps D14's training-time adversarial
examples on the exact same footing as everything it will be judged against. **This should be stated
explicitly in the D14 implementation before training, since it is not automatically implied by the
pre-registration memo's text** (the memo says "same PGD steps, step size, and attack conventions as
the prior D1-D13 evaluation unless the memo explicitly states otherwise" — this preflight report
recommends explicitly locking training-time PGD to the 10-step evaluation convention, not the
cheaper training-time convention some prior families used).

## 6. Ranking-loss implementation risk (dataloader / batch composition)

Read-only inspection of the training split (3,977 windows; no training or gradient step
performed):

| Class | Count |
|---|---|
| lie down | 525 |
| fall | 354 |
| walk | 1172 |
| pickup | 396 |
| run | 967 |
| sit down | 320 |
| stand up | 243 |
| **Total** | **3977** |

Fall fraction: 354/3977 = **8.90%**. Current training loader
(`train_converged_clean_baseline.build_loaders`): `batch_size=64, shuffle=True, drop_last=True`,
plain random sampling — **no balanced or stratified sampler exists anywhere in this codebase**
(confirmed by search; no `WeightedRandomSampler` or custom balanced sampler found).

- **Expected fall samples per batch of 64:** ~5.7 (mean).
- **Probability a given batch contains zero fall samples** (binomial approximation,
  p=0.0890, n=64): (1&minus;0.0890)^64 &asymp; **0.26%** — roughly 1 in 385 batches.
- **Probability a given batch contains zero non-fall samples:** effectively zero (non-fall is
  ~91% of the data).
- Over a full D14 run (62 batches/epoch x up to 70 epochs x 3 seeds x 2 configs, if both configs
  and all seeds are run to the same schedule as prior defenses), a small number of zero-fall
  batches (roughly 0.26% of ~26,000 batches, i.e. tens of batches total) will fall back to the
  cross-entropy-only term per the pre-registered rule ("if no fall or no non-fall samples in
  batch, L_rank = 0"). This is expected, pre-registered behavior, not a bug.

**Risk assessment: LOW.** The existing plain-shuffle dataloader is very unlikely to starve the
ranking loss of fall samples often enough to matter; L_rank will be non-zero and meaningfully
computed in the overwhelming majority (&gt;99.7%) of batches.

**Balanced-sampler question:** no balanced sampler currently exists, and none is recommended.
**Introducing one now would be an undeclared deviation from the pre-registered memo** — the memo
fixes Config A/B to differ only in `lambda_rank`, and freezes "attack setting[s]" and implicitly
the training data pipeline before training begins; adding a stratified/balanced sampler is a
methodological change to the training distribution that was not itself pre-registered. Given the
measured risk is low (0.26% zero-fall-batch rate), **no sampler change is needed or recommended**;
if one were ever wanted, it would require a separate written amendment to the D14 pre-registration
memo before any training run, applied identically to both Config A and Config B.

## 7. Proposed D14 file/folder layout (not yet created, except this report)

| Purpose | Path |
|---|---|
| Training script | `scripts/train_d14_partial_auc_low_far_ranking.py` |
| Validation-gate script | `scripts/analysis/d14_validation_gate.py` |
| Bootstrap script | `scripts/analysis/d14_bootstrap_stability.py` (or folded into the validation-gate script, matching the D13 audit's combined style) |
| D14 output folder | `results/d14_partial_auc_low_far_ranking/` (created; contains only this preflight report so far) |
| D14 preflight report | `results/d14_partial_auc_low_far_ranking/D14_PREFLIGHT_CHECK.md` (this file) |

Subfolders anticipated once training is authorized (not created now): `checkpoints_local_index/`
(pointers only, real checkpoints stay under the existing `checkpoints/` tree),
`training_logs/`, `val_eval/`, `validation_gate/`, `test_eval/` (created only if the validation gate
passes) — mirroring the structure already declared in the pre-registration memo's Section 14.

## 8. GO / NO-GO recommendation

**GO for implementation**, with two explicit notes to resolve in the training script before the
first run (not before this preflight, which is complete):

1. Lock the training-time PGD attack to the 10-step, alpha=epsilon/6, no-random-start evaluation
   convention (Section 5), rather than a cheaper training-time convention some prior defense
   families used, so D14's adversarial training examples match the same attack it will be
   evaluated and gated against.
2. Document, in the training script's header/docstring, that `s(x) = softmax(logits, dim=1)[:, 1]`
   before any training run, per the pre-registration's implementation constraint — this preflight
   confirms that convention is unambiguous and already fixed by every other script in the ledger.

No blocking issues were found. Both the primary (AFAC-score) and fallback (D10) checkpoints are
fully provenanced and usable; the score convention is unambiguous and consistent across every
existing script; the attack settings are fully documented; and the ranking-loss's batch-composition
risk is low and does not require any change to the existing dataloader.
