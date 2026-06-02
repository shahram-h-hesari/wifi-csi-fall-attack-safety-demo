# SenseFi UT-HAR LeNet Short Clean Baseline Log



## Purpose



This note records the first shortened clean-baseline training run for the WiFi CSI fall detection attack-safety demo.



The goal of this run was to move beyond a one-epoch smoke test and confirm that the SenseFi UT-HAR LeNet baseline can train for multiple epochs, improve performance, and save structured metrics.



This is still not the final thesis experiment. It is a shortened clean baseline run used for reproducibility testing and GitHub documentation.



## Experiment Configuration



* Benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark

* Dataset: UT_HAR_data

* Model: LeNet

* Device: CPU

* Epochs: 5

* Original SenseFi training setting: 200 epochs

* Metrics file: `results/clean_baseline_short_metrics.csv`

* Dataset location: local only, not committed to GitHub



## Dataset Notes



UT-HAR contains seven activity classes:



```text

0 = lie down

1 = fall

2 = walk

3 = pickup

4 = run

5 = sit down

6 = stand up

```



For the later clinical-safety proxy layer, the planned binary mapping is:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



## Short Baseline Output



```text

Epoch 01/5 | train_acc=0.2858, train_loss=1.8020 | test_acc=0.2942, test_loss=1.7874

Epoch 02/5 | train_acc=0.2946, train_loss=1.7870 | test_acc=0.2942, test_loss=1.7805

Epoch 03/5 | train_acc=0.3233, train_loss=1.7412 | test_acc=0.4207, test_loss=1.6117

Epoch 04/5 | train_acc=0.4919, train_loss=1.4322 | test_acc=0.5161, test_loss=1.2782

Epoch 05/5 | train_acc=0.6142, train_loss=1.0603 | test_acc=0.6596, test_loss=1.0014

```



## Interpretation



The shortened clean baseline completed successfully.



The model improved from approximately 29% test accuracy after the first epoch to approximately 66% test accuracy after five epochs. This confirms that the clean training pipeline is functioning and that LeNet is learning useful structure from the UT-HAR CSI data.



These results should not be interpreted as final benchmark performance because the run used only five epochs on CPU. The original SenseFi configuration uses 200 training epochs.



## Claim Boundary



This experiment is a research implementation baseline for WiFi CSI fall-related activity recognition.



The current result is a window-level machine-learning baseline. It is not clinical validation, medical-device validation, real patient deployment, diagnostic evidence, or regulatory evaluation.



## Next Step



Modify the evaluation pipeline to export clean predictions:



```text

sample_id

true_label

predicted_label

fall_true_binary

fall_pred_binary

prediction_confidence

```



These saved predictions will allow calculation of fall-vs-non-fall safety-proxy metrics such as missed fall rate, false alarm count, recall, precision, specificity, and F1-score.


