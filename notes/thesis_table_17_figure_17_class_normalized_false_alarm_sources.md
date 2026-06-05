# Thesis Table 17 and Figure 17: Class-Normalized False-Fall-Alarm Sources

This note documents the class-normalized false-fall-alarm source analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 17 and Figure 17 ask:

```text
Which true non-fall activities are most likely to be falsely predicted as fall?
```

This is different from counting false fall alarms only. A class can produce many false fall alarms because it has many windows, or because the model has a high class-specific tendency to confuse that activity with fall.

## Files Created

```text
Table 17:
results\thesis_table_17_class_normalized_false_fall_alarm_sources.csv

Figure 17:
figures\thesis_figure_17_class_normalized_false_fall_alarm_heatmap.png

Companion note:
notes\thesis_table_17_figure_17_class_normalized_false_alarm_sources.md
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

## Metric Definition

For each condition and each true non-fall class:

```text
class-normalized false-fall-alarm rate =
false fall alerts from that true class / total true windows of that class
```

The heatmap cells show this value as a percentage. Counts and denominators are reported in Table 17.

## Key Findings

- Clean: highest normalized source = stand up (18.03%, 11/61 windows).
- FGSM Attack: highest normalized source = run (20.66%, 50/242 windows).
- PGD Attack: highest normalized source = stand up (26.23%, 16/61 windows).
- Defended Clean: highest normalized source = stand up (16.39%, 10/61 windows).
- Defended FGSM: highest normalized source = stand up (26.23%, 16/61 windows).
- Defended PGD: highest normalized source = stand up (18.03%, 11/61 windows).

## Interpretation

This artifact strengthens the thesis because it identifies which non-fall activities are most vulnerable to being misclassified as fall.

Raw false-alert counts alone can be misleading because they depend on how many windows each activity class contributes. The class-normalized view makes the error source more interpretable by asking whether a class has a high false-fall-alarm rate relative to its own class size.

Higher heatmap values identify non-fall activities that are more likely to be misclassified as fall within each condition.

## Claim Boundary

This is a descriptive window-level class-normalized false-alert source analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
