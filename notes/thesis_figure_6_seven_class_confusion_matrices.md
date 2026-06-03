# Thesis Figure 6: Seven-Class Confusion Matrix Figure

This figure visualizes seven-class confusion matrices for the clean, attacked, and defended conditions in the WiFi CSI Fall Attack-Safety Demo.

## Claim Boundary

Research implementation only; window-level seven-class confusion-matrix visualization; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_6_seven_class_confusion_matrices.png`

## Conditions Included

| Condition | Total Windows | Seven-Class Accuracy | Fall Windows | Detected Fall Windows | Missed Fall Windows | False Fall Alarms |
|---|---:|---:|---:|---:|---:|---:|
| Undefended Clean | 996 | 0.6596 | 89 | 57 | 32 | 32 |
| Undefended FGSM epsilon = 0.030 | 996 | 0.0100 | 89 | 0 | 89 | 119 |
| Undefended PGD epsilon = 0.030 | 996 | 0.0000 | 89 | 0 | 89 | 115 |
| Defended Clean | 996 | 0.6074 | 89 | 36 | 53 | 22 |
| Defended FGSM epsilon = 0.030 | 996 | 0.1526 | 89 | 0 | 89 | 72 |
| Defended PGD epsilon = 0.030 | 996 | 0.0773 | 89 | 0 | 89 | 56 |

## Interpretation

Figure 6 complements Table 8 by showing the full seven-class confusion structure behind the binary fall-vs-non-fall safety-proxy metrics.

The figure helps identify whether attack and defense conditions mainly change fall windows into specific non-fall classes, or whether they convert non-fall activities into false fall alarms.

This visualization should be described as a window-level multiclass confusion-matrix analysis. It should not be described as event-level fall validation or clinical fall validation.

## Relationship to Table 8

Table 8 provides the detailed high-risk fall-related error taxonomy. Figure 6 provides the visual seven-class confusion-matrix view of the same prediction behavior.
