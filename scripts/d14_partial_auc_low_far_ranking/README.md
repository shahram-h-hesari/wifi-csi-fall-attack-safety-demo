# D14 -- Partial-AUC / Low-FAR Ranking-Loss Fine-Tuning (Final F20 Attempt)

Implementation of the pre-registered D14 experiment. **D14 is the final F20 attempt.** All design
values here are locked by the pre-registration memo in the thesis repo
(`provenance/appendices/internal_defense_experiment_ledger/decision_memos/20260704_d14_partial_auc_low_far_preregistration.md`,
commit `7ee228369052461682741a372a1ac2c3209fecb1`) and the preflight report
(`results/d14_partial_auc_low_far_ranking/D14_PREFLIGHT_CHECK.md`, commit
`67efeda578db53ae4eab0ca82dccb0d5c9373f23`).

## Locked design

- **One family only.** Seeds: **42, 43, 44** (no 45/46 without a written memo amendment).
- **Two configs, differing only in `lambda_rank`:**
  - Config A: `lambda_ce = 1.00`, `lambda_rank = 0.50`
  - Config B: `lambda_ce = 1.00`, `lambda_rank = 1.00`
- **Starting checkpoint:** AFAC-score (`optionB_maxscore`) primary; D10 (`GR1_v2macroF1`) fallback
  only if AFAC-score is unusable (must be declared before training via `--use-d10-fallback`).
- **Score `s(x)`** = `softmax(logits)[:, 1]` (fall class index 1); higher = more fall-like.
- **PGD (training and evaluation):** epsilon 0.030, 10 steps, alpha = epsilon/6 (~0.005), no random
  start, L-infinity projection, no [0,1] clamp, untargeted cross-entropy loss.
- **Ranking loss** (per PGD-attacked minibatch): `H` = top-k non-fall by `s(x)`,
  `k = max(1, ceil(0.20 * N_nonfall_batch))`, margin `m = 0.10`,
  `L_rank = mean_{i in fall, j in H} max(0, m - (s_i - s_j))` (0 if the batch lacks fall or
  non-fall samples). `L_D14 = lambda_ce * L_PGD_CE + lambda_rank * L_rank`.

## Validation threshold rule

- Primary FAR cap **0.17** (buffered); secondary cap **0.20** (comparison only).
- Threshold grid: midpoints between sorted unique validation non-fall scores.
- Tie-break: maximize recall s.t. FAR cap; then lower FAR; then higher threshold.

## Validation gate (all required)

Judged on the **median seed** of the selected config at FAR cap 0.17:
1. median-seed recall >= 38/44 = 0.8636.
2. stratified bootstrap (>= 2,000 resamples): recall >= 0.80 in >= 75% of resamples.
3. stratified bootstrap: gain >= +2 TP over the AFAC validation reference (36/44) in >= 70%.
4. clean guard: clean accuracy >= 0.70, clean macro-F1 >= 0.65, clean fall recall >= 0.90.

**Config selection:** higher median-seed recall@0.17 -> lower median-seed FAR -> Config A.
**Median-seed selection:** median recall@0.17 -> lower FAR -> smaller seed number.

## Stop rule

- Gate fails -> **no test read**, emit `D14_FAIL_VALIDATION_GATE.md`, F20 chase ends.
- Gate passes -> emit `D14_GATE_PASS_NEEDS_APPROVAL.md` and freeze thresholds;
  **do NOT run the test automatically.** Wait for explicit human approval.
- No D15. No fusion reopening. No gate relaxation. No test tuning.

## Files

| File | Role |
|------|------|
| `d14_common.py` | Locked constants + shared score/threshold helpers (no I/O at import). |
| `train_d14_low_far_ranking.py` | Fine-tunes one config/seed; validation-only; writes checkpoints, log, canonical val scores, metadata. Never touches test. |
| `evaluate_d14_validation_gate.py` | Reads D14 validation exports, applies the gate, emits FAIL or GATE_PASS_NEEDS_APPROVAL. Never reads test. |
| `apply_d14_locked_test_once.py` | Guarded single-test-read runner. Refuses to run without both a gate-pass frozen-thresholds file and an explicit acknowledgement flag. |
| `README.md` | This file. |

## Commands allowed later (after this Phase-1 review)

```
# train each config/seed (validation-only; 6 runs max = 2 configs x 3 seeds)
python scripts/d14_partial_auc_low_far_ranking/train_d14_low_far_ranking.py --config A --seed 42
...
# evaluate the validation gate (validation-only)
python scripts/d14_partial_auc_low_far_ranking/evaluate_d14_validation_gate.py
```

## Commands forbidden now (Phase 1)

- Any `train_d14_low_far_ranking.py` run WITHOUT `--dry-run` (that trains).
- `evaluate_d14_validation_gate.py` (only run after training exports exist).
- `apply_d14_locked_test_once.py` in any form (single held-out test read; approval-gated).

Only `--help` and `--dry-run` are used during Phase 1 verification.
