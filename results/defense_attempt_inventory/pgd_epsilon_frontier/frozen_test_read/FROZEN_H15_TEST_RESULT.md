# FROZEN H15 TEST RESULT — VERDICT: **H15 PASS**

Protocol: `H15-TEST-EPS0015-AFAC-20260705` (pre-registered at commit
`92f7bbb20817a8c5e003b1304ac20ad4071d7d07`, "Pre-register H15 epsilon frontier frozen test
protocol"). Authorization: signed line in `../AUTHORIZATION_REQUIRED_BEFORE_TEST.md`
(Shahram Hesari, 2026-07-05). Executed: 2026-07-05, exactly **one** test read.

Evidence label: **held-out test, frozen validation-selected threshold, single pre-registered
read, PGD ε=0.015 (PGD-10, α=ε/6, white-box, digital-domain, window-level, seed-42 LeNet
family).**

## Protocol integrity confirmations

- HEAD at execution = pre-registration commit `92f7bbb2…` — verified before the run.
- Checkpoint SHA256 verified before the run:
  `b85c68a7f4834c514a06d737af167542c9139bed45dde8a40380eac78cab1146` (match).
- Exact test probability CSV used:
  `results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/AFAC_maxscore_eps0015_TESTREAD_pgd_probabilities_test_epsilon_0_015.csv`
  (500 windows: 45 fall / 455 non-fall; PGD condition rows).
- **tau = 0.168754 was applied exactly, once.** No threshold sweep was performed; no threshold
  was recomputed; no other operating point was evaluated on test.
- **No second model and no second epsilon was tested.** The only test-split inference performed
  was the single export command frozen in the protocol.
- FGSM/clean CSVs produced by the export pipeline are byte-stored as pipeline by-products; only
  the PGD file (decision) and the clean file (pre-registered disclosure at the same tau) were
  evaluated.

## Result at the frozen threshold (PGD ε=0.015, tau=0.168754)

| Quantity | Value |
|---|---|
| TP | **41** / 45 |
| FN | 4 |
| FP | **60** / 455 |
| TN | 395 |
| Fall recall | **0.9111** (Wilson 95% CI 0.793–0.965) |
| FAR | **0.1319** (Wilson 95% CI 0.104–0.166) |
| Success rule | TP ≥ 39 AND FP ≤ 68 |
| Rule satisfied? | **YES** (41 ≥ 39; 60 ≤ 68) |
| **Verdict** | **H15 PASS** (recall 0.9111 > 0.85; FAR 0.1319 < 0.15) |

Machine-readable twin: `frozen_h15_test_confusion.csv` (this folder).

## Pre-registered disclosures

1. **Clean condition at the same frozen tau:** TP 44 / FN 1 / FP 41 / TN 414 — clean recall
   0.9778, clean FAR 0.0901.
2. **Validation→test transfer realized:** validation (frozen) 0.9091 recall / 0.1084 FAR →
   test 0.9111 / 0.1319. Recall decay ≈ 0 (+0.002); FAR drift +0.024, absorbed by the
   pre-registered 0.12-cap buffer exactly as designed.
3. **Error structure at the frozen tau (fixed tables, no exploration):**
   - False-alarm sources: run 21, walk 16, stand up 10, pickup 8, lie down 3, sit down 2
     (run+walk = 62% of FPs, consistent with all prior diagnosis).
   - Missed-fall destinations: walk 3, run 1.
4. **Epsilon-selection disclosure:** ε=0.015 was chosen by a validation-only epsilon frontier
   search (rounds at 0.015/0.0225/0.02625/0.024375, no test contact). The claim certified here
   is **H15 at PGD ε=0.015** — it does not alter, and is not comparable to, the ledger's
   ε=0.030 evidence (where H15 remains unmet and F20 remains post-hoc-only).
5. **Gate-5 argmax caveat:** this checkpoint's clean 7-class argmax accuracy is 0.694 < 0.70
   (historical Gate-5 rejection of the argmax rule); the H15 result concerns the binary
   fall-score threshold rule, not the multi-class argmax decision.
6. **Claim boundary:** window-level, processed-CSI-tensor, digital-domain, white-box, single
   seed (42), LeNet family. Not clinical, not deployment-validated, not certified robustness.

## Finality

Per the pre-registered protocol this verdict is binary and final. The read is consumed: no
re-read, no threshold or epsilon adjustment, and no additional candidate may be tested under
this protocol. Protocol twin files remain byte-unchanged.
