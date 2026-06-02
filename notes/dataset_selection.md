# Dataset and Baseline Selection

This document records the first dataset and baseline selection decision for the WiFi CSI fall detection attack-safety demo.

The goal is to select one reproducible WiFi CSI fall-detection or fall-related activity-recognition baseline that can support:

```text
clean WiFi CSI fall detection
→ saved clean predictions
→ adversarial perturbation
→ saved attacked predictions
→ clean-to-attacked clinical-safety metric comparison
```

---

## Current Decision Summary

```text
Selected first baseline: SenseFi / WiFi-CSI-Sensing-Benchmark
Selected first dataset: UT_HAR_data
Selected first model: LeNet
Selected first task: Binary fall vs non-fall classification
Selected first attack stage: FGSM first, PGD later
Metric scope: Window-level ML metrics and window-level clinical-safety proxy metrics
```

This decision is based on the SenseFi review note. SenseFi is public, PyTorch-based, includes a fall-containing HAR dataset, provides model code and dataset loaders, and can likely be modified to export clean and attacked predictions.

Important limitation:

```text
The first SenseFi/UT-HAR experiment should be described as a window-level safety-proxy demo, not full event-level clinical-safety validation.
```

Event-level metrics such as false alarms per day, detection latency, delayed detection rate, and long-lie risk proxy require timestamps, event IDs, fall impact times, or monitoring-duration metadata that are not confirmed in the visible SenseFi documentation.

---

## 1. Selection Goal

The first baseline should allow us to run a clean WiFi CSI model and export:

```text
y_true
y_pred_clean
prediction scores
binary fall vs non-fall labels
```

After that, the same baseline should allow FGSM and PGD adversarial perturbations so we can compare:

```text
clean missed fall rate vs attacked missed fall rate
clean false alarms vs attacked false alarms
clean precision vs attacked precision
clean recall vs attacked recall
clean F1-score vs attacked F1-score
```

The main goal is not only to report accuracy loss. The main goal is to translate clean-to-attacked model degradation into safety-facing outcomes.

---

## 2. Candidate Baselines

| Candidate | Type | Why It Matters | Current Priority | Current Decision |
|---|---|---|---|---|
| [SenseFi / WiFi-CSI-Sensing-Benchmark](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark) | WiFi CSI benchmark | General reusable WiFi CSI deep-learning benchmark with multiple models and datasets | Highest | Use as first baseline |
| FallDeFi | WiFi CSI fall detection | Directly focused on commodity WiFi fall detection | High | Review as second baseline or fallback |
| CSI-Bench | WiFi CSI benchmark | Newer large-scale in-the-wild benchmark; useful for later extension | Medium | Defer until first SenseFi demo works |
| Other WiFi CSI fall/HAR repository | Backup | Can be used if the main candidates are not practical | Medium | Use only if SenseFi/FallDeFi are blocked |

---

## 3. Selection Criteria

| Criterion | Requirement | Why It Matters | SenseFi/UT-HAR Status |
|---|---|---|---|
| Public code | Required | Needed for reproducible implementation | Yes |
| Dataset access or clear download path | Required | Needed to run experiments | Yes, processed data linked externally |
| Fall or fall-related class | Required | Needed for fall vs non-fall evaluation | Yes, UT-HAR includes `fall` |
| Clean inference can run | Required | Needed before adversarial attack | Likely yes through `run.py`; local run still pending |
| Can save `y_true` | Required | Needed for all metrics | Yes, with modification |
| Can save `y_pred_clean` | Required | Needed for clean baseline | Yes, with modification |
| Prediction scores/probabilities | Preferred | Useful for thresholding and AUC-PR | Yes, with modification using model outputs/softmax |
| PyTorch or modifiable ML framework | Preferred | Easier to add FGSM/PGD | Yes |
| Clear preprocessing steps | Preferred | Needed for reproducibility | Partially documented |
| Timestamps or event IDs | Preferred | Needed for event-level metrics and latency | Not confirmed |
| License/reuse terms available | Preferred | Needed for responsible public repo documentation | Code license and dataset links available; local license notes still need recording |
| Compatible with adversarial perturbation | Preferred | Needed for attack-safety demo | Yes, software-level processed-tensor FGSM/PGD appears feasible |

---

## 4. Review Table

| Candidate | Code Available? | Dataset Available? | Fall Label? | Non-Fall Labels? | PyTorch? | Clean Inference? | Can Save Predictions? | Timestamps/Event IDs? | License Clear? | Attack Feasible? | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SenseFi | Yes | Yes, externally linked | Yes, in UT-HAR and NTU-Fi_HAR | Yes | Yes | Likely yes; local run pending | Yes, with code modification | Not confirmed | Mostly yes; document exact terms | Yes, software-level FGSM/PGD feasible | Use as first baseline |
| FallDeFi | TBD | TBD | Expected, direct fall-detection focus | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Review as second baseline or fallback |
| CSI-Bench | TBD | TBD | Expected as task-level benchmark, verify later | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Defer until SenseFi demo works |
| Other | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Backup only |

---

## 5. Candidate 1: SenseFi Review

| Review Item | Finding |
|---|---|
| Repository URL | [xyanchen/WiFi-CSI-Sensing-Benchmark](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark) |
| Paper / benchmark reference | [SenseFi: A library and benchmark on deep-learning-empowered WiFi human sensing](https://www.sciencedirect.com/science/article/pii/S2666389923000405) |
| arXiv version | [arXiv:2207.07859](https://arxiv.org/abs/2207.07859) |
| Dataset / data source | [Mendeley Data: SenseFi](https://data.mendeley.com/datasets/dzvgyxkx2f/1) |
| Dataset DOI | [10.17632/dzvgyxkx2f.1](https://doi.org/10.17632/dzvgyxkx2f.1) |
| Dataset candidate inside SenseFi | `UT_HAR_data` |
| First model candidate | `LeNet` |
| Fall label exists? | Yes |
| Fall-related label exists? | Yes |
| Binary fall vs non-fall mapping possible? | Yes |
| PyTorch code available? | Yes |
| Clean training script available? | Yes, through `run.py` |
| Clean inference script available? | Partially; `run.py` includes testing after training |
| Prediction scores available? | Yes, with modification using model outputs/softmax |
| Can save `y_true`? | Yes, with modification |
| Can save `y_pred_clean`? | Yes, with modification |
| Timestamps available? | Not confirmed |
| Event IDs available? | Not confirmed |
| License clear? | Code license is MIT; dataset license should be recorded before use |
| FGSM/PGD attack feasible? | Yes, as software-level attacks on processed CSI tensors |
| Main limitation | Event-level timing metrics are not confirmed |
| Decision | Use as first baseline |

---

## 6. Candidate 2: FallDeFi Review

FallDeFi remains important because it is directly focused on commodity WiFi fall detection.

Current status:

```text
Not yet reviewed in this selection file.
```

Reason for deferral:

```text
SenseFi currently appears easier for the first PyTorch-based clean-vs-attacked safety-proxy demo. FallDeFi should be reviewed as a second baseline or fallback after the first SenseFi clean baseline is attempted.
```

| Review Item | Finding |
|---|---|
| Paper URL | TBD |
| Code repository URL | TBD |
| Dataset URL | TBD |
| Dataset available? | TBD |
| Fall label exists? | TBD |
| Non-fall labels exist? | TBD |
| Binary fall vs non-fall mapping possible? | TBD |
| Implementation language | TBD |
| PyTorch available? | TBD |
| TensorFlow available? | TBD |
| MATLAB or other framework? | TBD |
| Clean training script available? | TBD |
| Clean inference script available? | TBD |
| Prediction scores available? | TBD |
| Can save `y_true`? | TBD |
| Can save `y_pred_clean`? | TBD |
| Timestamps available? | TBD |
| Event IDs or trial IDs available? | TBD |
| License clear? | TBD |
| FGSM/PGD attack feasible? | TBD |
| Main limitation | TBD |
| Decision | Review later as second baseline / fallback |

---

## 7. Candidate 3: CSI-Bench Review

CSI-Bench remains useful as a later extension because it is newer and more in-the-wild, but it should not be the first implementation target.

Current status:

```text
Deferred until the first SenseFi/UT-HAR clean-vs-attacked safety-proxy demo works.
```

| Review Item | Finding |
|---|---|
| Project page | TBD |
| Paper URL | TBD |
| Code repository URL | TBD |
| Dataset URL | TBD |
| Dataset available? | TBD |
| Fall detection task available? | TBD |
| Breathing/respiration task available? | TBD |
| Binary fall vs non-fall mapping possible? | TBD |
| PyTorch code available? | TBD |
| Clean inference script available? | TBD |
| Prediction scores available? | TBD |
| Timestamps available? | TBD |
| Event IDs available? | TBD |
| License clear? | TBD |
| FGSM/PGD attack feasible? | TBD |
| Main limitation | TBD |
| Decision | Use later / Defer |

---

## 8. Binary Fall vs Non-Fall Mapping

For the first selected dataset, use UT-HAR labels from SenseFi.

```text
fall = 1
all other activities = 0
```

### UT-HAR Binary Mapping

| Original Label | Binary Safety Label | Notes |
|---|---:|---|
| fall | 1 | True fall class |
| lie down | 0 | High-risk confusion class; may resemble fall-like CSI patterns |
| walk | 0 | Non-fall activity of daily living |
| pickup | 0 | Bending/pickup may trigger false alarms |
| run | 0 | Non-fall movement |
| sit down | 0 | Fall-confusable transition activity |
| stand up | 0 | Non-fall transition activity |

### NTU-Fi_HAR Backup Mapping

If UT-HAR is blocked, NTU-Fi_HAR can be considered as a backup fall-containing dataset.

| Original Label | Binary Safety Label | Notes |
|---|---:|---|
| fall | 1 | True fall class |
| box | 0 | Non-fall activity |
| circle | 0 | Non-fall activity |
| clean | 0 | Non-fall activity |
| run | 0 | Non-fall movement |
| walk | 0 | Non-fall activity of daily living |

---

## 9. Selection Decision

Final selected baseline:

```text
Selected baseline: SenseFi / WiFi-CSI-Sensing-Benchmark
Dataset name: UT_HAR_data
Model: LeNet
Source repository: https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark
Paper reference: SenseFi: A library and benchmark on deep-learning-empowered WiFi human sensing
Reason for selection: SenseFi is public, PyTorch-based, includes UT-HAR with a fall class and clinically relevant non-fall confusion classes, and can likely be modified to export clean and attacked predictions for window-level safety-proxy evaluation.
```

Candidates deferred:

| Candidate | Reason Deferred |
|---|---|
| FallDeFi | Important direct fall-detection source, but SenseFi appears easier for the first PyTorch-based implementation. Review as second baseline or fallback. |
| CSI-Bench | Promising newer benchmark, but better suited for later extension after the first demo works. |
| Other WiFi CSI fall/HAR repo | Backup only if SenseFi and FallDeFi become blocked. |

---

## 10. Metric Feasibility

After choosing SenseFi/UT-HAR, the first metric scope should be window-level.

| Metric | Possible? | Required Data | Notes |
|---|---|---|---|
| Accuracy | Yes | `y_true`, `y_pred` | Window/sample-level |
| Precision | Yes, with modification | TP, FP | Window-level after prediction export |
| Recall / sensitivity | Yes, with modification | TP, FN | Window-level after binary fall mapping |
| F1-score | Yes, with modification | TP, FP, FN | Window-level |
| Specificity | Yes, with modification | TN, FP | Window-level |
| Missed fall rate | Yes, as safety proxy | FN, TP | Window-level missed fall proxy |
| False alarm count | Yes, as safety proxy | FP | Window-level false alarm proxy |
| False positive rate | Yes, with modification | FP, TN | Window-level |
| False alarms per day | Not confirmed | FP, monitoring duration | Requires monitoring duration |
| False alarms per user-day | Not confirmed | FP, user-days | Requires users and duration |
| Event-level recall | Not confirmed | Event IDs | Requires event annotations |
| Event-level missed fall rate | Not confirmed | Event IDs | Requires event annotations |
| Detection latency | Not confirmed | Fall impact time, alert time | Requires timestamps |
| Delayed detection rate | Not confirmed | Latency threshold | Requires timestamps |
| Long-lie risk proxy | Not confirmed | Missed events and severe delays | Requires event/timestamp data |

Recommended first metric wording:

```text
window-level ML metrics and window-level clinical-safety proxy metrics
```

Do not describe the first SenseFi/UT-HAR demo as full event-level clinical-safety evaluation.

---

## 11. Decision Options

The selected decision is:

```text
Use as first baseline
```

Reason:

```text
SenseFi/UT_HAR_data is accessible, fall labels are documented, binary fall vs non-fall mapping is possible, PyTorch models are available, and clean prediction export appears feasible with code modification.
```

Other options remain available if blocked:

```text
Use FallDeFi as second baseline or fallback.
Use CSI-Bench later as a larger in-the-wild extension.
```

---

## 12. Completion Criteria

This selection step is complete when:

- [x] SenseFi has been reviewed
- [x] One first baseline has been selected
- [x] Dataset/code access path has been identified
- [x] Fall or fall-related label has been confirmed
- [x] Binary `fall` vs `non-fall` mapping is possible
- [x] Clean prediction export appears possible with code modification
- [x] Metric feasibility is documented
- [x] Limitations are documented
- [ ] FallDeFi has been reviewed as a second baseline or fallback
- [ ] CSI-Bench has been reviewed as a later extension option
- [ ] Local dataset download and clean baseline run have been tested

Note:

```text
The first selection decision is complete enough to move to the clean baseline attempt. FallDeFi and CSI-Bench can be reviewed later as second-baseline or extension tasks.
```

---

## 13. Next Step

Move to:

```text
Run clean WiFi CSI fall-detection baseline
```

The next implementation target is:

```text
Dataset: UT_HAR_data
Model: LeNet
Command pattern: python run.py --model LeNet --dataset UT_HAR_data
```

The next implementation goal is to produce:

```text
results/predictions_clean.csv
results/metrics_clean.csv
results/clean_baseline_summary.md
```

Required modification:

```text
Modify the SenseFi test/evaluation loop to export:
sample_id
true_label
binary_true_label
clean_prediction
clean_score
```

If timestamps, event IDs, subject IDs, or environment IDs are unavailable, use:

```text
NA
```

Do not remove those columns from output CSVs.

---

## 14. Claim Boundary

This document supports research implementation planning only.

It does not claim:

- clinical validation,
- medical-device readiness,
- diagnostic capability,
- real patient deployment,
- regulatory approval,
- formal clinical standard compliance,
- physical-world adversarial attack validation, or
- event-level clinical fall-safety validation.

This document only concludes that SenseFi/UT-HAR appears suitable for a first reproducible **window-level fall/non-fall clean-vs-attacked safety-proxy demo**.

Use careful wording:

```text
research implementation baseline
window-level safety-proxy evaluation
clinically motivated metric translation
software-level adversarial perturbation
processed CSI tensor attack
clean-to-attacked safety degradation
```

Avoid overclaiming:

- Do not describe this selection as clinical fall-detection validation.
- Do not imply real patient monitoring or real home deployment.
- Do not describe the experiment as medical-device evaluation.
- Do not describe FGSM/PGD on processed CSI tensors as a physical-layer packet attack.
- Do not describe the experiment as an over-the-air wireless attack.
- Do not call this framework a formal clinical standard.
- Do not claim full event-level clinical-safety evaluation unless timestamps, event IDs, and monitoring duration are available.

Important limitation:

```text
Event-level metrics such as false alarms per day, detection latency, delayed detection rate, and long-lie risk proxy require timestamps, event IDs, fall impact times, or monitoring-duration metadata that are not confirmed in the visible SenseFi documentation.
```
