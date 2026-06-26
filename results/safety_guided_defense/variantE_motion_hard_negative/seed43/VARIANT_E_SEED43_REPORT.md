# Variant E (motion hard-negative, λ=1.0) — seed-43 replication report

> **Scope:** seed 43 only, λ=1.0 only, LeNet only, same UT-HAR/SenseFi split. New outputs in
> the seed-43 Variant E namespace; the frozen Variant D protocol/results and the seed-42 Variant E
> artifacts were not modified. No hyperparameter search, no λ=0.5/2.0, no seeds 44–46, no thesis
> `.tex` edits. Window-level, digital-domain, white-box; not solved/certified/clinical/over-the-air.
> All numbers test n=500, ε=0.030 unless noted.

**Headline:** The seed-42 result **replicates partially and with weaker magnitude.** The *core
mechanism* holds — Variant E λ=1.0 reduces total and walk/run false alarms vs Variant D, keeps PGD
recall far above the FGSM defense, improves the matched-recall frontier across the epsilon sweep,
and leaves residual motion false alarms high-confidence. But on seed 43 the false-alarm reduction
is much smaller (~6% total / ~9% walk-run vs ~25% / ~33% on seed 42), and the **clean-accuracy
improvement did NOT replicate — it reversed** (clean acc and macro-F1 dropped vs Variant D). The
safety-selected operating point is seed-sensitive (recall-heavy selection landed on a different
epoch).

## Commands run

```
python scripts/train_variantE_motion_hard_negative.py --lambda-motion 1.0 --seed 43 \
    --epochs 70 --patience 15 --min-epochs 35
# both selected checkpoints (bySafetyScore, byValMacroF1):
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet --epsilon 0.03 \
    --attacks both --run-name E_lam1p0_<sel> --results-dir <seed43>/test_eval
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet --attacks both \
    --epsilon-sweep --run-name E_lam1p0_<sel> --results-dir <seed43>/test_eval
python scripts/export_probability_predictions.py --checkpoint <ckpt> --model lenet --epsilon 0.03 \
    --run-name E_lam1p0_<sel> --out-dir <seed43>/test_eval --split test
python scripts/analyze_variantE_seed.py --seed 43
```
Runtime (CPU): training 1188 s (35 epochs, best safety epoch 18); eval ~20 min.
(`analyze_variantE_seed.py` is a new seed-parametric sibling that reuses `analyze_variantE.py`'s
tested helpers; the committed `analyze_variantE.py` — hard-coded to seed 42 — was not modified.)

## Results (test, ε=0.030)

| Model / selection | Clean acc | Clean macro-F1 | Clean fall recall | **PGD recall** | PGD FP | walk+run→fall | PGD precision | PGD specificity | PGD binary-F1 | Missed | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Existing FGSM defense | 0.902 | 0.901 | 0.956 | 0.022 | 35 | 26 | 0.028 | 0.923 | 0.025 | 44 | 0.018 |
| **Variant D safety-guided** | 0.720 | 0.676 | 1.000 | 0.289 | 160 | 119 | 0.075 | 0.648 | 0.119 | 32 | 0.030 |
| Variant D macro-F1 | 0.794 | — | 0.956 | 0.111 | 77 | 57 | 0.061 | 0.831 | 0.079 | 40 | 0.018 |
| **E λ=1.0 safety-guided** | 0.630 | 0.600 | 0.978 | **0.378** | **151** | **108** | 0.101 | 0.668 | 0.160 | 28 | 0.030 |
| E λ=1.0 macro-F1 | 0.792 | 0.778 | 0.889 | 0.022 | 38 | 21 | 0.026 | 0.916 | 0.024 | 44 | 0.018 |

## The 7 required answers

**1. Did the seed-42 result replicate on seed 43?** **Partially.** The qualitative direction
replicates (E reduces total + walk/run false alarms vs D, keeps recall ≫ FGSM defense, improves the
matched-recall frontier, residual FAs stay high-confidence). The *magnitude* is much weaker, and
the clean-accuracy gain reversed (§5). So this is a qualified, not clean, replication.

**2. Did Variant E reduce total false alarms vs Variant D?** **Yes, but marginally:** 160 → 151
(−5.6%), versus −25% on seed 42. Across the epsilon sweep E has lower PGD false alarms at every ε
(ΔFP −2 to −20), again smaller than seed 42's −24 to −62.

**3. Did Variant E reduce walk/run → fall false alarms vs Variant D?** **Yes, but marginally:**
119 → 108 (−9.2%), versus −33% on seed 42.

**4. Did Variant E keep PGD recall meaningfully above the FGSM defense?** **Yes, clearly:** 0.378 vs
the FGSM defense's 0.022 (~17×). Notably, on seed 43 E's recall is *higher* than Variant D's (0.289)
— the opposite of seed 42, where E traded recall down.

**5. Did clean accuracy / macro-F1 improve or degrade vs Variant D?** **Degraded** — clean accuracy
0.630 vs 0.720 (−0.09) and clean macro-F1 0.600 vs 0.676 (−0.08). This is the **opposite of seed 42**
(where E improved both). Both still clear the clean-collapse guard, but only modestly. This is the
clearest non-replication.

**6. Did residual false alarms remain high-confidence?** **Yes — replicated.** For E λ=1.0 safety,
residual walk/run false alarms have median fall-probability ≈ 0.71 (walk) / 0.75 (run) while true
falls sit at ≈ 0.26. The inverted geometry persists, so thresholding still would not separate them.
Variant E remains a partial mitigation, not a geometry fix — consistent with seed 42.

**7. Does this support Variant E λ=1.0 as the better recipe for broader confirmation?**
**Qualified yes, with an important caveat.** On seed 43, E λ=1.0 safety is actually **Pareto-better
than Variant D on every attacked metric** (recall 0.378>0.289, FP 151<160, missed 28<32, binary-F1
0.160>0.119, specificity 0.668>0.648) — a genuinely better attacked operating point — but at a
clean-accuracy cost (0.630 vs 0.720). Combined with seed 42 (where E improved clean accuracy and cut
false alarms but traded recall down), the *consistent* story is: **E λ=1.0 improves the attacked
recall/false-alarm trade-off vs Variant D on both seeds**, but *how* it spends the gain (recall vs
false alarms vs clean accuracy) is **seed-sensitive**, driven by which epoch the recall-heavy safety
score selects. This supports E λ=1.0 as a promising direction but does **not** yet establish it as a
reliably *uniformly* better recipe.

## Seed 42 vs seed 43 (E λ=1.0 safety vs Variant D safety; test, ε=0.030)

| Effect | Seed 42 | Seed 43 | Replicated? |
|---|---|---|---|
| PGD recall (E vs D) | 0.356 vs 0.444 (down) | 0.378 vs 0.289 (**up**) | direction differs |
| Total PGD FP (E vs D) | 117 vs 157 (−25%) | 151 vs 160 (−6%) | direction yes, magnitude weak |
| walk/run→fall (E vs D) | 80 vs 120 (−33%) | 108 vs 119 (−9%) | direction yes, magnitude weak |
| Clean accuracy (E vs D) | 0.806 vs 0.746 (**up**) | 0.630 vs 0.720 (**down**) | **no — reversed** |
| Clean macro-F1 (E vs D) | 0.790 vs 0.700 (up) | 0.600 vs 0.676 (down) | no — reversed |
| PGD binary-F1 (E vs D) | 0.180 = 0.180 | 0.160 vs 0.119 (up) | E ≥ D both |
| Residual FAs high-conf | yes | yes | **yes** |
| Matched-recall frontier (E better) | yes | yes (smaller margin) | **yes** |
| PGD collapse ε | 0.030 = 0.030 | 0.030 = 0.030 | **yes** |

## Interpretation and recommendation

What replicates robustly: **E λ=1.0 improves the attacked recall/false-alarm frontier vs Variant D
and keeps recall far above the FGSM defense, with unchanged collapse ε and persistent
high-confidence residual motion false alarms.** What does not replicate: the *magnitude* of
false-alarm reduction and, importantly, the *clean-accuracy* effect (improved on seed 42, degraded
on seed 43). The divergence traces to the recall-heavy safety score selecting different epochs per
seed (seed 43 chose an early high-recall epoch 18).

**Recommendation:** do **not** yet promote E λ=1.0 to a multi-seed claim on this evidence. Two
seeds show a consistent *direction* but inconsistent *operating point* and a reversed clean-accuracy
effect. The next most informative step is to address the **selection sensitivity** that is causing
the heterogeneity — i.e. revisit a false-alarm-constrained / cost-sensitive checkpoint-selection
score (evaluated per seed on saved validation logs) so the operating point is comparable across
seeds — before committing to seeds 44–46. Alternatively, run one more seed (e.g. seed 44) purely to
characterize variance. Either way, report the trade-off honestly: E λ=1.0 is a promising but
seed-sensitive improvement, not a settled better recipe.

## Limitations

- Two seeds (42, 43); heterogeneous operating points; not a multi-seed claim.
- Clean-accuracy effect is inconsistent across seeds.
- Residual motion false alarms remain high-confidence (geometry unsolved).
- Window-level, digital-domain, white-box only; no clinical/over-the-air/certified claims.
