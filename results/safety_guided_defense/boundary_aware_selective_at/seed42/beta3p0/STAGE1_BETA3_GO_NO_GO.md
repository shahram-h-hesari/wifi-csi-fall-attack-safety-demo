# Safety-TRADES / BASAT Stage 1 — β=3.0 seed-42 go/no-go (VALIDATION only)

_Frozen G1 objective + β·mean_{adv fall}(sg[p_f(x_clean)] − p_f(x_adv))². 70 epochs, no early stop
(elapsed 6611 s). Selection-v2 + clean guard unchanged. NO test set used. Eval attack PGD-10 (α=ε/6),
byte-identical to the G1 baseline export. Bar from g1_baseline_val_frontier (best G1 checkpoint)._

## Verdict: **NO-GO**

Best Safety-TRADES val PGD AUROC = **0.876**, which is **exactly G1's best (0.876)**; bar was > 0.906.
The threshold-free fall/non-fall separability under PGD did **not** move beyond noise.

## Validation PGD AUROC of P(fall), by selected checkpoint (β=3.0)

| checkpoint (epoch) | clean AUROC | **PGD AUROC** [CI95] | recall@FAR≤10% | argmax op-point |
|---|---|---|---|---|
| v2safety=v2maxrec (67) | 0.994 | 0.8235 [0.779, 0.866] | 0.227 (FP38) | rec 0.636 / FAR 0.246 |
| v2lowFA (57) | 0.995 | 0.8640 [0.825, 0.900] | **0.477** (FP45) | rec 0.159 / FAR 0.053 |
| v2macroF1 (65) | 0.999 | **0.8760** [0.840, 0.908] | 0.455 (FP43) | rec 0.250 / FAR 0.066 |

## Bar (best G1 checkpoint) vs achieved

| criterion | bar | best Safety-TRADES β=3.0 | result |
|---|---|---|---|
| 1. val PGD AUROC | > 0.906 (G1 0.876 + 0.03) | 0.876 (v2macroF1) | **FAIL** (= G1, no gain) |
| 2. val recall@FAR≤10% | ≥ 0.477 | 0.477 (v2lowFA) | tie (no improvement) |
| 3. clean guard | acc≥0.70, mF1≥0.65 | held all epochs; clean AUROC ~0.99 | pass |
| 4. PGD-20 no masking | — | moot (PGD-10 showed no gain to mask) | n/a |

## Paired bootstrap of the AUROC difference (same val windows; + = Safety-TRADES better)

- ST1 v2safety **vs** G1 v2safety(=maxrec): **d = +0.0155, CI95 [−0.0053, +0.0361]** — CI includes 0.
- ST1 best (v2macroF1) **vs** G1 best (v2lowFA): **d = +0.0004, CI95 [−0.0243, +0.0261]** — ≈ 0.

## Reading

The consistency term was active and well-behaved (it ran up to ~0.035 and visibly shrank the clean→adv
fall-probability gap, e.g. ~0.60→0.45 on falls). But that local gap-shrinking did **not** translate into
better PGD-conditional separability of P(fall): the best Safety-TRADES checkpoint lands exactly on G1's
best (0.876), and the paired best-vs-best difference is +0.0004. This is the **same pattern as Option B**
— the operating point moves, the frontier does not. At the matched selector there is a small positive
nudge (+0.0155) but it is within single-checkpoint noise (CI includes 0).

Per the standing instruction: a Safety-TRADES NO-GO does **NOT** imply SAT/GAIRAT/MART cannot help —
those test a different mechanism (selective/boundary reweighting vs. boundary consistency). Decision on
β∈{1.0,6.0} dose-response completion and on a SAT-only/GAIRAT-only pilot is deferred to Shahram.
