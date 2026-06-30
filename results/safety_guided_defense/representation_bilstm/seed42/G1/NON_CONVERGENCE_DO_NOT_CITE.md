# BiLSTM + G1-from-scratch (seed 42) — NON-CONVERGENCE. DO NOT cite as a representation-ceiling result.

This run trained a UT_HAR_BiLSTM from random init under the LeNet-tuned G1 adversarial-training recipe
(50% clean / 25% FGSM / 25% PGD multi-eps + targeted-to-fall PGD + margin penalties + fall-weight 3,
Adam lr=1e-3, NO gradient clipping). It **failed to converge** and answers NOTHING about the BiLSTM
representation's PGD-AUROC envelope.

## Evidence of training failure (70 epochs)
- max val clean accuracy ever reached: **0.474** (never near the 0.70 clean guard)
- **val clean fall recall = 0.000 in EVERY epoch** (never detected a single fall, even unattacked)
- val PGD fall recall = 0.000 throughout
- **zero clean-guard-eligible epochs** -> v2safety/v2maxrec/v2lowFA selected_epoch = -1 (no valid checkpoint)
- only a degenerate v2macroF1 checkpoint (epoch 44, acc 0.474, macro-F1 0.343, fall recall 0) exists

## Why
Recurrent nets are hard to train under heavy adversarial perturbation from scratch; the LeNet recipe
(no gradient clipping, lr 1e-3) does not transfer. The SenseFi benchmark obtains ~0.9 clean accuracy from
BiLSTM under normal training, so the architecture CAN learn UT-HAR -- the adversarial recipe broke it,
not the representation.

## Disposition
Superseded by the clean-baseline recovery: representation_bilstm/clean_baseline/seed42/ (Step 1 clean
BiLSTM with gradient clipping + lower LR), then a G1 fine-tune FROM the converged clean checkpoint
(Step 3). This run's checkpoints are NOT used for any claim.
