# BASAT — within-training defense line CLOSEOUT (LeNet, seed 42)

_Synthesis of the paper-driven (TRADES/MART/GAIRAT/SAT) single-ingredient pilots on the frozen G1
LeNet objective. All VALIDATION-only; the TEST set was never used in any pilot. Threshold-free primary
endpoint: AUROC of P(fall) under eval PGD-10 (alpha=eps/6, eps=0.030). Go/no-go bar = best G1 checkpoint:
AUROC > 0.906, recall@FAR<=10% >= 0.477._

## Headline

**Four mechanistically distinct interventions all land on the same ~0.876 PGD-AUROC separability
envelope, none expanding it, none reaching the (recall >= 0.80, FAR <= 0.10) target.** On a LeNet UT-HAR
representation, training-time interventions can move *where on the envelope* a checkpoint sits, but not
the envelope itself.

## The envelope, across every intervention tried

| line | mechanism | best val PGD AUROC | best recall@FAR<=10% | clean guard | verdict |
|---|---|---|---|---|---|
| G1 baseline | fall-weighted AT + margins | **0.876** | 0.477 | held | reference |
| DS-SGE | post-hoc dual-specialist gate | ~0.81 (R) | — (nested) | n/a | NO (nested specialists) |
| Option B | adaptive Lagrangian dual-tail | 0.840 | ~0.34 | gap on test | NO |
| Stage 1 (BASAT) | TRADES fall-prob consistency (b=3) | 0.876 | 0.477 | held | NO-GO |
| Stage 1 (BASAT) | TRADES fall-prob consistency (b=6) | 0.869 | 0.364 | held | NO-GO |
| Stage 2 (BASAT) | GAIRAT boundary-margin reweighting | 0.871 | 0.341 | held | NO-GO |
| Stage 3 (BASAT) | SAT calibrated asymmetric selection | 0.873 | 0.523* | held | NO-GO |

\* SA1 recall@FAR<=10%=0.523 is a 2-fall (n=44) operating-point blip; its threshold-free AUROC (0.873) is
statistically identical to G1 (paired Δ=−0.003), so it is NOT an envelope gain and is not claimed.

## Paired best-vs-best AUROC differences (same val windows, vs G1 best 0.876)

- Stage 1 b=3: +0.0004 [−0.024, +0.026]   |  Stage 2 GAIRAT: −0.0044 [−0.036, +0.027]
- Stage 3 SAT:  −0.0028 [−0.025, +0.020]
All include / center on 0: no intervention expands the envelope.

## What each mechanism demonstrably DID (so the negative is not "they didn't work")

- TRADES consistency: real, dose-dependent, significant at the matched selector (val AUROC 0.808→0.824→0.847
  across G1/b3/b6, paired +0.039 at b=6) — but only tightens the weak checkpoint toward the envelope.
- GAIRAT: correctly up-weighted boundary-adjacent falls (~1.4x) — most targeted lever, still no expansion.
- SAT: asymmetric filter protected 100% of falls; converged model had ~nothing to filter (keep→1.0).

## Interpretation (committee-grade)

The bottleneck is the **PGD-conditional separability of the LeNet representation around true-fall
windows** (clean AUROC ~0.99 -> PGD ~0.876). Output combination (DS-SGE), constrained optimization
(Option B), boundary regularization (TRADES), boundary reweighting (GAIRAT), and data selection (SAT) are
all interventions on a *fixed representation*; the consistent ~0.876 ceiling across all five is strong
(not proven) evidence that the ceiling is **representational**. This motivates the next axis: a
**representation change (BiLSTM / temporal model)**, evaluated with the SAME threshold-free PGD-AUROC
endpoint and bar.

## Honest scope / non-claims

Seed 42 only (no multi-seed yet); LeNet only; n_fall(val/test)=44/45 -> single-checkpoint operating-point
numbers have ~±14pt CIs, which is why the threshold-free AUROC is the primary endpoint. No test set used.
No certified/clinical/over-the-air claims. A valid thesis outcome: paper-driven boundary/selective AT does
not reach the target region on this representation, establishing a representation-level frontier ceiling.
