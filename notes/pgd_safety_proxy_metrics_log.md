\# PGD Safety-Proxy Metrics Log



This note documents the window-level fall-vs-non-fall safety-proxy metrics computed from the first Projected Gradient Descent (PGD) attacked prediction export.



\## Experiment Context



\* Repository: `secure-wifi-csi-healthcare-sensing`

\* Experiment folder: `experiments/fall\_detection\_attack\_safety\_demo`

\* Baseline source: SenseFi / `WiFi-CSI-Sensing-Benchmark`

\* Dataset: `UT\_HAR\_data`

\* Model: `LeNet`

\* Task: seven-class WiFi CSI activity recognition

\* Safety translation: binary fall vs non-fall window-level proxy evaluation

\* Attack: PGD applied to processed UT-HAR CSI tensors



\## Input File



```text

results/pgd\_predictions\_short\_epsilon\_0\_03.csv

```



\## Output File



```text

results/pgd\_safety\_proxy\_metrics\_epsilon\_0\_03.csv

```



\## PGD Settings



```text

attack\_type = PGD

epsilon = 0.030

alpha = 0.005

pgd\_steps = 10

epochs = 5

device = CPU

```



\## Evaluation Window Counts



```text

total windows: 996

fall windows: 89

non-fall windows: 907

```



The evaluation set matches the previous clean and FGSM workflow:



```text

496 validation windows + 500 test windows = 996 evaluation windows

```



\## PGD Safety-Proxy Metrics



```text

TP detected falls: 0

FN missed falls: 89

FP false fall alarms: 115

TN correct non-falls: 792

```



```text

seven-class accuracy: 0.0000

binary accuracy: 0.7952

recall / sensitivity: 0.0000

missed fall rate: 1.0000

specificity: 0.8732

false positive rate: 0.1268

precision: 0.0000

F1-score: 0.0000

balanced accuracy: 0.4366

```



\## Interpretation



At `epsilon = 0.030`, the PGD attack caused the model to miss all fall windows in the evaluation set.



In fall-safety proxy terms:



```text

89 out of 89 fall windows were missed.

0 out of 89 fall windows were detected.

115 non-fall windows were incorrectly predicted as fall.

```



This means the PGD-attacked model produced:



\* complete loss of fall recall at this epsilon

\* a missed fall rate of 1.0000

\* zero precision and zero F1-score for the binary fall-vs-non-fall proxy task

\* increased false fall alarms compared with the clean baseline



\## Clean vs PGD Comparison



Previously documented clean baseline safety-proxy metrics were:



```text

TP detected falls: 57

FN missed falls: 32

FP false fall alarms: 32

TN correct non-falls: 875

recall / sensitivity: 0.6404

missed fall rate: 0.3596

precision: 0.6404

F1-score: 0.6404

balanced accuracy: 0.8026

```



PGD at `epsilon = 0.030` produced:



```text

TP detected falls: 0

FN missed falls: 89

FP false fall alarms: 115

TN correct non-falls: 792

recall / sensitivity: 0.0000

missed fall rate: 1.0000

precision: 0.0000

F1-score: 0.0000

balanced accuracy: 0.4366

```



Clean-to-PGD safety degradation:



```text

detected falls decreased from 57 to 0

missed falls increased from 32 to 89

false fall alarms increased from 32 to 115

recall decreased from 0.6404 to 0.0000

missed fall rate increased from 0.3596 to 1.0000

F1-score decreased from 0.6404 to 0.0000

balanced accuracy decreased from 0.8026 to 0.4366

```



\## FGSM vs PGD Note



The earlier FGSM result at `epsilon = 0.030` also reduced fall recall to zero. At the same epsilon, PGD produced a very similar fall-safety outcome.



This single-epsilon result should not be overinterpreted as a complete FGSM-vs-PGD comparison. A PGD epsilon sweep and a direct FGSM-vs-PGD comparison table are still needed before making broader claims about relative attack strength across settings.



\## Claim Boundary



These metrics are window-level safety-proxy metrics derived from model predictions.



They are not:



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



This result supports a research implementation workflow for translating adversarial model degradation into clinically motivated safety-proxy metrics.



\## Current Step Status



The PGD safety-proxy metrics step is complete.



New files from this step:



```text

scripts/compute\_pgd\_safety\_metrics.py

results/pgd\_safety\_proxy\_metrics\_epsilon\_0\_03.csv

notes/pgd\_safety\_proxy\_metrics\_log.md

```



Recommended commit message:



```text

Add PGD safety proxy metrics

```

