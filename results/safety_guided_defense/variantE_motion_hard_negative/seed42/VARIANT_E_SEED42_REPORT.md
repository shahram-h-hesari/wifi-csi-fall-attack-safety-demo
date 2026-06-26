# Variant E (motion-class hard-negative defense) — seed-42 pilot report

> **Scope:** seed 42 only, LeNet only, same UT-HAR/SenseFi split. A NEW variant in its
> own namespace; the frozen Variant D protocol, script, and results were not modified, and
> no seed-42/seed-43 artifacts were overwritten. No thesis `.tex` edits. Seeds 43–46 not run.
> Window-level, digital-domain, white-box; **not** solved/certified robustness, not clinical,
> not over-the-air. All numbers test n=500, ε=0.030 unless noted.

## Objective (exact)

Variant E = the frozen Variant D recipe (FGSM+PGD multi-ε {0.005,0.015,0.030} adversarial
training, fall-weighted CE, safety-guided checkpoint selection + clean-collapse guard, macro-F1
selection kept as comparison) **plus a motion-class hard-negative penalty**. Per training batch:

```
loss = fall_weighted_CE(outputs, labels)                              # Variant D term
     + lambda_motion * mean( softmax(outputs_adv_motion)[:, fall] )    # Variant E term
```

where `outputs_adv_motion` are the outputs for the **adversarial** sub-batch samples whose true
label is **walk (2)** or **run (4)**. The penalty is the mean fall-class **probability** assigned
to adversarial walk/run windows; minimizing it pushes the model to stop calling adversarial
motion windows "fall". Chosen over a logit-margin form because it directly targets the diagnosed
failure (high fall-probability on adversarial walk/run), is bounded in [0,1] (stable across
λ/batches), and needs no reference logit. The adversary that generates perturbations is unchanged
(untargeted, unweighted CE); only the defender's training loss gains the term. Pilots: E1 λ=0.5,
E2 λ=1.0, E3 λ=2.0.

## Commands run

```bash
for lam in 0.5 1.0 2.0; do
  python scripts/train_variantE_motion_hard_negative.py --lambda-motion $lam --seed 42 \
      --epochs 70 --patience 15 --min-epochs 35
done
# per checkpoint (bySafetyScore, byValMacroF1):
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet --epsilon 0.03 \
    --attacks both --run-name E_lam<X>_<sel> --results-dir <variantE>/test_eval
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet --attacks both \
    --epsilon-sweep --run-name E_lam<X>_<sel> --results-dir <variantE>/test_eval
python scripts/export_probability_predictions.py --checkpoint <ckpt> --model lenet --epsilon 0.03 \
    --run-name E_lam<X>_<sel> --out-dir <variantE>/test_eval --split test
python scripts/analyze_variantE.py
```

## Runtime (CPU)

Training: E1 1177 s (35 ep), E2 ~2340 s (70 ep), E3 2062 s (64 ep) ≈ 1.55 h total.
Eval (6 checkpoints × single-ε + two 18-ε sweeps + probability export): ~59 min.

## Files created

New scripts: `scripts/train_variantE_motion_hard_negative.py`, `scripts/analyze_variantE.py`.
Under `results/safety_guided_defense/variantE_motion_hard_negative/seed42/`: `VARIANT_E_SEED42_REPORT.md`,
`variantE_seed42_comparison.csv`, `analysis/{false_alarm_class_sources,binary_alert_metrics,probability_diagnosis}.csv`,
`figures/{fig_recall_vs_false_alarms,fig_walk_run_false_alarm_reduction}.png`, `logs/` (3 training
logs + 3 metadata + console/driver logs), `metadata/`, `test_eval/` (per-checkpoint predictions,
safety metrics, 18-ε sweeps, and per-class probability/logit CSVs).
Checkpoints (local-only, gitignored `*.pt`): `checkpoints/safety_guided_defense/variantE_motion_hard_negative/seed42/` (6 `*_best.pt` + 3 `*_last.pt`).

## Results (test, ε=0.030)

| Model / selection | Clean acc | Clean macro-F1 | Clean fall recall | **PGD fall recall** | PGD FP | walk+run→fall | PGD precision | PGD specificity | PGD binary-F1 | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|---|---|
| Existing FGSM defense | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | 0.069 | 0.881 | 0.078 | 0.018 |
| **Variant D safety-guided** | 0.746 | 0.700 | 1.000 | **0.444** | 157 | 120 | 0.113 | 0.655 | 0.180 | 0.030 |
| Variant D macro-F1 | 0.848 | 0.813 | 0.956 | 0.133 | 79 | 61 | 0.071 | 0.826 | 0.092 | 0.025 |
| E1 λ=0.5 safety | 0.654 | — | 0.911 | 0.089 | 145 | 100 | 0.027 | 0.681 | 0.041 | 0.018 |
| E1 λ=0.5 macro-F1 | 0.800 | — | 0.911 | 0.044 | 51 | 35 | 0.038 | 0.888 | 0.041 | 0.015 |
| **E2 λ=1.0 safety** | **0.806** | **0.790** | 0.978 | **0.356** | **117** | **80** | 0.120 | 0.743 | 0.180 | 0.030 |
| E2 λ=1.0 macro-F1 | 0.836 | — | 0.911 | 0.000 | 20 | 15 | 0.000 | 0.956 | 0.000 | 0.013 |
| E3 λ=2.0 safety | 0.730 | 0.706 | 0.933 | 0.178 | 122 | 88 | 0.062 | 0.732 | 0.091 | 0.025 |
| E3 λ=2.0 macro-F1 | 0.850 | — | 0.956 | 0.067 | 30 | 16 | 0.091 | 0.934 | 0.077 | 0.018 |

## Verdict — does Variant E meet the success criterion?

**Success criterion:** reduce walk/run false alarms vs frozen Variant D while preserving
meaningful PGD fall recall above the existing FGSM defense (need not beat Variant D on raw
recall if the missed-fall/false-alarm operating point is better).

**Yes — for E2 (λ=1.0, safety-guided).** Versus Variant D safety-guided:

- **walk/run → fall false alarms: 120 → 80 (−33%)**; total PGD false alarms 157 → 117 (−25%).
- **PGD fall recall 0.356** — below Variant D's 0.444 but **4× the FGSM defense's 0.089** (meaningful).
- **Clean accuracy 0.806 (+0.06), clean macro-F1 0.790 (+0.09), clean fall recall 0.978** — all
  improved/preserved; no clean collapse.
- **Same robust ε-range** (PGD collapse ε 0.030) and **identical PGD binary-F1 (0.180)** at a
  **better specificity (0.743 vs 0.655)**, for the cost of **4 more missed falls (29 vs 25)**.

So E2 is a **new, lower-false-alarm operating point on the recall/false-alarm frontier**, with
better clean performance — it relocates favorably along the trade-off rather than dominating
Variant D outright.

## λ behaviour and selection

- **λ=0.5 (E1): too weak.** Safety pick barely changes false alarms (145) and drops recall to the
  FGSM-defense level (0.089). Not useful.
- **λ=1.0 (E2): the sweet spot** (above).
- **λ=2.0 (E3): over-penalized.** The safety pick is worse than λ=1.0 (recall 0.178, FP 122) — more
  penalty did not buy more false-alarm reduction at the safety-selected checkpoint.
- **macro-F1-selected Variant E checkpoints drive false alarms very low (20–51) but collapse PGD
  recall to 0.0–0.067 — below the FGSM-defense bar (0.089).** A detector that misses essentially
  all attacked falls is not a valid safety defense, so these do **not** meet the criterion despite
  the low false-alarm counts. (They do show the penalty *can* suppress motion false alarms hard if
  recall is sacrificed.)

## Probability diagnosis — partial mitigation, not a geometry fix

For E2 λ=1.0 safety, the **residual** walk/run false alarms are **still high-confidence**: median
fall-probability ≈ 0.82 (walk) / 0.83 (run), while true falls sit at ≈ 0.26. The inverted
fall-probability geometry from the decision analysis **persists**. The motion penalty therefore
reduced the **number** of walk/run false alarms (and overall fall-bias) but did **not** make the
remaining ones low-confidence. This is consistent with thresholding still being unable to separate
them, and means Variant E is a **partial mitigation**, not a resolution of the underlying
adversarial decision geometry.

## Guardrails / collapse

No degenerate collapse: every reported checkpoint clears the clean-collapse guard. E2 λ=1.0 safety
clean accuracy 0.806 and macro-F1 0.790 are the best clean numbers among the safety-selected
robust checkpoints.

## Limitations

- **Seed 42 only (n=1).** No multi-seed claim; the λ=1.0 advantage must be checked for stability.
- **Not a Pareto improvement** over Variant D: E2 gives up 0.088 PGD recall (4 true falls) for the
  false-alarm/clean gains. Whether that trade is "better" depends on the deployed FN:FP cost.
- Residual motion false alarms remain high-confidence (above).
- Window-level, digital-domain, white-box only; no clinical/over-the-air/certified claims.

## Recommendation

**Variant E with λ=1.0 and safety-guided selection is a promising, better-balanced operating point**
and is the recipe worth confirming. Suggested next step: a **seed-43-only** confirmation of
**E (λ=1.0)** against frozen Variant D (same eval protocol, probability export on), to test whether
the −33% walk/run-false-alarm / +clean-accuracy / recall-0.356 trade replicates before any
multi-seed or any Chapter-6 write-up. Do not run seeds 44–46 or revise the frozen Variant D
protocol until that single-seed replication is reviewed.
