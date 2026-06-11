\# PGD Epsilon Sweep Log



This note documents the Projected Gradient Descent (PGD) epsilon sweep for the WiFi CSI Fall Attack-Safety Demo.



\## Experiment Context



\* Repository: `secure-wifi-csi-healthcare-sensing`

\* Experiment folder: `experiments/fall\_detection\_attack\_safety\_demo`

\* Baseline source: SenseFi / `WiFi-CSI-Sensing-Benchmark`

\* Dataset: `UT\_HAR\_data`

\* Model: `LeNet`

\* Task: seven-class WiFi CSI activity recognition

\* Safety translation: binary fall vs non-fall window-level proxy evaluation

\* Attack: PGD applied to processed UT-HAR CSI tensors



\## Script



```text

scripts/run\_pgd\_epsilon\_sweep\_short.py

```



\## Output File



```text

results/pgd\_epsilon\_sweep\_summary.csv

```



\## PGD Sweep Settings



```text

epochs = 5

device = CPU

pgd\_steps = 10

epsilon values = 0.000, 0.005, 0.010, 0.020, 0.030

alpha = epsilon / 6

```



For `epsilon = 0.000`, no adversarial perturbation is applied and `alpha = 0.000`.



\## Evaluation Window Counts



```text

training windows: 3977

validation windows: 496

test windows: 500

evaluation windows: 996

```



The 996 evaluation windows match the previous clean, FGSM, and PGD single-epsilon workflow:



```text

496 validation windows + 500 test windows = 996 evaluation windows

```



\## Clean Baseline Before PGD Sweep



The PGD sweep script first trained the same shortened clean LeNet baseline for five epochs.



```text

Epoch 01/5 | train\_acc=0.2858 | train\_loss=1.8020 | test\_acc=0.2942 | test\_loss=1.7874

Epoch 02/5 | train\_acc=0.2946 | train\_loss=1.7870 | test\_acc=0.2942 | test\_loss=1.7805

Epoch 03/5 | train\_acc=0.3233 | train\_loss=1.7412 | test\_acc=0.4207 | test\_loss=1.6117

Epoch 04/5 | train\_acc=0.4919 | train\_loss=1.4322 | test\_acc=0.5161 | test\_loss=1.2782

Epoch 05/5 | train\_acc=0.6142 | train\_loss=1.0603 | test\_acc=0.6596 | test\_loss=1.0014

```



\## PGD Epsilon Sweep Results



```text

epsilon=0.000 | alpha=0.000000 | seven\_class\_acc=0.659639 | missed\_fall\_rate=0.359551 | false\_alarms=32  | recall=0.640449 | f1=0.640449 | prediction\_change\_rate=0.000000

epsilon=0.005 | alpha=0.000833 | seven\_class\_acc=0.389558 | missed\_fall\_rate=0.786517 | false\_alarms=43  | recall=0.213483 | f1=0.251656 | prediction\_change\_rate=0.310241

epsilon=0.010 | alpha=0.001667 | seven\_class\_acc=0.172691 | missed\_fall\_rate=1.000000 | false\_alarms=70  | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.561245

epsilon=0.020 | alpha=0.003333 | seven\_class\_acc=0.013052 | missed\_fall\_rate=1.000000 | false\_alarms=111 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.745984

epsilon=0.030 | alpha=0.005000 | seven\_class\_acc=0.000000 | missed\_fall\_rate=1.000000 | false\_alarms=115 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.778112

```



\## Interpretation



The PGD epsilon sweep shows increasing safety-proxy degradation as perturbation strength increases.



At `epsilon = 0.000`, the results match the clean baseline:



```text

missed fall rate = 0.359551

false alarms = 32

recall = 0.640449

F1-score = 0.640449

prediction change rate = 0.000000

```



At `epsilon = 0.005`, PGD already caused substantial degradation:



```text

missed fall rate increased to 0.786517

recall decreased to 0.213483

F1-score decreased to 0.251656

false alarms increased to 43

prediction change rate increased to 0.310241

```



At `epsilon = 0.010` and above, PGD caused complete loss of fall recall in the window-level binary fall-vs-non-fall safety-proxy evaluation:



```text

missed fall rate = 1.000000

recall = 0.000000

F1-score = 0.000000

```



This shows that the model becomes highly vulnerable to iterative software-level adversarial perturbation in this shortened baseline setting.



\## Safety-Proxy Meaning



In fall-safety proxy terms, the most important trend is not only the seven-class accuracy drop.



The important safety-oriented changes are:



```text

missed fall rate increases

fall recall decreases

F1-score decreases

false fall alarm count increases

prediction change rate increases

```



These metrics help translate adversarial model degradation into caregiver-relevant questions such as:



```text

Will the system miss real fall windows?

Will it create more false fall alerts?

Will alert trustworthiness decrease?

Will the model become unstable under perturbation?

```



\## FGSM vs PGD Note



This PGD sweep should later be compared directly with the FGSM epsilon sweep.



From the current PGD sweep, PGD reaches complete fall-recall loss by `epsilon = 0.010`.



A direct FGSM-vs-PGD comparison table and figure should be added next before making broader claims about relative attack strength across epsilon values.



\## Claim Boundary



This PGD epsilon sweep is a software-level adversarial robustness experiment on processed UT-HAR CSI tensors.



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



This result supports a research implementation workflow for translating adversarial WiFi CSI model degradation into window-level fall-focused safety-proxy metrics.



\## Current Step Status



The PGD epsilon sweep step is complete and verified.



New files from this step:



```text

scripts/run\_pgd\_epsilon\_sweep\_short.py

results/pgd\_epsilon\_sweep\_summary.csv

notes/pgd\_epsilon\_sweep\_log.md

```



Recommended commit message:



```text

Add PGD epsilon sweep results

```

