# Thesis Table 24 and Figure 24: Defense Recovery Fraction and Residual Safety Gap

## Purpose

Table 24 and Figure 24 ask:

```text
How much of the attack-induced safety-priority degradation is recovered by the defended model, and how much gap remains relative to clean baseline?
```

This directly follows Table/Figure 23. Figure 23 shows the safety-priority score under missed-fall weighting. Figure 24 explains how much of the attack-induced gap is recovered by defense.

## Files Created

**Table 24**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\thesis_table_24_defense_recovery_residual_gap.csv`

**Figure 24**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\figures\thesis_figure_24_defense_recovery_residual_gap.png`

**Companion note**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\notes\thesis_table_24_figure_24_defense_recovery_residual_gap.md`

## Input Files and Prediction Columns

- Clean baseline: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\clean_predictions_short.csv` using `fall_pred_binary`
- FGSM attack: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\fgsm_predictions_short_epsilon_0_03.csv` using `attacked_fall_pred_binary`
- PGD attack: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary`
- Defended FGSM: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_fgsm_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_fgsm_defended`
- Defended PGD: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_pgd_defended`
- Defended clean: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_predictions_short.csv` using `fall_pred_binary_clean_defended`

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Metric Definitions

For each attack type and missed-fall-priority scenario:

```text
attack gap to clean =
attack score − clean baseline score

defended gap to clean =
defended attack score − clean baseline score

score reduction by defense =
attack score − defended attack score

recovery fraction =
(attack score − defended attack score) /
(attack score − clean baseline score)

residual gap fraction =
(defended attack score − clean baseline score) /
(attack score − clean baseline score)
```

A recovery fraction of 1.0 means full recovery to clean-baseline score. A recovery fraction near 0 means little recovery. A negative recovery fraction would mean the defense made the score worse than the attack.

## Key Findings

- FGSM: recovery decreases from 7.0% under 1:1 weighting to 0.8% under 10:1 weighting, leaving 99.2% residual gap under 10:1.
- PGD: recovery decreases from 8.9% under 1:1 weighting to 1.0% under 10:1 weighting, leaving 99.0% residual gap under 10:1.
- The defense mostly reduces false-alert contribution, but it does not recover missed-fall behavior because defended attack FNR remains high.

## Interpretation

This artifact shows that the defended model recovers only a small fraction of the attack-induced safety-priority gap. The recovery fraction becomes smaller as missed-fall errors are given more weight because the defended attack conditions still miss all true fall windows in this tested configuration.

This result is important because it shows that reducing false-alert burden is not enough if missed-fall behavior remains unresolved.

## Claim Boundary

This is a descriptive window-level defense-recovery and residual-gap analysis using the current UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, patient deployment, clinical utility analysis, health-economic analysis, alarm-fatigue validation, event-level fall validation, long-lie validation, time-to-alarm validation, subject-level generalization validation, room-level generalization validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
