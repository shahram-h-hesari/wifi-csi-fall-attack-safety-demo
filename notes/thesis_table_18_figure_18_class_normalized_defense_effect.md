# Thesis Table 18 and Figure 18: Class-Normalized Defense Effect on False-Fall-Alarm Sources

This note documents the matched defense-effect analysis for class-normalized false-fall-alarm rates.

## Purpose

Table 18 and Figure 18 ask:

```text
For each true non-fall activity, did the defended model reduce or increase false fall alarms compared with the matched attack?
```

The matched comparisons are:

```text
FGSM Attack -> Defended FGSM
PGD Attack -> Defended PGD
```

## Files Created

```text
Table 18:
results\thesis_table_18_class_normalized_defense_effect.csv

Figure 18:
figures\thesis_figure_18_class_normalized_defense_effect_heatmap.png

Companion note:
notes\thesis_table_18_figure_18_class_normalized_defense_effect.md
```

## Input Files

```text
results\fgsm_predictions_short_epsilon_0_03.csv
results\defended_fgsm_predictions_short_epsilon_0_03.csv
results\pgd_predictions_short_epsilon_0_03.csv
results\defended_pgd_predictions_short_epsilon_0_03.csv
```

## Metric Definition

For each matched attack/defense pair and each true non-fall class:

```text
class-normalized defense effect =
defended class-normalized false-alert rate - attacked class-normalized false-alert rate
```

Therefore:

```text
negative value = defense reduced false-fall-alarm rate
positive value = defense increased false-fall-alarm rate
zero = no class-normalized rate change
```

Figure 18 reports this as percentage-point change, abbreviated as pp.

## Key Findings

- FGSM Attack -> Defended FGSM: largest reduction = walk (10.58 percentage points; 36 -> 5 false alerts).
  Largest increase = stand up (9.84 percentage points; 10 -> 16 false alerts).
- PGD Attack -> Defended PGD: largest reduction = walk (11.60 percentage points; 35 -> 1 false alerts).
  Largest increase = pickup (1.01 percentage points; 0 -> 1 false alerts).

## Interpretation

This artifact strengthens the thesis because it shows where the short defended model reduced false-fall-alarm tendency and where it did not.

Table 16 showed that defended FGSM/PGD reduced total false fall alerts compared with matched attacks, while PPV remained zero because TP remained zero. Table 18 adds class-level detail by showing which true non-fall activities drove those reductions or increases.

For the tested configuration, most class-specific false-alert rates decreased under defense. However, the FGSM stand-up class increased and the PGD pickup class slightly increased, showing that the short defense did not uniformly improve every false-alert source.

## Claim Boundary

This is a descriptive window-level matched defense-effect analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
