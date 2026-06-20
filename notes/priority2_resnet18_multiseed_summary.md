# Priority 2 — ResNet18 Multi-Seed Summary (Clean-Qualified)

Thesis-ready aggregate for the ResNet18 multi-seed extension of the Priority 2
cross-architecture study. Built **only** from already-committed ResNet18 seed
results (no experiment was rerun; no raw result file was modified).

## Headline
- **4/4 clean-qualified ResNet18 seeds (42, 43, 44, 46) collapsed to zero PGD
  fall recall at ε=0.03** — every one of the 45 fall windows missed in each seed.
- **Seed 45 was non-converged and excluded from clean-qualified
  adversarial-degradation aggregation** (documented in
  `notes/priority2_resnet_seed45_nonconverged.md`).
- This strengthens the architecture-check claim beyond the seed-42 pilot: the
  ResNet18 safety-proxy collapse is not unique to a single seed. It does **not**
  imply full multi-seed cross-architecture reliability for every model family
  (only LeNet has full five-seed evidence, from Priority 1; GRU/BiLSTM/Transformer
  remain seed-42 pilots).

## Convergence status (all 5 seeds)
| Seed | Status | Clean accuracy | Clean fall recall | Best epoch |
|---|---|---|---|---|
| 42 | clean-qualified | 0.942 | 0.978 | 43 |
| 43 | clean-qualified | 0.964 | 0.956 | 21 |
| 44 | clean-qualified | 0.984 | 0.978 | 70 |
| 45 | **non-converged** | 0.294 | **0.000** | 1 |
| 46 | clean-qualified | 0.982 | 0.978 | 44 |

Seed 45 diverged under the fixed protocol (Adam lr 1e-3): val loss rose to ~10¹⁵,
the model became a trivial "walk"-only predictor, and clean fall recall was 0.000
*before* any attack — so its attacked 0.000 fall recall is not adversarial-collapse
evidence. It is retained only as a training-stability observation.

## Clean-qualified aggregate (seeds 42, 43, 44, 46; n = 4)
Test split: n = 500 windows (45 fall / 455 non-fall). Mean ± SD (95% CI, Student-t df=3).

| Condition | Metric | Mean ± SD | 95% CI |
|---|---|---|---|
| Clean | Fall recall | 0.972 ± 0.011 | [0.955, 0.990] |
| Clean | Missed-fall rate | 0.028 ± 0.011 | [0.010, 0.045] |
| Clean | False-fall alarms | 1.25 ± 0.96 | [0, 2.8] |
| Clean | Accuracy | 0.968 ± 0.020 | [0.937, 0.999] |
| Clean | Macro-F1 | 0.949 ± 0.034 | [0.894, 1.000] |
| Clean | MCC | 0.970 ± 0.016 | [0.945, 0.995] |
| FGSM ε=0.03 | Fall recall | 0.011 ± 0.013 | [0, 0.032] |
| FGSM ε=0.03 | False-fall alarms | 31.25 ± 23.34 | [0, 68.4] |
| FGSM ε=0.03 | MCC | −0.059 ± 0.052 | [−0.141, 0.024] |
| **PGD ε=0.03** | **Fall recall** | **0.000 ± 0.000** | **[0.000, 0.000]** |
| PGD ε=0.03 | False-fall alarms | 55.0 ± 36.9 | [0, 113.7] |
| PGD ε=0.03 | MCC | −0.107 ± 0.043 | [−0.175, −0.039] |

(CI lower bounds shown as 0 where the symmetric-t interval goes slightly negative
on a non-negative quantity.)

The defining result: clean fall recall is high and tight (0.972 ± 0.011), yet
**PGD at ε=0.03 drives fall recall to exactly 0.000 in every clean-qualified
seed** (zero variance). FGSM at ε=0.03 is near-total (mean 0.011). False-fall
alarms are inflated but high-variance across seeds (PGD 17–105).

## Collapse thresholds (smallest ε on the grid; clean-qualified seeds)
| Seed | FGSM recall=0 ε | PGD recall=0 ε |
|---|---|---|
| 42 | 0.035 | 0.0075 |
| 43 | 0.0075 | 0.0075 |
| 44 | 0.015 | 0.010 |
| 46 | 0.010 | 0.0075 |
| **mean ± SD** | 0.0169 ± 0.0123 | 0.0081 ± 0.0013 |

PGD reaches zero fall recall by ε ≤ 0.010 in all four seeds (tight; mean ≈ 0.008).

## Generated package files
- `results/cross_architecture/resnet/resnet18_clean_qualified_seedwise_metrics.csv`
- `results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv`
- `results/cross_architecture/resnet/resnet18_clean_qualified_thresholds.csv`
- `results/cross_architecture/resnet/resnet18_seed_convergence_status.csv`
- `results/cross_architecture/resnet/figures/resnet18_clean_qualified_fall_recall_vs_epsilon.png`
- `results/cross_architecture/resnet/figures/resnet18_pgd_false_alarms_at_003_clean_qualified.png`
- `results/cross_architecture/resnet/figures/resnet18_collapse_threshold_distribution.png`
- `tables/chapter_resnet18_multiseed_table.tex`, `tables/chapter_resnet18_multiseed_figure_caption.tex`
- Per-seed raw results: `results/cross_architecture/resnet/resnet18_seed{42..46}_*` (commits 3578136, 5024193, dd3460b, 6db1485, 9cf6172)

## Limitations & wording
- This is a **ResNet18 multi-seed** result over **4 clean-qualified seeds**
  (42, 43, 44, 46) plus **1 non-converged, excluded seed (45)**.
- Do **not** state "5/5 ResNet18 seeds collapsed"; the correct statement is
  "4/4 clean-qualified ResNet18 seeds collapsed to zero PGD fall recall at ε=0.03,
  with seed 45 excluded as non-converged."
- Do **not** claim full multi-seed cross-architecture reliability for all
  architectures (GRU/BiLSTM/Transformer are seed-42 pilots only).
- Do **not** claim clinical unsafe behavior, over-the-air validation, or
  certified robustness. All quantities are window-level safety-proxy metrics on
  digital-domain, processed-tensor perturbations.
