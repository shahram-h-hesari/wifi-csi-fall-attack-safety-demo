# Final FGSM/PGD Attack-Safety Lab Report



This report summarizes the first completed clean-to-adversarial attack-safety workflow for the WiFi CSI Fall Attack-Safety Demo.



The experiment uses a reproducible WiFi CSI activity-recognition baseline and translates clean and attacked model outputs into fall-focused safety-proxy metrics.



---



## 1. Experiment Purpose



Many WiFi CSI sensing and adversarial machine learning studies report technical metrics such as model accuracy, attack success rate, or classification error.



This experiment asks a more safety-oriented question:



```text

If a WiFi CSI fall-related activity-recognition model is degraded by adversarial perturbation,

does the model miss more fall windows, create more false fall alarms, reduce recall,

reduce F1-score, or become less stable?

```



The goal is not to claim clinical validation. The goal is to build a reproducible research workflow that converts model outputs into safety-proxy metrics that are easier to interpret for healthcare-relevant sensing research.



---



## 2. Repository and Experiment Context



```text

Repository:

secure-wifi-csi-healthcare-sensing



Experiment folder:

experiments/fall\_detection\_attack\_safety\_demo



Baseline source:

SenseFi / WiFi-CSI-Sensing-Benchmark



Dataset:

UT\_HAR\_data



Model:

LeNet



Device:

CPU



Training setting:

Short 5-epoch baseline



Evaluation split:

SenseFi validation + test loader



Evaluation windows:

996

```



The 996 evaluation windows are composed of:



```text

496 validation windows + 500 test windows = 996 evaluation windows

```



---



## 3. Label Mapping



The UT-HAR dataset contains seven activity classes:



```text

0 = lie down

1 = fall

2 = walk

3 = pickup

4 = run

5 = sit down

6 = stand up

```



For the safety-proxy layer, the seven-class labels are mapped into binary fall-vs-non-fall labels:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



This binary mapping allows the experiment to compute fall-focused safety-proxy metrics from model predictions.



---



## 4. Completed Workflow



The completed workflow is:



```text

SenseFi + UT-HAR + LeNet clean baseline

clean prediction export

clean fall-vs-non-fall safety-proxy metrics

FGSM attacked prediction export

FGSM fall-vs-non-fall safety-proxy metrics

FGSM epsilon sweep

FGSM epsilon sweep figures

PGD attacked prediction export

PGD fall-vs-non-fall safety-proxy metrics

PGD epsilon sweep

PGD epsilon sweep figures

FGSM vs PGD comparison table

FGSM vs PGD comparison figure

README documentation

experiment status summary documentation

```



This completes the first reproducible clean-to-attacked safety-proxy pipeline for the fall-detection attack-safety demo.



---



## 5. Clean Baseline Result



The shortened clean baseline completed successfully.



```text

Epoch 01/5 | train\_acc=0.2858 | train\_loss=1.8020 | test\_acc=0.2942 | test\_loss=1.7874

Epoch 02/5 | train\_acc=0.2946 | train\_loss=1.7870 | test\_acc=0.2942 | test\_loss=1.7805

Epoch 03/5 | train\_acc=0.3233 | train\_loss=1.7412 | test\_acc=0.4207 | test\_loss=1.6117

Epoch 04/5 | train\_acc=0.4919 | train\_loss=1.4322 | test\_acc=0.5161 | test\_loss=1.2782

Epoch 05/5 | train\_acc=0.6142 | train\_loss=1.0603 | test\_acc=0.6596 | test\_loss=1.0014

```



The model improved from approximately 29% seven-class test accuracy after the first epoch to approximately 66% after five epochs.



This short training run was used for pipeline development and reproducibility testing. It should not be interpreted as final benchmark performance.



---



## 6. Clean Safety-Proxy Metrics



The clean binary fall-vs-non-fall evaluation produced:



```text

Total windows: 996

Fall windows: 89

Non-fall windows: 907



TP / detected falls: 57

FN / missed falls: 32

FP / false fall alarms: 32

TN / correct non-falls: 875



Binary accuracy: 0.9357

Recall / sensitivity: 0.6404

Missed fall rate: 0.3596

Specificity: 0.9647

False positive rate: 0.0353

Precision: 0.6404

F1-score: 0.6404

Balanced accuracy: 0.8026

```



This binary accuracy is fall-vs-non-fall accuracy, not seven-class activity-recognition accuracy.



---



## 7. FGSM Attack Summary



FGSM was implemented as a software-level adversarial perturbation applied to processed UT-HAR CSI tensors.



FGSM is a one-step gradient-sign attack. In this experiment, it was used to evaluate how a processed CSI tensor perturbation changes fall-vs-non-fall safety-proxy metrics.



At epsilon 0.030, the FGSM attack produced strong degradation:



```text

TP / detected falls: 0

FN / missed falls: 89

FP / false fall alarms: 119

TN / correct non-falls: 788



Recall / sensitivity: 0.0000

Missed fall rate: 1.0000

Precision: 0.0000

F1-score: 0.0000

Balanced accuracy: 0.4344

```



Clean-to-FGSM degradation at epsilon 0.030:



```text

Detected falls decreased from 57 to 0

Missed falls increased from 32 to 89

False fall alarms increased from 32 to 119

Recall decreased from 0.6404 to 0.0000

Missed fall rate increased from 0.3596 to 1.0000

F1-score decreased from 0.6404 to 0.0000

Balanced accuracy decreased from 0.8026 to 0.4344

```



At this epsilon, FGSM caused complete loss of fall recall in the window-level binary safety-proxy evaluation.



---



## 8. FGSM Epsilon Sweep Summary



The FGSM epsilon sweep tested:



```text

epsilon = 0.000

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030

```



FGSM sweep result:



```text

epsilon=0.000 | seven\_class\_acc=0.659639 | missed\_fall\_rate=0.359551 | false\_alarms=32  | recall=0.640449 | f1=0.640449 | prediction\_change\_rate=0.000000

epsilon=0.005 | seven\_class\_acc=0.411647 | missed\_fall\_rate=0.741573 | false\_alarms=40  | recall=0.258427 | f1=0.302632 | prediction\_change\_rate=0.287149

epsilon=0.010 | seven\_class\_acc=0.238956 | missed\_fall\_rate=0.988764 | false\_alarms=45  | recall=0.011236 | f1=0.014815 | prediction\_change\_rate=0.483936

epsilon=0.020 | seven\_class\_acc=0.062249 | missed\_fall\_rate=1.000000 | false\_alarms=100 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.682731

epsilon=0.030 | seven\_class\_acc=0.010040 | missed\_fall\_rate=1.000000 | false\_alarms=119 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.743976

```



The FGSM sweep shows increasing fall-focused safety-proxy degradation as perturbation strength increases.



---



## 9. PGD Attack Summary



PGD was implemented as a software-level iterative adversarial perturbation applied to processed UT-HAR CSI tensors.



Unlike FGSM, which applies a single gradient-sign update, PGD applies multiple smaller gradient-based updates and projects the perturbation back inside the allowed epsilon range after each step.



Single-epsilon PGD setting:



```text

epsilon = 0.030

alpha = 0.005

pgd\_steps = 10

epochs = 5

device = CPU

```



At epsilon 0.030, the PGD attack produced strong degradation:



```text

Total windows: 996

Fall windows: 89

Non-fall windows: 907



TP / detected falls: 0

FN / missed falls: 89

FP / false fall alarms: 115

TN / correct non-falls: 792



Seven-class accuracy: 0.0000

Binary accuracy: 0.7952

Recall / sensitivity: 0.0000

Missed fall rate: 1.0000

Specificity: 0.8732

False positive rate: 0.1268

Precision: 0.0000

F1-score: 0.0000

Balanced accuracy: 0.4366

```



Clean-to-PGD degradation at epsilon 0.030:



```text

Detected falls decreased from 57 to 0

Missed falls increased from 32 to 89

False fall alarms increased from 32 to 115

Recall decreased from 0.6404 to 0.0000

Missed fall rate increased from 0.3596 to 1.0000

F1-score decreased from 0.6404 to 0.0000

Balanced accuracy decreased from 0.8026 to 0.4366

```



At this epsilon, PGD caused complete loss of fall recall in the window-level binary safety-proxy evaluation.



---



## 10. PGD Epsilon Sweep Summary



The PGD epsilon sweep tested:



```text

epsilon = 0.000

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030

```



For the PGD epsilon sweep:



```text

pgd\_steps = 10

alpha = epsilon / 6

epochs = 5

device = CPU

```



PGD sweep result:



```text

epsilon=0.000 | seven\_class\_acc=0.659639 | missed\_fall\_rate=0.359551 | false\_alarms=32  | recall=0.640449 | f1=0.640449 | prediction\_change\_rate=0.000000

epsilon=0.005 | seven\_class\_acc=0.389558 | missed\_fall\_rate=0.786517 | false\_alarms=43  | recall=0.213483 | f1=0.251656 | prediction\_change\_rate=0.310241

epsilon=0.010 | seven\_class\_acc=0.172691 | missed\_fall\_rate=1.000000 | false\_alarms=70  | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.561245

epsilon=0.020 | seven\_class\_acc=0.013052 | missed\_fall\_rate=1.000000 | false\_alarms=111 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.745984

epsilon=0.030 | seven\_class\_acc=0.000000 | missed\_fall\_rate=1.000000 | false\_alarms=115 | recall=0.000000 | f1=0.000000 | prediction\_change\_rate=0.778112

```



The PGD sweep shows that fall-focused safety-proxy degradation increases as perturbation strength increases.



At epsilon 0.010 and above, PGD caused complete loss of fall recall in this shortened baseline setting.



---



## 11. FGSM vs PGD Comparison



The experiment includes a direct FGSM vs PGD epsilon-sweep comparison.



Comparison summary:



```text

epsilon=0.000 | FGSM missed=0.359551 | PGD missed=0.359551 | FGSM recall=0.640449 | PGD recall=0.640449 | FGSM F1=0.640449 | PGD F1=0.640449

epsilon=0.005 | FGSM missed=0.741573 | PGD missed=0.786517 | FGSM recall=0.258427 | PGD recall=0.213483 | FGSM F1=0.302632 | PGD F1=0.251656

epsilon=0.010 | FGSM missed=0.988764 | PGD missed=1.000000 | FGSM recall=0.011236 | PGD recall=0.000000 | FGSM F1=0.014815 | PGD F1=0.000000

epsilon=0.020 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000

epsilon=0.030 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000

```



At epsilon 0.005, PGD caused slightly stronger degradation than FGSM in missed fall rate, recall, and F1-score.



At epsilon 0.010, PGD reached complete fall-recall loss, while FGSM was already nearly fully degraded.



At epsilon 0.020 and epsilon 0.030, both attacks caused complete fall-recall loss in this shortened baseline setting.



---



## 12. Generated Scripts



```text

scripts/run\_sensefi\_smoke\_test.py

scripts/run\_sensefi\_clean\_baseline\_short.py

scripts/export\_clean\_predictions\_short.py

scripts/compute\_clean\_safety\_metrics.py

scripts/export\_fgsm\_predictions\_short.py

scripts/compute\_fgsm\_safety\_metrics.py

scripts/run\_fgsm\_epsilon\_sweep\_short.py

scripts/plot\_fgsm\_epsilon\_sweep.py

scripts/plot\_fgsm\_epsilon\_combined\_summary.py

scripts/export\_pgd\_predictions\_short.py

scripts/compute\_pgd\_safety\_metrics.py

scripts/run\_pgd\_epsilon\_sweep\_short.py

scripts/plot\_pgd\_epsilon\_sweep.py

scripts/plot\_fgsm\_vs\_pgd\_comparison.py

```



---



## 13. Generated Results



```text

results/clean\_baseline\_short\_metrics.csv

results/clean\_predictions\_short.csv

results/clean\_safety\_proxy\_metrics.csv

results/fgsm\_predictions\_short\_epsilon\_0\_03.csv

results/fgsm\_safety\_proxy\_metrics\_epsilon\_0\_03.csv

results/fgsm\_epsilon\_sweep\_summary.csv

results/pgd\_predictions\_short\_epsilon\_0\_03.csv

results/pgd\_safety\_proxy\_metrics\_epsilon\_0\_03.csv

results/pgd\_epsilon\_sweep\_summary.csv

results/fgsm\_vs\_pgd\_epsilon\_comparison.csv

```



---



## 14. Generated Figures



```text

figures/fgsm\_epsilon\_combined\_safety\_summary.png

figures/fgsm\_epsilon\_vs\_missed\_fall\_rate.png

figures/fgsm\_epsilon\_vs\_false\_alarm\_count.png

figures/fgsm\_epsilon\_vs\_recall.png

figures/fgsm\_epsilon\_vs\_f1\_score.png

figures/pgd\_epsilon\_combined\_safety\_summary.png

figures/pgd\_epsilon\_vs\_missed\_fall\_rate.png

figures/pgd\_epsilon\_vs\_false\_alarm\_count.png

figures/pgd\_epsilon\_vs\_recall.png

figures/pgd\_epsilon\_vs\_f1\_score.png

figures/fgsm\_vs\_pgd\_safety\_comparison.png

```



---



## 15. Main Finding



The first completed attack-safety demo shows that a shortened SenseFi UT-HAR LeNet baseline is highly vulnerable to software-level adversarial perturbations applied to processed CSI tensors.



Both FGSM and PGD substantially increased missed fall rate and reduced fall recall as epsilon increased.



The most safety-relevant observation is that adversarial degradation is not only an accuracy problem. It changes the fall-focused safety-proxy behavior of the model:



```text

missed fall windows increase

fall recall decreases

F1-score collapses

false fall alarms increase

prediction stability decreases

```



This supports the thesis direction of translating adversarial WiFi CSI degradation into healthcare-relevant safety-proxy metrics.



---



## 16. Claim Boundary



This report summarizes a research implementation workflow.



It is not:



```text

clinical validation

medical-device validation

real patient deployment

diagnostic evidence

regulatory evaluation

physical-layer attack validation

packet-level attack validation

preamble-level attack validation

SDR validation

over-the-air validation

event-level fall validation

long-lie validation

```



The attacks in this experiment are software-level adversarial perturbations applied to processed UT-HAR CSI tensors after preprocessing.



This experiment does not reproduce a physical-layer, packet-level, preamble-level, SDR, or over-the-air attack.



The safety metrics are window-level safety-proxy metrics, not event-level clinical fall detection metrics.



---



## 17. Limitations



This phase has several important limitations:



```text

The baseline is a shortened 5-epoch model, not a fully optimized benchmark model.

The evaluation is window-level, not event-level.

The dataset does not provide clinical fall event timing or long-lie timing.

The attacks are applied to processed CSI tensors, not transmitted WiFi signals.

The experiment does not validate real patient monitoring performance.

The experiment does not test physical-world adversarial feasibility.

The experiment uses one dataset and one model as the first reproducible baseline.

```



These limitations are expected for this phase. They define the next research steps rather than invalidate the workflow.



---



## 18. Next Research Steps



Recommended next steps:



```text

perform final GitHub review and polish

prepare thesis-ready result tables

run a longer clean training baseline

rerun FGSM and PGD sweeps on the longer-trained model

compare 5-epoch vs longer-trained robustness

add adversarial training defense

compare defended vs undefended safety-proxy metrics

add window-level vs event-level limitation note

evaluate a second dataset or model after the first pipeline is thesis-ready

```



---



## 19. Current Step Status



This final FGSM/PGD attack-safety lab report summarizes the completed first implementation phase.



Status:



```text

complete

```



Recommended commit message:



```text

Add final FGSM PGD lab report

```

