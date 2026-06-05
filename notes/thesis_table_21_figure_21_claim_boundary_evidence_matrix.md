# Thesis Table 21 and Figure 21: Claim Boundary and Evidence Strength Matrix

This note documents the claim-boundary and evidence-strength summary for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 21 and Figure 21 ask:

```text
What claims are supported by the current experiment, and what claims require future data, validation, or collaboration?
```

This artifact strengthens the thesis and GitHub repository because it prevents overclaiming while showing a clear path for future collaboration.

## Files Created

```text
Table 21:
results\thesis_table_21_claim_boundary_evidence_matrix.csv

Figure 21:
figures\thesis_figure_21_claim_boundary_evidence_matrix.png

Companion note:
notes\thesis_table_21_figure_21_claim_boundary_evidence_matrix.md
```

## Evidence Source

```text
UT-HAR / SenseFi window-level research workflow.
```

This supports descriptive window-level proxy analysis and software-level adversarial stress testing. It does not support clinical validation, medical-device validation, event-level fall validation, deployment validation, or physical-layer / over-the-air validation.

## Evidence Strength Categories

```text
Directly supported now = current experiment directly supports this research claim
Window-level proxy only = current result is useful, but only as a window-level clinical-safety proxy
Future work needed = current results should not be used to make this claim yet
```

## Count by Category

```text
Directly supported now: 4
Window-level proxy only: 6
Future work needed: 8
```

## Directly Supported Research Claims

- Software-level FGSM/PGD adversarial stress test: Software-level adversarial stress test
- Defended vs undefended comparison: Defended-vs-undefended descriptive comparison
- Same-window paired clean/attack/defense transitions: Paired window-level transition analysis
- Reproducible table/figure workflow: Reproducible table/figure workflow

## Window-Level Proxy Claims

- Window-level fall-vs-non-fall safety proxy: Window-level safety-proxy analysis
- Missed-fall-rate / recall degradation proxy: Window-level missed-fall / recall-degradation proxy
- False-alert trustworthiness / PPV composition: Window-level alert-trustworthiness proxy
- Class-normalized false-fall-alarm sources: Window-level false-alert source analysis
- Missed-fall destination classes: Window-level missed-fall destination analysis
- Fall-window recovery and failure persistence: Window-level fall-recovery proxy

## Claims Requiring Future Evidence

- Event-level fall detection: Future event-level validation needed
- Detection latency / time-to-alarm: Future time-to-alarm analysis needed
- False alarms per hour/day: Future alarm-burden analysis needed
- Long-lie / delayed-rescue risk: Future long-lie proxy analysis needed
- Subject-level generalization: Future subject-level generalization needed
- Room/environment-level generalization: Future room-level generalization needed
- Physical-layer / over-the-air attack validation: Future physical-layer validation needed
- Clinical / regulatory / medical-device validation: Research prototype; not clinical validation

## Interpretation

The current evidence package strongly supports a research-prototype claim: software-level adversarial perturbations can degrade window-level fall-detection safety proxies, and defended/undefended outputs can be compared using clinical-safety-oriented window-level metrics.

The current evidence package also supports paired same-window transition analysis and a reproducible table/figure workflow, but only supports several clinically motivated interpretations as window-level proxies rather than as clinical or event-level validation.

The current evidence package does not support clinical validation, medical-device validation, patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, subject-level generalization, room-level generalization, or over-the-air physical-layer attack validation.

This matrix can be used in the thesis, README, Wiki, and collaboration discussions to clearly separate what is shown now from what future datasets or external partnerships can add.

## Claim Boundary

This is a descriptive claim-boundary and evidence-strength summary based on the current UT-HAR / SenseFi window-level research workflow.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
