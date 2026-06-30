# Safety-TRADES / BASAT Stage 1 — CLOSEOUT (seed 42, dose-bracketed NO-GO)

_Frozen Variant G G1 objective + β·mean_{adv fall}(sg[p_f(x_clean)] − p_f(x_adv))². Two doses, β∈{3.0, 6.0},
seed 42, same UT-HAR split, same FGSM/PGD ε=0.030, same clean guard (0.70/0.65) and selection-v2.
VALIDATION ONLY — the TEST set was never used. Eval attack PGD-10 (α=ε/6), byte-identical to the
G1 baseline export. Go/no-go bar from g1_baseline_val_frontier (best G1 checkpoint)._

## Verdict: NO-GO at both doses. Stage 1 (Safety-TRADES / consistency mechanism) is CLOSED.

The TRADES-style fall-probability consistency term does **not** expand the PGD-conditional fall/non-fall
separability envelope of the LeNet UT-HAR model beyond G1.

## Best-checkpoint envelope (the frontier) — val PGD

| metric | bar (best G1) | β=3.0 best | β=6.0 best | moved? |
|---|---|---|---|---|
| val PGD AUROC of P(fall) | 0.876 (>0.906 to GO) | 0.876 | 0.869 | **no** (flat→down) |
| val recall@FAR≤10% | 0.477 | 0.477 | 0.364 | **no** (tie→down) |
| clean guard / clean AUROC | acc≥.70 | held / ~0.99 | held / ~0.99 | preserved |

Neither dose clears the AUROC bar (0.906); best β values land at/below G1's best (0.876). On the
operational metric (recall@FAR≤10%) the stronger dose regressed (0.477 → 0.364).

## Matched-selector dose-response (v2safety vs G1 v2safety) — val PGD AUROC

| | G1 v2safety | β=3.0 v2safety | β=6.0 v2safety |
|---|---|---|---|
| val PGD AUROC | 0.808 | 0.824 | **0.847** |
| paired Δ vs G1 (CI95) | — | +0.0155 [−0.005, +0.036] | **+0.0392 [+0.015, +0.065]** |
| best-vs-best Δ (CI95) | — | +0.0004 [−0.024, +0.026] | −0.0066 [−0.029, +0.018] |

The matched-selector AUROC rises monotonically with β (0.808 → 0.824 → 0.847) and is **statistically
significant at β=6.0** (CI excludes 0). So the consistency mechanism is **real, not inert** — it tightens
the recall-tilted (safety-score) checkpoint. But it only moves that checkpoint **up toward where G1's
other checkpoints (v2lowFA, 0.876) already sit**; the best-vs-best difference is ≈0. The envelope does
not expand.

## Interpretation (committee-grade)

1. **Mechanism works locally, not globally.** Consistency regularization redistributes PGD-separability
   across the selection-v2 checkpoints (tightening the weakest one) but cannot push the achievable
   envelope past ~0.876 AUROC.
2. **Same signature as Option B / DS-SGE**, now with a cleaner basis: the operating point / per-checkpoint
   separability moves; the frontier envelope does not. Three independent post-hoc/training interventions
   (gate, Lagrangian dual-tail, TRADES consistency) all hit the same ~0.876 PGD-AUROC ceiling on LeNet.
3. **This is consistent with — but does NOT by itself prove — a LeNet representation ceiling.** Per the
   standing instruction, this NO-GO does **not** imply SAT/GAIRAT/MART cannot help: those reshape *which*
   adversarial windows drive training (selective / boundary-margin reweighting), a different mechanism
   from boundary consistency. Whether a SAT-only or GAIRAT-only pilot is justified is a joint decision.

## Provenance

- β=3.0: results/.../boundary_aware_selective_at/seed42/beta3p0/ (STAGE1_BETA3_GO_NO_GO.md, val_eval/)
- β=6.0: results/.../boundary_aware_selective_at/seed42/beta6p0/ (val_eval/)
- baseline: results/.../boundary_aware_selective_at/seed42/g1_baseline_val_frontier.{json,md}
- code: scripts/train_basat.py (--self-check/--smoke/--pilot), scripts/compute_g1_baseline_val_frontier.py
- β=1.0 was intentionally not run (lower-value dose; user chose "confirm with β=6.0 then close").
- No test set used at any point in Stage 1.
