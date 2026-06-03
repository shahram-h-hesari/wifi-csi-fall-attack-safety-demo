# Thesis Table 3: Defense Tradeoff Table

This table summarizes the tradeoff between the undefended baseline and the first short 5-epoch FGSM adversarial-training defense using window-level fall-vs-non-fall safety-proxy metrics.

The table compares clean, FGSM-attacked, and PGD-attacked conditions.

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Table

| Comparison | Epsilon | False Alarm Reduction | Recall Recovery | Missed Fall Rate Change | F1-Score Change | Balanced Accuracy Change |
|---|---:|---:|---:|---:|---:|---:|
| Clean: defended vs undefended | 0.000 | 10 | -0.2360 | 0.2360 | -0.1507 | -0.1125 |
| FGSM epsilon 0.030: defended vs undefended | 0.030 | 47 | 0.0000 | 0.0000 | 0.0000 | 0.0259 |
| PGD epsilon 0.030: defended vs undefended | 0.030 | 59 | 0.0000 | 0.0000 | 0.0000 | 0.0325 |

## Interpretation

The defended model reduced false fall alarms compared with the undefended model in all three comparisons. Under FGSM attack, false fall alarms decreased from 119 to 72. Under PGD attack, false fall alarms decreased from 115 to 56.

However, the defense did not recover fall recall under the attacked conditions at epsilon 0.030. Both defended FGSM and defended PGD still had recall/sensitivity of 0.0000 and missed fall rate of 1.0000. This suggests that the first short 5-epoch FGSM adversarial-training defense reduced alarm burden but did not solve the missed-fall safety-proxy failure under attack.

For the clean condition, the defended model reduced false fall alarms but also reduced fall recall and F1-score compared with the undefended clean baseline. This shows a clean-performance tradeoff that should be evaluated carefully before interpreting the defense as beneficial.

## Output Files

- `results/thesis_table_3_defense_tradeoff.csv`
- `notes/thesis_table_3_defense_tradeoff.md`
- Input: `results/defended_vs_undefended_safety_comparison.csv`
