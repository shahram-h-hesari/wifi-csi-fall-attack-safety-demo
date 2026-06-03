# Thesis Figure 4: Clean vs Defended Clean Tradeoff

This figure compares the undefended clean baseline against the defended clean model to show the clean-performance cost of the first short 5-epoch FGSM adversarial-training defense.

The figure focuses only on the clean condition, without FGSM or PGD attack.

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Main Result

- Recall/sensitivity changed from `0.6404` to `0.4045`, a change of `-0.2360`.
- Missed fall rate changed from `0.3596` to `0.5955`, a change of `0.2360`.
- Precision changed from `0.6404` to `0.6207`, a change of `-0.0198`.
- F1-score changed from `0.6404` to `0.4898`, a change of `-0.1507`.
- Balanced accuracy changed from `0.8026` to `0.6901`, a change of `-0.1125`.
- False fall alarms changed from `32` to `22`, a reduction of `10`.

## Interpretation

The defended clean model reduced false fall alarms from 32 to 22, but this came with a reduction in fall recall/sensitivity, F1-score, and balanced accuracy. Missed fall rate increased from 0.3596 to 0.5955. This clean-condition tradeoff is important because a defense that reduces false alarms may still be undesirable if it increases missed falls.

## Output Files

- `figures/thesis_figure_4_clean_defense_tradeoff.png`
- `notes/thesis_figure_4_clean_defense_tradeoff.md`
- Input: `results/defended_vs_undefended_safety_comparison.csv`
