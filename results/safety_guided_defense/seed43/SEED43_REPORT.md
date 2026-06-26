# Seed-43 confirmation report — frozen Variant D safety-guided defense

> **Scope:** seed 43 only. Frozen Variant D protocol, unchanged (FGSM+PGD multi-ε
> adversarial training, fall-weighted loss, safety-guided checkpoint selection with the
> clean-collapse guard; macro-F1 selection kept as the standard-selection comparison).
> No hyperparameter search, no SafetyScore/guard redesign, no thesis `.tex` edits, no
> seed-42 artifacts modified. Window-level, digital-domain, white-box; processed CSI only.
> Seeds 44–46 were **not** run.

## 1. Exact commands run

```bash
# Step 3 — train frozen Variant D, seed 43:
python scripts/train_safety_guided_defense.py --variant D --seed 43 \
    --epochs 70 --patience 15 --min-epochs 35

# Step 4 — for each selected checkpoint (bySafetyScore, byValMacroF1):
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet \
    --epsilon 0.03 --attacks both --run-name variantD_<sel> \
    --results-dir results/safety_guided_defense/seed43/test_eval
python scripts/run_converged_attacks.py --checkpoint <ckpt> --model lenet \
    --attacks both --epsilon-sweep --run-name variantD_<sel> \
    --results-dir results/safety_guided_defense/seed43/test_eval
python scripts/export_probability_predictions.py --checkpoint <ckpt> --model lenet \
    --epsilon 0.03 --run-name variantD_<sel> \
    --out-dir results/safety_guided_defense/seed43/test_eval --split test

# Step 5 — derived comparison table, class-source + binary analysis, figures:
python scripts/analyze_safety_guided_seed.py --seed 43
```

## 2. Runtime notes (CPU-only)

- Training: **1242 s (~21 min)**, 38 epochs (early-stopped; best SafetyScore epoch 23,
  best val macro-F1 epoch 38). Deterministic (seed 43).
- Test-eval (both checkpoints: single-ε + two 18-point sweeps + probability export): **~20 min**.

## 3. Files created

New (seed-43 only; seed-42 untouched):
- Checkpoints (**local-only, gitignored `*.pt`**): `checkpoints/safety_guided_defense/seed43/seed43_variantD_*_{bySafetyScore,byValMacroF1,last}.pt`
- Training log + metadata: `results/safety_guided_defense/seed43/logs/seed43_variantD_*_training_log.csv`, `..._metadata.json`
- Test-eval: `results/safety_guided_defense/seed43/test_eval/` — standard predictions + safety_metrics (single-ε), 18-ε FGSM/PGD sweeps (test + legacy), attack/sweep metadata, **and 6 new probability/logit CSVs** (`variantD_{bySafetyScore,byValMacroF1}_{clean,fgsm,pgd}_probabilities_test_epsilon_0_03.csv`)
- Derived: `results/safety_guided_defense/seed43/seed43_defense_comparison.csv`, `analysis/false_alarm_class_sources.csv`, `analysis/binary_alert_metrics.csv`
- Figures: `results/safety_guided_defense/seed43/figures/fig1_fall_recall_vs_epsilon.png`, `fig2_false_fall_alarms_vs_epsilon.png`, `fig3_clean_fgsm_pgd_bar_summary.png`
- New scripts (logging/analysis only; existing scripts unmodified): `scripts/export_probability_predictions.py`, `scripts/analyze_safety_guided_seed.py`

## 4. Clean / FGSM / PGD metrics (test, n=500, ε=0.030)

| Model / selection | Clean acc | Clean macro-F1 | Clean fall recall | FGSM fall recall | FGSM FP | **PGD fall recall** | PGD FP | FGSM collapse ε | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|---|
| Clean LeNet baseline | 0.978 | — | 0.978 | 0.000 | 68 | 0.000 | 65 | 0.007 | 0.007 |
| **Existing FGSM defense** | 0.902 | — | 0.956 | 0.400 | 12 | **0.022** | 35 | 0.030 | 0.018 |
| **Variant D · safety-guided** | 0.720 | 0.676 | 1.000 | 0.644 | 136 | **0.289** | 160 | 0.035 | 0.030 |
| Variant D · macro-F1 | 0.794 | 0.751 | 0.956 | 0.200 | 57 | 0.111 | 77 | 0.025 | 0.018 |

Binary fall-alert metrics (from `analysis/binary_alert_metrics.csv`), PGD@0.030:
Variant D safety — recall 0.289, precision 0.075, specificity 0.648, FPR(non-fall) 0.352,
binary F1 0.119, missed-fall 32. Variant D macro-F1 — recall 0.111, FPR 0.169, missed-fall 40.

## 5. Did PGD@0.030 fall recall improve over the existing FGSM defense?

**Yes — clearly.** Variant D safety-guided **0.289 vs 0.022** for the seed-43 FGSM defense
(≈13×). Even Variant D macro-F1 (0.111) beats the FGSM defense. FGSM@0.030 fall recall also
improves (0.644 vs 0.400). (Note: the seed-43 FGSM defense is itself weaker under PGD than
seed-42's, 0.022 vs 0.089 — so the gap the safety-guided defense closes is even larger here.)

## 6. Did safety-guided selection beat macro-F1 selection?

**Yes.** On the same frozen Variant D run, PGD@0.030 fall recall is **0.289 (safety) vs 0.111
(macro-F1)**; FGSM recall 0.644 vs 0.200. Macro-F1 selection keeps clean accuracy higher
(0.794 vs 0.720) and false alarms lower (PGD FP 77 vs 160) but gives up most of the robustness.
This reproduces the seed-42 finding that **selection method is the main lever**.

## 7. Are false alarms dominated by walk/run again?

**Yes — same pattern.** Variant D safety-guided, false-fall sources under PGD@0.030 (of 160):
run 67 + walk 52 = **119 (74%)**; lie down 14, sit down 5, pickup 11, stand up 11. The
fall-adjacent static postures (lie down/sit down) remain minor; high-motion classes dominate,
exactly as on seed 42 (where run+walk were 76%). *(`analysis/false_alarm_class_sources.csv`)*

## 8. Did clean fall recall remain acceptable?

**Yes.** Variant D safety-guided clean fall recall = **1.000** (no missed falls on clean test);
macro-F1 selection 0.956. Clean fall recall is preserved/improved, as on seed 42.

## 9. Did clean accuracy / macro-F1 collapse?

**No collapse.** Variant D safety-guided clean accuracy 0.720 and clean macro-F1 0.676 — both
clear the clean-collapse guard (≥0.60 / ≥0.50) and are far from the degenerate always-fall
regime (~0.09). They are lower than the clean baseline (0.978), consistent with the seed-42
clean cost (0.746 / 0.700). The guard again did its job (the un-guarded best is logged in the
training metadata).

## 10. Does the result support continuing to seed 44?

**Yes.** Seed 43 reproduces every qualitative seed-42 conclusion: (i) safety-guided Variant D
beats the FGSM defense on PGD recall, (ii) safety-guided beats macro-F1 selection, (iii) false
alarms are walk/run-dominated, (iv) clean fall recall preserved, (v) no clean collapse, (vi) the
recall gain is bought with a large false-alarm increase. The **magnitude differs** (PGD recall
0.289 vs seed-42's 0.444; FGSM-defense PGD recall 0.022 vs 0.089), which is exactly the seed
variability the multi-seed confirmation is meant to quantify. Recommend proceeding to seed 44
under the same frozen protocol.

### Seed 42 vs seed 43 (Variant D safety-guided, test n=500, ε=0.030)

| Metric | Seed 42 | Seed 43 |
|---|---|---|
| PGD fall recall | 0.444 | 0.289 |
| PGD false-alarms | 157 | 160 |
| FGSM fall recall | 0.778 | 0.644 |
| FGSM false-alarms | 123 | 136 |
| Clean accuracy | 0.746 | 0.720 |
| Clean fall recall | 1.000 | 1.000 |
| PGD collapse ε | 0.030 | 0.030 |
| Walk+run share of PGD false alarms | 76% | 74% |
| FGSM-defense PGD recall (reference) | 0.089 | 0.022 |

*(This is a simple two-seed note, not a multi-seed aggregate or claim.)*

## 11. Missing artifacts / limitations

- **n = 2 seeds** (42, 43). This is not yet a multi-seed claim; seeds 44–46 remain to run.
- Per-class **probabilities/logits are now saved** for seed 43 (the new export), enabling later
  threshold calibration; seed-42 probability CSVs were not generated and would require a
  (no-retrain) re-eval of the existing seed-42 checkpoints if calibration is run across both.
- Clean macro-F1 for the clean baseline / FGSM defense is not shown in the table above (not in
  the existing single-ε comparison CSV); it is available in the per-checkpoint safety_metrics
  CSVs if needed.
- All claims remain window-level, digital-domain, white-box; no clinical, over-the-air, or
  certified-robustness claims.

**Bottom line:** seed 43 confirms the frozen Variant D safety-guided defense reproduces the
seed-42 PGD-recall improvement and the walk/run false-alarm signature, with the same
clean-preservation and the same false-alarm trade-off, at a somewhat smaller magnitude. The
evidence supports continuing the frozen protocol to seed 44.
