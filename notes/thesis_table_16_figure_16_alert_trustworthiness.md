# Thesis Table 16 and Figure 16: Alert Trustworthiness

This note documents the alert-trustworthiness analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 16 and Figure 16 focus on predicted fall alerts.

The key question is:

```text
When the model raises a fall alert, how often is it actually a fall?
```

This is important because aggregate model accuracy does not directly tell a caregiver or reviewer whether fall alerts are trustworthy.

## Files Created

```text
Table 16:
results\thesis_table_16_alert_trustworthiness.csv

Figure 16:
figures\thesis_figure_16_fall_alert_composition.png

Companion note:
notes\thesis_table_16_figure_16_alert_trustworthiness.md
```

## Input Files

```text
results\clean_predictions_short.csv
results\fgsm_predictions_short_epsilon_0_03.csv
results\pgd_predictions_short_epsilon_0_03.csv
results\defended_predictions_short.csv
results\defended_fgsm_predictions_short_epsilon_0_03.csv
results\defended_pgd_predictions_short_epsilon_0_03.csv
```

## Metric Definitions

```text
predicted fall alerts = TP + FP
true fall alerts = TP
false fall alerts = FP
alert precision / PPV = TP / (TP + FP)
false-alert share among alerts = FP / (TP + FP)
missed fall count = FN
```

## Important Figure Interpretation

Figure 16 bars show predicted fall alerts only:

```text
bar height = TP + FP
```

FN is shown above each bar as missed-fall context and is not part of the bar height.

A PPV value of 0.00 with TP = 0 and nonzero FP means the model raised fall alerts, but every predicted fall alert was false. It does not mean that the model raised no alerts.

For the tested defended FGSM and defended PGD conditions, false fall alarms were reduced compared with their matched undefended attack conditions. However, PPV remained 0.00 because TP remained 0.

## Key Findings

- Clean: predicted fall alerts = 89, TP alerts = 57, FP alerts = 32, PPV = 0.640, FP share = 0.360, missed falls = 32.
- FGSM Attack: predicted fall alerts = 119, TP alerts = 0, FP alerts = 119, PPV = 0.000, FP share = 1.000, missed falls = 89.
- PGD Attack: predicted fall alerts = 115, TP alerts = 0, FP alerts = 115, PPV = 0.000, FP share = 1.000, missed falls = 89.
- Defended Clean: predicted fall alerts = 58, TP alerts = 36, FP alerts = 22, PPV = 0.621, FP share = 0.379, missed falls = 53.
- Defended FGSM: predicted fall alerts = 72, TP alerts = 0, FP alerts = 72, PPV = 0.000, FP share = 1.000, missed falls = 89.
- Defended PGD: predicted fall alerts = 56, TP alerts = 0, FP alerts = 56, PPV = 0.000, FP share = 1.000, missed falls = 89.

## Interpretation

This artifact strengthens the thesis because it separates three safety-relevant questions:

```text
Did the system detect real fall windows?
Were the fall alerts trustworthy when raised?
How many true fall windows were missed at the same time?
```

A model can have high or moderate aggregate accuracy while still producing clinically concerning alert behavior. For example, under the tested FGSM and PGD attack conditions, the undefended model produced fall alerts that were all false alarms while also missing all true fall windows.

The defended attacked conditions reduced false fall alarms compared with the matched undefended attacked conditions, but did not restore fall recall under the tested epsilon 0.030 attack setting.

## Claim Boundary

This is a descriptive window-level fall-alert trustworthiness analysis using binary fall-vs-non-fall predictions.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
