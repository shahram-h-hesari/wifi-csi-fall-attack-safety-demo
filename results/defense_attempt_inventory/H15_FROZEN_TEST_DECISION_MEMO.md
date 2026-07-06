# H15 Frozen-Test Decision Memo — ε=0.015 / AFAC_maxscore

Date: 2026-07-05. Status: **decision memo only — NO test read performed, none authorized by this
document alone.** All numbers below are validation-only (496 windows, 44 fall / 452 non-fall),
from the saved epsilon-sweep exports (`pgd_epsilon_frontier/val_sweep/`) plus a zero-cost
stability analysis of the saved ε=0.015 round-1 files
(`pgd_epsilon_frontier/h15_frozen_test_gate_numbers_eps0015.csv`). Prior held-out-test results
are cited only as transfer-history evidence, never for selection.

H15 on the 500-window test split (45 fall / 455 non-fall): recall > 0.85 AND FAR < 0.15 →
**TP ≥ 39 and FP ≤ 68** at a single frozen threshold, single read.

---

## 1. Should we attempt a frozen held-out H15 test read at all?

**Conditional YES — exactly one pre-registered read, at ε=0.015 only, and only after the
protocol files in §10 are saved and you sign off.** The conservative case for yes:

- The validation margin at ε=0.015 is *structurally* different from anything previously taken to
  test: the best candidate holds recall 0.909 at FAR ≤ 0.108 under a **buffered** cap (0.12),
  with a 0.056-wide H15-feasible threshold window — versus the 0.00028 knife edge that defined
  the ε=0.030 evidence.
- The one lesson of the D10/D11 failure is encoded as a hard condition below: the frozen
  checkpoint must have *previously demonstrated* small frozen-threshold val→test decay. Only one
  candidate has.

And the conservative boundaries: no read at 0.0225 or 0.024375 under any circumstances (§6);
one read total; failure closes H15-at-0.015 permanently; no epsilon or threshold may be revisited
after seeing test (the ε was chosen by validation search, so the read is one-shot at the single
frozen ε — touching test at a second epsilon would be test tuning).

## 2. Which epsilon should be frozen?

**ε = 0.015.** Rejections:

- **ε = 0.024375:** AFAC's pass is TP 38/44 — *zero* windows above the minimum passing count
  (37 fails). Any positive recall decay fails it; the realized FAR (0.142) plus the historically
  observed +0.014 drift already exceeds 0.15. Fragile — reject.
- **ε = 0.0225:** AFAC TP 38 (zero margin); ST1b6/SA1 have 1–2 window margins but realized FARs
  of 0.142–0.146, which the observed +0.014–0.034 drift pushes over the bar. Reject.
- **ε = 0.015:** margins of 2–4 windows above the bar at buffered FAR (0.095–0.113 vs 0.15), and
  the FAR headroom absorbs the worst historically observed drift. The only defensible point.

## 3. Which model should be frozen?

**AFAC_maxscore (`seed42_optionB_maxscore_best.pt`), single candidate — no multi-candidate
pre-registration.** This is the decisive judgment call, and it goes *against* the prettiest
validation numbers:

| Candidate (ε=0.015, tau @ FAR≤0.12) | Val recall (TP) | Val FAR | Window | Bootstrap joint pass | **Measured frozen val→test decay (ε=0.030)** |
|---|---|---|---|---|---|
| **AFAC_maxscore** | 0.909 (40) | 0.108 | 0.056 | 0.892 | **recall −0.018 / FAR +0.014 (best in ledger)** |
| ST1b6_lowFA | 0.955 (42) | 0.095 | 0.079 | 0.996 | recall **−0.220** (worst in ledger) |
| SA1_lowFA | 0.955 (42) | 0.113 | 0.057 | 0.988 | recall −0.130 |

ST1b6 has the best validation stability profile at 0.015 — exactly as D11a (the same checkpoint)
had the best validation recall at 0.030 before losing 0.22 recall on test. Validation-side
stability metrics demonstrably do not detect the fall-distribution shift that killed D10/D11;
the only evidence that predicts transfer is measured transfer, and AFAC/D8b's is the only good
one (its frozen 0.20-cap threshold reproduced test recall to within 0.018). One candidate, one
read: a disclosed "secondary candidate" doubles test exposure and muddies the evidence under
multiplicity. AFAC's one nominal weakness — a wide tau re-selection CI (0.076) — is benign for a
*frozen*-tau read: the CI spans a recall-flat plateau inside the 0.056 feasible window, and the
statistic that matters for a frozen threshold is the bootstrap joint pass at that tau (0.892).

## 4. Frozen threshold-selection rule (validation only)

The ledger rule at a **buffered cap**: tau = max validation recall s.t. validation FAR ≤ **0.12**
(tie-break lower FAR, then higher tau), computed on
`val_sweep/eps0015/AFAC_maxscore_eps0015_pgd_probabilities_val_epsilon_0_015.csv`.

**Frozen value: tau = 0.168754** (val: TP 40/44 = 0.909, FAR 0.108). The 0.12 buffer absorbs the
historically observed +0.014–0.034 FAR drift with margin (0.108 + 0.034 = 0.142 < 0.15). This tau
is frozen by this memo; it may not be recomputed, re-buffered, or replaced after any test result.

## 5. Validation margin required before test is justified (the gate)

All five conditions, on saved validation artifacts only — **current status: ALL PASS for
AFAC_maxscore**:

1. Val recall ≥ 0.909 (40/44) at FAR ≤ 0.12 → **0.909 / 0.108: PASS** (margin over the test bar
   0.867: +0.042 recall, +0.042 FAR headroom before drift).
2. H15-feasible tau window (val recall > 0.85 AND FAR < 0.15) width ≥ 0.03 → **0.056: PASS.**
3. Stratified bootstrap (2,000 resamples) at the frozen tau: joint P(recall > 0.85 AND
   FAR < 0.15) ≥ 0.80 → **0.892: PASS** (recall 95% lower 0.818; FAR 95% upper 0.137).
4. Clean guard at the frozen tau: clean recall ≥ 0.95 and clean FAR ≤ 0.12 → **0.977 / 0.062:
   PASS.** (The known Gate-5 argmax caveat — optionB clean 7-class accuracy 0.694 < 0.70 — must
   be disclosed alongside any result, as in every prior optionB report.)
5. Transfer-history condition (the D10/D11 lesson): the checkpoint must have a previously
   measured frozen-threshold val→test recall decay ≤ 0.05 at some epsilon → **−0.018 at ε=0.030:
   PASS. Only AFAC satisfies this; it is why ST1b6/SA1 are excluded despite better val numbers.**

## 6. Why ε=0.024375 is too fragile

The pass there is a single-window event: TP 38/44 with 37 failing, realized FAR 0.142 against a
0.15 bar that historical drift alone (+0.014) breaches, and a bootstrap joint pass probability
near 0.5 by construction (the operating point sits *on* the bar). It is the D8b-knife-edge
failure mode again, one epsilon lower. By contrast ε=0.015 is not fragile in the same sense:
2–4 window margins, buffered FAR with ~3× the observed drift in headroom, and an 0.89–0.99
bootstrap joint pass. The honest residual risk at 0.015 is not the margin — it is the
possibility of a D11a-magnitude (−0.22) fall-distribution shift, which no validation metric can
exclude and which the transfer-history condition only makes less likely, not impossible.

## 7. What counts as success on held-out test

At the frozen tau = 0.168754, PGD ε=0.015 (PGD-10, α=ε/6), single read of the 500-window test
split: **TP ≥ 39 / 45 AND FP ≤ 68 / 455** (recall > 0.85, FAR < 0.15) → H15 met at ε=0.015,
reported with binomial CIs and the clean-condition numbers at the same tau, plus the Gate-5
argmax disclosure. Expected point under AFAC's own measured decay: recall ≈ 0.89 (TP ≈ 40),
FAR ≈ 0.12 (FP ≈ 56) — pass, but with single-read binomial noise of roughly ±2 fall windows.

## 8. What counts as failure

Anything else. Pre-declared bands, fixed before the read:
- **Informative near-miss** (still a FAIL for H15): TP ≥ 37 AND FP ≤ 75 — reported as the best
  frozen-threshold operating point in the ledger; **no second read, no threshold change, no
  epsilon change.**
- **Failure:** below the near-miss band. Interpretation: the val→test shift dominates even at
  weaker attack strength; H15 is closed at all epsilons for this family.
In every non-success case the H15-at-0.015 question is closed permanently; there is no re-read,
re-thresholding, seed swap, or epsilon shopping. A second read would require a new advisor
authorization and a materially new model, not a protocol tweak.

## 9. Exact command for the frozen test read — **DO NOT RUN**

```
# DO NOT RUN — requires §10 files saved + explicit advisor sign-off recorded first
.venv/Scripts/python.exe scripts/export_probability_predictions.py \
  --checkpoint checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt \
  --model lenet --epsilon 0.015 --run-name AFAC_maxscore_eps0015_TESTREAD \
  --out-dir results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read \
  --split test
# then apply ONLY tau=0.168754 to the pgd CSV; no sweep, no re-selection.
```

## 10. Files that must be saved before any test read

1. `H15_PREREGISTERED_TEST_PROTOCOL.md` — copy of §§2–9 of this memo as the binding protocol:
   checkpoint path + SHA256, ε, frozen tau, decision bands, single-read rule, disclosure list.
   Checkpoint SHA256 (computed now): `b85c68a7f4834c514a06d737af167542c9139bed45dde8a40380eac78cab1146`.
2. `h15_frozen_test_gate_numbers_eps0015.csv` — already saved (gate evidence, all three
   candidates, including the transfer-history column).
3. The validation score files the tau was frozen from —
   `val_sweep/eps0015/AFAC_maxscore_eps0015_{pgd,clean}_probabilities_val_epsilon_0_015.csv`
   (already saved; must remain byte-unchanged).
4. A signed advisor authorization line (date + "one read at ε=0.015, tau=0.168754, AFAC
   checkpoint b85c68a7…") appended to the protocol file.
5. Git commit of items 1–3 is recommended *by you* before the read (this session does not
   commit), so the pre-registration timestamp is independent of the result.

---

### Final printed summary

1. **Test now or not?** Not now — one pre-registered read is *justified* at ε=0.015 (all five
   gate conditions pass), but only after the §10 protocol files are saved and you sign off.
2. **Best frozen epsilon:** 0.015.
3. **Best frozen model:** AFAC_maxscore (`seed42_optionB_maxscore_best.pt`, SHA256 b85c68a7…) —
   the only candidate with measured small val→test decay; ST1b6/SA1 excluded on transfer
   history despite better validation numbers.
4. **Frozen validation threshold rule:** max val recall s.t. val FAR ≤ 0.12 (tie-break lower
   FAR, then higher tau) on the saved ε=0.015 validation PGD export → **tau = 0.168754**
   (val 0.909 recall / 0.108 FAR).
5. **Main risk:** an unmeasurable D11a-magnitude fall-distribution shift between validation and
   test at ε=0.015 — validation-side metrics cannot exclude it; the transfer-history condition
   mitigates but does not eliminate it. Single-read binomial noise (±2 fall windows) is the
   second risk.
6. **DO NOT RUN test command:** the §9 block above (export `--split test` at ε=0.015 on the
   AFAC checkpoint, then apply only tau=0.168754).
