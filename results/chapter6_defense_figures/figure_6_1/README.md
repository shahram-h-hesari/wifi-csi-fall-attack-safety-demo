# Chapter 6 Figure 6.1 Provenance Package

## Figure

Chapter 6 Figure 6.1: defense-effect summary.

This figure is a two-panel summary of:

1. Fall recall
2. False-fall alarms among the 455 non-fall windows

The conditions are clean, FGSM at epsilon = 0.030, and PGD at epsilon = 0.030.

## Source metrics

| Condition | Model | Fall recall | False-fall alarms | Non-fall denominator |
|---|---|---:|---:|---:|
| Clean | Undefended | 0.9556 | 0 | 455 |
| Clean | Defended FGSM-AT | 0.9111 | 8 | 455 |
| FGSM 0.03 | Undefended | 0.0000 | 47 | 455 |
| FGSM 0.03 | Defended FGSM-AT | 0.3111 | 27 | 455 |
| PGD 0.03 | Undefended | 0.0000 | 48 | 455 |
| PGD 0.03 | Defended FGSM-AT | 0.0889 | 54 | 455 |

Fall denominator: 45 windows.  
Non-fall denominator: 455 windows.  
Total test split: 500 windows.

## Files

- `figure_6_1_summary.csv`: compact source data for the figure.
- `generate_figure_6_1.py`: self-contained plotting script.
- `figure_6_1_defense_effect_summary.png`: generated output figure.
- `README.md`: this provenance note.

## Regeneration command

From this folder:

```powershell
python generate_figure_6_1.py
```

## Thesis destination

The thesis copy of the generated image is used at:

```text
C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked\images\ch06_figure_6_1_defense_effect_summary.png
```

## Scope note

This package does not run training or attacks. It only packages the already-verified Chapter 6 Figure 6.1 metrics and regenerates the plotted summary.
