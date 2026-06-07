# Thesis Table 22 and Figure 22: End-to-End Evidence Map

## Purpose

Table 22 and Figure 22 summarize the full artifact package for the fall attack-safety demo in a form that is useful for research discussion and collaboration meetings.

This version is designed to answer three practical questions:

1. **What was done?**
2. **What evidence was produced?**
3. **Where could collaboration with richer datasets add value?**

## Files Created

**Table 22**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\thesis_table_22_thesis_artifact_evidence_map.csv`

**Figure 22**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\figures\thesis_figure_22_thesis_artifact_evidence_map.png`

**Companion note**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\notes\thesis_table_22_figure_22_thesis_artifact_evidence_map.md`

## Structure of the figure

The figure is organized into three large columns:

- **Research Workflow** — what was run in the demo
- **Evidence Generated** — what the demo measured and revealed
- **What Collaboration Could Enable** — how richer real-world datasets could strengthen validation

## 1. Research Workflow
This column explains what was run in the demo: dataset/workflow setup, software FGSM/PGD stress testing, and defended-vs-undefended comparison.

### A. Dataset / Workflow
Role: Research workflow foundation
- UT-HAR / SenseFi workflow
- Workflow setup + metadata audit
- Output index / artifact inventory
- Baseline fall-safety summary

### B. Software Attack Stress Test
Role: Attack degradation test
- FGSM attack results
- PGD attack results
- Epsilon-sweep summaries
- Clean-vs-attacked comparisons

### C. Defense Comparison
Role: Defended vs undefended comparison
- Defended vs undefended behavior
- Matched attack-defense effect
- Paired safety-state transitions
- Defense-effect heatmap

## 2. Safety-Proxy Findings
This column summarizes the evidence products produced by the demo: safety-proxy metrics, alert-trustworthiness analysis, and failure-pattern analysis.

### A. Safety-Proxy Metrics
Role: Window-level safety evidence
- TP / FN / FP / TN safety metrics
- Recall and missed-fall-rate proxy
- False-alert proxy
- Safety tradeoff summary

### B. Alert Trustworthiness
Role: Alert composition and source analysis
- Alert trustworthiness / PPV proxy
- Fall-alert composition
- False-alert source classes
- Class-normalized false-alert sources

### C. Failure-Pattern Analysis
Role: Failure-mode evidence
- Missed-fall destination classes
- Fall-window recovery / persistence
- Attack-defense failure patterns
- Claim-boundary evidence summary

## 3. Collaboration Pathway
This column makes the collaboration opportunity explicit by separating what the current demo can support from what richer real-world or partner-owned datasets could enable next.

### A. What We Can Support Now
Role: Current defensible scope
- Window-level safety indicators
- Software attack stress testing
- Descriptive defense comparison
- Reproducible research workflow

### B. Richer Datasets Could Enable
Role: Next validation targets
- Event-level fall validation
- Time-to-alarm and alarm burden
- Long-lie / delayed-rescue analysis
- Subject / room / site generalization
- Clinical and care-setting relevance

### C. Partner Data That Would Help
Role: Useful richer-data examples
- Event IDs and timestamps
- Monitoring duration and alarm counts
- Subject / room metadata
- Realistic home/care-setting data
- Cross-dataset replication opportunities


## Interpretation

The figure is not intended as a performance plot. Instead, it is an **evidence map**.

It shows that the current demo already supports:

- a reproducible window-level workflow,
- software FGSM/PGD attack stress testing,
- descriptive defended-vs-undefended analysis,
- and window-level safety-indicator interpretation.

It also makes the next collaboration opportunity visible:

- event-level validation,
- time-to-alarm and alarm-burden analysis,
- long-lie / delayed-rescue analysis,
- subject / room / site generalization,
- and stronger clinical / care-setting relevance,

all of which would benefit from richer partner-owned datasets.

## Claim Boundary

This is a descriptive artifact-map and collaboration-oriented summary for the UT-HAR / SenseFi fall attack-safety demo.

The current evidence supports:

- window-level proxy analysis,
- software-level FGSM/PGD stress testing,
- descriptive defense comparison,
- and reproducible artifact organization.

The current evidence does **not** establish:

- clinical validation,
- medical-device validation,
- real-patient deployment,
- event-level fall validation,
- false alarms per hour/day,
- time-to-alarm validation,
- long-lie validation,
- subject-level generalization,
- room-level generalization,
- or physical-layer / over-the-air validation.
