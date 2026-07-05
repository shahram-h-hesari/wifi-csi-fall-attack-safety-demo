# D14 Seed-42 Health & Provenance Review (Config A vs Config B)

Date: 2026-07-04. Phase 2A: technical health and provenance review of the two seed-42 training runs
(Config A and Config B). **No validation gate was run. No held-out test read was performed. Nothing
was committed.**

> **Seed 42 metrics are reviewed only for technical health and provenance. They are not used to
> change D14 configs, seeds, thresholds, checkpoint choice, validation gate, or test-read rules.**

Per the D14 protocol, seed 42 is a technical/provenance checkpoint only. The protocol continues to
seeds 43 and 44; D14 success/failure is not decided from seed 42, and no protocol change is
recommended from these runs.

## Provenance anchors

- Experiment implementation commit (git HEAD at run time, clean working tree): `a00d767be40b2eb59624c3270d4a5a55fe495c54`
- Thesis pre-registration commit: `7ee228369052461682741a372a1ac2c3209fecb1`
- Thesis clarification commit: `06c93abb635b3bcaf2e5591f214bd57d00faf831`
- Preflight commit: `67efeda578db53ae4eab0ca82dccb0d5c9373f23`

Both runs were produced with git HEAD = `a00d767` and a clean working tree, so they are
reproducibly tied to the pushed implementation commit. The metadata JSONs record the
pre-registration, clarification, and preflight commits; they do not self-embed `a00d767` (a script
cannot embed its own commit hash at authoring time), so `a00d767` is anchored here via the verified
clean HEAD. (Optional future no-op: capture git HEAD into metadata at runtime.)

## Run outcomes

| Item | Config A (seed 42) | Config B (seed 42) |
|------|--------------------|--------------------|
| Command | `--config A --seed 42` | `--config B --seed 42` |
| Exit status | 0 (completed) | 0 (completed) |
| lambda_ce / lambda_rank | 1.00 / 0.50 | 1.00 / 1.00 |
| Start checkpoint | AFAC-score (`optionB_maxscore`) | AFAC-score (`optionB_maxscore`) |
| Output directory | `results/d14_partial_auc_low_far_ranking/config_A/seed42/` | `.../config_B/seed42/` |
| Epochs run | 40 | 40 |
| Best epoch | None | None |
| Elapsed | ~3858 s (~64 min) | ~3706 s (~62 min) |
| Losses finite | Yes | Yes |
| Checkpoints created | `d14_config_A_seed42_last.pt` (no best) | `d14_config_B_seed42_last.pt` (no best) |
| Metadata JSON | created | created |
| Training log CSV | created | created |
| Validation score export | **not created** (no best checkpoint) | **not created** (no best checkpoint) |
| `test_set_used` | False | False |

## Training-health metrics

| Metric | Config A | Config B |
|--------|----------|----------|
| PGD-CE loss (first / final / mean) | 1.606 / 1.259 / 1.357 | 1.612 / 1.268 / 1.364 |
| Ranking loss (first / final / mean) | 0.113 / 0.084 / 0.094 | 0.111 / 0.078 / 0.088 |
| Total loss (final / mean) | 1.301 / 1.404 | 1.346 / 1.453 |
| Ranking-loss active fraction (min / mean) | 0.968 / 0.996 | 0.968 / 0.996 |
| Clean val accuracy (min / final) | 0.675 / 0.724 | 0.669 / 0.726 |
| Clean val macro-F1 (min / final) | 0.668 / 0.719 | 0.674 / 0.727 |
| Clean val fall recall (min / max / final) | 0.568 / 0.886 / 0.636 | 0.500 / 0.886 / 0.659 |
| Epochs passing the clean guard | 0 / 40 | 0 / 40 |
| Val PGD recall @ FAR cap 0.17 (min / max / final) | 0.682 / 0.886 / 0.886 | 0.705 / 0.864 / 0.864 |
| Val PGD FAR @ cap 0.17 (min / max) | 0.137 / 0.168 | 0.131 / 0.168 |

(Loss monotone-decreasing over training; ranking loss active in essentially every batch; PGD-CE
and ranking losses both finite throughout.)

## Health assessment (technical only)

- **Both runs are technically valid:** completed without crash (exit 0), 40 epochs each, all
  losses finite, ranking loss active in ~99.6% of batches on average (min 96.8%). The full-batch
  PGD-AT loop and the low-FAR ranking term behaved as implemented.
- **Provenance is complete and correct:** both metadata files record config, seed 42, the correct
  lambda pair, the AFAC-score starting checkpoint, and the pre-registration / clarification /
  preflight commits; both record `test_set_used: False`, `adv_fraction: 1.0`, and the explicit
  full-batch-PGD statement. Runs are anchored to `a00d767` via clean HEAD.
- **Clean guard failed on every epoch in both configs.** The clean guard requires clean validation
  accuracy >= 0.70 AND macro-F1 >= 0.65 AND fall recall >= 0.90 simultaneously. Clean fall recall
  peaked at 0.886 and never reached 0.90 (final 0.636 / 0.659), so `best_epoch = None`, no best
  checkpoint was saved, and consequently no canonical validation score export was produced. This is
  the training script correctly following its clean-guard-gated selection logic — **not a bug and
  not a provenance issue.** It is a technical/provenance observation only; it is not used here to
  judge D14 or to change any protocol element, and the protocol continues to seeds 43 and 44.

## Test-access confirmation

- Neither run accessed the held-out test split. Both metadata files record `test_set_used: False`
  and the no-test-read statement; the training script references only the train and validation
  loaders (the test loader is destructured and never used). No `val_eval/`, no validation-gate
  output (`D14_FAIL_VALIDATION_GATE.md` / `D14_GATE_PASS_NEEDS_APPROVAL.md` /
  `d14_frozen_gate_thresholds.json`), and no locked-test output (`D14_LOCKED_TEST_RESULT.json` /
  `test_eval/`) exist anywhere under the D14 results tree.

## Bug / provenance issues

None. Both runs are technically valid and fully provenanced. The absence of a best checkpoint and
validation export in each config is expected behavior given the clean-guard failure, not a defect.
