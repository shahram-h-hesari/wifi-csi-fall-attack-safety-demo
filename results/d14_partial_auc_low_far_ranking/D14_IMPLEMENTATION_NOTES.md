# D14 Implementation Notes (Phase 1)

Date: 2026-07-04. **Phase 1 implementation only. No training run. No validation evaluation run. No
held-out test access. Nothing committed by this task.** Scripts were created and verified by
syntax-compile, `--help`, `--dry-run`, and pure-logic/tensor-math checks that load no dataset and no
model.

## Thesis-repo provenance

- D14 pre-registration commit: `7ee228369052461682741a372a1ac2c3209fecb1`
- D14 clarification commit: `06c93abb635b3bcaf2e5591f214bd57d00faf831`

## Alignment after the thesis-side clarification (2026-07-04)

The pre-registration clarification resolved two previously-underspecified details. This
implementation was aligned to them **before any D14 training run, before validation-gate execution,
and before any D14 held-out test read**:

- **Full-batch PGD-only training (LOCKED).** D14 uses full-batch PGD adversarial fine-tuning; each
  training minibatch is attacked before computing both `L_PGD_CE` and `L_rank`. **No 50/50
  clean/PGD mixture is used.** In code this is `d14_common.ADV_FRACTION = 1.0` (now documented as
  locked by the clarification) and `train_one_epoch`, which attacks the whole minibatch. The
  training metadata records the explicit statement: "D14 uses full-batch PGD adversarial
  fine-tuning; no 50/50 clean/PGD mixture was used." Clean behavior is protected by the
  pre-registered clean validation guard.
- **Paired bootstrap = primary Gate-3 (LOCKED).** Gate condition 3 uses the paired stratified
  bootstrap as the primary gate: for each resample, D14 and the AFAC validation reference are scored
  on the same resampled window IDs, and the gate requires `Delta TP = TP_D14 - TP_AFAC >= 2` in
  `>= 70%` of resamples. The fixed 36/44 comparison is computed and reported as a **sensitivity
  check only** and is never used for the gate decision. If the paired AFAC reference is unavailable,
  the primary Gate-3 cannot be evaluated and the gate does not pass on the fixed result alone
  (`evaluate_d14_validation_gate.py`, `cond3 = gain_paired is not None and gain_paired >= 0.70`).

Both thesis commits are now recorded in `d14_common.py` (`D14_PREREG_COMMIT`,
`D14_CLARIFICATION_COMMIT`), in the training metadata JSON, and in the gate's emitted report header.

## Files created

| Path | Role |
|------|------|
| `scripts/d14_partial_auc_low_far_ranking/d14_common.py` | Locked constants (seeds, configs, PGD, ranking-loss, caps, clean guard, gate bars, checkpoint paths, provenance commits) + shared pure helpers (midpoint-grid threshold selection with tie-break, confusion/rates, AUROC, `tail_k`, seed/config guards, test-path refusal). No I/O at import. |
| `scripts/d14_partial_auc_low_far_ranking/train_d14_low_far_ranking.py` | Fine-tunes one config/seed from the AFAC-score checkpoint; full-batch PGD-AT + low-FAR ranking loss; per-epoch validation clean-guard + PGD recall@cap-0.17 diagnostics; saves best/last checkpoints, training log, metadata; exports canonical validation scores via `export_probability_predictions.py --split val`. Never references the test loader. |
| `scripts/d14_partial_auc_low_far_ranking/evaluate_d14_validation_gate.py` | Reads D14 validation exports, applies the four-condition gate on the selected config's median seed, emits `D14_FAIL_VALIDATION_GATE.md` or `D14_GATE_PASS_NEEDS_APPROVAL.md`, and (on pass) writes frozen thresholds. Never reads test files. |
| `scripts/d14_partial_auc_low_far_ranking/apply_d14_locked_test_once.py` | Guarded single-test-read runner. Refuses without both a gate-pass frozen-thresholds JSON and the `--i-understand-this-consumes-the-single-d14-test-read` flag. |
| `scripts/d14_partial_auc_low_far_ranking/README.md` | Script-directory overview and allowed/forbidden commands. |
| `results/d14_partial_auc_low_far_ranking/D14_IMPLEMENTATION_NOTES.md` | This file. |

## How the scripts enforce the pre-registration

- **Seeds** restricted to {42, 43, 44}; any other seed is refused with a clear message
  (`validate_seed`). **Configs** restricted to {A, B} by argparse `choices` and `validate_config`.
- **`lambda` values are read only from `CONFIGS`** in `d14_common.py` (A = 1.00/0.50, B = 1.00/1.00);
  the training script never accepts lambda on the command line, so configs can differ only in
  `lambda_rank`.
- **PGD settings** are module constants (eps 0.030, 10 steps, alpha eps/6, no random start, L-inf
  projection, no clamp, untargeted CE) used identically for training-loop attacks, per-epoch
  validation diagnostics, and the canonical exports.
- **Score `s(x)`** is computed exactly one way (`softmax(logits)[:, 1]`) in both the ranking loss
  and the validation scoring, and the canonical val/test exports are produced by the existing
  `export_probability_predictions.py` (byte-identical to every AFAC/D10/D11/D13 export).
- **Ranking loss** implements the pre-registered formula exactly: `H` = top-k non-fall by detached
  `s(x)`, `k = max(1, ceil(0.20 * N_nonfall_batch))`, margin `m = 0.10`, hinge mean over
  fall×H pairs, 0 when the batch lacks fall or non-fall samples. Verified on synthetic tensors
  (hand-computed 0.5167 matched; gradient finite; empty-fall batch returns 0/inactive).
- **Threshold rule** is the shared `select_threshold` (midpoint grid over non-fall scores; tie-break
  recall → lower FAR → higher threshold). **Caps** 0.17 primary / 0.20 secondary are constants.
- **Validation gate** encodes all four conditions and the config/median-seed tie-breaks from the
  memo. On pass it does NOT run the test; it writes a frozen-thresholds JSON and a
  `..._NEEDS_APPROVAL` report.
- **Stop rule** is enforced structurally: the only path to a test read is the guarded stub, which
  requires the gate-pass JSON plus an explicit acknowledgement flag.

## How the scripts avoid test access

- The training script destructures `build_loaders` as `train_loader, val_loader, _test_loader_unused,
  split_sizes` and never references `_test_loader_unused` again; it asserts `val == 496`.
- `d14_common.refuse_if_test_path` hard-stops on any path containing `test_eval`, `/test`, `_test_`,
  `x_test`, or `y_test`; it is called on the start checkpoint and on every score file the gate reads.
- The gate script only ever constructs `..._val_epsilon_0_03.csv` paths and reads the existing AFAC
  **validation** reference; it has no test path anywhere.
- The locked-test stub is the single place a `--split test` export can occur, and it refuses to run
  without both preconditions.
- Grep confirms no `test_eval` / `X_test` / `y_test` / `test_loader` usage in `d14_common.py`,
  `train_d14_low_far_ranking.py`, or `evaluate_d14_validation_gate.py` (the stub references
  `--split test` by design, inside its guarded runner only).

## Design decisions — resolution status

Two decisions previously flagged as underspecified (items 1 and 4) are now **RESOLVED and LOCKED by
the clarification commit** `06c93abb635b3bcaf2e5591f214bd57d00faf831`. Items 2 and 3 remain
implementer defaults, each a single value **identical across both configs and all three seeds** so
only `lambda_rank` ever differs.

1. **[RESOLVED — LOCKED] Clean/adversarial mixing = full-batch PGD-AT (`ADV_FRACTION = 1.0`).** The
   clarification fixes this: D14 uses full-batch PGD adversarial fine-tuning, **no 50/50 clean/PGD
   mixture**; each minibatch is attacked before both `L_PGD_CE` and `L_rank` are computed. Clean
   behavior is protected by the pre-registered clean validation guard. Implemented in
   `train_one_epoch` and documented as locked in `d14_common.ADV_FRACTION`.
2. **[implementer default] Fine-tune schedule: `--epochs 40`, `--lr 3e-4` (Adam), `--batch-size 64`.**
   Not specified by the memo; chosen as a modest fine-tune from a strong checkpoint. Identical
   across configs/seeds. Overridable on the command line if you want a different (single) schedule.
3. **[implementer default] In-run checkpoint selection = best validation PGD recall @ cap-0.17 among
   clean-guard-passing epochs (tie-break: lower FAR, then earlier epoch).** The memo fixes the gate
   but not the within-run epoch-selection metric; this choice aligns the selected checkpoint with the
   exact quantity the gate judges. Identical across configs/seeds.
4. **[RESOLVED — LOCKED] Gate criterion 3 = PAIRED bootstrap (primary); fixed 36/44 = sensitivity
   only.** The clarification fixes this: the paired stratified bootstrap (D14 and AFAC scored on the
   same resampled window IDs; `Delta TP = TP_D14 - TP_AFAC >= 2` in `>= 70%`) is the primary Gate-3.
   The fixed 36/44 comparison is computed and reported as a sensitivity check only and is never used
   for the gate decision; if the paired AFAC reference is unavailable, Gate-3 cannot pass on the
   fixed result. Implemented in `evaluate_d14_validation_gate.py`
   (`cond3 = gain_paired is not None and gain_paired >= 0.70`). Bootstrap N = 2000, seed 1337.

## Syntax / help / logic checks run (no data, no model, no training)

- `python -m py_compile` on all four scripts → all compiled OK.
- `train_d14_low_far_ranking.py --help` and `--config A --seed 42 --dry-run` → prints resolved
  config, loads no data, exits.
- `train ... --seed 45 --dry-run` → refused (exit 1); `--config C` → argparse error (exit 2).
- `evaluate_d14_validation_gate.py --help` → OK.
- `apply_d14_locked_test_once.py --help` → OK; with no flag and no frozen JSON → refused (exit 1);
  with flag but no frozen JSON → still refused (exit 1). No test access occurred.
- Pure-logic check of `d14_common` (`tail_k`, `select_threshold`, guards) on hardcoded lists → OK.
- Tensor-math check of `ranking_loss` on synthetic tensors → hand-computed 0.5167 matched, gradient
  finite, empty-fall batch returns 0/inactive.

## Remaining steps before training

1. Confirm the four underspecified design decisions above (especially #1 mixing and #4 bootstrap
   reference), amending the pre-registration memo if any choice should be locked differently.
2. On approval, run the 6 training jobs (2 configs × 3 seeds), validation-only.
3. Run `evaluate_d14_validation_gate.py` (validation-only) to emit FAIL or GATE_PASS_NEEDS_APPROVAL.
4. Only on a gate pass, and only after separate explicit human approval, run
   `apply_d14_locked_test_once.py` for the single locked test read.
