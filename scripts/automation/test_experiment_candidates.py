#!/usr/bin/env python
"""REG-CANDIDATES acceptance tests for the experiment-candidate registry validator.

Synthetic in-memory fixtures ONLY for failure cases -- the real committed registry, paper
registry, and other real sources are only ever READ (never touching the thesis/experiment
repositories, never the network, never requiring a checkpoint or PDF to exist).

Run: python scripts/automation/test_experiment_candidates.py
"""
from __future__ import annotations

import copy
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_experiment_candidates as vec  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required")

REPO = Path(__file__).resolve().parents[2]

PAPERS_DOC = {
    "papers": [
        {"paper_id": "paper_a_2020_direct", "candidate_direction_tags": [
            {"direction": "neyman_pearson_far_control", "relationship": "direct"}]},
        {"paper_id": "paper_b_2021_indirect", "candidate_direction_tags": [
            {"direction": "low_far_afac_calibration", "relationship": "indirect"}]},
        {"paper_id": "paper_c_2019_ensemble", "candidate_direction_tags": [
            {"direction": "ensemble_or_gating", "relationship": "direct"}]},
    ],
    "literature_gaps": [
        {"gap_id": "gap_synthetic_calibration", "direction": "low_far_afac_calibration"},
    ],
}
GOALS_DOC = {"goals": [
    {"id": "fall_detection", "status": "ACTIVE_THESIS_PRIMARY"},
    {"id": "walking_detection", "status": "DATA_AVAILABLE_NOT_EVALUATED"},
    {"id": "walking_pattern_recognition", "status": "NO_DATA"},
    {"id": "future_fall_risk_prediction", "status": "NO_DATA_ASPIRATIONAL"},
]}
DATASETS_DOC = {"datasets": [{"id": "sensefi_ut_har"}]}
FRONTIER_DOC = {"frozen_protocol_registry": [{"protocol_id": "H15-TEST-EPS0015-AFAC-20260705"}]}
REF_EVIDENCE_DOC = {"reference_results": [
    {"key": "H15_eps0015_frozen", "evidence_level": "frozen-test"},
    {"key": "AFAC_eps0030_F20_posthoc", "evidence_level": "test-post-hoc"},
]}
IDENTITY_DOC = {"evaluations": [{"evaluation_id": "eval_synthetic_v1"}]}


def base_candidate(**over):
    c = {
        "candidate_id": "candidate_synthetic_v1",
        "title": "Synthetic candidate",
        "hypothesis": "A synthetic hypothesis.",
        "target_gap": "A synthetic gap.",
        "direction_tags": ["low_far_afac_calibration"],
        "literature_support": [{"paper_id": "paper_b_2021_indirect", "relationship": "indirect"}],
        "literature_gap_ids": ["gap_synthetic_calibration"],
        "current_evidence_refs": [
            {"source": "research_os", "identity": "H15_eps0015_frozen", "relationship": "background",
             "note": "context only"},
        ],
        "current_evidence_summary": "Short summary of what the evidence shows.",
        "prior_negative_evidence_refs": [],
        "our_rationale": "OUR INTERPRETATION: a synthetic rationale distinct from the summary.",
        "required_dataset_ids": ["sensefi_ut_har"],
        "target_goal_ids": ["fall_detection"],
        "dataset_readiness": "available",
        "allowed_split": "validation_only",
        "frozen_protocol_requirement": None,
        "test_read_risk": "none",
        "other_risks": [],
        "evidence_strength": "local_supported_literature_indirect",
        "status": "proposed",
        "claim_boundaries": ["this record is not a GO/REVIEW/NO-GO verdict"],
        "supersedes": None,
        "superseded_by": None,
        "notes": None,
    }
    c.update(over)
    return c


def base_doc(candidates=None):
    return {
        "schema_version": 1,
        "registry_scope": {"source_policy": "local_cited_sources_only", "clinical_claims_allowed": False},
        "controlled_vocabularies": {
            "direction_tags": ["low_far_afac_calibration", "neyman_pearson_far_control",
                               "low_far_partial_auc_objective", "temporal_false_alarm_reduction",
                               "ensemble_or_gating", "walking_detection_baseline",
                               "gait_or_fall_risk_data_acquisition"],
            "literature_relationship": ["direct", "indirect", "background", "not_established"],
            "dataset_readiness": ["available", "available_not_evaluated", "unavailable", "aspirational_only"],
            "allowed_split": ["validation_only", "training_and_validation",
                              "requires_new_frozen_protocol", "existing_frozen_protocol_only",
                              "no_experiment_allowed"],
            "test_read_risk": ["none", "low", "requires_review", "blocked_without_protocol"],
            "evidence_strength": ["strong_local_and_literature", "local_supported_literature_indirect",
                                  "literature_only", "local_negative_evidence", "literature_gap",
                                  "dataset_blocked"],
            "candidate_status": ["proposed", "under_review", "approved_for_planning", "rejected", "superseded"],
        },
        "candidates": candidates if candidates is not None else [base_candidate()],
    }


PASSED = 0
FAILED = 0


def check(name, ok, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}  {detail}")


def errs(doc):
    return vec.validate(doc, PAPERS_DOC, GOALS_DOC, DATASETS_DOC, FRONTIER_DOC,
                         REF_EVIDENCE_DOC, IDENTITY_DOC)


def has_err(doc, pattern):
    return any(re.search(pattern, e, re.I) for e in errs(doc))


def run():
    # P1: the real committed registry validates (read-only)
    real = yaml.safe_load((REPO / "automation" / "registry" / "experiment_candidates.yaml").read_text(encoding="utf-8"))
    real_papers = yaml.safe_load((REPO / "automation" / "literature" / "paper_registry.yaml").read_text(encoding="utf-8"))
    real_goals = yaml.safe_load((REPO / "automation" / "registry" / "goals.yaml").read_text(encoding="utf-8"))
    real_datasets = yaml.safe_load((REPO / "automation" / "registry" / "datasets.yaml").read_text(encoding="utf-8"))
    real_frontier = yaml.safe_load((REPO / "automation" / "frontier.yaml").read_text(encoding="utf-8"))
    real_ref_ev = yaml.safe_load((REPO / "automation" / "registry" / "reference_evidence.yaml").read_text(encoding="utf-8"))
    real_identity = yaml.safe_load((REPO / "automation" / "registry" / "experiment_identity.yaml").read_text(encoding="utf-8"))
    real_errors = vec.validate(real, real_papers, real_goals, real_datasets, real_frontier,
                                real_ref_ev, real_identity)
    check("real registry valid", not real_errors, f"errors: {real_errors[:3]}")

    # duplicate candidate ID
    d = base_doc([base_candidate(), base_candidate()])
    check("duplicate candidate ID rejected", has_err(d, "duplicate candidate_id"))

    # invalid paper reference
    d = base_doc([base_candidate(literature_support=[{"paper_id": "paper_does_not_exist", "relationship": "direct"}])])
    check("invalid paper reference rejected", has_err(d, "not found in paper_registry"))

    # invalid literature-gap reference
    d = base_doc([base_candidate(literature_gap_ids=["gap_does_not_exist"])])
    check("invalid literature-gap reference rejected", has_err(d, "not found in paper_registry.*literature_gaps"))

    # exaggerated literature relationship (paper is only 'indirect' for this direction; claiming 'direct')
    d = base_doc([base_candidate(literature_support=[{"paper_id": "paper_b_2021_indirect", "relationship": "direct"}])])
    check("exaggerated literature relationship rejected", has_err(d, "exceeds the accepted"))

    # invalid dataset or goal
    d_ds = base_doc([base_candidate(required_dataset_ids=["nonexistent_dataset"])])
    d_goal = base_doc([base_candidate(target_goal_ids=["nonexistent_goal"])])
    check("invalid dataset rejected", has_err(d_ds, "not found in datasets.yaml"))
    check("invalid goal rejected", has_err(d_goal, "not found in goals.yaml"))

    # readiness disagreement
    d = base_doc([base_candidate(target_goal_ids=["walking_detection"], dataset_readiness="available")])
    check("readiness disagreement rejected", has_err(d, "disagrees with goal"))

    # future-risk dataset overclaim
    d = base_doc([base_candidate(target_goal_ids=["future_fall_risk_prediction"],
                                 dataset_readiness="available", allowed_split="no_experiment_allowed")])
    check("future-risk dataset overclaim rejected", has_err(d, "future_fall_risk_prediction cannot be marked"))

    # missing prior-negative evidence for D13/D14-related candidates
    d = base_doc([base_candidate(direction_tags=["ensemble_or_gating"],
                                 literature_support=[{"paper_id": "paper_c_2019_ensemble", "relationship": "direct"}],
                                 literature_gap_ids=[], prior_negative_evidence_refs=[])])
    check("missing D13 prior-negative evidence rejected", has_err(d, "requires prior_negative_evidence_refs"))
    d_ok = base_doc([base_candidate(direction_tags=["ensemble_or_gating"],
                                    literature_support=[{"paper_id": "paper_c_2019_ensemble", "relationship": "direct"}],
                                    literature_gap_ids=[],
                                    prior_negative_evidence_refs=[
                                        {"source": "research_os", "identity": "results/d13_score_fusion/stage0_validation_complementarity_audit/D13_STAGE0_COMPLEMENTARITY_AUDIT.md",
                                         "relationship": "direct", "note": "D13 failed its gate"}])])
    check("D13 prior-negative evidence present validates", not errs(d_ok))

    # AFAC post-hoc mislabelled as frozen
    d = base_doc([base_candidate(current_evidence_refs=[
        {"source": "research_os", "identity": "AFAC_eps0030_F20_posthoc", "relationship": "direct",
         "note": "this is frozen evidence"}])])
    check("AFAC mislabelled as frozen rejected", has_err(d, "must not describe it as frozen"))
    d_ok = base_doc([base_candidate(current_evidence_refs=[
        {"source": "research_os", "identity": "AFAC_eps0030_F20_posthoc", "relationship": "direct",
         "note": "this is not a frozen read, it is post-hoc"}])])
    check("AFAC correctly labelled test-post-hoc validates", not errs(d_ok))

    # manually asserted verdict rejected
    d = base_doc([base_candidate(verdict="GO")])
    check("manually asserted verdict field rejected", has_err(d, "unexpected field|verdict-named"))

    # queue auto-promotion rejected (an extra field trying to link into the queue)
    d = base_doc([base_candidate(queue_entry_id="EQ-2026-07-14-J1")])
    check("queue auto-promotion field rejected", has_err(d, "unexpected field"))

    # unauthorized test read rejected (validation_only claiming a frozen protocol requirement)
    d = base_doc([base_candidate(allowed_split="validation_only",
                                 frozen_protocol_requirement="H15-TEST-EPS0015-AFAC-20260705")])
    check("unauthorized test read via validation_only+protocol rejected",
          has_err(d, "frozen_protocol_requirement null"))

    # missing frozen-protocol requirement (new-protocol split without the literal marker)
    d = base_doc([base_candidate(allowed_split="requires_new_frozen_protocol",
                                 frozen_protocol_requirement=None, test_read_risk="requires_review")])
    check("missing frozen-protocol requirement rejected", has_err(d, "new_protocol_required"))

    # new-frozen-protocol candidate cannot claim low risk (rule 20)
    d = base_doc([base_candidate(allowed_split="requires_new_frozen_protocol",
                                 frozen_protocol_requirement="new_protocol_required", test_read_risk="low")])
    check("new-frozen-protocol low-risk claim rejected", has_err(d, "never be low-risk"))

    # existing_frozen_protocol_only must cite a REAL protocol id
    d = base_doc([base_candidate(allowed_split="existing_frozen_protocol_only",
                                 frozen_protocol_requirement="MADE-UP-PROTOCOL", test_read_risk="low")])
    check("fabricated existing-protocol id rejected", has_err(d, "real protocol_id"))
    d_ok = base_doc([base_candidate(allowed_split="existing_frozen_protocol_only",
                                    frozen_protocol_requirement="H15-TEST-EPS0015-AFAC-20260705",
                                    test_read_risk="low")])
    check("real existing-protocol id validates", not errs(d_ok))

    # dataset_blocked must use no_experiment_allowed
    d = base_doc([base_candidate(evidence_strength="dataset_blocked", allowed_split="validation_only")])
    check("dataset_blocked without no_experiment_allowed rejected",
          has_err(d, "dataset_blocked must use allowed_split no_experiment_allowed"))

    # absolute path rejected
    d = base_doc([base_candidate(current_evidence_refs=[
        {"source": "research_os", "identity": r"C:\Users\someone\notes.md", "relationship": "background", "note": ""}])])
    check("absolute path rejected", has_err(d, "absolute"))

    # clinical claim rejected
    d = base_doc([base_candidate(our_rationale="OUR INTERPRETATION: this candidate is deployment-ready.")])
    check("clinical/deployment claim rejected", has_err(d, "clinical/deployment claim"))

    # embedded experiment command rejected
    d = base_doc([base_candidate(other_risks=["run: .venv/Scripts/python.exe scripts/train_x.py --seed 42"])])
    check("embedded experiment command rejected", has_err(d, "embedded experiment command"))

    # embedded markdown table / excessive text rejected
    d = base_doc([base_candidate(current_evidence_summary="lorem ipsum " * 100)])
    check("excessive text field rejected", has_err(d, "must not duplicate a full paper summary"))
    d2 = base_doc([base_candidate(notes="| a | b | c | d | e | f |")])
    check("embedded markdown table row rejected", has_err(d2, "embedded markdown table row"))

    # our_rationale duplicating current_evidence_summary rejected
    same = "Identical text."
    d = base_doc([base_candidate(current_evidence_summary=same, our_rationale=same)])
    check("rationale duplicating evidence summary rejected", has_err(d, "must stay separate"))

    # overlap between current and prior-negative evidence identity rejected
    d = base_doc([base_candidate(
        current_evidence_refs=[{"source": "research_os", "identity": "H15_eps0015_frozen", "relationship": "background", "note": ""}],
        prior_negative_evidence_refs=[{"source": "research_os", "identity": "H15_eps0015_frozen", "relationship": "direct", "note": ""}])])
    check("overlapping evidence identity rejected", has_err(d, "appears in both"))

    # no external repository or network requirement
    src = Path(vec.__file__).read_text(encoding="utf-8")
    check("no network imports", not re.search(r"\b(requests|urllib|http\.client|socket)\b", src))
    check("no PDF requirement", ".pdf" not in src.lower())

    # deterministic ordering
    buf1, buf2 = io.StringIO(), io.StringIO()
    with redirect_stdout(buf1):
        rc1 = vec.main([])
    with redirect_stdout(buf2):
        rc2 = vec.main([])
    check("deterministic output", rc1 == rc2 == 0 and buf1.getvalue() == buf2.getvalue())

    # purity: validate() never mutates its inputs
    d = base_doc()
    snapshot = copy.deepcopy(d)
    vec.validate(d, PAPERS_DOC, GOALS_DOC, DATASETS_DOC, FRONTIER_DOC, REF_EVIDENCE_DOC, IDENTITY_DOC)
    check("validate() is pure (input unmutated)", d == snapshot)

    # missing required field rejected
    d = base_doc([{k: v for k, v in base_candidate().items() if k != "hypothesis"}])
    check("missing required field rejected", has_err(d, "missing required field"))

    print()
    print(f"RESULT: {'ALL PASS' if FAILED == 0 else 'FAILURES'} ({PASSED}/{PASSED + FAILED})")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
