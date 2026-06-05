# Thesis Table 20 and Figure 20: Fall-Window Recovery and Failure Persistence

This note documents the fall-window recovery and failure-persistence analysis.

## Purpose

Table 20 and Figure 20 ask:

```text
For true fall windows, how many were detected cleanly, lost under attack, recovered by defense, or still missed after defense?
```

This complements Figure 19, which showed where missed fall windows were redirected. Figure 20 focuses on whether the fall-window detection itself was recovered.

## Files Created

```text
Table 20:
results\thesis_table_20_fall_window_recovery_persistence.csv

Figure 20:
figures\thesis_figure_20_fall_window_recovery_persistence.png

Companion note:
notes\thesis_table_20_figure_20_fall_window_recovery_persistence.md
```

## Input Files

```text
results\clean_predictions_short.csv
results\fgsm_predictions_short_epsilon_0_03.csv
results\pgd_predictions_short_epsilon_0_03.csv
results\defended_fgsm_predictions_short_epsilon_0_03.csv
results\defended_pgd_predictions_short_epsilon_0_03.csv
```

## Definitions

```text
TP = true fall window predicted as fall
FN = true fall window predicted as non-fall
Clean TP -> Attack FN = clean-detected fall window lost under attack
Attack FN -> Defended TP = attack-missed fall window recovered by defense
Attack FN -> Defended FN = attack-missed fall window still missed after defense
```

## Key Findings

- FGSM path: clean TP=57, clean FN=32; attack TP=0, attack FN=89; defended attack TP=0, defended attack FN=89.
  Clean TP -> Attack FN: 57 (100.00% of clean TP windows). Attack FN -> Defended TP: 0 (0.00% of attack FN windows). Attack FN -> Defended FN: 89 (100.00% of attack FN windows).
- PGD path: clean TP=57, clean FN=32; attack TP=0, attack FN=89; defended attack TP=0, defended attack FN=89.
  Clean TP -> Attack FN: 57 (100.00% of clean TP windows). Attack FN -> Defended TP: 0 (0.00% of attack FN windows). Attack FN -> Defended FN: 89 (100.00% of attack FN windows).

## Interpretation

This artifact strengthens the thesis by separating false-alarm improvement from fall-window recovery.

The short defended model may reduce some false-alert burden in earlier figures, but this analysis directly checks whether the defended attacked condition restores fall-window detection. Under the tested epsilon 0.030 FGSM/PGD conditions, the defended attacked outputs recover 0 attack-missed fall windows and all attack-missed fall windows persist.

## Claim Boundary

This is a descriptive window-level paired recovery analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
