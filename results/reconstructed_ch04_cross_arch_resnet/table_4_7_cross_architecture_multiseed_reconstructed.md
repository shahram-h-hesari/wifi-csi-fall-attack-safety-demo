# Reconstructed Table 4.7

Source: results/cross_architecture/cross_architecture_multiseed_summary.csv

| Model | Type | Clean fall recall | FGSM eps=0.03 | PGD eps=0.03 | Exact 0.000 at eps=0.03 (FGSM / PGD) |
| --- | --- | --- | --- | --- | --- |
| LeNet | Shallow CNN | 0.978 +/- 0.016 | 0.049 +/- 0.046 | 0.000 +/- 0.000 | 2/5 / 5/5 |
| GRU | Recurrent | 0.920 +/- 0.012 | 0.009 +/- 0.012 | 0.000 +/- 0.000 | 3/5 / 5/5 |
| BiLSTM | Bidirectional recurrent | 0.884 +/- 0.043 | 0.022 +/- 0.050 | 0.004 +/- 0.010 | 4/5 / 4/5 |
| Transformer | Attention (ViT) | 0.947 +/- 0.049 | 0.004 +/- 0.010 | 0.000 +/- 0.000 | 4/5 / 5/5 |
| ResNet18 | Deep CNN | 0.978 +/- 0.016 | 0.009 +/- 0.012 | 0.000 +/- 0.000 | 3/5 / 5/5 |

PGD reaches exactly 0.000 fall recall at epsilon 0.03 in 24/25 clean-qualified seed-runs and all 25 by epsilon <= 0.035.
