# SenseFi Review for Fall Detection Attack-Safety Demo

This note reviews SenseFi / WiFi-CSI-Sensing-Benchmark as a candidate starting point for the fall detection attack-safety demo.

The goal is to determine whether SenseFi can support:

```text
clean WiFi CSI fall detection
→ saved clean predictions
→ FGSM/PGD adversarial perturbation
→ attacked predictions
→ clean-to-attacked clinical-safety metric comparison
```

---

## 1. Review Goal

SenseFi is being reviewed as a possible first implementation baseline because it may provide reusable WiFi CSI datasets, deep-learning model code, and benchmark structure.

This review should answer:

```text
Can SenseFi be used to run a clean WiFi CSI fall or fall-related activity baseline and export predictions for later adversarial testing?
```

---

## 2. Repository and Reference

| Item | Finding |
|---|---|
| Repository URL | [xyanchen/WiFi-CSI-Sensing-Benchmark](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark) |
| Paper / benchmark reference | [SenseFi: A library and benchmark on deep-learning-empowered WiFi human sensing](https://www.sciencedirect.com/science/article/pii/S2666389923000405) |
| Journal / publisher | [Patterns, Cell Press / Elsevier, Volume 4, Issue 3, Article 100703, 2023](https://www.sciencedirect.com/science/article/pii/S2666389923000405) |
| Paper DOI | [10.1016/j.patter.2023.100703](https://doi.org/10.1016/j.patter.2023.100703) |
| arXiv version | [arXiv:2207.07859](https://arxiv.org/abs/2207.07859) |
| Authors | Jianfei Yang; Xinyan Chen; Dazhuo Wang; Han Zou; Chris Xiaoxuan Lu; Sumei Sun; Lihua Xie |
| Dataset / data source | [Mendeley Data: SenseFi: A Library and Benchmark on Deep Learning Empowered WiFi Human Sensing](https://data.mendeley.com/datasets/dzvgyxkx2f/1) |
| Dataset DOI | [10.17632/dzvgyxkx2f.1](https://doi.org/10.17632/dzvgyxkx2f.1) |
| Code archive / Zenodo DOI | [10.5281/zenodo.7501869](https://doi.org/10.5281/zenodo.7501869) |
| Main framework | WiFi CSI human-sensing benchmark and model-zoo library |
| Programming language | Python |
| Deep-learning library | PyTorch |
| Available models | MLP; LeNet/CNN; ResNet18; ResNet50; ResNet101; RNN; GRU; LSTM; BiLSTM; CNN+GRU; ViT |
| Available datasets | UT_HAR_data; NTU-Fi_HAR; NTU-Fi-HumanID; Widar |
| Code license | [MIT license](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/LICENSE) |
| Dataset license | [CC BY 4.0 on Mendeley Data](https://data.mendeley.com/datasets/dzvgyxkx2f/1) |
| Initial relevance to this project | High: SenseFi includes reusable WiFi CSI model code, processed datasets, and fall-containing or fall-related HAR datasets that may support clean fall vs non-fall baseline evaluation. |
| Initial limitation | SenseFi is a general WiFi CSI benchmark, not a clinical fall-safety benchmark; event-level timestamps, false alarms per day, and detection latency still need to be checked. |

---

## 3. Dataset Availability

| Question | Finding |
|---|---|
| Does SenseFi provide dataset download instructions? | Yes. The SenseFi GitHub README includes a **Download Processed Data** section and instructs users to download and organize the processed datasets into a `Benchmark/Data/` structure. The README also links to processed datasets and pretrained weights. |
| Are datasets included directly or linked externally? | The datasets are **linked externally**, not stored directly in the GitHub repository. The GitHub README links to processed datasets through Google Drive, and the paper/data record links to Mendeley Data. |
| Is access public? | Yes, the processed dataset record is publicly available through Mendeley Data: [SenseFi: A Library and Benchmark on Deep Learning Empowered WiFi Human Sensing](https://data.mendeley.com/datasets/dzvgyxkx2f/1). The Mendeley page provides a `Download All` option and lists the dataset DOI as [10.17632/dzvgyxkx2f.1](https://doi.org/10.17632/dzvgyxkx2f.1). |
| Is the dataset size manageable? | TBD after download. The GitHub README lists processed datasets and sample counts, including UT-HAR with 3,977 training samples and 996 test samples, NTU-Fi_HAR with 936 training samples and 264 test samples, NTU-Fi-HumanID with 546 training samples and 294 test samples, and Widar with 34,926 training samples and 8,726 test samples. This suggests UT-HAR and NTU-Fi_HAR are likely manageable first-start candidates, but actual file size should still be checked before implementation. |
| Is the data format documented? | Partially yes. The GitHub README documents expected folder structure and dataset shapes. UT-HAR is listed as CSI size `1 x 250 x 90`; NTU-Fi_HAR and NTU-Fi-HumanID are listed as CSI size `3 x 114 x 500`; Widar is listed as BVP size `22 x 20 x 20`. The README also notes that UT-HAR data files are CSV format but should be loaded through the provided code because they may not be readable in Excel due to encoding. |
| Are preprocessing steps documented? | Partially yes. The README provides dataset organization and run instructions, while `dataset.py` shows important loading/preprocessing steps. For UT-HAR, the loader reshapes data to `1 x 250 x 90` and applies min-max normalization. For NTU-Fi-style data, the loader loads `.mat` files, normalizes CSI amplitude, downsamples from 2000 to 500 by sampling every fourth point, and reshapes to `3 x 114 x 500`. For Widar, the loader reads CSV files, normalizes values, and reshapes to `22 x 20 x 20`. |
| Are labels documented? | Yes for the benchmark-level classes. The GitHub README documents UT-HAR classes as `lie down`, `fall`, `walk`, `pickup`, `run`, `sit down`, and `stand up`. It documents NTU-Fi_HAR classes as `box`, `circle`, `clean`, `fall`, `run`, and `walk`. NTU-Fi-HumanID is a 14-subject identification dataset, and Widar contains 22 gesture classes. For this project, UT-HAR and NTU-Fi_HAR are the most relevant SenseFi datasets because both include a `fall` class and non-fall activity classes. |

---

## 4. Fall Label Review

| Question | Finding |
|---|---|
| Does SenseFi include a fall label? | Yes. SenseFi includes at least two relevant human-activity-recognition datasets with a `fall` class: **UT-HAR** and **NTU-Fi_HAR**. The SenseFi README lists UT-HAR classes as `lie down`, `fall`, `walk`, `pickup`, `run`, `sit down`, and `stand up`. It lists NTU-Fi_HAR classes as `box`, `circle`, `clean`, `fall`, `run`, and `walk`. |
| Does it include a fall-related activity label? | Yes. UT-HAR includes several fall-related or fall-confusable activities, especially `lie down`, `sit down`, `stand up`, and `pickup`. NTU-Fi_HAR includes `fall` plus non-fall motion classes such as `box`, `circle`, `clean`, `run`, and `walk`. |
| Which dataset inside SenseFi is most relevant? | **UT-HAR is the best first candidate** because it has 7 activity classes and includes both `fall` and clinically important fall-confusion classes such as `lie down`, `sit down`, and `stand up`. **NTU-Fi_HAR is the second candidate** because it also includes `fall`, but its non-fall labels are less directly related to fall-safety confusion. |
| Are non-fall activity labels available? | Yes. UT-HAR has multiple non-fall labels: `lie down`, `walk`, `pickup`, `run`, `sit down`, and `stand up`. NTU-Fi_HAR has non-fall labels: `box`, `circle`, `clean`, `run`, and `walk`. |
| Can labels be converted to binary `fall` vs `non-fall`? | Yes. Both UT-HAR and NTU-Fi_HAR can be converted into binary labels by assigning `fall = 1` and all other activity labels as `non-fall = 0`. This supports window-level fall/non-fall classification and allows calculation of missed fall rate, false alarm count, precision, recall, F1-score, and confusion matrix. |

---

### Candidate Dataset Priority

| Dataset | Fall Label? | Non-Fall Labels | Priority | Reason |
|---|---|---|---|---|
| UT-HAR | Yes | `lie down`; `walk`; `pickup`; `run`; `sit down`; `stand up` | First choice | Best first candidate because it includes fall plus realistic confusion classes such as lying down, sitting down, standing up, and pickup. |
| NTU-Fi_HAR | Yes | `box`; `circle`; `clean`; `run`; `walk` | Second choice | Useful fallback because it includes fall, but the non-fall classes are less directly aligned with clinical fall-confusion scenarios. |
| NTU-Fi-HumanID | No fall class | Subject identity labels | Not suitable for first fall demo | Human identification dataset, not fall detection. |
| Widar | No fall class | Gesture classes | Not suitable for first fall demo | Gesture-recognition dataset, not fall detection. |

---

### Proposed Binary Mapping: UT-HAR

| Original Label | Binary Safety Label | Notes |
|---|---:|---|
| fall | 1 | True fall class |
| lie down | 0 | High-risk confusion class; may look similar to fall in CSI patterns |
| walk | 0 | Non-fall activity of daily living |
| pickup | 0 | Important confusion class; bending/pickup may trigger false alarms |
| run | 0 | Non-fall movement |
| sit down | 0 | Important transition activity; may be confused with fall |
| stand up | 0 | Non-fall transition activity |

---

### Proposed Binary Mapping: NTU-Fi_HAR

| Original Label | Binary Safety Label | Notes |
|---|---:|---|
| fall | 1 | True fall class |
| box | 0 | Non-fall activity |
| circle | 0 | Non-fall activity |
| clean | 0 | Non-fall activity |
| run | 0 | Non-fall movement |
| walk | 0 | Non-fall activity of daily living |

---

### Initial Decision

```text
SenseFi should remain a high-priority candidate for the first clean fall/non-fall baseline.
```

Recommended first dataset:

```text
UT-HAR
```

Reason:

```text
UT-HAR includes a fall class and multiple clinically relevant non-fall confusion classes. It is more suitable than NTU-Fi_HAR for the first fall safety translation demo because missed falls and false fall alarms can be interpreted against activities such as lie down, sit down, stand up, pickup, walk, and run.
```

Limitation:

```text
The SenseFi README documents class labels and sample counts, but event-level timestamps, continuous monitoring duration, and fall impact times still need to be checked. Therefore, the first SenseFi experiment may support window-level clinical-safety proxies rather than full event-level metrics such as detection latency or false alarms per day.
```

Key finding:

```text
SenseFi is usable for fall/non-fall mapping, and UT-HAR should be the first candidate inside SenseFi.
```

Reference:

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [SenseFi paper in Patterns / Cell Press](https://www.sciencedirect.com/science/article/pii/S2666389923000405)
- [SenseFi arXiv version](https://arxiv.org/abs/2207.07859)

---

## 5. Code Usability Review

| Question | Finding |
|---|---|
| Can the repo be cloned? | Yes. The repository is public and can be cloned from [xyanchen/WiFi-CSI-Sensing-Benchmark](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark). |
| Is installation documented? | Partially yes. The README provides a **Requirements** section and a **Run** section. It instructs users to install PyTorch/torchvision and then run `pip install -r requirements.txt`. It also notes that the code runs best on Linux/Ubuntu and may require path changes on Windows. |
| Are dependencies listed? | Yes. The repository includes `requirements.txt`, which lists `scipy==1.7.3`, `numpy==1.21.5`, and `einops==0.4.0`. The README separately states that PyTorch and torchvision are required, specifically `pytorch==1.12.0` and `torchvision==0.13.0`. |
| Is PyTorch used? | Yes. The README states that SenseFi is implemented in PyTorch. The code imports `torch`, `torch.nn`, `torch.utils.data`, and defines multiple PyTorch `nn.Module` models. |
| Is there a clean training script? | Yes. The main supervised training and testing script is `run.py`. It supports the command `python run.py --model [model name] --dataset [dataset name]`. The script loads data/model using `load_data_n_model()`, trains the model, and then runs testing. |
| Is there a clean inference script? | Partially. There is no separate standalone inference-only script. However, `run.py` includes a `test()` function that runs model evaluation on the test loader after training. This function can be modified to export clean predictions. |
| Can the model output prediction scores? | Yes, with modification. In `run.py`, the model produces `outputs = model(inputs)`, and predictions are currently generated with `torch.argmax(outputs, dim=1)`. These `outputs` can be converted to scores or probabilities using `torch.softmax(outputs, dim=1)` before saving. |
| Can `y_true` be saved? | Yes, with modification. The `test()` loop already receives `labels` from the test loader. These labels can be saved as `y_true` or converted into binary `fall` vs `non-fall` labels before export. |
| Can `y_pred_clean` be saved? | Yes, with modification. The `test()` function already computes `predict_y = torch.argmax(outputs, dim=1)`. This value can be saved as `y_pred_clean`. |
| Can the code be modified to save CSV outputs? | Yes. The current code prints validation accuracy and loss but does not save prediction CSVs by default. A practical next step is to modify `test()` or create a wrapper script that saves `sample_id`, `true_label`, `binary_true_label`, `clean_prediction`, and `clean_score` into `results/predictions_clean.csv`. |

---

### Code Usability Summary

SenseFi is usable as a first implementation candidate because it provides:

- public GitHub code,
- documented dataset organization,
- PyTorch-based model implementations,
- supervised training/testing through `run.py`,
- reusable dataset loaders,
- multiple model choices,
- UT-HAR support with a fall class,
- model outputs that can be converted into prediction scores.

However, SenseFi needs modification for this project because it does not currently export the prediction files required for clinical-safety translation.

The required modification is:

```text
Modify the test/evaluation loop to save:
sample_id
true_label
binary_true_label
clean_prediction
clean_score
```

---

### Recommended First Implementation Choice

Use this starting configuration first:

```bash
python run.py --model LeNet --dataset UT_HAR_data
```

Reason:

```text
UT_HAR_data includes a fall class and clinically relevant non-fall confusion classes. LeNet is a simpler CNN-style model than ResNet or ViT, making it easier to debug before adding FGSM and PGD attacks.
```

Alternative model choices:

```text
MLP      = simplest model, easiest to debug
LeNet    = simple CNN-style model, good first practical choice
ResNet18 = stronger CNN baseline, useful after LeNet works
CNN+GRU  = useful later for temporal modeling
ViT      = useful later, but more complex for first demo
```

---

### Required Code Modification

The current `test()` function should be extended from accuracy-only evaluation to prediction export.

Current behavior:

```text
model input
→ outputs
→ argmax prediction
→ validation accuracy/loss printed
```

Needed behavior:

```text
model input
→ outputs
→ clean prediction
→ clean score
→ save y_true
→ save y_pred_clean
→ save prediction score
→ export CSV
```

Target output file:

```text
experiments/fall_detection_attack_safety_demo/results/predictions_clean.csv
```

Required columns:

```csv
sample_id,timestamp,event_id,subject_id,environment_id,true_label,binary_true_label,clean_prediction,clean_score
```

For unavailable fields, use:

```text
NA
```

---

### Practical Code Feasibility Decision

```text
SenseFi code is usable for the first clean baseline, but it must be modified to save prediction outputs.
```

Reason:

```text
The repository already provides PyTorch models, dataset loaders, and supervised training/testing. The missing piece is prediction export. Because the test loop already has access to model outputs and labels, saving y_true, y_pred_clean, and clean_score should be straightforward.
```

Limitation:

```text
SenseFi appears to support window-level or sample-level prediction export. Event-level metrics such as detection latency, false alarms per day, and long-lie risk still require timestamps, event IDs, or monitoring-duration metadata, which must be checked separately.
```

---

### Reference Links

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [run.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/run.py)
- [util.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/util.py)
- [dataset.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/dataset.py)
- [requirements.txt](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/requirements.txt)
- [UT_HAR_model.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/UT_HAR_model.py)

---

## 6. Attack Feasibility

| Question | Finding |
|---|---|
| Can input tensors be accessed before model inference? | Yes. In `run.py`, both the `train()` and `test()` loops receive `inputs, labels` from the data loader before calling `outputs = model(inputs)`. This means CSI input tensors can be accessed before inference and can be modified for adversarial testing. |
| Is the model differentiable? | Yes. SenseFi uses PyTorch models built with differentiable layers such as `nn.Linear`, `nn.Conv2d`, `nn.ReLU`, `nn.MaxPool2d`, recurrent layers, ResNet-style blocks, and ViT-style modules. UT-HAR models in `UT_HAR_model.py` are PyTorch `nn.Module` classes, so gradients can be computed through the model. |
| Can gradients be computed with respect to CSI input? | Yes, with modification. The current training loop computes `loss.backward()` for model training. For FGSM/PGD, the input tensor can be changed to `inputs.requires_grad_(True)`, then the loss gradient with respect to `inputs` can be used to create adversarial CSI input. |
| Can FGSM be added at input-tensor level? | Yes. FGSM can be added after loading a batch and before attacked inference. The attack can perturb the normalized CSI tensor directly: `x_adv = x + epsilon * sign(gradient_x(loss(model(x), y)))`. This is a software-level adversarial robustness test, not a physical-layer packet or preamble perturbation. |
| Can PGD be added later? | Yes. PGD is feasible because it is an iterative extension of input-gradient attacks. Once FGSM works, PGD can be added by repeatedly applying small FGSM-like steps and projecting the perturbed tensor back into an epsilon-bounded region around the original input. |
| Does preprocessing make attack integration difficult? | Not for a first software-level attack. SenseFi loaders already convert data into PyTorch tensors before model inference. However, preprocessing affects how epsilon should be interpreted. UT-HAR is reshaped to `1 x 250 x 90` and min-max normalized, while NTU-Fi-style data is normalized and downsampled before being reshaped. Therefore, epsilon values should be treated as perturbations on the processed/normalized tensor, not as physical CSI perturbation strength. |

---

### Attack Feasibility Summary

SenseFi is feasible for software-level adversarial testing.

The practical attack workflow is:

```text
load clean CSI tensor
→ enable gradient on input
→ run model
→ compute classification loss
→ compute gradient with respect to input
→ perturb input using FGSM or PGD
→ run model on attacked input
→ save attacked prediction and score
```

This supports the first implementation goal:

```text
clean prediction
→ FGSM/PGD attacked prediction
→ clean-vs-attacked ML metrics
→ clean-vs-attacked clinical-safety metrics
```

---

### Recommended First Attack Target

Use this initial configuration:

```text
Dataset: UT_HAR_data
Model: LeNet
Attack: FGSM
Perturbation level: processed/normalized CSI tensor
```

Reason:

```text
UT_HAR_data includes a fall class and clinically relevant non-fall confusion classes. LeNet is simpler than ResNet or ViT, which makes it easier to debug input-gradient attacks before moving to stronger models.
```

---

### FGSM Implementation Sketch

The current `test()` loop can be adapted into an attacked evaluation loop.

Conceptual FGSM code:

```python
inputs = inputs.to(device)
labels = labels.to(device).long()

inputs.requires_grad_(True)

outputs = model(inputs)
loss = criterion(outputs, labels)

model.zero_grad()
loss.backward()

epsilon = 0.01
inputs_adv = inputs + epsilon * inputs.grad.sign()

outputs_adv = model(inputs_adv)
attacked_prediction = torch.argmax(outputs_adv, dim=1)
attacked_score = torch.softmax(outputs_adv, dim=1).max(dim=1).values
```

Recommended epsilon values to test first:

```text
0.001
0.005
0.01
0.05
```

The correct epsilon scale should be adjusted after checking the processed CSI tensor range.

---

### PGD Implementation Sketch

PGD can be added after FGSM works.

Conceptual PGD workflow:

```text
start from clean input
repeat for N steps:
    compute gradient
    take small gradient-sign step
    project perturbed input back into epsilon ball
    optionally clamp to valid processed input range
evaluate model on final perturbed input
```

Example parameters to test later:

```text
epsilon = 0.01
alpha = 0.002
steps = 10
```

---

### Important Implementation Notes

- FGSM/PGD should first be implemented as **software-level attacks on processed CSI tensors**.
- This does not represent a physical-world attacker yet.
- Epsilon values are not directly physical signal-power values.
- If inputs are normalized, the attack strength is in normalized feature space.
- If the model uses `model.eval()`, gradients can still be computed as long as the code does not use `torch.no_grad()`.
- The original SenseFi `test()` function does not currently use `torch.no_grad()`, so it can be adapted for gradient-based attack evaluation.
- Prediction export still needs to be added manually.

---

### Required Attack Output Format

FGSM attacked predictions should be saved to:

```text
experiments/fall_detection_attack_safety_demo/results/predictions_fgsm.csv
```

Required columns:

```csv
sample_id,timestamp,event_id,subject_id,environment_id,true_label,binary_true_label,clean_prediction,clean_score,attacked_prediction,attacked_score,attack_type,epsilon
```

Use:

```text
attack_type = FGSM
```

If a field is unavailable, use:

```text
NA
```

---

### Attack Feasibility Decision

```text
FGSM and PGD are feasible in SenseFi with code modification.
```

Reason:

```text
SenseFi exposes input tensors and labels in the training/testing loop, uses differentiable PyTorch models, and computes standard classification loss. Therefore, input-gradient attacks can be added at the processed CSI tensor level.
```

Limitation:

```text
This is a software-level adversarial robustness test on processed CSI tensors. It should not be described as a physical-layer packet perturbation, preamble perturbation, or real over-the-air wireless attack unless a separate physical attack implementation is added later.
```

---

### Reference Links

- [SenseFi GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [run.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/run.py)
- [dataset.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/dataset.py)
- [util.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/util.py)
- [UT_HAR_model.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/UT_HAR_model.py)

---

## 7. Metric Feasibility

| Metric | Possible? | Notes |
|---|---|---|
| Accuracy | Yes | Feasible at the sample/window level. SenseFi’s `run.py` already computes validation accuracy using `predict_y = torch.argmax(outputs, dim=1)` and compares predictions against labels. |
| Precision | Yes, with modification | Feasible after saving `y_true` and `y_pred_clean`. Precision can be computed from TP and FP after converting labels to binary `fall` vs `non-fall`. |
| Recall / sensitivity | Yes, with modification | Feasible after binary fall/non-fall conversion. Recall is especially important because it measures how many true fall samples/windows are detected. |
| F1-score | Yes, with modification | Feasible after computing precision and recall. Useful as a secondary ML metric, but it should not replace missed fall rate and false alarm analysis. |
| Specificity | Yes, with modification | Feasible after computing TN and FP for the non-fall class. Useful for measuring how well the model rejects non-fall activities. |
| Missed fall rate | Yes, as a window-level safety proxy | Feasible after converting `fall` to positive class and all other labels to non-fall. Formula: `FN / (TP + FN)`. This is a safety-relevant proxy, but it is not yet event-level unless event IDs are available. |
| False alarm count | Yes, as a window-level safety proxy | Feasible after converting labels to binary. False alarms are FP cases where non-fall samples/windows are predicted as fall. |
| False alarms per day | Not currently confirmed | Requires monitoring duration or timestamped continuous data. SenseFi’s visible README and loader structure document train/test samples and labels, but not monitoring duration. This should remain unavailable unless timestamps or recording duration are found after downloading the dataset. |
| Event-level recall | Not currently confirmed | Requires event IDs or a way to group multiple windows into the same fall event. SenseFi’s visible documentation supports sample/window-level classification, but event-level identifiers are not clearly documented. |
| Detection latency | Not currently confirmed | Requires fall impact time and alert time. SenseFi’s visible documentation does not show fall impact timestamps or alert timestamps. |
| Long-lie risk proxy | Not currently feasible from documented SenseFi metadata | Requires event-level missed falls, severe detection delay, or time-on-floor proxy. This cannot be responsibly calculated from sample-level labels alone. |

---

### Feasible Metrics for First SenseFi Demo

The first SenseFi-based demo can likely report these metrics:

```text
accuracy
precision
recall / sensitivity
specificity
F1-score
balanced accuracy
confusion matrix
missed fall rate
false alarm count
false positive rate
```

These should be described as:

```text
window-level ML metrics and window-level clinical-safety proxies
```

---

### Metrics That Need More Metadata

The following metrics should be marked as unavailable unless timestamp or event-level metadata is found after downloading the dataset:

```text
false alarms per day
false alarms per user-day
event-level recall
event-level missed fall rate
detection latency
delayed detection rate
long-lie risk proxy
```

Reason:

```text
These metrics require monitoring duration, event IDs, timestamps, fall impact time, or continuous recording structure. The visible SenseFi README and loader code document labels and samples/windows, but not full event-level clinical timing metadata.
```

---

### Recommended First Metric Set

For the first practical SenseFi experiment, report this metric set:

| Metric Type | Metrics | Interpretation |
|---|---|---|
| ML metrics | Accuracy; precision; recall; specificity; F1-score; balanced accuracy; confusion matrix | Standard model performance |
| Safety proxy metrics | Missed fall rate; false alarm count; false positive rate; alert precision | Safety-oriented interpretation from binary fall/non-fall labels |
| Adversarial degradation metrics | Clean-to-attacked change in recall, missed fall rate, false alarm count, precision, and F1-score | How FGSM/PGD changes safety-relevant outcomes |

---

### Important Wording

Use this wording in reports:

```text
This SenseFi/UT-HAR experiment supports window-level clinical-safety proxy metrics. Event-level metrics such as false alarms per day, detection latency, delayed detection rate, and long-lie risk proxy require timestamped or event-level annotations that are not confirmed in the visible SenseFi documentation.
```

Avoid saying:

```text
SenseFi provides clinical event-level fall detection metrics.
```

because that is not confirmed.

---

### Metric Feasibility Decision

```text
SenseFi is feasible for the first clean-vs-attacked fall/non-fall metric demo, but the first result should be framed as window-level safety-proxy evaluation rather than full event-level clinical-safety evaluation.
```

Reason:

```text
SenseFi provides fall-containing HAR datasets, labels, PyTorch models, and a test loop that can be modified to save predictions. This is enough to compute clean and attacked ML metrics plus missed fall and false alarm proxy metrics. However, false alarms per day, detection latency, event-level recall, and long-lie risk need additional timing or event metadata.
```

---

### Reference Links

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [run.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/run.py)
- [dataset.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/dataset.py)
- [SenseFi paper in Patterns / Cell Press](https://www.sciencedirect.com/science/article/pii/S2666389923000405)

---

## 8. Main Strengths

- **Public, reproducible benchmark structure.** SenseFi is a public WiFi CSI sensing benchmark with a GitHub repository, processed dataset links, documented run commands, requirements, model files, dataset loaders, and an MIT code license. This makes it a practical starting point for a reproducible clean baseline.

- **Fall-containing datasets are available.** SenseFi includes at least two human-activity-recognition datasets with a `fall` class: `UT_HAR_data` and `NTU-Fi_HAR`. UT-HAR is especially useful for the first demo because it includes `fall` plus clinically relevant non-fall confusion classes such as `lie down`, `sit down`, `stand up`, `pickup`, `walk`, and `run`.

- **PyTorch implementation supports attack modification.** SenseFi is implemented in PyTorch, and the training/testing workflow exposes `inputs`, `labels`, model outputs, and loss calculation. This makes it feasible to add software-level adversarial attacks such as FGSM and PGD at the processed CSI tensor level.

- **Multiple baseline models are available.** SenseFi includes several model families, including MLP, LeNet/CNN, ResNet18, ResNet50, ResNet101, RNN, GRU, LSTM, BiLSTM, CNN+GRU, and ViT. This allows the first experiment to start with a simple model such as LeNet and later compare robustness across stronger or more complex models.

- **UT-HAR is manageable for a first demo.** The SenseFi README lists UT-HAR with 3,977 training samples and 996 test samples, which appears more manageable than larger datasets such as Widar. This makes UT-HAR a reasonable first dataset for debugging clean prediction export, binary fall/non-fall mapping, and FGSM/PGD attack integration.

- **Prediction export appears straightforward.** Although SenseFi does not save `y_true`, `y_pred_clean`, or prediction scores by default, the existing `test()` loop already computes model outputs and predicted labels. This means prediction export can likely be added with a small code modification.

- **Good fit for a first safety-proxy experiment.** SenseFi can likely support window-level clean-vs-attacked safety-proxy metrics such as missed fall rate, false alarm count, precision, recall, F1-score, specificity, and confusion matrix after binary fall/non-fall conversion.

- **Good bridge between evidence and implementation.** SenseFi connects the evidence-hub work to practical implementation because it provides a reusable benchmark, public code, fall-containing datasets, and model outputs that can be extended into the clinical-safety translation pipeline.

---

### Strength Summary

```text
SenseFi is a strong first implementation candidate because it is public, PyTorch-based, benchmark-oriented, includes fall-containing HAR datasets, and can likely be modified to export clean and attacked predictions for clinical-safety proxy evaluation.
```

---

### Most Important Strength for This Project

```text
The strongest advantage of SenseFi is that UT-HAR provides a fall class and multiple non-fall confusion classes inside a PyTorch benchmark that can be modified for clean prediction export and FGSM/PGD adversarial testing.
```

---

### Practical Implication

```text
SenseFi should be used as the first candidate for a window-level fall/non-fall clean-vs-attacked safety-proxy demo. The first implementation should start with UT_HAR_data and a simple model such as LeNet before moving to stronger models or more complex datasets.
```

---

### Reference Links

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [SenseFi paper in Patterns / Cell Press](https://www.sciencedirect.com/science/article/pii/S2666389923000405)
- [SenseFi arXiv version](https://arxiv.org/abs/2207.07859)
- [SenseFi Mendeley Data record](https://data.mendeley.com/datasets/dzvgyxkx2f/1)

---

## 9. Main Limitations

- **SenseFi is a general WiFi CSI benchmark, not a clinical fall-safety benchmark.** SenseFi is designed for WiFi CSI human sensing and deep-learning benchmarking across tasks and datasets. It is not specifically designed to evaluate clinical fall safety, long-lie risk, alarm burden, detection latency, or caregiver-facing alert reliability.

- **The first SenseFi experiment will likely be window-level, not event-level.** The visible SenseFi documentation and code support sample/window-level classification, but event IDs, continuous monitoring duration, fall impact timestamps, and alert timestamps are not clearly documented. This means the first experiment should be framed as a window-level fall/non-fall safety-proxy evaluation.

- **False alarms per day cannot be calculated unless monitoring duration is available.** SenseFi can support false alarm count after binary fall/non-fall conversion, but false alarms per day or per user-day require time duration, timestamps, or continuous monitoring metadata that is not confirmed in the visible documentation.

- **Detection latency is not currently confirmed.** Detection latency requires a fall impact time and an alert time. SenseFi’s visible README and dataset loader structure document data samples and class labels, but not fall impact timestamps or event-level alert timing.

- **Long-lie risk proxy cannot be responsibly calculated from sample labels alone.** Long-lie risk requires event-level missed falls, severe detection delay, or time-on-floor proxy information. A sample-level fall/non-fall classification result is not enough to claim long-lie risk measurement.

- **Prediction export is not available by default.** SenseFi’s evaluation loop computes predictions and accuracy, but it does not appear to save `y_true`, `y_pred_clean`, prediction scores, or binary fall/non-fall outputs into CSV files by default. This project must modify the test/evaluation loop to export prediction files.

- **FGSM and PGD attacks are not implemented by default.** SenseFi provides PyTorch models and input tensors that make software-level attacks feasible, but adversarial attack scripts must be added separately. The first attack implementation should be described as a software-level perturbation on processed CSI tensors.

- **Attack strength is not physically interpretable by default.** If FGSM/PGD are applied to normalized or preprocessed CSI tensors, the epsilon value represents perturbation strength in processed feature space. It should not be described as a physical-layer packet, preamble, SDR, or over-the-air attack unless a separate physical attack model is implemented.

- **Processed datasets may hide some raw-signal details.** SenseFi provides processed dataset workflows, which are useful for reproducibility, but processed inputs may not preserve all raw CSI acquisition details needed for physical-layer attack realism or signal-level clinical interpretation.

- **Dataset access and file organization still need to be verified locally.** The SenseFi repository links datasets externally and provides expected folder structure, but the actual download process, file size, file format, and local loading behavior still need to be tested before implementation.

- **License and reuse should be documented before using the data.** The code license and dataset license appear usable for research documentation, but the project should still record the exact license terms before using or redistributing any data. Large or restricted datasets should not be copied into the repository unless redistribution is clearly allowed.

- **UT-HAR may not represent real clinical deployment.** UT-HAR is useful because it includes a `fall` class and relevant non-fall activities, but it should not be treated as real patient deployment data or clinical validation. Results should be presented as a reproducible research demo, not as clinical evidence.

- **Class balance and controlled conditions may affect interpretation.** Fall/non-fall sample counts and controlled collection conditions may not reflect real-world fall rarity, real home monitoring, caregiver workflows, or long-term false alarm burden. This should be clearly stated when interpreting missed fall rate or false alarm count.

- **Generalization is not guaranteed.** A model that works on UT-HAR may not generalize to different rooms, users, WiFi devices, sampling settings, or datasets. Later experiments should test FallDeFi, CSI-Bench, or another dataset to evaluate generalization.

---

### Limitation Summary

```text
SenseFi is suitable for the first reproducible clean-vs-attacked fall/non-fall demo, but the first result should be framed as a window-level safety-proxy evaluation, not as full event-level clinical-safety validation.
```

---

### Most Important Limitation for This Project

```text
The most important limitation is that event-level clinical-safety metrics such as false alarms per day, detection latency, delayed detection rate, and long-lie risk proxy are not confirmed from the visible SenseFi documentation. These metrics require timestamps, event IDs, monitoring duration, or fall impact annotations.
```

---

### Practical Implication

```text
Use SenseFi/UT-HAR first to prove the clean-vs-attacked safety-proxy pipeline:
clean predictions
→ FGSM/PGD attacked predictions
→ missed fall rate
→ false alarm count
→ precision / recall / F1
→ clean-to-attacked degradation.

Then use a richer dataset later if event-level timing or monitoring-duration metrics are needed.
```

---

### Wording to Use in Reports

Use:

```text
This experiment reports window-level clinical-safety proxy metrics using SenseFi/UT-HAR.
```

Avoid:

```text
This experiment validates clinical fall-detection performance.
```

Use:

```text
FGSM and PGD are implemented as software-level perturbations on processed CSI tensors.
```

Avoid:

```text
This experiment demonstrates a physical-world WiFi packet or preamble attack.
```

---

### Reference Links

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [SenseFi paper in Patterns / Cell Press](https://www.sciencedirect.com/science/article/pii/S2666389923000405)
- [SenseFi arXiv version](https://arxiv.org/abs/2207.07859)
- [SenseFi Mendeley Data record](https://data.mendeley.com/datasets/dzvgyxkx2f/1)
- [dataset.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/dataset.py)
- [run.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/run.py)

---

## 10. Decision

Final decision:

```text
Use SenseFi as first baseline.
```

Recommended first configuration:

```text
Dataset: UT_HAR_data
Model: LeNet
Task: Binary fall vs non-fall classification
Attack stage: FGSM first, PGD later
Metric stage: Window-level ML metrics and window-level clinical-safety proxy metrics
```

---

### Reason

SenseFi should be used as the first baseline because it provides a public, PyTorch-based WiFi CSI sensing benchmark with reusable model code, dataset loaders, documented run commands, processed dataset links, and fall-containing human-activity-recognition datasets.

The strongest starting point is `UT_HAR_data` because it includes a `fall` class and multiple clinically relevant non-fall confusion classes:

```text
lie down
fall
walk
pickup
run
sit down
stand up
```

This allows the dataset to be converted into a binary safety task:

```text
fall = 1
all other activities = 0
```

This supports the first implementation goal:

```text
clean WiFi CSI fall/non-fall baseline
→ saved y_true and y_pred_clean
→ FGSM/PGD attacked predictions
→ clean-to-attacked safety-proxy comparison
```

---

### Why SenseFi Is the Best First Baseline

| Reason | Explanation |
|---|---|
| Public code | The SenseFi repository is public and can be cloned. |
| PyTorch implementation | The benchmark is implemented in PyTorch, which makes it suitable for FGSM/PGD input-gradient attacks. |
| Fall-containing dataset | `UT_HAR_data` includes a `fall` class. |
| Useful non-fall classes | UT-HAR includes `lie down`, `pickup`, `sit down`, and `stand up`, which are useful fall-confusion activities. |
| Multiple models | SenseFi includes MLP, LeNet/CNN, ResNet, RNN, GRU, LSTM, BiLSTM, CNN+GRU, and ViT options. |
| Simple first model available | LeNet is simple enough for debugging clean prediction export and FGSM attack integration. |
| Prediction export is feasible | The current evaluation loop already computes model outputs and predicted labels, so `y_true`, `y_pred_clean`, and prediction scores can be added with code modification. |
| Attack integration is feasible | The PyTorch input tensors, labels, model outputs, and loss calculation can be used to compute gradients for FGSM and PGD. |

---

### Why Not Start With NTU-Fi_HAR?

`NTU-Fi_HAR` also includes a `fall` class, but it is a better second candidate rather than the first.

Reason:

```text
NTU-Fi_HAR has fall and non-fall classes, but its non-fall labels are less directly connected to fall-safety confusion than UT-HAR.
```

NTU-Fi_HAR labels:

```text
box
circle
clean
fall
run
walk
```

These are useful for activity recognition, but UT-HAR provides more clinically interpretable confusion classes such as `lie down`, `sit down`, `stand up`, and `pickup`.

---

### Why Not Start With Widar or NTU-Fi-HumanID?

| Dataset | Decision | Reason |
|---|---|---|
| NTU-Fi-HumanID | Not suitable for first demo | Human identification dataset, not fall detection |
| Widar | Not suitable for first demo | Gesture-recognition dataset, not fall detection |

---

### Expected First Output

The first SenseFi implementation should produce:

```text
results/predictions_clean.csv
results/metrics_clean.csv
results/clean_baseline_summary.md
```

Then the next stage should produce:

```text
results/predictions_fgsm.csv
results/metrics_fgsm.csv
results/clean_vs_fgsm_summary.csv
```

---

### Metric Scope for First Demo

The first SenseFi/UT-HAR result should be framed as:

```text
window-level ML metrics and window-level clinical-safety proxy metrics
```

Feasible first metrics:

```text
accuracy
precision
recall / sensitivity
specificity
F1-score
balanced accuracy
confusion matrix
missed fall rate
false alarm count
false positive rate
```

Metrics that require more metadata:

```text
false alarms per day
false alarms per user-day
event-level recall
event-level missed fall rate
detection latency
delayed detection rate
long-lie risk proxy
```

Reason:

```text
These event-level clinical-safety metrics require timestamps, event IDs, fall impact times, monitoring duration, or continuous recording structure. These are not confirmed in the visible SenseFi documentation.
```

---

### Final Decision Statement

```text
SenseFi/UT_HAR_data should be used as the first practical baseline for the fall detection attack-safety demo. The first implementation should use a simple PyTorch model such as LeNet, export clean predictions, convert labels into binary fall vs non-fall format, compute window-level ML and safety-proxy metrics, and then add FGSM followed by PGD for clean-to-attacked safety degradation analysis.
```

---

### Limitation Statement

```text
The first SenseFi/UT-HAR experiment should not be described as full clinical event-level fall-safety evaluation. It should be described as a reproducible window-level fall/non-fall safety-proxy demo. Event-level metrics such as false alarms per day, detection latency, delayed detection rate, and long-lie risk proxy require timestamped or event-level annotations that are not confirmed in the visible SenseFi documentation.
```

---

### Next Step

Move to:

```text
Run clean WiFi CSI fall-detection baseline
```

Implementation target:

```text
python run.py --model LeNet --dataset UT_HAR_data
```

Required modification:

```text
Modify the SenseFi test/evaluation loop to export y_true, y_pred_clean, binary_true_label, clean_prediction, and clean_score.
```

---

### Reference Links

- [SenseFi / WiFi-CSI-Sensing-Benchmark GitHub repository](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark)
- [SenseFi run.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/run.py)
- [SenseFi dataset.py](https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark/blob/main/dataset.py)
- [SenseFi paper in Patterns / Cell Press](https://www.sciencedirect.com/science/article/pii/S2666389923000405)
- [SenseFi arXiv version](https://arxiv.org/abs/2207.07859)
- [SenseFi Mendeley Data record](https://data.mendeley.com/datasets/dzvgyxkx2f/1)

---

## 11. Next Step

Because SenseFi is selected as the first implementation baseline, the next step is:

```text
Run clean WiFi CSI fall-detection baseline
```

The first implementation should use:

```text
Dataset: UT_HAR_data
Model: LeNet
Task: Binary fall vs non-fall classification
Repository: secure-wifi-csi-healthcare-sensing
Experiment folder: experiments/fall_detection_attack_safety_demo/
```

---

### Immediate Implementation Goal

The immediate goal is to run SenseFi on `UT_HAR_data` and produce clean prediction outputs before adding any adversarial perturbation.

The clean baseline should generate:

```text
y_true
y_pred_clean
clean prediction scores
binary fall vs non-fall labels
clean ML metrics
clean safety-proxy metrics
```

Expected first output files:

```text
results/predictions_clean.csv
results/metrics_clean.csv
results/clean_baseline_summary.md
```

---

### Recommended First Command

Start from the SenseFi command pattern:

```bash
python run.py --model LeNet --dataset UT_HAR_data
```

This command may need path adjustments depending on how SenseFi is cloned or integrated into this repository.

Recommended approach:

```text
1. Clone or reference the SenseFi repository locally.
2. Download or access the processed UT_HAR_data files.
3. Confirm the expected Benchmark/Data/ folder structure.
4. Run the clean LeNet + UT_HAR_data baseline.
5. Modify the evaluation/test loop to export predictions.
```

---

### Required Clean Prediction Export

The clean baseline should save predictions to:

```text
experiments/fall_detection_attack_safety_demo/results/predictions_clean.csv
```

Required columns:

```csv
sample_id,timestamp,event_id,subject_id,environment_id,true_label,binary_true_label,clean_prediction,clean_score
```

If a field is not available in SenseFi/UT-HAR, use:

```text
NA
```

Do not remove unavailable columns. Keeping a consistent schema will make later datasets easier to compare.

---

### Required Label Conversion

Convert the original UT-HAR labels into binary fall/non-fall labels:

```text
fall = 1
all other activities = 0
```

Recommended UT-HAR mapping:

| Original Label | Binary Safety Label | Notes |
|---|---:|---|
| fall | 1 | Positive fall class |
| lie down | 0 | High-risk confusion class |
| walk | 0 | Non-fall activity |
| pickup | 0 | Possible false-alarm confusion class |
| run | 0 | Non-fall movement |
| sit down | 0 | Fall-confusable transition |
| stand up | 0 | Non-fall transition |

---

### Clean Baseline Metrics to Compute

For the first clean baseline, compute:

```text
accuracy
precision
recall / sensitivity
specificity
F1-score
balanced accuracy
confusion matrix
missed fall rate
false alarm count
false positive rate
```

These should be described as:

```text
window-level ML metrics and window-level clinical-safety proxy metrics
```

Do not describe them as full event-level clinical-safety metrics unless timestamps, event IDs, or monitoring duration are confirmed.

---

### Project Board Update

After this SenseFi review is committed, update the GitHub Project board:

```text
#2 Review SenseFi for fall labels and usable PyTorch code → Done
#1 Select first reproducible WiFi CSI fall-detection baseline → Done
#5 Run clean WiFi CSI fall-detection baseline → In Progress
```

Keep these as future tasks:

```text
#3 Review FallDeFi for direct WiFi CSI fall-detection code → Todo
#4 Confirm dataset access, license, labels, timestamps, and event IDs → Todo or In Progress
#6 Add FGSM attack and save attacked predictions → Todo
#7 Compare clean vs attacked clinical-safety metrics → Todo
```

---

### When to Review FallDeFi

FallDeFi should be reviewed after the SenseFi clean baseline is attempted, or earlier only if SenseFi becomes blocked.

Use FallDeFi if:

```text
SenseFi data access fails
SenseFi code cannot run
UT-HAR labels cannot be loaded correctly
prediction export becomes impractical
a more direct WiFi CSI fall-detection baseline is needed
```

FallDeFi should be treated as:

```text
second baseline / fallback option
```

not the first task, because SenseFi currently appears easier for a first PyTorch-based clean-vs-attacked safety-proxy demo.

---

### Next File to Create or Update

Create or update this implementation note:

```text
experiments/fall_detection_attack_safety_demo/notes/clean_baseline_plan.md
```

This file should document:

```text
SenseFi clone/setup path
UT_HAR_data access path
model selected
run command
label mapping
prediction export modification plan
expected output CSV files
known limitations
```

---

### Next Practical Task

Move to the project card:

```text
Run clean WiFi CSI fall-detection baseline
```

Implementation target:

```text
SenseFi + UT_HAR_data + LeNet
```

First coding objective:

```text
Modify the SenseFi test/evaluation loop to save y_true, y_pred_clean, binary_true_label, clean_prediction, and clean_score.
```

---

## Claim Boundary

This SenseFi review supports research implementation planning only.

It does not claim:

- clinical validation,
- medical-device readiness,
- diagnostic capability,
- real patient deployment,
- regulatory approval,
- formal clinical standard compliance,
- physical-world adversarial attack validation, or
- event-level clinical fall-safety validation.

This review only concludes that SenseFi/UT-HAR appears suitable for a first reproducible **window-level fall/non-fall clean-vs-attacked safety-proxy demo**.

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

- Do not describe this review as clinical fall-detection validation.
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
