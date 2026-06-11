\# FGSM Adversarial Training Defense Baseline Log



This note documents the first runnable FGSM adversarial-training defense baseline for the WiFi CSI Fall Attack-Safety Demo.



The goal of this step is to add a simple defended-model training baseline before comparing defended and undefended model behavior in later safety-proxy evaluation.



\---



\## 1. Purpose



The purpose of this experiment is to train a SenseFi UT-HAR LeNet model using both clean CSI tensors and FGSM-perturbed CSI tensors during training.



This is intended as a first software-level adversarial training defense baseline.



The defense question is:



```text

If the model is trained with simple FGSM-perturbed examples,

does the trained model become more robust for later attacked fall-vs-non-fall safety-proxy evaluation?

```



This step does not yet prove improved robustness. It only creates and runs the first defended training baseline.



\---



\## 2. Repository Location



This experiment is located at:



```text

experiments/fall\_detection\_attack\_safety\_demo/

```



The main script added in this step is:



```text

scripts/train\_fgsm\_adversarial\_defense\_short.py

```



The main output file added in this step is:



```text

results/fgsm\_adversarial\_training\_short\_metrics.csv

```



\---



\## 3. Dataset and Model



Dataset:



```text

SenseFi / UT\_HAR\_data

```



Model:



```text

LeNet

```



Task framing:



```text

multi-class UT-HAR activity recognition

```



Fall-safety translation framing:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



The current training output is still a model-training metric log. Later steps will export defended predictions and compute fall-vs-non-fall safety-proxy metrics.



\---



\## 4. Defense Method



The script uses FGSM adversarial training.



For each training batch, the script computes:



```text

clean model loss

FGSM-perturbed input batch

adversarial model loss

weighted clean + adversarial training loss

```



Training loss combination:



```text

total loss = 0.5 \* clean loss + 0.5 \* adversarial loss

```



FGSM training epsilon:



```text

0.005

```



Short training length:



```text

5 epochs

```



Optimizer:



```text

Adam

```



Learning rate:



```text

0.001

```



Random seed:



```text

42

```



Device used:



```text

CPU

```



\---



\## 5. Claim Boundary



This is a software-level processed-tensor adversarial training baseline.



It is not:



```text

clinical validation

medical-device validation

diagnostic evidence

regulatory evaluation

real patient deployment evidence

event-level fall validation

long-lie validation

physical-layer defense

packet-level defense

preamble-level defense

SDR validation

over-the-air defense validation

```



The current workflow operates on processed CSI tensors from SenseFi/UT-HAR.



It does not modify WiFi packets, preambles, firmware, radios, or over-the-air transmissions.



\---



\## 6. Windows Loader Issue and Fix



During implementation, the first script runs failed with:



```text

KeyError: 'X\_train'

```



The issue was related to Windows path handling inside the local ignored SenseFi benchmark clone.



The final script solved this by:



```text

patching the local SenseFi dataset loader

normalizing UT-HAR dataset keys

forcing the wrapper to load from the known local SenseFi Data folder

```



The successful run printed:



```text

UT-HAR loader root: ...\\third\_party\\WiFi-CSI-Sensing-Benchmark\\Data/

Normalized UT-HAR keys: \['X\_test', 'X\_train', 'X\_val', 'y\_test', 'y\_train', 'y\_val']

```



This confirmed that the script loaded the UT-HAR arrays correctly.



\---



\## 7. Successful Run Command



The script was run from:



```text

experiments/fall\_detection\_attack\_safety\_demo/

```



Command:



```powershell

python scripts\\train\_fgsm\_adversarial\_defense\_short.py

```



\---



\## 8. Successful Run Summary



The script completed successfully.



Output summary:



```text

FGSM adversarial training defense completed successfully.

Metrics saved to: results\\fgsm\_adversarial\_training\_short\_metrics.csv

Rows saved: 5

Elapsed time: 127.1 seconds

```



\---



\## 9. Training Metrics



The output file is:



```text

results/fgsm\_adversarial\_training\_short\_metrics.csv

```



CSV columns:



```text

epoch

train\_total\_loss

train\_clean\_loss

train\_adversarial\_loss

train\_clean\_accuracy

train\_adversarial\_accuracy

test\_clean\_loss

test\_clean\_accuracy

fgsm\_train\_epsilon

clean\_loss\_weight

adversarial\_loss\_weight

```



Final epoch result:



```text

epoch = 5

train\_total\_loss = 1.264801

train\_clean\_loss = 1.153640

train\_adversarial\_loss = 1.375963

train\_clean\_accuracy = 0.565776

train\_adversarial\_accuracy = 0.453629

test\_clean\_loss = 1.165806

test\_clean\_accuracy = 0.575301

fgsm\_train\_epsilon = 0.005000

clean\_loss\_weight = 0.50

adversarial\_loss\_weight = 0.50

```



\---



\## 10. Interpretation



The first defended training run completed successfully and produced a model-training metrics CSV.



The final epoch reached:



```text

test clean accuracy: 0.575301

training clean accuracy: 0.565776

training adversarial accuracy: 0.453629

```



This suggests the adversarial training loop is functioning, but it does not yet establish whether the defended model improves attacked fall-safety behavior.



The next required step is to export defended model predictions under clean and attacked conditions, then compute the same fall-vs-non-fall safety-proxy metrics used for the undefended model.



\---



\## 11. Current Status



Completed in this step:



```text

FGSM adversarial training defense plan documented

FGSM adversarial training script added

FGSM adversarial training short run completed

FGSM adversarial training metrics CSV saved

script and metrics committed and pushed

```



Current commit:



```text

4626b94 Add FGSM adversarial training defense baseline

```



\---



\## 12. Next Step



The next step is to create a defended prediction export workflow.



The defended prediction export should save:



```text

sample\_id

true\_label

true\_class\_name

defended\_clean\_predicted\_label

defended\_clean\_predicted\_class\_name

defended\_attacked\_predicted\_label

defended\_attacked\_predicted\_class\_name

fall\_true\_binary

fall\_pred\_binary\_clean\_defended

fall\_pred\_binary\_attacked\_defended

prediction\_confidence\_clean\_defended

prediction\_confidence\_attacked\_defended

correct\_clean\_defended

correct\_attacked\_defended

```



After that, the project can compute defended safety-proxy metrics and compare:



```text

undefended clean

undefended attacked

defended clean

defended attacked

```



This will support Priority 8: compare defended vs undefended safety-proxy metrics.

