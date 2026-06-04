# Thesis Table 15 and Figure 15: Paired Safety-State Transitions

This note documents the paired safety-state transition analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 15 and Figure 15 compare the same evaluated windows across clean, attacked, and defended conditions.

Instead of only reporting aggregate condition-level metrics, this artifact asks:

```text
Which clean true-positive fall detections became missed falls under attack?
Which clean true-negative non-fall windows became false fall alarms under attack?
Which attacked missed-fall or false-alarm windows were recovered by the defended model?
Which attacked safety failures persisted after defense?
```

## Files Created

```text
Table 15:
results\thesis_table_15_paired_safety_state_transition_table.csv

Figure 15:
figures\thesis_figure_15_paired_safety_state_transition_heatmap.png

Companion note:
notes\thesis_table_15_figure_15_paired_safety_state_transitions.md
```

## Input Files

```text
results\clean_predictions_short.csv
results\fgsm_predictions_short_epsilon_0_03.csv
results\pgd_predictions_short_epsilon_0_03.csv
results\defended_fgsm_predictions_short_epsilon_0_03.csv
results\defended_pgd_predictions_short_epsilon_0_03.csv
```

## Safety-State Definition

The analysis maps each evaluated window into one of four binary fall-vs-non-fall safety states:

```text
TP = true fall predicted as fall
FN = true fall predicted as non-fall
FP = true non-fall predicted as fall
TN = true non-fall predicted as non-fall
```

## How to Read the Axes

For each panel:

```text
Y-axis = source safety state before transition
X-axis = destination safety state after transition
```

For example, in the Clean to FGSM Attack panel:

```text
TP row, FN column = windows that were true-positive fall detections in the clean condition and became missed falls under FGSM.
```

## Paired Window Count

```text
Total paired windows analyzed: 996
```

## Key Transition Findings

- clean detected falls converted to FGSM missed falls: 57 windows (100.00% of TP windows in the source condition).
- clean detected falls converted to PGD missed falls: 57 windows (100.00% of TP windows in the source condition).
- clean correct non-falls converted to FGSM false fall alarms: 104 windows (11.89% of TN windows in the source condition).
- clean correct non-falls converted to PGD false fall alarms: 104 windows (11.89% of TN windows in the source condition).
- FGSM missed falls that persisted after defense: 89 windows (100.00% of FN windows in the source condition).
- PGD missed falls that persisted after defense: 89 windows (100.00% of FN windows in the source condition).
- FGSM false alarms recovered by defense: 62 windows (52.10% of FP windows in the source condition).
- PGD false alarms recovered by defense: 69 windows (60.00% of FP windows in the source condition).

## How to Read the Percentages

The percentage shown inside each nonzero heatmap cell is a source-row percentage.

That means:

```text
source-row percentage = transition count / total windows in the source safety-state row
```

It is not the percentage of all evaluated windows.

For example, if a cell says:

```text
57
100.0%
```

then all 57 windows in that source row moved to that destination safety state.

## Interpretation

This analysis strengthens the thesis evidence package because it shows how safety outcomes changed at the same-window level, not only at the aggregate metric level.

The paired transition view is especially useful for explaining adversarial degradation:

```text
clean safety state
-> attacked safety state
-> defended attacked safety state
```

It also helps separate two different defense outcomes:

```text
recovered windows
persistent safety failures
```

The figure uses one shared color scale across all panels. Each nonzero cell shows the transition count and the source-row percentage. Row labels show the number of source-condition windows in each safety state. Small light-gray zero labels indicate zero-count transitions.

In the current short defended model, the most important interpretation remains consistent with Tables/Figures 1-14: the defense reduced some overconfident and false-alarm behavior, but it did not restore fall recall under the tested epsilon 0.030 FGSM/PGD conditions.

## Claim Boundary

This is a descriptive window-level safety-proxy analysis using paired sample IDs from the UT-HAR / SenseFi research workflow.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, subject-level robustness, trial-level robustness, room-level robustness, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
