# Thesis-Ready Summary — Priority 1 Multi-Seed Reliability

Packaging of the completed Priority 1 multi-seed reliability study for thesis
writing. No new experiments: every number below is read from the committed
aggregate CSVs (commit `3200a89`). All metrics are **window-level safety-proxy
metrics** computed on **digital-domain, processed-tensor** FGSM/PGD
perturbations against a **software-only FGSM adversarial-training defense
baseline**. No clinical, physical-layer/over-the-air, or certified-robustness
claims are made.

---

## 1. Headline result

Across **5 independent training seeds (42–46)** on the UT-HAR/SenseFi LeNet
pipeline, the adversarial safety-proxy collapse is **reproducible, not a
single-seed artifact**:

- Clean window-level fall recall is high and tight: **0.978 ± 0.016** (mean ± SD).
- Undefended **PGD at ε = 0.030 drives fall recall to exactly 0.000 in all 5
  seeds** (SD = 0); undefended FGSM to **0.049 ± 0.046**.
- FGSM adversarial training gives **partial, attack-specific recovery** that
  **mitigates but does not solve** the failure: defended FGSM recall recovers to
  **0.498 ± 0.135**, but defended PGD recall reaches only **0.084 ± 0.060**
  while PGD false-fall alarms remain high (**50.6 ± 14.4** of 455 non-fall
  windows).
- PGD collapses at a **lower perturbation budget** than FGSM and does so in
  every seed.

This directly answers the committee's statistical-strength objection: the
result does not depend on a single seed or the n = 45 fall-window draw.

---

## 2. Results — fall/non-fall safety proxies (mean ± SD, n = 5 seeds)

Test split: n = 500 windows (fall = 45, non-fall = 455).

| Condition | Fall recall | Missed-fall rate | False-fall alarms (of 455) | Macro-F1 |
|---|---|---|---|---|
| Clean (undefended) | 0.978 ± 0.016 | 0.022 ± 0.016 | 0.8 ± 0.4 | 0.955 ± 0.009 |
| FGSM ε=0.030 (undefended) | 0.049 ± 0.046 | 0.951 ± 0.046 | 57.8 ± 10.3 | 0.043 ± 0.026 |
| PGD ε=0.030 (undefended) | 0.000 ± 0.000 | 1.000 ± 0.000 | 58.4 ± 6.3 | 0.000 ± 0.000 |
| FGSM-AT defended — clean | 0.956 ± 0.035 | 0.044 ± 0.035 | 4.4 ± 3.9 | 0.875 ± 0.040 |
| FGSM-AT defended — FGSM ε=0.030 | 0.498 ± 0.135 | 0.502 ± 0.135 | 26.4 ± 12.4 | 0.442 ± 0.020 |
| FGSM-AT defended — PGD ε=0.030 | 0.084 ± 0.060 | 0.916 ± 0.060 | 50.6 ± 14.4 | 0.210 ± 0.041 |

95% confidence intervals for fall recall (Student-t, df = 4; bootstrap in
brackets):

- Clean: [0.958, 0.997] (boot [0.964, 0.991])
- Undefended FGSM ε=0.030: [-0.008, 0.105] (boot [0.013, 0.084])
- Undefended PGD ε=0.030: [0.000, 0.000] (boot [0.000, 0.000])
- Defended clean: [0.912, 0.999] (boot [0.929, 0.982])
- Defended FGSM ε=0.030: [0.330, 0.665] (boot [0.382, 0.596])
- Defended PGD ε=0.030: [0.010, 0.158] (boot [0.040, 0.133])

(The undefended-FGSM lower CI bound is slightly negative purely as an artifact
of the symmetric normal-t interval at a near-zero mean; recall is bounded at 0.)

---

## 3. Collapse thresholds (smallest ε meeting each criterion; mean ± SD)

| Attack | ε: recall drop ≥ 0.10 | ε: recall < 0.50 | ε: recall = 0 |
|---|---|---|---|
| FGSM | 0.0050 ± 0.0000 | 0.0070 ± 0.0011 | 0.0367 ± 0.0340 † |
| PGD  | 0.0045 ± 0.0011 | 0.0060 ± 0.0014 | 0.0125 ± 0.0031 |

† **Caveat:** undefended FGSM fall recall reached *exactly* 0 within the ε-grid
for only 3/5 seeds (seeds 42, 43, 45); for seeds 44 and 46 it bottomed out near
0.067 without hitting 0, so the FGSM "recall = 0" threshold is averaged over 3
seeds (hence the large SD). Undefended PGD reaches exactly 0 in **all 5** seeds.
Both attacks already cause a ≥ 0.10 recall drop by ε = 0.005 and fall below 0.50
recall by ε ≈ 0.006–0.007 in every seed.

---

## 4. LaTeX-ready figure caption (fall-recall-vs-ε)

Figure file: `figures/multiseed_robustness/multiseed_fall_recall_vs_epsilon.png`
(standalone copy of the caption in `tables/chapter_multiseed_figure_caption.tex`).

```latex
\caption[Multi-seed fall recall vs.\ perturbation budget]{%
  Window-level fall recall versus $L_\infty$ perturbation budget $\varepsilon$
  for undefended FGSM and PGD attacks on the UT-HAR/SenseFi LeNet classifier,
  aggregated over five independent training seeds (42--46). Solid lines are the
  per-$\varepsilon$ mean across seeds; shaded bands are 95\% confidence
  intervals (Student-$t$, $df=4$). Perturbations are digital-domain,
  processed-tensor perturbations on the held-out test split ($n=500$ windows,
  $45$ fall windows); they are not physical-layer or over-the-air attacks.
  Clean fall recall ($\varepsilon=0$) is $0.978\pm0.016$; PGD drives recall to
  $0.000$ in every seed by $\varepsilon\approx0.0125$, and FGSM to near zero by
  $\varepsilon\approx0.037$.}
\label{fig:multiseed-fall-recall-vs-epsilon}
```

---

## 5. Short thesis paragraph

> To test whether the observed adversarial safety-proxy collapse is a stable
> property of the classifier rather than an artifact of a single training run,
> the converged UT-HAR/SenseFi LeNet pipeline was retrained and re-evaluated
> under five independent random seeds (42--46), holding the data split, model
> architecture, attacks, and defense fixed. Clean window-level fall recall was
> high and consistent across seeds ($0.978 \pm 0.016$, mean $\pm$ SD), but
> remained extremely fragile: an undefended projected gradient descent (PGD)
> attack at $\varepsilon = 0.030$ reduced fall recall to exactly $0.000$ in
> every seed, and a single-step FGSM attack reduced it to $0.049 \pm 0.046$,
> while both attacks simultaneously inflated false-fall alarms from $0.8$ to
> roughly $58$ of $455$ non-fall windows. A software-only FGSM
> adversarial-training defense produced only partial, attack-specific recovery:
> defended fall recall under matched-attack FGSM rose to $0.498 \pm 0.135$, but
> under the stronger PGD attack it recovered only to $0.084 \pm 0.060$ while
> PGD false-fall alarms stayed high ($50.6 \pm 14.4$). The defense therefore
> mitigates but does not solve the safety-proxy failure, and no certified
> robustness is claimed. The consistency of these effects across seeds---
> including a zero-variance PGD recall collapse---indicates that the
> vulnerability is reproducible and not attributable to a single-seed or
> single-draw artifact of the $45$-window fall set. All quantities are
> window-level safety-proxy metrics computed on digital-domain, processed-tensor
> perturbations, not clinical, physical-layer, or over-the-air measurements.

---

## 6. Reproducibility checklist

| Item | Value |
|---|---|
| **Seeds used** | 42, 43, 44, 45, 46 (5 independent runs) |
| **Dataset / model** | UT-HAR (SenseFi), 7-class; `UT_HAR_LeNet`; fall = class index 1 |
| **Input** | Processed CSI tensors `(N, 1, 250, 90)`, SenseFi min-max normalized |
| **Test split size** | n = 500 windows (held-out test; never used for selection) |
| **Fall windows** | 45 fall / 455 non-fall in the test split |
| **Epsilon grid (sweep)** | 18 points: 0.0, 0.0025, 0.005, 0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020, 0.025, 0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060, 0.075 |
| **Matched epsilon** | 0.030 (headline table) |
| **FGSM settings** | Single-step, $L_\infty$, sign-gradient; no $[0,1]$ clamp (processed tensors) |
| **PGD settings** | $L_\infty$, 10 steps, step size $\alpha = \varepsilon/6$ (= 0.005 at ε=0.03), projected each step; no clamp |
| **Clean training** | Adam lr 1e-3, batch 64, max 200 epochs, early-stop patience 20, checkpoint by val macro-F1 (test never used for selection) |
| **Defense settings** | FGSM adversarial training, train-ε = 0.030, mixed loss 0.5·clean + 0.5·adv, Adam lr 1e-3, batch 64, max 200 epochs, patience 20; selection score = 0.5·val_clean_macroF1 + 0.5·val_FGSM_macroF1 |
| **Collapse-threshold definition** | Smallest ε (ascending grid) where: (a) clean_recall − recall ≥ 0.10; (b) recall < 0.50; (c) recall = 0.0. Clean reference = ε=0 sweep row. |
| **Mean/SD/CI method** | Across the 5 seed-level values: mean; sample SD (ddof=1); SEM = SD/√5; 95% CI via Student-t ($t_{0.975,4}=2.776$); plus 95% bootstrap percentile CI (1000 resamples of the 5 seed values, `numpy.random.default_rng(12345)`, 2.5/97.5 percentiles). MCC / Cohen's κ / balanced accuracy recomputed from per-window prediction CSVs. |
| **Missing inputs** | 0 (`multiseed_missing_inputs.csv` is header-only) |

### Exact source CSV filenames

Aggregate (committed, `results/multiseed_robustness/`):
- `multiseed_condition_metrics.csv` — 30 rows (5 seeds × 6 conditions), per-seed metrics
- `multiseed_summary_stats.csv` — mean/SD/SEM/95%-CI/bootstrap per (condition × metric)
- `multiseed_collapse_thresholds.csv` — per-seed thresholds + mean/SD rows
- `multiseed_missing_inputs.csv` — header-only (0 missing)
- figure: `figures/multiseed_robustness/multiseed_fall_recall_vs_epsilon.png`

Per-seed sources (`{S}` ∈ {42,43,44,45,46}):
- Clean: `results/converged_baseline/converged_seed{S}_fall_binary_metrics.csv`, `_summary_metrics.csv`, `_per_class_metrics.csv`, `_test_predictions.csv`
- Undefended matched ε=0.03: `results/converged_attacks/converged_seed{S}_{fgsm,pgd}_safety_metrics_test_epsilon_0_03.csv` (+ `_predictions_test_epsilon_0_03.csv`)
- Undefended sweep: `results/converged_attacks/converged_seed{S}_{fgsm,pgd}_epsilon_sweep_test.csv`
- Defended clean: `results/converged_defense/defended_fgsm_at_seed{S}_clean_metrics_test.csv`
- Defended matched ε=0.03: `results/converged_attacks/defended_fgsm_at_seed{S}_{fgsm,pgd}_safety_metrics_test_epsilon_0_03.csv`
- Defended sweep: `results/converged_attacks/defended_fgsm_at_seed{S}_{fgsm,pgd}_epsilon_sweep_test.csv`

### Commit hashes (branch `feature/converged-clean-baseline`)
- Final aggregate + figure + runtime log: **`3200a89`**
- Per-seed results: seed 43 `7dc8fe0`, seed 44 `6057696`, seed 45 `882adc0`, seed 46 `5f94267`
- Multi-seed wiring scripts: `d200491`
- Pipeline scripts: `scripts/run_multiseed_converged_pipeline.py`, `scripts/summarize_multiseed_robustness.py`
- Runtime timings: see `notes/multiseed_runtime_log.md`

### Regeneration command
```powershell
python scripts/summarize_multiseed_robustness.py --allow-missing --seeds 42 43 44 45 46
```
