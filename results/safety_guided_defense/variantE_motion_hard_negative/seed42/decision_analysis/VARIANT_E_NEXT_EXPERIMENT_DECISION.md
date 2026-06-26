# Variant E — next-experiment decision memo (seed 42)

> **Analysis-only.** No training was run, Variant E seed 43 / seeds 44–46 were not run, the
> frozen Variant D protocol/results and existing Variant E artifacts were not modified, and no
> thesis `.tex` files were touched. New derived files live under
> `results/safety_guided_defense/variantE_motion_hard_negative/seed42/decision_analysis/`.
> All numbers test n=500 (val n=496), ε=0.030 unless noted; window-level, digital-domain,
> white-box; not solved/certified/clinical/over-the-air.

**Decision question:** is Variant E λ=1.0 good enough to replicate (A), or should the next step
refine the design — tune λ (B), change the penalty form (C), rescore checkpoints (D), or build a
binary fall-alert objective (E)?

**Recommendation (short):** **Option A — replicate E λ=1.0 on seed 43.** E λ=1.0 already meets the
desired operating point on seed 42 and, crucially, **improves the recall/false-alarm frontier
across the entire epsilon sweep** (not just at one point). The refinement options are either ruled
out by the evidence (rescoring) or premature on a single seed (λ search, margin penalty, binary
head). The gating evidence now is whether the seed-42 frontier gain replicates.

---

## 1. What Variant E solved (E λ=1.0 safety vs Variant D safety; test, ε=0.030)

| Metric | Variant D safety | E λ=1.0 safety | Change |
|---|---|---|---|
| PGD fall recall | 0.444 | 0.356 | −0.088 (still 4× FGSM defense's 0.089) |
| Total PGD false alarms | 157 | 117 | **−25%** |
| walk/run → fall false alarms | 120 | 80 | **−33%** |
| Clean accuracy | 0.746 | 0.806 | **+0.060** |
| Clean macro-F1 | 0.700 | 0.790 | **+0.090** |
| Clean fall recall | 1.000 | 0.978 | −0.022 (still ≥0.95) |
| PGD precision | 0.113 | 0.120 | +0.007 |
| PGD specificity | 0.655 | 0.743 | **+0.088** |
| PGD binary-F1 | 0.180 | 0.180 | 0 |
| PGD collapse ε | 0.030 | 0.030 | unchanged |

Variant E cut false alarms (total and motion-specific) and improved clean performance and
specificity, at a modest PGD-recall cost, with the robust ε-range preserved.

## 2. What Variant E did NOT solve

*(`analysis/probability_diagnosis.csv`)* For E λ=1.0 safety, the **residual** walk/run false
alarms remain **high-confidence**: median fall-probability ≈ 0.82 (walk) / 0.83 (run), while true
falls sit at ≈ 0.26. The **inverted geometry persists** (true falls have lower fall-probability
than the residual motion false alarms), so **threshold calibration is still unlikely to help** the
remaining false alarms. The penalty reduced the *count* of motion false alarms (and overall
fall-bias) but did not make the survivors low-confidence. **E2 is a partial mitigation, not a
geometry fix.**

## 3. λ behaviour (safety-guided selected checkpoints; test)

| λ | Clean acc | Clean macro-F1 | PGD recall | PGD FP | walk/run→fall | motion penalty (end) |
|---|---|---|---|---|---|---|
| 0.5 | 0.654 | — | 0.089 | 145 | 100 | ~0.11 |
| **1.0** | **0.806** | **0.790** | **0.356** | **117** | **80** | ~0.05 |
| 2.0 | 0.730 | 0.706 | 0.178 | 122 | 88 | ~0.05 |

- **λ=1.0 is a real sweet spot** on the safety-selected operating point: it has the highest PGD
  recall, the fewest false alarms, and the best clean numbers of the three.
- **λ=0.5 under-penalizes:** false alarms barely move (145) and recall drops to the FGSM-defense
  level (0.089).
- **λ=2.0 over-penalizes:** the safety pick is *worse* than λ=1.0 (recall 0.178, FP 122) — more
  penalty did not buy more false-alarm reduction at the safety-selected checkpoint (the macro-F1
  picks at λ≥1.0 cut FP hard but collapse recall to ≤0.067, below the FGSM-defense bar).
- **Is a fine search (0.75 / 1.25) justified?** Weakly. The 0.5→1.0→2.0 pattern brackets a clear
  interior optimum near 1.0; the expected marginal gain from 0.75/1.25 is small relative to the
  cost, and would still be a single-seed result. Lower priority than confirming replication.

## 4. Loss-form diagnosis

Current penalty: `λ · mean(fall_probability for adversarial walk/run samples)`.

| Form | Expected benefit | Risk | Complexity | Supported now? |
|---|---|---|---|---|
| **A. fall-probability (current)** | Bounded, stable; already improved the frontier (§6) | Saturates — once fall-prob is mid-range the gradient weakens, leaving high-conf residuals (§2) | low | In use; works partially |
| **B. fall-logit penalty** | Unbounded pressure on the fall logit; may push residual high-conf FAs down where probability saturates | Can destabilize / over-suppress recall; scale-sensitive | low | Plausible but speculative |
| **C. margin penalty (true-logit > fall-logit for adv walk/run)** | Directly targets the *geometry* (§2): forces the correct class above fall, not just lowers fall-prob | Could trade more recall; needs a margin hyperparameter | medium | **Best-motivated by §2** if a geometry fix is wanted |
| **D. class-conditional false-alarm cost in the validation score** | Selection-time only, no retraining | §5 shows it does not change the pick — won't help here | low | **Not supported** (see §5) |
| **E. binary fall-alert auxiliary head** | Decouples the alert from 7-class argmax; could calibrate directly | Largest redesign; new failure modes; may not address the adversarial geometry | high | Premature on n=1 |

The current form (A) is adequate as a first mitigation. If, after replication, a *geometry* fix is
pursued, **(C) margin penalty** is the best-motivated next form (it attacks the residual
high-confidence inversion that (A) leaves behind).

## 5. Checkpoint-selection diagnosis (rescore from saved validation logs)

*(`e2_validation_rescore.csv`)* Re-selecting the E2 (λ=1.0) checkpoint from the per-epoch
validation log under alternative rules:

| Rule | Selected epoch | Saved? | val PGD recall | val PGD FP |
|---|---|---|---|---|
| current safety (W=0.10) | 56 | **safety (saved)** | 0.386 | 101 |
| stronger FP penalty (W=0.30) | 56 | safety (saved) | 0.386 | 101 |
| stronger FP penalty (W=0.50) | 56 | safety (saved) | 0.386 | 101 |
| cost FN×10 + FP | 56 | safety (saved) | 0.386 | 101 |
| max recall s.t. val FP≤80 | 58 | no test metrics | 0.250 | 79 |
| cost FN×5 + FP | 70 | no test metrics | 0.250 | 60 |
| cost FN×2 + FP | 66 | macro-F1 (saved) | 0.000 | 13 |

**The safety score is not "too recall-heavy" in a fixable way.** Epoch 56 (the saved safety
checkpoint) wins under the current score, under *stronger* false-alarm penalties, and under
FN-weighted cost — it dominates because its recall is high enough to offset its false alarms. Only
rules that weight false alarms very heavily pick a different epoch, and those (58, 70) are
**not saved** (no test metrics) and have lower recall, or (66) collapse recall to zero.
**Conclusion: no existing checkpoint gives a better operating point than the selected E2 safety
checkpoint; rescoring (Option D) will not help.**

## 6. Epsilon-sweep behaviour (D safety vs E λ=1.0 safety; test)

*(`sweep_frontier_D_vs_E.csv`)*

- **E reduces false alarms at *every* epsilon, not only at 0.030** (PGD ΔFP ranges −24 to −62
  across the sweep; clean ε=0: 14 vs 38). The effect is systemic, not a single-point artifact.
- **E loses some recall at fixed epsilon** (PGD Δrecall −0.02 to −0.16), modest at low ε.
- **At matched recall, E has far fewer false alarms** — e.g. at recall ≈0.89: E ≈30 FP (ε≈0.0075)
  vs D ≈119 FP (ε≈0.0175); at recall ≈0.60: E 103 vs D ≈150. So **E improves the recall/false-alarm
  frontier**, it does not merely slide along D's curve.
- **Collapse ε unchanged** (first ε with recall<0.50 = 0.030 for both). FGSM sweep shows the same
  lower-FP-everywhere pattern (and E is slightly *more* robust than D at very high FGSM ε).

This is the strongest single piece of evidence that E λ=1.0 is a genuine improvement rather than a
lucky operating point.

## 7. Desired operating point for the next defense (experiment-design targets, not clinical)

- PGD@0.030 fall recall **meaningfully above** the FGSM defense (≥ ~0.20; bar = 0.089).
- PGD false alarms **< Variant D** (< 157).
- walk/run → fall false alarms **< Variant D** (< 120).
- Clean fall recall **≥ 0.95**.
- Clean accuracy / macro-F1 **not collapsed** (≥ guard; ideally ≥ Variant D).
- Ideally **specificity or binary-F1 improved** vs Variant D.

**E λ=1.0 safety already meets all of these except binary-F1** (which is equal to D, with
specificity improved instead): recall 0.356, PGD FP 117, walk/run 80, clean fr 0.978, clean acc
0.806 / macro-F1 0.790, specificity 0.743. So the seed-42 operating point is **good enough to be
worth confirming.**

## 8. Candidate next experiments

| Option | Verdict | Why |
|---|---|---|
| **A. Replicate E λ=1.0 on seed 43** | **Recommended** | E2 meets the target on seed 42 and improves the whole-sweep frontier; the one missing thing is replication. Cheap (~25 min train + eval), and it gates everything else. |
| B. λ refinement (0.75, 1.25) on seed 42 | Defer | §3: 1.0 is a clear interior optimum; small expected gain; still single-seed. |
| C. Margin-based penalty on seed 42 | Defer (strong fallback) | §2/§4: best-motivated *geometry* fix for the residual high-conf FAs — but a bigger redesign, better justified after confirming A. |
| D. False-alarm-constrained re-selection | **Rejected** | §5: rescoring does not beat the existing E2 safety checkpoint. |
| E. Binary fall-alert auxiliary head | Defer | §4: largest redesign; premature on n=1; may not fix the adversarial geometry. |
| F. Continue seeds without redesign | Lower priority | The defense now has a candidate recipe (E λ=1.0); confirming *that* recipe (A) is more informative than adding Variant D seeds. |

## 9. Recommendation

**Replicate Variant E λ=1.0 on seed 43 (Option A).** Evidence: (i) E λ=1.0 meets the desired
operating point on seed 42 (§1, §7); (ii) it improves the recall/false-alarm frontier across the
*entire* epsilon sweep with unchanged collapse ε (§6) — a systemic, not point, improvement; (iii)
rescoring cannot do better (§5) and λ-refinement has low expected payoff (§3), so further seed-42
design tuning risks overfitting one seed; (iv) the single open weakness (residual high-confidence
motion false alarms, §2) is a *geometry* problem whose fix (margin penalty, Option C) is a larger
redesign that should only be undertaken if the cheaper, current recipe first proves it replicates.
A seed-43 replication is the lowest-cost, highest-information next step: if the frontier gain
replicates, proceed to multi-seed (E λ=1.0); if it does not, revisit Option C (margin) before any
multi-seed commitment.

## 10. Exact next prompt

```
Replicate Variant E (motion hard-negative, lambda_motion = 1.0) on seed 43 only.

Constraints:
- Seed 43 only. Do NOT run seeds 44-46. Do NOT modify the frozen Variant D protocol/results or
  the existing seed-42 Variant E artifacts. New outputs only, under the existing Variant E
  namespace (results/.../variantE_motion_hard_negative/seed43/ and
  checkpoints/.../variantE_motion_hard_negative/seed43/).
- Use the committed scripts unchanged: train_variantE_motion_hard_negative.py --lambda-motion 1.0
  --seed 43 --epochs 70 --patience 15 --min-epochs 35; then run_converged_attacks.py (single-eps
  0.030 + 18-eps FGSM/PGD sweeps) and export_probability_predictions.py for both selected
  checkpoints; then analyze with a seed-43 analysis.
- LeNet only, same UT-HAR/SenseFi split, same eval protocol (PGD steps=10, alpha=eps/6).
- Report E lambda=1.0 seed-43 vs frozen Variant D seed-43 and the existing FGSM defense seed-43:
  PGD fall recall, total PGD false alarms, walk/run->fall false alarms, clean accuracy, clean
  macro-F1, clean fall recall, PGD specificity/precision/binary-F1, collapse epsilon, and the
  epsilon-sweep recall/false-alarm frontier. State explicitly whether the seed-42 result
  (walk/run FA -33%, total FA -25%, clean acc up, recall ~4x FGSM defense, better matched-recall
  frontier) replicates on seed 43.
- Honest trade-off framing; no solved/certified/clinical/over-the-air claims. Do not edit thesis
  .tex. Do not commit until I approve.
```
