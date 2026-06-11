\# FGSM vs PGD Comparison Summary



This note documents the FGSM vs PGD epsilon-sweep comparison for the WiFi CSI Fall Attack-Safety Demo.



\## Experiment Context



\* Repository: `secure-wifi-csi-healthcare-sensing`

\* Experiment folder: `experiments/fall\_detection\_attack\_safety\_demo`

\* Dataset: `UT\_HAR\_data`

\* Model: `LeNet`

\* Task: seven-class WiFi CSI activity recognition

\* Safety translation: binary fall vs non-fall window-level proxy evaluation

\* Attacks compared: FGSM and PGD applied to processed UT-HAR CSI tensors



\## Input Files



```text

results/fgsm\_epsilon\_sweep\_summary.csv

results/pgd\_epsilon\_sweep\_summary.csv

```



\## Script



```text

scripts/plot\_fgsm\_vs\_pgd\_comparison.py

```



\## Output Files



```text

results/fgsm\_vs\_pgd\_epsilon\_comparison.csv

figures/fgsm\_vs\_pgd\_safety\_comparison.png

```



\## Compared Epsilon Values



```text

epsilon = 0.000

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030

```



\## FGSM vs PGD Summary



```text

epsilon=0.000 | FGSM missed=0.359551 | PGD missed=0.359551 | FGSM recall=0.640449 | PGD recall=0.640449 | FGSM F1=0.640449 | PGD F1=0.640449

epsilon=0.005 | FGSM missed=0.741573 | PGD missed=0.786517 | FGSM recall=0.258427 | PGD recall=0.213483 | FGSM F1=0.302632 | PGD F1=0.251656

epsilon=0.010 | FGSM missed=0.988764 | PGD missed=1.000000 | FGSM recall=0.011236 | PGD recall=0.000000 | FGSM F1=0.014815 | PGD F1=0.000000

epsilon=0.020 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000

epsilon=0.030 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000

```



\## Interpretation



The comparison shows that both FGSM and PGD strongly degrade fall-focused safety-proxy metrics as epsilon increases.



At `epsilon = 0.005`, PGD caused slightly stronger safety degradation than FGSM:



```text

FGSM missed fall rate = 0.741573

PGD missed fall rate = 0.786517



FGSM recall = 0.258427

PGD recall = 0.213483



FGSM F1-score = 0.302632

PGD F1-score = 0.251656

```



At `epsilon = 0.010`, PGD reached complete fall-recall loss:



```text

PGD missed fall rate = 1.000000

PGD recall = 0.000000

PGD F1-score = 0.000000

```



FGSM was also nearly fully degraded at the same epsilon:



```text

FGSM missed fall rate = 0.988764

FGSM recall = 0.011236

FGSM F1-score = 0.014815

```



At `epsilon = 0.020` and `epsilon = 0.030`, both attacks caused complete fall-recall loss in this shortened baseline setting.



\## Safety-Proxy Meaning



This comparison is more informative than seven-class accuracy alone because it shows how adversarial perturbations affect fall-focused safety questions:



```text

Does the attacked model miss fall windows?

Does fall recall collapse?

Does F1-score collapse?

Does false alarm burden increase?

Does prediction stability decrease?

```



The comparison suggests that the shortened LeNet baseline is highly vulnerable to both one-step FGSM and iterative PGD perturbations on processed CSI tensors.



\## Claim Boundary



This comparison uses software-level adversarial perturbations applied to processed UT-HAR CSI tensors.



It is not:



\* clinical validation

\* medical-device validation

\* diagnostic evidence

\* regulatory evaluation

\* real patient deployment evidence

\* event-level fall detection validation

\* long-lie validation

\* physical-layer attack validation

\* packet-level attack validation

\* preamble-level attack validation

\* SDR validation

\* over-the-air validation



This result supports a research implementation workflow for comparing clean, FGSM-attacked, and PGD-attacked WiFi CSI model behavior using window-level safety-proxy metrics.



\## Current Step Status



The FGSM vs PGD comparison step is complete and verified.



New files from this step:



```text

scripts/plot\_fgsm\_vs\_pgd\_comparison.py

results/fgsm\_vs\_pgd\_epsilon\_comparison.csv

figures/fgsm\_vs\_pgd\_safety\_comparison.png

notes/fgsm\_vs\_pgd\_comparison\_summary.md

```



Recommended commit message:



```text

Add FGSM vs PGD comparison

```

