# Thesis Table 1: Clean, Attacked, and Defended Fall Safety-Proxy Metrics

This table summarizes the first thesis-ready comparison of clean, attacked, and defended fall-vs-non-fall safety-proxy metrics for the WiFi CSI Fall Attack-Safety Demo.

The table is generated from:

```text
results/defended_vs_undefended_safety_comparison.csv
```

Generated outputs:

```text
results/thesis_table_1_safety_metrics.csv
notes/thesis_table_1_safety_metrics.md
```

---

## Table 1

| Condition | Attack | TP | FN | FP | TN | Missed Fall Rate | Recall | Precision | F1-score | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Undefended clean | none | 57 | 32 | 32 | 875 | 0.3596 | 0.6404 | 0.6404 | 0.6404 | 0.8026 |
| Undefended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 119 | 788 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4344 |
| Undefended PGD, epsilon 0.03 | PGD | 0 | 89 | 115 | 792 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4366 |
| Defended clean | none | 36 | 53 | 22 | 885 | 0.5955 | 0.4045 | 0.6207 | 0.4898 | 0.6901 |
| Defended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 72 | 835 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4603 |
| Defended PGD, epsilon 0.03 | PGD | 0 | 89 | 56 | 851 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4691 |

---

## Suggested Thesis Caption

Table 1. Window-level fall-vs-non-fall safety-proxy metrics for the SenseFi UT-HAR LeNet baseline under clean, FGSM-attacked, PGD-attacked, and short FGSM-adversarial-training defended conditions. The first short defended model reduced false fall alarms under FGSM and PGD attack but did not recover fall recall at epsilon 0.03.

---

## Key Interpretation

The undefended clean model detected 57 of 89 fall windows and missed 32 fall windows.

Both undefended attacks at epsilon 0.03 caused complete fall-recall loss:

```text
undefended FGSM: TP = 0, FN = 89
undefended PGD:  TP = 0, FN = 89
```

The short FGSM-adversarial-training defended model also had complete fall-recall loss under FGSM and PGD attack at epsilon 0.03:

```text
defended FGSM: TP = 0, FN = 89
defended PGD:  TP = 0, FN = 89
```

However, the defended model reduced false fall alarms under attack:

```text
FGSM false fall alarms: 119 -> 72
PGD false fall alarms:  115 -> 56
```

This supports a careful conclusion: the first short defense baseline reduced false alarm burden under attack but did not restore fall sensitivity.

---

## Claim Boundary

This table is a window-level software comparison on processed CSI tensors.

It is not:

```text
clinical validation
medical-device validation
diagnostic evidence
regulatory evaluation
real patient deployment evidence
event-level fall validation
long-lie validation
time-to-detection validation
physical-layer attack validation
physical-layer defense validation
packet-level validation
preamble-level validation
SDR validation
over-the-air validation
```
