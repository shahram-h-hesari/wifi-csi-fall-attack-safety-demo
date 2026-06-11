# FGSM Epsilon Sweep Figures Summary



## Purpose



This note summarizes the figures generated from the FGSM epsilon sweep for the WiFi CSI fall detection attack-safety demo.



The goal of these figures is to show how increasing software-level FGSM perturbation strength affects both seven-class activity recognition performance and fall-vs-non-fall safety-proxy metrics.



This is a processed-tensor adversarial stress test. It is not a physical-layer, packet-level, preamble-level, SDR, or over-the-air attack validation.



---



## Input Data



The figures were generated from:



```text

results/fgsm_epsilon_sweep_summary.csv

```



The plotting script was:



```text

scripts/plot_fgsm_epsilon_sweep.py

```



---



## Generated Figures



The following figures were generated and committed:



```text

figures/fgsm_epsilon_vs_missed_fall_rate.png

figures/fgsm_epsilon_vs_false_alarm_count.png

figures/fgsm_epsilon_vs_recall.png

figures/fgsm_epsilon_vs_f1_score.png

```



---



## Epsilon Sweep Values



The sweep tested five FGSM perturbation levels:



```text

epsilon = 0.000

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030

```



---



## Summary Table



| Epsilon | Seven-Class Accuracy | Missed Fall Rate | False Fall Alarms | Recall / Sensitivity | F1-Score | Prediction Change Rate |

|---:|---:|---:|---:|---:|---:|---:|

| 0.000 | 0.6596 | 0.3596 | 32 | 0.6404 | 0.6404 | 0.0000 |

| 0.005 | 0.4116 | 0.7416 | 40 | 0.2584 | 0.3026 | 0.2871 |

| 0.010 | 0.2390 | 0.9888 | 45 | 0.0112 | 0.0148 | 0.4839 |

| 0.020 | 0.0622 | 1.0000 | 100 | 0.0000 | 0.0000 | 0.6827 |

| 0.030 | 0.0100 | 1.0000 | 119 | 0.0000 | 0.0000 | 0.7440 |



---



## Figure Interpretation



The missed fall rate figure shows that fall-related safety degradation increases quickly as FGSM epsilon increases.



At epsilon 0.000, the clean missed fall rate is approximately 0.36. By epsilon 0.010, the missed fall rate is approximately 0.99, meaning nearly all fall windows are missed under that attack setting. At epsilon 0.020 and 0.030, the missed fall rate reaches 1.00.



The false fall alarm count figure shows that false alarms also increase as perturbation strength increases. The clean baseline produces 32 false fall alarms. At epsilon 0.030, this increases to 119 false fall alarms.



The recall figure shows the same degradation from the fall-detection perspective. Clean recall is approximately 0.64. At epsilon 0.010, recall drops to approximately 0.01. At epsilon 0.020 and 0.030, recall becomes 0.00.



The F1-score figure shows that alert usefulness decreases as both missed falls and false alarms increase. Clean F1-score is approximately 0.64. At epsilon 0.010, F1-score drops to approximately 0.015. At epsilon 0.020 and 0.030, F1-score becomes 0.00.



---



## Main Takeaway



The epsilon sweep shows that reporting only seven-class accuracy or attack success rate is not enough for healthcare-relevant WiFi CSI sensing.



A safety-proxy view shows which errors matter:



```text

more missed fall windows

more false fall alarms

lower recall

lower F1-score

lower alert trustworthiness

```



This supports the research motivation for translating adversarial degradation into fall-focused safety-proxy metrics.



---



## Claim Boundary



These figures summarize window-level research metrics from a shortened SenseFi UT-HAR LeNet experiment.



They are not:



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



The current result should be interpreted as a reproducible software pipeline showing how adversarial perturbations can be translated into fall-focused safety-proxy metrics.

