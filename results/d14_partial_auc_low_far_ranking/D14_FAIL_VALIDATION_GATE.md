# D14_FAIL_VALIDATION_GATE

Pre-registration commit `7ee228369052461682741a372a1ac2c3209fecb1`; clarification commit `06c93abb635b3bcaf2e5591f214bd57d00faf831` (paired bootstrap = primary Gate-3; fixed 36/44 = sensitivity only).

Validation-only D14 gate. **No held-out test read has been performed by this script.**

- Chosen config (tie-break: higher median recall@0.17 -> lower FAR -> Config A): **B**
- Median seed of chosen config: **44** (best epoch 1, status OK)
- Median-seed cap-0.17 operating point: threshold=0.156507, TP/FN/FP/TN=32/12/70/382, recall=0.7273, FAR=0.1549
- Median-seed cap-0.20 comparison: threshold=0.137347, recall=0.8182, FAR=0.1947
- Median-seed validation PGD AUROC: 0.8732

## Per config/seed status
- Config A seed 42: CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT
- Config A seed 43: CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT
- Config A seed 44: CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT
- Config B seed 42: CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT
- Config B seed 43: OK (cap-0.17 recall 0.7727)
- Config B seed 44: OK (cap-0.17 recall 0.7273)

## Gate conditions
1. median-seed recall >= 38/44 (0.8636): FAIL (TP=32)
2. bootstrap recall >= 0.80 in >= 75%: FAIL (observed 0.117, n=2000)
3. PAIRED bootstrap gain (Delta TP = TP_D14 - TP_AFAC >= 2) in >= 70% [PRIMARY]: FAIL (paired observed 0.062). Fixed 36/44 comparison (SENSITIVITY ONLY, not used for gate): 0.030
4. clean guard (acc>=0.70, mF1>=0.65, fallR>=0.90): PASS (acc=0.706, mF1=0.695, fallR=0.909)

## VERDICT: D14_FAIL_VALIDATION_GATE

At least one condition failed. Per the pre-registration, there is NO held-out test read; the F20 chase ends, and the next step is the D9 TRADES/MART baseline-completeness rerun.

_No held-out test read has been performed by this script._