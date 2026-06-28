# Option A / A1 seed42 — informative-negative result review

> **RESULT REVIEW.** Records the completed A1 seed-42 pilot + a minimal held-out test kill-check. No further
> training, no further evaluation, no A2/A0, no H2/H3, no seed 44/45/46, no architecture change, no `.tex`
> edit, no Variant G/G1 change. Window-level, digital-domain, white-box, processed CSI; test n=500
> (45 fall / 455 non-fall), validation n=496 (44 falls), ε=0.030. **No product / clinical / deployment /
> certified / over-the-air claim.** The joint target (PGD recall > 80% AND false-alarm rate < 10%) remains
> **unmet**.

## 1. Training command and exit code

```
.venv\Scripts\python.exe scripts\train_variantH_dual_tail_budget.py --pilot --setting A1 --seed 42
```
Exit code **0** — `Done in 8337.3s (70 epochs)`. No stop condition (no NaN/inf, no always-zero TopK term,
no traceback).

Minimal test kill-check command (eval only, no training; `export_probability_predictions.py` unchanged):
```
.venv\Scripts\python.exe scripts\export_probability_predictions.py --checkpoint <A1 v2safety .pt> \
  --model lenet --run-name A1_v2safety --out-dir <A1/seed42/test_eval> --split test --epsilon 0.03 --pgd-steps 10
```
Exit code **0** (clean / FGSM / PGD-10 per-window CSVs; only clean + PGD-10 used for this kill-check).

## 2. Git HEAD

`fc96eeab52a779b505b73f2657586e1b1f154e9e` (`fc96eea Add A1 gatefix review approval`).

## 3. A1 parameters (match OPTION_A_REBALANCED_PREREGISTRATION.md)

`lambda_b = 0.25`, `lambda_r = 1.0`, `nonfall k_frac = 0.25`, `fall_rescue k_frac = 0.25`,
**`fall_rescue k_abs_min = 4`**, `gamma_b = 0.5`, `gamma_r = 0.5`. Base (Variant G G1)
`lambda_s = lambda_f = lambda_t = 1.0`, `w_wr = 2.0`, fall weight 3 — unchanged. `run_pilot` threaded
`fall_k_abs_min = cfg.get("k_abs_min")`; the floor was active a mean of **95.7%** of batches (final epoch
98.4%), with mean fall-selected count **2.645/batch** (= `min(4, n_adv_falls)`, well above H1's k ≈ 1).

## 4. Scope actually run

**A1 seed 42 only.** One pilot run + one minimal test export on the `v2safety`/`v2maxrec` checkpoint.

## 5. Scope confirmations

- **No A2/A0** ran (`OPTIONA_RUNNABLE = {A1}` blocks them).
- **No H2/H3** ran.
- **No seed 44/45/46** ran (seed gate).
- **No architecture change** (LeNet; splits/batch unchanged).
- **No `.tex` edit.**
- **Variant G/G1 files unmodified.**

## 6. Validation summary (selection-v2 candidates; validation split, 44 falls / 452 non-fall)

| candidate | epoch | clean acc | macro-F1 | val PGD recall | val PGD FP | val FAR (/452) |
|---|---|---|---|---|---|---|
| v2safety / v2maxrec | 70 | 0.724 | 0.722 | **0.500** | 71 | **15.7%** |
| v2macroF1 | 68 | 0.750 | 0.752 | 0.273 | 40 | 8.8% |
| v2lowFA | 67 | 0.720 | 0.726 | 0.182 | 29 | 6.4% |

Cold-start recovered normally (clean fall recall > 0 at epoch 30; val PGD recall > 0 at epoch 31).
Maximum validation PGD recall achieved across the whole run is **0.500** (at FAR 15.7%); the only
sub-10%-FAR points are the low-recall checkpoints.

## 7. Minimal held-out test kill-check (v2safety / v2maxrec, epoch 70)

| metric | value |
|---|---|
| clean accuracy | **0.678** |
| clean macro-F1 | **0.635** |
| clean fall recall | **0.933** (42/45) |
| PGD-10 fall recall | **0.556** (25/45) |
| PGD-10 TP / FN | 25 / 20 |
| PGD-10 FP | **68** |
| PGD-10 FAR (/455) | **15.0%** |

The clean guard that held on *validation* (acc 0.724) **fails on test** (acc 0.678, mF1 0.635) — a
validation→test generalization gap, the same pattern that rejected H1.

## 8. Minimum-useful gate (pre-registered §8)

| gate | threshold | A1 v2safety | result |
|---|---|---|---|
| PGD recall | ≥ 0.60 | 0.556 | **FAIL** |
| PGD FP | < 104 (G1 seed42) | 68 | PASS |
| clean acc | ≥ 0.70 | 0.678 | **FAIL** |
| macro-F1 | ≥ 0.65 | 0.635 | **FAIL** |
| clean fall recall | ≥ 0.90 | 0.933 | PASS |

Three of five gates fail.

## 9. Final classification

**REJECT — informative-negative result.** A1 does not reach minimum-useful and does not advance the
recall / false-alarm frontier.

## 10. Interpretation

- A1 **mechanically fixed** the fall-rescue under-power (floor active ~96% of batches, ~2.6 falls/batch vs
  H1's k ≈ 1) and **improved somewhat over H1** (test PGD recall 0.556 vs 0.489; FP 68 vs 94).
- But A1 is **dominated by Variant G G1 seed42** on both attacked recall (0.556 vs 0.689) and clean
  performance (acc 0.678 vs 0.716; mF1 0.635 vs 0.670).
- A1 **lowers FP relative to G1 seed42** (15.0% vs 22.9%) but **still fails the <10% FAR target.**
- The low-FP validation checkpoints (v2macroF1 8.8%, v2lowFA 6.4%) reach sub-10% FAR **only by suppressing
  fall recall** (0.27, 0.18) — the two tails trade rather than separate.
- **Conclusion:** the static-weight dual-tail does not improve the recall / false-alarm frontier; a fixed
  `lambda_b` either under-cuts FP or over-suppresses recall, never holding both. This is the same structural
  failure across H1 and A1.

## 11. No-claim boundary

- **No thesis claim.**
- **No clinical claim.**
- **No deployment / product claim.**
- **No certified-robustness claim.**
- **No over-the-air (OTA) claim.**

All results are window-level, digital-domain, white-box, benchmark-level, research-stage. The joint
> 80%-recall / < 10%-FAR target is **unmet**; A1 is an informative negative.

## 12. Recommended next direction

- **Retire static-weight dual-tail tuning** (H1/A1 line closed as informative negatives).
- **Pre-register a FAR-constrained rescue with an adaptive Lagrangian budget:** treat the < 10% false-alarm
  rate as an explicit constraint and let a dual variable on the budget term adapt during training (raise
  pressure only when FAR exceeds target, release otherwise), instead of a fixed `lambda_b`. This directly
  targets the H1/A1 root cause (a constant budget weight cannot hold recall and FAR simultaneously). Requires
  its own pre-registration, smoke/self-check, and code review before any run.

### Scope reminder
Result review only — no training/evaluation beyond the single completed pilot + minimal kill-check; no
A2/A0/H2/H3/seed44-46/architecture/`.tex`/Variant G change. Recommends retiring the static dual-tail and
pre-registering an adaptive-Lagrangian design; starts nothing.
