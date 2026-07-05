# D14 Seed-43 Health & Provenance Review (Config A vs Config B)

Date: 2026-07-05. Phase 2B: technical health and provenance review of the two seed-43 training runs
(Config A and Config B). **No validation gate was run. No held-out test read was performed. Nothing
was committed.**

> **Seed 43 metrics are reviewed only for technical health and provenance. They are not used to
> change D14 configs, seeds, thresholds, checkpoint choice, validation gate, or test-read rules.**

Per the D14 protocol, seed 43 is a technical/provenance checkpoint only. The protocol continues to
seed 44; D14 success/failure is not decided from seed 43, and no protocol change is recommended
from these runs.

## Provenance anchors

- Gate robustness patch commit (git HEAD at run time, clean tree): `edb9e5793291b0e91dcc5b044ead26c5737e6e37`
- Implementation commit (verified ancestor of HEAD): `a00d767be40b2eb59624c3270d4a5a55fe495c54`
- Preflight commit: `67efeda578db53ae4eab0ca82dccb0d5c9373f23`
- Thesis pre-registration commit: `7ee228369052461682741a372a1ac2c3209fecb1`
- Thesis clarification commit: `06c93abb635b3bcaf2e5591f214bd57d00faf831`

Both runs were produced with git HEAD = `edb9e57` and a clean working tree, with `a00d767` verified
as an ancestor of HEAD, so they are reproducibly anchored to the pushed implementation and
gate-patch commits. The metadata JSONs record the pre-registration, clarification, and preflight
commits; `a00d767` and `edb9e57` are anchored here via the verified git history (a script cannot
self-embed its own commit hash).

## Run outcomes

| Item | Config A (seed 43) | Config B (seed 43) |
|------|--------------------|--------------------|
| Command | `--config A --seed 43` | `--config B --seed 43` |
| Exit status | 0 (completed) | 0 (completed) |
| lambda_ce / lambda_rank | 1.00 / 0.50 | 1.00 / 1.00 |
| Start checkpoint | AFAC-score (`optionB_maxscore`) | AFAC-score (`optionB_maxscore`) |
| Output directory | `.../config_A/seed43/` | `.../config_B/seed43/` |
| Epochs run | 40 | 40 |
| Epochs passing clean guard | 0 / 40 | 1 / 40 (epoch 1 only) |
| Best epoch | None | 1 |
| Elapsed | ~3821 s (~64 min) | ~3910 s (~65 min) |
| Losses finite | Yes | Yes |
| Best checkpoint created | No (only `last.pt`) | **Yes** (`..._best.pt`, epoch 1) + `last.pt` |
| Validation score export created | **No** | **Yes** (clean/FGSM/PGD, 496/44/452) |
| Metadata JSON | created | created |
| Training log CSV | created | created |
| `test_set_used` | False | False |

## Training-health metrics

| Metric | Config A | Config B |
|--------|----------|----------|
| PGD-CE loss (final / mean) | 1.262 / 1.359 | 1.273 / 1.366 |
| Ranking loss (final / mean) | 0.090 / 0.095 | 0.083 / 0.089 |
| Ranking-loss active fraction (min / mean) | 0.984 / 0.997 | 0.984 / 0.997 |
| Clean val accuracy (min / final) | 0.657 / 0.724 | 0.657 / 0.716 |
| Clean val macro-F1 (min / final) | 0.667 / 0.719 | 0.662 / 0.716 |
| Clean val fall recall (min / max / final) | 0.545 / 0.864 / 0.727 | 0.500 / 0.909 / 0.705 |
| Epochs passing the clean guard | 0 / 40 | 1 / 40 (epoch 1) |
| Val PGD recall @ FAR cap 0.17 (min / max / final) | 0.682 / 0.841 / 0.773 | 0.682 / 0.909 / 0.841 |
| Val PGD FAR @ cap 0.17 (min / max) | 0.155 / 0.168 | 0.153 / 0.168 |

(Both runs: losses finite throughout; ranking loss active in ~99.7% of batches on average.)

## Health assessment (technical only)

- **Both runs are technically valid:** exit 0, 40 epochs each, all losses finite, ranking loss
  active in ~99.7% of batches (min 98.4%). The full-batch PGD-AT loop and the low-FAR ranking term
  behaved as implemented.
- **Provenance is complete and correct:** both metadata files record config, seed 43, the correct
  lambda pair, the AFAC-score starting checkpoint, and the pre-registration / clarification /
  preflight commits; both record `test_set_used: False`, `adv_fraction: 1.0`, and the explicit
  full-batch-PGD statement. Runs are anchored to `edb9e57` (HEAD) and `a00d767` (ancestor) via git.
- **Config A seed 43: no clean-guard-eligible best checkpoint.** Clean fall recall peaked at 0.864
  and never reached the required 0.90, so 0/40 epochs passed the guard, `best_epoch = None`, no best
  checkpoint and no validation export were produced. Same pattern as both seed-42 runs. This is the
  training script correctly following its clean-guard-gated selection logic, not a bug.
- **Config B seed 43: one clean-guard-eligible epoch (epoch 1).** At epoch 1 the model was still
  close to the AFAC-score starting checkpoint (clean fall recall 0.909 >= 0.90, clean acc and
  macro-F1 within guard), so epoch 1 passed the guard; adversarial fine-tuning then pulled clean
  fall recall below 0.90 for all remaining epochs. The in-run selection therefore chose epoch 1 as
  the best checkpoint, and the canonical validation score export was produced. This is the first D14
  run to yield a clean-guard-eligible best checkpoint and validation export. **Reported as a
  technical/provenance fact only:** the selected "best" checkpoint is effectively the barely-
  fine-tuned starting model (one epoch), so this is not treated as evidence of D14 quality and is
  not used to judge D14 or change any protocol element. The protocol continues to seed 44.

## Test-access confirmation

- Neither run accessed the held-out test split. Both metadata files record `test_set_used: False`
  and the no-test-read statement; the training script references only the train and validation
  loaders. Config B's validation export was verified to be the 496-window / 44-fall validation
  split (not test). No validation-gate output, `d14_frozen_gate_thresholds.json`, `D14_LOCKED_TEST_*`,
  or `test_eval/` exists anywhere under the D14 results tree.

## Bug / provenance issues

None. Both runs are technically valid and fully provenanced. Config A's absence of a best
checkpoint/validation export is expected behavior given its clean-guard failure; Config B's single
guard-passing epoch (epoch 1) and resulting best checkpoint/validation export are also expected
behavior given how the clean-guard-gated in-run selection works. Neither is a defect.
