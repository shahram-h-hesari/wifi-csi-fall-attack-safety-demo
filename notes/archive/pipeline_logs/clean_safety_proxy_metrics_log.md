# Clean Fall-vs-Non-Fall Safety-Proxy Metrics Log



## Purpose



This note records the first clean fall-vs-non-fall safety-proxy metric calculation for the WiFi CSI fall detection attack-safety demo.



The goal of this step was to move beyond general machine-learning accuracy and translate the clean SenseFi UT-HAR LeNet prediction output into fall-focused safety-proxy metrics.



This is still a research implementation baseline. These are window-level metrics from a shortened clean baseline run, not clinical validation.



## Input Files



The metric script used the clean prediction export file:



```text

results/clean_predictions_short.csv

```



The generated output file is:



```text

results/clean_safety_proxy_metrics.csv

```



The script used to compute the metrics is:



```text

scripts/compute_clean_safety_metrics.py

```



## Dataset and Model Context



\- Benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark

\- Dataset: UT_HAR_data

\- Model: LeNet

\- Training duration: 5 epochs

\- Device: CPU

\- Prediction split: SenseFi validation + test loader

\- Total prediction rows: 996



The original SenseFi configuration uses 200 epochs, so this result should be treated as a shortened reproducibility baseline, not final benchmark performance.



## Binary Fall Mapping



UT-HAR is a seven-class activity recognition dataset:



```text

0 = lie down

1 = fall

2 = walk

3 = pickup

4 = run

5 = sit down

6 = stand up

```



For the safety-proxy layer, the labels were mapped into a binary fall-vs-non-fall task:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



This mapping allows the experiment to report whether the model missed fall windows or generated false fall alarms.



## Clean Confusion Matrix



The clean binary fall-vs-non-fall confusion matrix was:



```text

TP / detected falls: 57

FN / missed falls: 32

FP / false fall alarms: 32

TN / correct non-falls: 875

```



The total number of windows was:



```text

Total windows: 996

Fall windows: 89

Non-fall windows: 907

```



## Clean Safety-Proxy Metrics



```text

Accuracy: 0.9357

Recall / sensitivity: 0.6404

Missed fall rate: 0.3596

Specificity: 0.9647

False positive rate: 0.0353

Precision: 0.6404

F1-score: 0.6404

Balanced accuracy: 0.8026

False alarm count: 32

Missed fall count: 32

```



## Interpretation



The clean binary fall-vs-non-fall accuracy is high because most windows are non-fall windows and because all non-fall activity classes are grouped together in the binary safety-proxy task.



However, the fall-focused metrics show a more safety-relevant picture. Out of 89 fall windows, the model detected 57 and missed 32. This corresponds to a clean missed fall rate of approximately 35.96% for this shortened 5-epoch baseline.



This result is useful because it shows why overall accuracy alone is not enough for a fall-safety evaluation. A model can look strong under aggregate accuracy while still missing a meaningful number of fall windows.



The current clean result should be improved in later baseline runs by increasing training duration, comparing models, or using stronger training settings. For the attack-safety demo, this clean baseline establishes the reference point before adversarial perturbation is added.



## Claim Boundary



This result is a window-level research safety-proxy evaluation.



It is not clinical validation, medical-device validation, real patient deployment, diagnostic evidence, regulatory evaluation, or evidence of event-level fall detection performance.



The metrics are intended to support research analysis of how clean and adversarial WiFi CSI model behavior can be translated into fall-focused safety-proxy outcomes.



## Next Step



The next technical step is to add an adversarial perturbation stage, beginning with a software-level FGSM attack on the processed CSI tensors.



The later comparison will be:



```text

clean predictions

clean safety-proxy metrics

attacked predictions

attacked safety-proxy metrics

clean-to-attacked safety degradation

```


