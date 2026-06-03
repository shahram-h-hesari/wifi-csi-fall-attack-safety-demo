# Thesis Table 2: Attack Impact Delta Table

This table compares the clean SenseFi UT-HAR LeNet baseline against the software-level FGSM and PGD attacked conditions using window-level fall-vs-non-fall safety-proxy metrics.

The purpose is to show how adversarial perturbations change safety-relevant proxy metrics such as missed fall rate, recall/sensitivity, F1-score, false fall alarm count, balanced accuracy, and prediction change rate.

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Table

| Comparison | Epsilon | Missed Fall Rate Change | Recall/Sensitivity Change | F1-Score Change | False Alarm Count Change | Balanced Accuracy Change | Prediction Change Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Clean vs FGSM | 0.030 | 0.6404 | -0.6404 | -0.6404 | 87 | -0.3682 | 0.7440 |
| Clean vs PGD | 0.030 | 0.6404 | -0.6404 | -0.6404 | 83 | -0.3660 | 0.7781 |

## Interpretation

At epsilon 0.030, both FGSM and PGD increased the missed fall rate from the clean baseline and reduced recall/sensitivity and F1-score. Both attacks also increased the number of false fall alarms. This table translates attack impact into fall-safety proxy terms instead of relying only on aggregate seven-class accuracy.

## Output Files

- `results/thesis_table_2_attack_impact_delta.csv`
- `notes/thesis_table_2_attack_impact_delta.md`
