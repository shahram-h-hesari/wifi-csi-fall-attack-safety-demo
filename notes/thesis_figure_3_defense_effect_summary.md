# Thesis Figure 3: Defense Effect Summary

This figure provides a compact visual summary of the first short 5-epoch FGSM adversarial-training defense.

The figure uses two panels:

- False fall alarm count under FGSM and PGD attack before and after defense
- Missed fall rate under FGSM and PGD attack before and after defense

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Main Result

- FGSM false fall alarms decreased from `119` to `72`, a reduction of `47`.
- PGD false fall alarms decreased from `115` to `56`, a reduction of `59`.
- FGSM missed fall rate remained `1.0000` after defense at epsilon `0.030`.
- PGD missed fall rate remained `1.0000` after defense at epsilon `0.030`.
- FGSM recall/sensitivity remained `0.0000` after defense at epsilon `0.030`.
- PGD recall/sensitivity remained `0.0000` after defense at epsilon `0.030`.

## Interpretation

The defense reduced false fall alarm burden under both FGSM and PGD attacks, but it did not recover fall recall/sensitivity or missed-fall performance at epsilon 0.030. Missed fall rate remained 1.0000 for both defended FGSM and defended PGD. This means the first short 5-epoch FGSM adversarial-training defense reduced one safety-proxy failure mode, false alarms, while leaving the most critical attacked condition, missed falls, unresolved.

## Output Files

- `figures/thesis_figure_3_defense_effect_summary.png`
- `notes/thesis_figure_3_defense_effect_summary.md`
- Input: `results/defended_vs_undefended_safety_comparison.csv`
