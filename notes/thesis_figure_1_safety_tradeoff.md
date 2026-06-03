# Thesis Figure 1: Defended vs Undefended Safety Tradeoff

This note documents the first thesis-ready figure for the WiFi CSI Fall Attack-Safety Demo.

Generated figure:

```text
figures/thesis_figure_1_safety_tradeoff.png
```

Input data:

```text
results/defended_vs_undefended_safety_comparison.csv
```

---

## Figure Purpose

The figure compares two fall-focused safety-proxy outcomes across clean, attacked, and defended conditions:

```text
missed fall rate
false fall alarm count
```

The compared conditions are:

```text
undefended clean
undefended FGSM epsilon 0.03
undefended PGD epsilon 0.03
defended clean
defended FGSM epsilon 0.03
defended PGD epsilon 0.03
```

---

## Suggested Thesis Caption

Figure 1. Window-level fall safety-proxy tradeoff for the SenseFi UT-HAR LeNet baseline under clean, FGSM-attacked, PGD-attacked, and short FGSM-adversarial-training defended conditions. The defended model reduced false fall alarms under attack but did not recover fall recall at epsilon 0.03, so missed fall rate remained 1.0 under defended FGSM and defended PGD attack.

---

## Key Interpretation

The figure highlights two different safety-proxy effects.

First, the attacked models missed all fall windows at epsilon 0.03:

```text
undefended FGSM missed fall rate = 1.0000
undefended PGD missed fall rate = 1.0000
defended FGSM missed fall rate = 1.0000
defended PGD missed fall rate = 1.0000
```

Second, the defended model reduced false fall alarms under attack:

```text
FGSM false fall alarms: 119 -> 72
PGD false fall alarms:  115 -> 56
```

This supports a careful interpretation: the first short FGSM adversarial-training defense reduced false alarm burden under attack but did not restore fall sensitivity.

---

## Claim Boundary

This figure is a window-level software comparison on processed CSI tensors.

It is not:

```text
clinical validation
medical-device validation
diagnostic evidence
regulatory evaluation
real patient deployment evidence
event-level fall validation
long-lie validation
time-to-detection validation
physical-layer attack validation
physical-layer defense validation
packet-level validation
preamble-level validation
SDR validation
over-the-air validation
```
