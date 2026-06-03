# Thesis Figure 5: Binary Confusion Matrix Figure

This figure shows binary fall-vs-non-fall confusion matrices for clean, FGSM-attacked, and PGD-attacked conditions before and after defense.

Matrix layout:

```text
Rows = true class
Columns = predicted class

                 Predicted Fall    Predicted Non-Fall
True Fall              TP                  FN
True Non-Fall          FP                  TN
```

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Confusion Matrix Summary

| Condition | TP | FN | FP | TN | Recall/Sensitivity | Missed Fall Rate | Precision | F1-Score | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Undefended Clean | 57 | 32 | 32 | 875 | 0.6404 | 0.3596 | 0.6404 | 0.6404 | 0.8026 |
| Undefended FGSM epsilon = 0.030 | 0 | 89 | 119 | 788 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.4344 |
| Undefended PGD epsilon = 0.030 | 0 | 89 | 115 | 792 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.4366 |
| Defended Clean | 36 | 53 | 22 | 885 | 0.4045 | 0.5955 | 0.6207 | 0.4898 | 0.6901 |
| Defended FGSM epsilon = 0.030 | 0 | 89 | 72 | 835 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.4603 |
| Defended PGD epsilon = 0.030 | 0 | 89 | 56 | 851 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.4691 |

## Interpretation

The confusion matrices show which binary safety-proxy errors changed across clean, attacked, and defended conditions.

Under FGSM and PGD attack, true detected falls drop to zero and missed falls rise to all 89 fall windows. The defended model reduces false fall alarms under attack but does not recover detected falls at epsilon 0.030.

The clean defended model reduces false fall alarms compared with the clean undefended baseline, but it also increases missed falls from 32 to 53 fall windows.

## Output Files

- `figures/thesis_figure_5_confusion_matrices.png`
- `notes/thesis_figure_5_confusion_matrices.md`
- Input: `results/defended_vs_undefended_safety_comparison.csv`
