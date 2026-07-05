# D14 Seed-44 Health & Provenance Review (Config A vs Config B)

Date: 2026-07-05. Phase 2C: technical health and provenance review of the two seed-44 training runs
(Config A and Config B) — the final pair of the six pre-registered D14 runs. **No validation gate
was run. No held-out test read was performed. Nothing was committed.**

> **Seed 44 metrics are reviewed only for technical health and provenance. They are not used to
> change D14 configs, seeds, thresholds, checkpoint choice, validation gate, or test-read rules.**

Per the D14 protocol, seed 44 is a technical/provenance checkpoint only. The D14 decision happens
only after all six runs are complete and the validation-gate script is run separately — not from
this or any single seed's review.

## Provenance anchors

- Git HEAD at run time (clean tree): `253b0bee73589fbd2d9a6db4b3c61e6717168798` (D14 seed-43 health
  review commit)
- Implementation commit (verified ancestor of HEAD): `a00d767be40b2eb59624c3270d4a5a55fe495c54`
- Gate robustness patch commit (verified ancestor of HEAD): `edb9e5793291b0e91dcc5b044ead26c5737e6e37`
- Preflight commit: `67efeda578db53ae4eab0ca82dccb0d5c9373f23`
- Thesis pre-registration commit: `7ee228369052461682741a372a1ac2c3209fecb1`
- Thesis clarification commit: `06c93abb635b3bcaf2e5591f214bd57d00faf831`

Both runs were produced with git HEAD = `253b0be` and a clean working tree; the metadata JSONs
record the pre-registration, clarification, and preflight commits (a script cannot self-embed its
own commit hash, so the implementation and gate-patch commits are anchored here via verified git
ancestry rather than in the JSON itself).

## Run outcomes

| Item | Config A (seed 44) | Config B (seed 44) |
|------|--------------------|--------------------|
| Command | `--config A --seed 44` | `--config B --seed 44` |
| Exit status | 0 (completed) | 0 (completed) |
| lambda_ce / lambda_rank | 1.00 / 0.50 | 1.00 / 1.00 |
| Start checkpoint | AFAC-score (`optionB_maxscore`) | AFAC-score (`optionB_maxscore`) |
| Output directory | `.../config_A/seed44/` | `.../config_B/seed44/` |
| Epochs run | 40 | 40 |
| Epochs passing clean guard | 0 / 40 | 1 / 40 (epoch 1 only) |
| Best epoch | None | 1 |
| Elapsed | ~4186 s (~70 min) | ~3922 s (~65 min) |
| Losses finite | Yes | Yes |
| Best checkpoint created | No (only `last.pt`) | **Yes** (`..._best.pt`, epoch 1) + `last.pt` |
| Validation score export created | **No** | **Yes** (clean/FGSM/PGD, verified 496/44/452) |
| Metadata JSON | created | created |
| Training log CSV | created | created |
| `test_set_used` | False | False |

## Training-health metrics

| Metric | Config A | Config B |
|--------|----------|----------|
| PGD-CE loss (final / mean) | 1.269 / 1.359 | 1.278 / 1.366 |
| Ranking loss (final / mean) | 0.090 / 0.095 | 0.083 / 0.089 |
| Ranking-loss active fraction (min / mean) | 0.984 / 0.999 | 0.984 / 0.999 |
| Clean val accuracy (min / final) | 0.669 / 0.716 | 0.669 / 0.712 |
| Clean val macro-F1 (min / final) | 0.674 / 0.712 | 0.676 / 0.705 |
| Clean val fall recall (min / max / final) | 0.591 / 0.886 / 0.705 | 0.545 / 0.909 / 0.591 |
| Epochs passing the clean guard | 0 / 40 | 1 / 40 (epoch 1) |
| Val PGD recall @ FAR cap 0.17 (min / max / final) | 0.659 / 0.864 / 0.795 | 0.682 / 0.886 / 0.864 |
| Val PGD FAR @ cap 0.17 (min / max) | 0.133 / 0.168 | 0.144 / 0.168 |

(Both runs: losses finite throughout; ranking loss active in ~99.8-99.9% of batches on average.)

## Health assessment (technical only)

- **Both runs are technically valid:** exit 0, 40 epochs each, all losses finite, ranking loss
  active in ~99.8-99.9% of batches (min 98.4%). The full-batch PGD-AT loop and the low-FAR ranking
  term behaved as implemented.
- **Provenance is complete and correct:** both metadata files record config, seed 44, the correct
  lambda pair, the AFAC-score starting checkpoint, and the pre-registration / clarification /
  preflight commits; both record `test_set_used: False`, `adv_fraction: 1.0`, and the explicit
  full-batch-PGD statement. Runs are anchored to `253b0be` (HEAD) with `a00d767` and `edb9e57`
  verified as ancestors.
- **Config A seed 44: no clean-guard-eligible best checkpoint.** Clean fall recall peaked at 0.886
  and never reached the required 0.90, so 0/40 epochs passed the guard, `best_epoch = None`, no best
  checkpoint and no validation export were produced. This matches the pattern of Config A seed 42
  and Config A seed 43. This is the training script correctly following its clean-guard-gated
  selection logic, not a bug.
- **Config B seed 44: one clean-guard-eligible epoch (epoch 1).** Clean fall recall reached 0.909
  at epoch 1 (>= 0.90) before adversarial fine-tuning pulled it down for the remaining epochs; the
  in-run selection chose epoch 1 as the best checkpoint, and the canonical validation score export
  was produced (verified 496 windows / 44 fall — validation split, not test). This exactly matches
  the pattern observed for Config B seed 43 (also best_epoch = 1). **Reported as a
  technical/provenance fact only:** as with seed 43, the selected "best" checkpoint is effectively
  the barely-fine-tuned starting model (one epoch), and this observation is not used to judge D14
  or change any protocol element.

## Cross-seed pattern summary (technical observation only, not a D14 verdict)

Across all three seeds now run (42, 43, 44):

| Seed | Config A best_epoch | Config A val export | Config B best_epoch | Config B val export |
|------|---------------------|----------------------|----------------------|----------------------|
| 42 | None | No | None | No |
| 43 | None | No | 1 | Yes |
| 44 | None | No | 1 | Yes |

Config A never passed the clean guard in any of the three seeds. Config B passed the guard only at
epoch 1 in seeds 43 and 44 (and never in seed 42). This is a consistent technical pattern across
all six completed runs, reported here for provenance transparency; per the pre-registration and the
interpretation rule for this phase, it is **not** used to decide D14 success/failure or to change
any protocol element. That decision is reserved for the validation-gate script, to be run separately
once all six runs are reviewed.

## Test-access confirmation

- Neither run accessed the held-out test split. Both metadata files record `test_set_used: False`
  and the no-test-read statement; the training script references only the train and validation
  loaders. Config B's validation export was verified to be the 496-window / 44-fall validation
  split (not test). No validation-gate output, `d14_frozen_gate_thresholds.json`, `D14_LOCKED_TEST_*`,
  or `test_eval/` exists anywhere under the D14 results tree.

## Bug / provenance issues

None. Both runs are technically valid and fully provenanced. Config A's absence of a best
checkpoint/validation export, and Config B's single guard-passing epoch (epoch 1) with its
resulting best checkpoint/validation export, are expected behavior given how the clean-guard-gated
in-run selection works. Neither is a defect.
