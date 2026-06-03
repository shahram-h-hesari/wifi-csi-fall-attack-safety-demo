# UT-HAR Dataset Metadata Audit for Event-Level Safety Metrics



This note audits the local SenseFi / UT-HAR dataset files used in the WiFi CSI Fall Attack-Safety Demo to determine whether the current dataset supports event-level fall-safety metrics beyond window-level safety-proxy metrics.



The goal is to avoid overclaiming. Before creating additional thesis tables or figures, the dataset must be checked for metadata needed to compute event-level outcomes such as detection latency, time-to-detection, delayed detection, long-lie proxy, false alarms per monitoring time, or missed fall events.



---



## 1. Dataset Location



Local dataset path:



```text

third_party/WiFi-CSI-Sensing-Benchmark/Data/UT_HAR

```



The local UT-HAR package contains:



```text

Data/UT_HAR/data/X_train.csv

Data/UT_HAR/data/X_val.csv

Data/UT_HAR/data/X_test.csv

Data/UT_HAR/label/y_train.csv

Data/UT_HAR/label/y_val.csv

Data/UT_HAR/label/y_test.csv

```



Important note: although these files use the `.csv` extension, inspection shows that they are NumPy binary array files.



---



## 2. Local UT-HAR Array Shapes



The local processed UT-HAR files have the following shapes:



| File | Shape | Data Type | Meaning |

|---|---:|---|---|

| `X_train.csv` | `(3977, 250, 90)` | `float64` | Training CSI windows |

| `X_val.csv` | `(496, 250, 90)` | `float64` | Validation CSI windows |

| `X_test.csv` | `(500, 250, 90)` | `float64` | Test CSI windows |

| `y_train.csv` | `(3977,)` | `int64` | Training labels |

| `y_val.csv` | `(496,)` | `int64` | Validation labels |

| `y_test.csv` | `(500,)` | `int64` | Test labels |



This confirms that the current experiment uses processed window-level CSI tensors and corresponding activity labels.



---



## 3. Activity Label Mapping



The SenseFi README describes UT-HAR as a seven-class dataset with the following activity classes:



```text

lie down, fall, walk, pickup, run, sit down, stand up

```



For the current fall-vs-non-fall safety-proxy evaluation, the demo treats:



```text

fall = positive class

all other activities = non-fall

```



Based on the known UT-HAR class ordering used in this workflow:



| Label | Activity | Binary Safety-Proxy Mapping |

|---:|---|---|

| 0 | lie down | non-fall |

| 1 | fall | fall |

| 2 | walk | non-fall |

| 3 | pickup | non-fall |

| 4 | run | non-fall |

| 5 | sit down | non-fall |

| 6 | stand up | non-fall |



---



## 4. Label Distribution in Local Files



### Training Split



| Label | Count |

|---:|---:|

| 0 | 525 |

| 1 | 354 |

| 2 | 1172 |

| 3 | 396 |

| 4 | 967 |

| 5 | 320 |

| 6 | 243 |



### Validation Split



| Label | Count |

|---:|---:|

| 0 | 66 |

| 1 | 44 |

| 2 | 146 |

| 3 | 49 |

| 4 | 121 |

| 5 | 40 |

| 6 | 30 |



### Test Split



| Label | Count |

|---:|---:|

| 0 | 66 |

| 1 | 45 |

| 2 | 147 |

| 3 | 50 |

| 4 | 121 |

| 5 | 40 |

| 6 | 31 |



This confirms that the local test split contains 45 fall-labeled windows and 455 non-fall windows.



---



## 5. Metadata Search Result



The local dataset was searched for metadata filenames and source/documentation terms related to event-level evaluation.



The following metadata terms were not found as local dataset files:



```text

timestamp

time

duration

subject_id

subject

trial_id

trial

event_id

event

recording_id

fall_start

fall_end

window_start

window_end

annotation

metadata

meta

```



The local `UT_HAR.zip` archive contains only the processed data and label folders:



```text

UT_HAR/

UT_HAR/.ipynb_checkpoints/

UT_HAR/data/

UT_HAR/data/X_test.csv

UT_HAR/data/X_train.csv

UT_HAR/data/X_val.csv

UT_HAR/label/

UT_HAR/label/y_test.csv

UT_HAR/label/y_train.csv

UT_HAR/label/y_val.csv

```



No separate metadata file, annotation file, subject table, trial table, event table, timestamp file, or recording-duration file was found in the local UT-HAR copy.



---



## 6. Metrics Supported by the Current Local Dataset



Because the current local UT-HAR files provide processed windows and labels, the dataset supports window-level classification and window-level safety-proxy metrics.



Supported metrics include:



| Metric Type | Supported? | Reason |

|---|---|---|

| Seven-class accuracy | Yes | True and predicted activity labels are available |

| Binary fall-vs-non-fall accuracy | Yes | Fall labels can be mapped to binary fall/non-fall |

| TP, FN, FP, TN | Yes | Window-level true and predicted binary labels are available |

| Recall / sensitivity | Yes | Computable from TP and FN |

| Missed fall rate | Yes | Computable as FN / fall windows |

| Specificity | Yes | Computable from TN and FP |

| False positive rate | Yes | Computable from FP and TN |

| Precision | Yes | Computable from TP and FP |

| F1-score | Yes | Computable from precision and recall |

| Balanced accuracy | Yes | Computable from sensitivity and specificity |

| False fall alarm count | Yes | Computable as window-level FP count |

| Prediction change rate under attack | Yes | Clean and attacked predictions can be compared |



These metrics are valid as \*\*window-level safety-proxy metrics\*\*.



---



## 7. Metrics Not Supported by the Current Local Dataset



The current local UT-HAR copy does not provide enough metadata for stronger event-level clinical-safety metrics.



| Metric Type | Supported? | Missing Requirement |

|---|---|---|

| Event-level fall detection rate | No | Requires fall event IDs or trial/event grouping |

| Event-level missed fall count | No | Requires event-level ground truth |

| Detection latency / time-to-detection | No | Requires timestamps or fall onset/impact time |

| Delayed detection rate | No | Requires time threshold and event timing |

| Long-lie risk proxy | No | Requires fall time, alert time, and delay threshold |

| False alarms per hour/day | No | Requires recording duration or monitoring time |

| Subject-level robustness | No | Requires subject IDs |

| Trial-level robustness | No | Requires trial IDs |

| Cross-subject generalization | No | Requires subject split metadata |

| Room/session-level analysis | No | Requires room/session/recording IDs |



These are not rejected as unimportant. They are important safety metrics, but the current local dataset does not provide the metadata required to compute them defensibly.



---



## 8. Interpretation for Thesis and GitHub



The current SenseFi / UT-HAR implementation supports a strong first-stage research workflow:



```text

processed WiFi CSI windows

â†’ clean model predictions

â†’ software-level adversarial perturbations

â†’ attacked predictions

â†’ binary fall-vs-non-fall safety-proxy metrics

```



This supports the current thesis contribution: translating adversarial degradation into fall-vs-non-fall safety-proxy outcomes such as missed fall rate, false fall alarm count, recall, precision, F1-score, and balanced accuracy.



However, the current local UT-HAR dataset does not support event-level clinical claims. Therefore, the current results should continue to be described as:



```text

window-level safety-proxy evaluation

```



not:



```text

event-level fall detection validation

clinical fall detection validation

long-lie validation

time-to-alarm validation

real patient monitoring

medical-device evaluation

```



---



## 9. Collaboration and Future Dataset Opportunity



The missing metadata identifies a useful future research direction.



A stronger future dataset or collaboration should seek access to:



```text

subject_id

trial_id

event_id

recording_id

timestamp

window_start_time

window_end_time

fall_start_time

fall_impact_time

alert_time or model detection time

recording_duration

room/session metadata

monitoring duration

```



With those fields, future experiments could compute:



```text

event-level missed fall rate

event-level false alarm rate

time-to-detection

delayed detection rate

long-lie risk proxy

false alarms per hour/day

subject-level robustness

trial-level robustness

cross-subject robustness

```



This is a strong collaboration discussion point for future work with healthcare, aging-technology, or home-sensing researchers who may have access to richer event-level annotations.



---



## 10. Claim Boundary



This audit supports the following claim boundary:



The current WiFi CSI Fall Attack-Safety Demo is a research implementation using SenseFi / UT-HAR processed CSI windows. It provides window-level safety-proxy analysis under clean, FGSM, PGD, and defended conditions. It does not provide clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.



---



## 11. Bottom Line



The current local UT-HAR dataset is sufficient for:



```text

window-level fall-vs-non-fall safety-proxy metrics

```



It is not sufficient for:



```text

event-level clinical fall-safety metrics

```



Therefore, Table 7 should distinguish between metrics that are computable now and metrics that require additional dataset metadata or future collaboration.


