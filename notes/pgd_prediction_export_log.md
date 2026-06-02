\# PGD Prediction Export Log



This note documents the first Projected Gradient Descent (PGD) attacked prediction export for the WiFi CSI Fall Attack-Safety Demo.



\## Experiment Context



\* Repository: `secure-wifi-csi-healthcare-sensing`

\* Experiment folder: `experiments/fall\_detection\_attack\_safety\_demo`

\* Baseline source: SenseFi / `WiFi-CSI-Sensing-Benchmark`

\* Dataset: `UT\_HAR\_data`

\* Model: `LeNet`

\* Task: seven-class WiFi CSI activity recognition

\* Safety translation: window-level fall vs non-fall proxy evaluation



\## Attack Type



This step adds a PGD attack export script:



```text

scripts/export\_pgd\_predictions\_short.py

```



PGD is an iterative adversarial attack. In this implementation, it is applied to processed UT-HAR CSI tensors after data preprocessing.



Unlike FGSM, which applies a single gradient-sign update, PGD applies multiple smaller gradient-based updates and projects the perturbation back inside the allowed epsilon range after each step. This makes PGD a stronger iterative software-level adversarial attack for this research implementation.



\## PGD Settings



```text

epsilon = 0.030

alpha = 0.005

pgd\_steps = 10

epochs = 5

device = CPU

```



\## Output File



```text

results/pgd\_predictions\_short\_epsilon\_0\_03.csv

```



\## Verification Summary



The exported CSV was checked after generation.



```text

rows: 996

attack types: \['PGD']

settings: \[('0.03', '0.005', '10')]

```



The 996 evaluation windows match the previous clean and FGSM workflow:



```text

496 validation windows + 500 test windows = 996 evaluation windows

```



\## Fall vs Non-Fall Label Check



The true binary label counts were verified:



```text

non-fall windows: 907

fall windows: 89

```



The PGD-attacked prediction distribution was:



```text

predicted non-fall windows: 881

predicted fall windows: 115

```



\## Claim Boundary



This PGD implementation is a software-level adversarial perturbation applied to processed UT-HAR CSI tensors.



It is not:



\* a physical-layer attack

\* a packet-level attack

\* a preamble-level attack

\* an SDR implementation

\* an over-the-air attack

\* clinical validation

\* medical-device validation

\* diagnostic evidence

\* regulatory evaluation



This output supports a research implementation workflow for comparing clean, FGSM-attacked, and PGD-attacked model behavior using window-level safety-proxy metrics.



\## Current Step Status



The PGD prediction export step is complete and verified.



Expected new files before commit:



```text

notes/pgd\_prediction\_export\_log.md

results/pgd\_predictions\_short\_epsilon\_0\_03.csv

scripts/export\_pgd\_predictions\_short.py

```



Recommended commit message:



```text

Add PGD prediction export

```

