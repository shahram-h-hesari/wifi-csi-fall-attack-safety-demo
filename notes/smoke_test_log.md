# SenseFi UT-HAR LeNet Smoke Test Log



## Purpose



This note records the first successful clean-baseline smoke test for the WiFi CSI fall detection attack-safety demo.



The goal of this run was not final model performance. The goal was to confirm that the local environment, dataset loader, UT-HAR data files, PyTorch model, training loop, and test loop can run successfully.



## Experiment Configuration



\- Benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark

\- Dataset: UT\_HAR\_data

\- Model: LeNet

\- Device: CPU

\- Smoke test epochs: 1

\- Original SenseFi training setting: 200 epochs

\- Dataset location: local only, not committed to GitHub



## Local Setup Notes



The UT-HAR files from the SenseFi Mendeley Data package use NumPy binary array format even though the filenames end in `.csv`.



The original SenseFi loader required a small local Windows path-separator patch because Windows returned dataset keys such as `data\\\\X\_train` and `label\\\\y\_train` instead of `X\_train` and `y\_train`.



This patch was applied locally inside the ignored third-party SenseFi clone.



## Smoke Test Output



```text

using dataset: UT-HAR DATA

using model: LeNet

Clean baseline smoke test

\----------------------------------------

Device: cpu

Original SenseFi train epochs: 200

Smoke test epochs: 1

\----------------------------------------

Epoch:1, Accuracy:0.2916,Loss:1.801470430

validation accuracy:0.3038, loss:1.78827

\----------------------------------------

Smoke test completed.

