# Thesis Table 19 and Figure 19: Missed-Fall Destination Classes

This note documents the missed-fall destination analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 19 and Figure 19 ask:

```text
When a true fall window is missed, what non-fall class does the model predict instead?
```

This is useful because the safety meaning of a missed fall window can depend on the predicted destination class. For example, a fall window predicted as lie down, sit down, walk, or stand up may suggest different failure modes and different confusion patterns.

## Files Created

```text
Table 19:
results\thesis_table_19_missed_fall_destination_classes.csv

Figure 19:
figures\thesis_figure_19_missed_fall_destination_heatmap.png

Companion note:
notes\thesis_table_19_figure_19_missed_fall_destination_classes.md
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

For each condition and each predicted non-fall destination class:

```text
destination rate among true fall windows =
true fall windows missed as that destination class / total true fall windows
```

The figure also reports share among missed fall windows:

```text
share among missed fall windows =
true fall windows missed as that destination class / total missed fall windows
```

Figure 19 uses two complementary percentages:

```text
top cell value = destination rate among true fall windows
parenthetical value = share among missed fall windows in that row
```

## Key Findings

- Clean: top missed-fall destination = run (20 windows; 22.47% of true fall windows; 62.50% of missed fall windows).
- FGSM Attack: top missed-fall destination = walk (60 windows; 67.42% of true fall windows; 67.42% of missed fall windows).
- PGD Attack: top missed-fall destination = walk (54 windows; 60.67% of true fall windows; 60.67% of missed fall windows).
- Defended Clean: top missed-fall destination = walk (39 windows; 43.82% of true fall windows; 73.58% of missed fall windows).
- Defended FGSM: top missed-fall destination = walk (42 windows; 47.19% of true fall windows; 47.19% of missed fall windows).
- Defended PGD: top missed-fall destination = walk (27 windows; 30.34% of true fall windows; 30.34% of missed fall windows).

## Interpretation

This artifact strengthens the thesis because it moves beyond saying that fall windows were missed. It shows what the model predicted instead when it failed to recognize true fall windows.

This is especially important under attack and defended-attack conditions where missed-fall rate can be high. The destination-class view helps identify whether fall windows are being redirected toward particular non-fall activities.

In this tested configuration, FGSM and PGD attacks missed all true fall windows. The defended FGSM and defended PGD conditions also missed all true fall windows, but the destination patterns changed. FGSM and PGD mostly redirected missed fall windows toward walk and run, while defended PGD spread missed-fall destinations across more non-fall classes.

## Claim Boundary

This is a descriptive window-level missed-fall destination analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
