# Third-Party Notices

This repository may include or reference third-party open-source projects for the following purposes:
- Literature review and academic comparison
- Technical code review and reproducibility testing
- Research inspiration and methodology reference
- Evaluation of sensing pipelines and security approaches

Third-party projects are **not** part of the core fall-detection pipeline of this repository unless explicitly stated. Third-party claims (e.g., accuracy figures, system performance) are **not** treated as validated unless independently supported by our own experiments. The current implementation uses **synthetic CSI-like data only**.

> **Last Updated:** 2026-05-24

---

## License and Attribution Policy

- All third-party code remains under its original license.
- Any code copied or adapted from a third-party project must retain the original attribution and license notices.
- Adapted code will be clearly marked with a comment referencing the original source.
- This repository's MIT License applies only to original work authored by the repository contributors.
- **No third-party code or datasets have been copied into this repository.** All third-party items are external references only.

---

## Third-Party Projects Referenced

### WiFi Sensing

Projects related to WiFi CSI sensing, activity recognition, fall detection, and related applications are organized under `third_party/wifi_sensing/`.

### WiFi Sensing Security

Projects related to adversarial attacks, CSI spoofing, privacy leakage, physical-layer security, and robustness evaluation are organized under `third_party/wifi_sensing_security/`.

---

## Individual Project Notices

### RuView
- **Original Repository:** https://github.com/ruvnet/RuView
- **Original Authors:** ruvnet and contributors
- **License:** MIT (verified)
- **Category:** WiFi sensing — real-time spatial intelligence, vital sign monitoring, and presence detection
- **Use in This Repository:** Third-party open-source reference and experimental target.
- **Validation Status:** RuView's claims are **not independently validated** in this repository.

---

### SenseFi / WiFi CSI Sensing Benchmark
- **Original Repository:** https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark
- **Original Authors:** xyanchen and contributors
- **License:** MIT (verified)
- **Category:** WiFi CSI sensing benchmark — deep-learning-based WiFi CSI human sensing evaluation framework
- **Use in This Repository:** External reference for benchmark methodology.
- **Validation Status:** Claims not independently validated.

---

### Attack\_WiFi\_Sensing
- **Original Repository:** https://github.com/Guolin-Yin/Attack_WiFi_Sensing
- **Original Authors:** Guolin-Yin and contributors
- **License:** MIT (verified)
- **Category:** WiFi sensing security — adversarial evasion attacks, universal perturbation, robustness evaluation
- **Use in This Repository:** Core adversarial reference for thesis threat model.
- **Validation Status:** External reference only; no code copied.

---

### Awesome-WS-Security
- **Original Repository:** https://github.com/Intelligent-Perception-Lab/Awesome-WS-Security
- **Original Authors:** Intelligent-Perception-Lab and contributors
- **License:** Pending verification
- **Category:** WiFi sensing security — curated literature and resource list
- **Use in This Repository:** Literature survey resource.
- **Validation Status:** External reference only.

---

### AntiEave-WiFi-Sensing
- **Original Repository:** https://github.com/MoWING-Lab/AntiEave-WiFi-Sensing
- **Original Authors:** MoWING-Lab and contributors
- **License:** Pending verification
- **Category:** WiFi sensing security — anti-eavesdropping defense (IEEE INFOCOM 2023)
- **Use in This Repository:** Defense mechanism reference for privacy-preserving WiFi sensing.
- **Validation Status:** External reference only; no code copied.

---

### WiFi-ADG
- **Original Repository:** https://github.com/siwangzhou/WiFi-ADG
- **Original Authors:** siwangzhou and contributors
- **License:** Pending verification
- **Category:** WiFi sensing security — adversarial data generation
- **Use in This Repository:** Adversarial data generation reference for thesis defense pipeline.
- **Validation Status:** External reference only; no code copied.

---

### goop-veil
- **Original Repository:** https://github.com/kobepaw/goop-veil
- **Original Authors:** kobepaw and contributors
- **License:** Apache-2.0
- **Category:** WiFi sensing security — software-only WiFi privacy defense
- **Use in This Repository:** Privacy defense reference for CSI-based surveillance mitigation.
- **Validation Status:** External reference only; no code copied.

---

### CsiGAN
- **Original Repository:** https://github.com/ChunjingXiao/CsiGAN
- **Original Authors:** ChunjingXiao and contributors
- **License:** Pending verification
- **Category:** WiFi CSI data augmentation — semi-supervised GAN for robust activity recognition
- **Use in This Repository:** Data augmentation and victim-model reference.
- **Validation Status:** External reference only; no code copied.

---

### NoiSec
- **Original Repository:** https://github.com/shahriar0651/NoiSec
- **Original Authors:** shahriar0651 and contributors
- **License:** MIT (verified)
- **Category:** WiFi sensing security — noise-based adversarial defense and signal obfuscation
- **Use in This Repository:** Defense taxonomy reference: noise injection and signal-layer defense methods.
- **Validation Status:** External reference only; no code copied.

---

### CSI-Bench
- **Original Repository:** https://github.com/guozhen-jenn-zhu/CSI-Bench-Real-WiFi-Sensing-Benchmark
- **Original Authors:** guozhen-jenn-zhu and contributors
- **License:** MIT (verified)
- **Category:** WiFi sensing benchmark — standardized real WiFi sensing benchmark
- **Use in This Repository:** Future dataset/benchmark candidate (not yet integrated or downloaded).
- **Validation Status:** External reference only; no data copied.

---

### Awesome-RIS-Security
- **Original Repository:** Pending verification
- **Original Authors:** Pending verification
- **License:** Pending verification
- **Category:** Physical-layer security — reconfigurable intelligent surface (RIS) attack and defense literature tracker
- **Use in This Repository:** Physical-layer attack literature reference for threat model expansion.
- **Validation Status:** External reference only; literature aggregator.
- **Note:** Repository URL and license require independent verification.

---

### unilateral-csi-entropy
- **Original Repository:** Pending verification
- **Original Authors:** Pending verification
- **License:** Pending verification
- **Category:** CSI security — CSI-based entropy analysis for edge security
- **Use in This Repository:** Cryptographic entropy reference for CSI-layer security discussion.
- **Validation Status:** External reference only; no code copied.
- **Note:** Repository URL and license require independent verification.

---

## Pending Verification Items

The following items require independent verification of license, repository URL, or access method before any use:

| Item | Category | Status |
|---|---|---|
| Awesome-RIS-Security | Physical-layer attack literature | Repository URL and license: Pending verification |
| unilateral-csi-entropy | CSI edge security | Repository URL and license: Pending verification |
| CsiGAN | Data augmentation | License: Pending verification |
| Awesome-WS-Security | Security literature | License: Pending verification |
| AntiEave-WiFi-Sensing | Anti-eavesdropping defense | License: Pending verification |
| WiFi-ADG | Adversarial data generation | License: Pending verification |

---

*This file is maintained as part of the Secure WiFi CSI Healthcare Sensing research prototype at Portland State University.*
*Last Updated: 2026-05-24*
