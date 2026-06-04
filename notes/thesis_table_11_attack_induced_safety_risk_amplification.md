# Thesis Table 11: Attack-Induced Safety Risk Amplification Ratios

This table translates clean-to-attacked and clean-to-defended changes into window-level safety-risk amplification and retention ratios.

## Claim Boundary

Research implementation only; window-level safety-risk amplification ratios; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Input File

- `results/defended_vs_undefended_safety_comparison.csv`

## Output File

- `results/thesis_table_11_attack_induced_safety_risk_amplification.csv`

## Reference Condition

All ratios are computed relative to the undefended clean baseline.

```text
reference condition = undefended clean
reference missed fall rate = 0.359551
reference false fall alarm count = 32
reference recall/sensitivity = 0.640449
reference F1-score = 0.640449
reference balanced accuracy = 0.802584
```

## Ratio Definitions

```text
missed fall rate ratio = condition missed fall rate / clean missed fall rate
false alarm count ratio = condition false alarm count / clean false alarm count
recall retention = condition recall / clean recall
F1 retention = condition F1-score / clean F1-score
balanced accuracy retention = condition balanced accuracy / clean balanced accuracy
```

## Table Preview

| Condition | Missed Fall Ratio | False Alarm Ratio | Recall Retention | F1 Retention | Balanced Accuracy Retention |
|---|---:|---:|---:|---:|---:|
| Undefended clean reference | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Undefended FGSM epsilon 0.03 | 2.781247 | 3.718750 | 0.000000 | 0.000000 | 0.541251 |
| Undefended PGD epsilon 0.03 | 2.781247 | 3.593750 | 0.000000 | 0.000000 | 0.543998 |
| Defended clean | 1.656249 | 0.687500 | 0.631579 | 0.764770 | 0.859871 |
| Defended FGSM epsilon 0.03 | 2.781247 | 2.250000 | 0.000000 | 0.000000 | 0.573534 |
| Defended PGD epsilon 0.03 | 2.781247 | 1.750000 | 0.000000 | 0.000000 | 0.584523 |

## Interpretation

Table 11 provides a compact way to describe how much safety-relevant risk increases or useful performance is retained relative to the undefended clean baseline.

A missed fall rate ratio above 1.0 means the condition has more missed fall behavior than the clean baseline. A recall, F1, or balanced accuracy retention below 1.0 means the condition retains less of the clean baseline performance.

The attacked conditions show severe missed-fall amplification because the missed fall rate increases from the clean baseline value of 0.359551 to 1.000000 under FGSM and PGD at epsilon 0.030. The defended attacked conditions reduce false fall alarm burden relative to the undefended attacked conditions, but still do not recover fall recall at epsilon 0.030.

These ratios should be interpreted as window-level safety-proxy ratios, not clinical risk ratios, event-level fall rates, or medical-device validation metrics.
