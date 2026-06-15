# Safety Translation Pipeline Diagram

This figure summarizes the safety-translation pipeline used in the WiFi CSI Fall Attack-Safety Demo.

## Claim Boundary

Research implementation only; conceptual safety-translation pipeline; window-level safety-proxy evaluation; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_8_safety_translation_pipeline.png`

## Purpose

The figure explains how the current workflow translates WiFi CSI model outputs into window-level safety-proxy evidence while separating current computable outputs from future event-level requirements.

The current pipeline is:

```text
processed WiFi CSI windows
-> clean model prediction
-> software-level FGSM / PGD perturbation
-> attacked prediction
-> binary fall-vs-non-fall mapping
-> window-level safety-proxy metrics
```

## Current Computable Outputs

The current dataset and prediction files support window-level metrics such as missed fall rate, false fall alarm count, recall, precision, F1-score, balanced accuracy, robustness thresholds, and multiclass error-taxonomy analysis.

## Current Thesis Evidence

The current workflow produces thesis-ready tables, figures, scripts, and notes that compare clean, attacked, and defended model behavior. These outputs support window-level safety-proxy analysis, robustness threshold analysis, and multiclass error interpretation.

## Metadata Gap

The local UT-HAR copy does not provide event IDs, timestamps, subject IDs, trial IDs, recording duration, fall onset time, alert time, or monitoring duration. Therefore, event-level metrics are not computed in this demo.

## Future Extension

A future dataset or collaboration with richer metadata could support event-level fall detection rate, time-to-detection, delayed detection, long-lie proxy, false alarms per hour/day, subject-level robustness, and trial-level robustness.

## Interpretation

Figure 8 is useful for the thesis because it clearly separates the current research contribution from future clinical-safety extensions. The current contribution is not clinical validation. It is a reproducible workflow for translating adversarial degradation into window-level fall safety-proxy metrics.
