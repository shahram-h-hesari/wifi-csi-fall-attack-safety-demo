# BASAT Stage 2 — GAIRAT-only (GR1) seed-42 go/no-go (VALIDATION only)

_Frozen G1 + margin-based boundary reweighting of the adversarial CE (mean-1 weights, burn-in 10,
reduces to G1 exactly at w==1). 70 epochs (7251 s). Same split, FGSM/PGD ε=0.030, clean guard, selection-v2.
NO test set used. Eval PGD-10 (α=ε/6), byte-identical to the G1 baseline. Bar = best G1 checkpoint._

## Verdict: **NO-GO**

Best GR1 val PGD AUROC = **0.871** (< bar 0.906, < G1 best 0.876). recall@FAR≤10% best = **0.341**
(< G1 best 0.477). The boundary-margin reweighting did **not** expand the separability envelope.

## Validation PGD AUROC of P(fall), by selected checkpoint

| checkpoint (epoch) | clean AUROC | **PGD AUROC** [CI95] | recall@FAR≤10% | argmax | guard |
|---|---|---|---|---|---|
| v2safety=maxrec (57) | 0.991 | 0.8190 [0.772, 0.865] | 0.295 | 0.682/0.230 | OK |
| v2lowFA (62) | 0.996 | 0.8597 [0.824, 0.892] | 0.250 | 0.182/0.064 | OK |
| v2macroF1 (69) | 0.997 | **0.8712** [0.838, 0.901] | 0.341 | 0.250/0.091 | OK |

## Bar vs achieved

| criterion | bar | best GR1 | result |
|---|---|---|---|
| val PGD AUROC | > 0.906 | 0.871 | **FAIL** (< G1 best 0.876) |
| recall@FAR≤10% | ≥ 0.477 | 0.341 | **FAIL** (regressed) |
| clean guard | acc≥.70, mF1≥.65 | held; clean AUROC ~0.99 | pass |

## Paired bootstrap (same val windows; + = GAIRAT better)

- GR1 v2safety vs G1 v2safety: d = **+0.0111**, CI95 [−0.0100, +0.0336] — includes 0.
- GR1 best vs G1 best (v2lowFA 0.876): d = **−0.0044**, CI95 [−0.0360, +0.0271] — ≈ 0.

## Reading

The weighting was active and on-target (falls up-weighted ~1.4×, non-fall ~0.95×, fall margins small &
positive — i.e. it correctly poured emphasis onto boundary-adjacent falls). Yet the best checkpoint lands
at 0.871, essentially on the same ~0.876 envelope as G1 / Stage 1 / Option B / DS-SGE, and the paired
best-vs-best difference is ≈0. GAIRAT was the **most mechanistically targeted** boundary intervention
available (it directly up-weights the falls that flip), and it still did not expand the envelope — which
strengthens (without proving) the LeNet representation-ceiling interpretation.

Per the standing rule, this does not by itself prove SAT cannot help; SAT (selective filtering) is a
different lever. Decision on SAT-only vs a representation change is deferred to Shahram.
