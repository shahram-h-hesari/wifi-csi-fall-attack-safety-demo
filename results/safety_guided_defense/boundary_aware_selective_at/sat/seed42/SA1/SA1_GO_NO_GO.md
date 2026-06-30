# BASAT Stage 3 — SAT-only (SA1) seed-42 go/no-go (VALIDATION only)

_Frozen G1 + calibrated asymmetric confidence-collapse filtering of the adversarial CE (tau on val NLL,
refit every 10 ep; alpha_f=0.03 / alpha_n=0.08; burn-in 15; reduces to G1 when all kept). Early-stopped
at 60 epochs (5677 s). NO test set used. Eval PGD-10 (alpha=eps/6). Bar = best G1 checkpoint._

## Verdict: **NO-GO** (envelope unchanged; the one nominal gain is operating-point noise)

Best SA1 val PGD AUROC = **0.873** (< bar 0.906; paired best-vs-best vs G1 = −0.003 ≈ 0). The separability
envelope did not move.

## Validation PGD, by selected checkpoint

| checkpoint (epoch) | clean AUROC | **PGD AUROC** [CI95] | recall@FAR≤10% | guard |
|---|---|---|---|---|
| v2safety=maxrec (45) | 0.995 | 0.8213 [0.777, 0.861] | 0.273 (FP45) | OK |
| v2lowFA (58) | 0.996 | **0.8728** [0.837, 0.905] | **0.523** (FP45) | OK |
| v2macroF1 (60) | 0.997 | 0.8537 [0.815, 0.890] | 0.295 (FP44) | OK |

## Bar vs achieved

| criterion | bar | best SA1 | result |
|---|---|---|---|
| 1. val PGD AUROC | > 0.906 | 0.873 | **FAIL** (envelope = G1) |
| 2. val recall@FAR≤10% | ≥ 0.477 | 0.523 (v2lowFA) | nominally met — but see note |
| 3. clean guard | acc≥.70, mF1≥.65 | held; clean AUROC ~0.99 | pass |

## The recall@FAR≤10% = 0.523 is operating-point noise, NOT a frontier gain

SA1 v2lowFA reads 23/44 TP at FP=45 (FAR 0.0996) vs G1 v2lowFA's 21/44 at FP=42 — **2 more falls at 3 more
false alarms, both pinned at the FAR cap**. But SA1 v2lowFA's threshold-free AUROC (0.873) is *lower* than
G1 v2lowFA's (0.876), and the paired best-vs-best AUROC difference is **−0.0028, CI95 [−0.025, +0.020]**
(≈0). So the ROC is essentially identical; SA1 just happens to have 2 extra TP at the FPR≈0.10 corner.
At n_fall(val)=44 that is well within noise (1 fall = 2.3 recall points), it is a *validation* number at a
val-tuned threshold, and it is **not claimed** — it would not be expected to survive on test.

## Why SAT had little to act on

tau calibrated to 0.50 (sharpening an under-confident model) drove the confidence range above alpha_n for
essentially all windows in the trained regime, so **keep-rate → 1.00 by ~epoch 45+ (SAT == G1 at the
selected checkpoints)**. The "harmful collapsed adversarials" SAT targets are largely a cold-model
phenomenon; the converged model has almost nothing to filter. Asymmetry worked (falls always kept).

Paired matched-selector: SA1 v2safety vs G1 v2safety d = +0.0134, CI95 [−0.006, +0.033] (includes 0).
