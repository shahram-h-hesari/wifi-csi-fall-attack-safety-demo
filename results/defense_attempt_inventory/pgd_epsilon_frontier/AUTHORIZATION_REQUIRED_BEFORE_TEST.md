# AUTHORIZATION REQUIRED BEFORE TEST — H15-TEST-EPS0015-AFAC-20260705

**THE TEST HAS NOT BEEN RUN.** As of 2026-07-05, no test-split file has been opened, exported,
or evaluated under this protocol.

Binding conditions, fixed before any test read:

1. **One frozen test read is allowed only after explicit user (Shahram) authorization**, recorded
   by appending a signed line to this file in the form:
   `AUTHORIZED: <date> — one read, eps=0.015, tau=0.168754, checkpoint b85c68a7f4834c51... — <name>`.
   Until that line exists, the command in the protocol is forbidden.
2. **No threshold change is allowed after test.** tau = 0.168754 is final; it may not be
   recomputed, re-buffered, or replaced regardless of the result.
3. **No second candidate may be tested if AFAC fails.** ST1b6_lowFA, SA1_lowFA, and every other
   checkpoint remain untested at ε=0.015 permanently under this protocol; a new protocol would
   require new advisor authorization and a materially new model, not a substitution.
4. **No epsilon change is allowed after test.** ε = 0.015 is the single frozen evaluation point;
   running test at any other epsilon after seeing the result would constitute test tuning and is
   forbidden.
5. **The result must be accepted as pass or fail.** PASS = TP ≥ 39/45 AND FP ≤ 68/455.
   FAIL = TP ≤ 38 OR FP ≥ 69. The verdict is binary, final, and enters the ledger as-is; a
   failure is reported as an H15 failure with no threshold or epsilon tuning afterward.

Protocol twin files (must remain byte-unchanged after the read):
- `FROZEN_H15_TEST_PROTOCOL_EPS0015_AFAC.md`
- `frozen_h15_test_protocol_eps0015_afac.json`
- `h15_frozen_test_gate_numbers_eps0015.csv`
- `val_sweep/eps0015/AFAC_maxscore_eps0015_{pgd,clean}_probabilities_val_epsilon_0_015.csv`

Recommended (user action, not performed by this session): commit the files above before
authorizing the read, so the pre-registration timestamp is independent of the result.

---

(authorization lines below this rule)
