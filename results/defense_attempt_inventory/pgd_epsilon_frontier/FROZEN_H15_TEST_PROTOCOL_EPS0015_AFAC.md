# FROZEN H15 TEST PROTOCOL — ε=0.015 / AFAC_maxscore (PRE-REGISTERED)

Protocol ID: `H15-TEST-EPS0015-AFAC-20260705`
Created: 2026-07-05. Status: **PRE-REGISTERED, TEST NOT RUN.** This document is binding: after
the single authorized test read, no field in it may be changed, reinterpreted, or superseded.

## Purpose

Convert the ε=0.015 H15 validation result (H15_FROZEN_TEST_DECISION_MEMO.md, gate: 5/5 PASS)
into exactly **one** admissible held-out test read. This protocol freezes the model, attack,
epsilon, split, threshold, decision rule, and reporting rules *before* any test-split file is
opened, so the eventual result — pass or fail — is frozen-threshold evidence, not post-hoc
characterization.

## Frozen candidate

| Field | Frozen value |
|---|---|
| Model | **AFAC_maxscore** (LeNet, `--model lenet`) |
| Checkpoint path | `checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt` |
| Checkpoint SHA256 | `b85c68a7f4834c514a06d737af167542c9139bed45dde8a40380eac78cab1146` |
| Attack | PGD, 10 steps, α = ε/6, frozen pipeline (`run_converged_attacks.generate_attacked_batch` via `export_probability_predictions.py`) |
| Epsilon | **0.015** |
| Split for the read | test (500 windows: 45 fall / 455 non-fall), read **once** |
| Frozen threshold | **tau = 0.168754** (decision rule: fall alarm iff `fall_probability >= tau`) |
| Threshold provenance | max validation recall s.t. validation FAR ≤ **0.12**, tie-break lower FAR then higher tau, computed on `val_sweep/eps0015/AFAC_maxscore_eps0015_pgd_probabilities_val_epsilon_0_015.csv` |
| Threshold recomputation after test | **FORBIDDEN** |

## Validation gate evidence (all computed before this protocol; saved)

Source: `h15_frozen_test_gate_numbers_eps0015.csv` and H15_FROZEN_TEST_DECISION_MEMO.md §5.

1. Val PGD recall 0.909 (TP 40/44) at FAR 0.108 under the buffered 0.12 cap — PASS.
2. H15-feasible tau window width 0.056 (≥ 0.03 required) — PASS.
3. Stratified bootstrap (2,000): joint P(recall > 0.85 AND FAR < 0.15) at frozen tau = 0.892
   (≥ 0.80 required); recall 95% lower 0.818; FAR 95% upper 0.137 — PASS.
4. Clean guard at frozen tau: clean recall 0.977, clean FAR 0.062 — PASS.
5. Transfer-history condition: measured frozen-threshold val→test decay at ε=0.030 was
   recall −0.018 / FAR +0.014 (best in ledger; ST1b6 −0.220 and SA1 −0.130 were excluded on
   this condition) — PASS.

## Test success definition (H15)

At tau = 0.168754 on the PGD ε=0.015 test export, single evaluation:
**TP ≥ 39 / 45 AND FP ≤ 68 / 455** (recall > 0.85 AND FAR < 0.15) → **H15 PASS at ε=0.015.**

## Test failure definition

**TP ≤ 38 OR FP ≥ 69 → H15 FAIL.** The verdict is binary and final. A result in the range
TP ≥ 37 AND FP ≤ 75 may be *described* in the report as an informative near-miss, but the
verdict remains FAIL and triggers no further action. On failure: report as H15 failure; do not
tune threshold or epsilon; H15-at-ε=0.015 is closed for this model family.

## Exact allowed test command — DO NOT RUN UNTIL AUTHORIZED

```
# DO NOT RUN UNTIL AUTHORIZED (see AUTHORIZATION_REQUIRED_BEFORE_TEST.md)
.venv/Scripts/python.exe scripts/export_probability_predictions.py \
  --checkpoint checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt \
  --model lenet --epsilon 0.015 --run-name AFAC_maxscore_eps0015_TESTREAD \
  --out-dir results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read \
  --split test
```

Followed only by: applying tau = 0.168754 to the resulting
`AFAC_maxscore_eps0015_TESTREAD_pgd_probabilities_test_epsilon_0_015.csv` to produce one
TP/FN/FP/TN table, plus the clean-condition table at the same tau for disclosure.

## Exact forbidden actions

1. Running the test export more than once, or for any model other than the frozen checkpoint
   (SHA256 must match before the run).
2. Any threshold sweep, threshold re-selection, or threshold adjustment on test scores.
3. Any epsilon other than 0.015 on the test split.
4. Testing a second candidate (ST1b6_lowFA, SA1_lowFA, or any other) if AFAC fails.
5. Reading, summarizing, or plotting any test-score distribution beyond the fixed
   TP/FN/FP/TN + class-source breakdown at the frozen tau (no operating-region exploration).
6. Re-running validation selection after seeing test results.
7. Changing this protocol, the JSON twin, or the gate CSV after the read.

## How results must be reported

- One report: `results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/`
  `H15_EPS0015_TEST_RESULT.md`, containing: verdict (PASS/FAIL, binary); the TP/FN/FP/TN table
  at tau = 0.168754 with recall/FAR and binomial 95% CIs; the clean-condition table at the same
  tau; false-alarm source classes and missed-fall destination classes at the frozen tau;
  checkpoint SHA256 verification line; and the evidence label
  **"held-out test, frozen validation-selected threshold, single pre-registered read,
  PGD ε=0.015"**.
- Mandatory disclosures: (a) the ε=0.015 operating point was selected by a validation-only
  epsilon search — the claim is "H15 at ε=0.015", not H15 at the ledger's historical ε=0.030
  evaluation point; (b) the Gate-5 argmax caveat (optionB clean 7-class accuracy 0.694 < 0.70)
  accompanies any use of this checkpoint; (c) the result is window-level, digital-domain,
  white-box, seed-42 LeNet-family — not clinical, not deployment-validated, not certified.
- The verdict must be accepted as-is; both PASS and FAIL are final ledger entries.
