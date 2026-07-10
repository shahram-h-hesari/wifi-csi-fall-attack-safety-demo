#!/usr/bin/env python
"""D4a-1 acceptance tests for the paper-registry validator (P1-P25 + extras).

Synthetic in-memory/temp fixtures ONLY for failure cases -- the real committed registry is only
ever READ (P1/P24/P25). No network, no PDF requirement, no subprocess, no --split command.

Run: python scripts/automation/test_paper_registry.py
"""
from __future__ import annotations

import copy
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_paper_registry as vpr  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required")

REPO = Path(__file__).resolve().parents[2]
REAL_REGISTRY = REPO / "automation" / "literature" / "paper_registry.yaml"
REAL_GOALS = REPO / "automation" / "registry" / "goals.yaml"

GOALS_DOC = {"goals": [{"id": g} for g in (
    "fall_detection", "walking_detection", "walking_pattern_recognition",
    "gait_or_mobility_change_detection", "future_fall_risk_prediction")]}


def base_paper(**over):
    p = {
        "paper_id": "paper_doe_2020_synthetic_method",
        "display_citation": "Doe (2020), A Synthetic Method, SynthConf",
        "title": "A Synthetic Method for Testing",
        "authors": ["Doe, Jane"],
        "year": 2020,
        "venue": "Synthetic Conference",
        "citation_keys": ["doe2020synthetic"],
        "identifiers": {"doi": None, "arxiv": None, "other": None},
        "metadata_status": "complete_local",
        "verification_status": "local_bib_only",
        "source_records": [
            {"repository": "thesis_overleaf", "path": "references.bib",
             "source_type": "bibliography", "citation_key": "doe2020synthetic", "note": "synthetic"}
        ],
        "paper_type": "method",
        "task_tags": ["adversarial_robustness"],
        "method_tags": ["adversarial_training"],
        "dataset_tags": [],
        "defense_line_tags": [],
        "candidate_direction_tags": [],
        "paper_contribution_summary": "Per the synthetic framing: proposes a method.",
        "paper_limitations_summary": None,
        "relevance_to_current_results": "OUR INTERPRETATION: synthetic relevance only.",
        "interpretation_status": "local_interpretation",
        "claim_boundaries": ["The paper's results are not this thesis's results."],
        "full_text_status": "not_stored_locally",
        "notes": None,
    }
    p.update(over)
    return p


def base_doc(papers=None, gaps=None):
    return {
        "schema_version": 1,
        "registry_scope": {
            "source_policy": "local_cited_sources_only",
            "external_metadata_verification": "pending",
            "clinical_claims_allowed": False,
            "allowed_repositories": ["research_os", "thesis_overleaf"],
        },
        "papers": papers if papers is not None else [base_paper()],
        "literature_gaps": gaps or [],
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
    return vpr.validate(doc, GOALS_DOC)


def has_err(doc, pattern):
    return any(re.search(pattern, e, re.I) for e in errs(doc))


def run():
    # P1: the real committed registry validates (read-only)
    real = yaml.safe_load(REAL_REGISTRY.read_text(encoding="utf-8"))
    real_goals = yaml.safe_load(REAL_GOALS.read_text(encoding="utf-8"))
    real_errors = vpr.validate(real, real_goals)
    check("P1 valid real registry", not real_errors, f"errors: {real_errors[:3]}")

    # P2: duplicate paper_id rejected
    d = base_doc([base_paper(), base_paper(citation_keys=["other2020key"],
                                            title="A Different Synthetic Title")])
    check("P2 duplicate paper ID rejected", has_err(d, "duplicate paper_id"))

    # P3: citation key owned by two papers rejected
    d = base_doc([base_paper(),
                  base_paper(paper_id="paper_roe_2021_other", title="Another Synthetic Title",
                             citation_keys=["doe2020synthetic"])])
    check("P3 citation key assigned to two papers rejected", has_err(d, "citation key .* owned by both"))

    # P4: duplicate DOI rejected
    d = base_doc([base_paper(identifiers={"doi": "10.1000/xyz", "arxiv": None, "other": None}),
                  base_paper(paper_id="paper_roe_2021_other", title="Another Synthetic Title",
                             citation_keys=["roe2021other"],
                             identifiers={"doi": "10.1000/XYZ", "arxiv": None, "other": None})])
    check("P4 duplicate DOI rejected", has_err(d, "duplicate DOI"))

    # P5: normalized duplicate title rejected
    d = base_doc([base_paper(),
                  base_paper(paper_id="paper_roe_2021_other", citation_keys=["roe2021other"],
                             title="A  synthetic METHOD for testing!")])
    check("P5 normalized duplicate title rejected", has_err(d, "normalized duplicate title"))

    # P6: missing required metadata rejected (complete_local without venue)
    d = base_doc([base_paper(venue=None)])
    check("P6 missing required metadata rejected", has_err(d, "complete_local requires venue"))

    # P7: unresolved metadata allowed only with honest status
    d_ok = base_doc([base_paper(metadata_status="partial_local", venue=None,
                                notes="venue missing from the local bibliography")])
    d_bad = base_doc([base_paper(metadata_status="partial_local", venue=None, notes=None)])
    check("P7 unresolved metadata allowed only with honest status",
          not errs(d_ok) and has_err(d_bad, "partial_local requires a notes"))

    # P8: invalid year rejected
    d = base_doc([base_paper(year="twenty-twenty")])
    d2 = base_doc([base_paper(year=1450)])
    check("P8 invalid year rejected", has_err(d, "invalid year") and has_err(d2, "invalid year"))

    # P9: absolute local path rejected
    d = base_doc([base_paper(source_records=[
        {"repository": "thesis_overleaf", "path": r"C:\Users\someone\references.bib",
         "source_type": "bibliography", "citation_key": "doe2020synthetic", "note": ""}])])
    check("P9 absolute local path rejected", has_err(d, "absolute"))

    # P10: paper without source record rejected
    d = base_doc([base_paper(source_records=[])])
    check("P10 paper without source record rejected", has_err(d, "at least one source_records"))

    # P11: invented verified DOI / premature external verification rejected
    d = base_doc([base_paper(verification_status="externally_verified")])
    d2 = base_doc([base_paper(identifiers={"doi": "10.1/x", "arxiv": None, "other": None,
                                            "doi_verified": True})])
    check("P11 invented verified DOI rejected",
          has_err(d, "externally_verified while") and has_err(d2, "doi_verified"))

    # P12: internal experiment label used as paper rejected
    d = base_doc([base_paper(title="AFAC")])
    d2 = base_doc([base_paper(paper_id="paper_h15_2026_frozen")])
    d3 = base_doc([base_paper(title="D8b")])
    check("P12 internal experiment label used as paper rejected",
          has_err(d, "internal experiment label") and has_err(d2, "internal experiment label")
          and has_err(d3, "internal experiment label"))

    # P13: candidate mapping without relationship strength rejected
    d = base_doc([base_paper(candidate_direction_tags=[{"direction": "ensemble_or_gating"}])])
    d2 = base_doc([base_paper(candidate_direction_tags=["ensemble_or_gating"])])
    check("P13 candidate mapping without relationship strength rejected",
          has_err(d, "direction, relationship") and has_err(d2, "direction, relationship"))

    # P14: invalid goal/task tag rejected
    d = base_doc([base_paper(task_tags=["clinical_deployment_success"])])
    check("P14 invalid goal/task tag rejected", has_err(d, "not an approved goal ID"))

    # P15: unsupported future-fall-risk implication rejected
    d = base_doc([base_paper(dataset_tags=["sensefi_ut_har"],
                             task_tags=["future_fall_risk_prediction"])])
    check("P15 unsupported future-fall-risk implication rejected",
          has_err(d, "must not co-occur with unsupported task"))

    # P16: bibliography aliases deduplicated into one paper (validates cleanly)
    d = base_doc([base_paper(citation_keys=["doe2020synthetic", "doe2020syn_oldkey"])])
    check("P16 bibliography aliases deduplicated into one paper", not errs(d))

    # P17: conflicting local metadata represented honestly
    d_ok = base_doc([base_paper(metadata_status="conflicting_local",
                                metadata_conflicts=["two local sources disagree on the title"])])
    d_bad = base_doc([base_paper(metadata_status="conflicting_local")])
    check("P17 conflicting local metadata represented honestly",
          not errs(d_ok) and has_err(d_bad, "requires metadata_conflicts"))

    # P18: paper claim and our interpretation remain separate
    same = "Identical text in both fields."
    d = base_doc([base_paper(paper_contribution_summary=same,
                             relevance_to_current_results=same)])
    d2 = base_doc([base_paper(
        paper_contribution_summary="OUR INTERPRETATION: leaked into the paper claim field.")])
    check("P18 paper claim and our interpretation remain separate",
          has_err(d, "must stay separate") and has_err(d2, "contains interpretation text"))

    # P19: literature-gap record validates; duplicates/missing fields rejected
    gap = {"gap_id": "gap_synthetic", "direction": "walking_pattern_recognition",
           "current_status": "not_locally_cited", "reason": "no local citation",
           "required_future_action": "find and cite a real publication"}
    d_ok = base_doc(gaps=[gap])
    d_dup = base_doc(gaps=[gap, dict(gap)])
    d_missing = base_doc(gaps=[{"gap_id": "gap_two", "direction": "walking_pattern_recognition",
                                "current_status": "not_locally_cited", "reason": ""}])
    check("P19 literature-gap record validates",
          not errs(d_ok) and has_err(d_dup, "duplicate literature gap_id")
          and has_err(d_missing, "missing"))

    # P20: clinical overclaim rejected (negated boundary phrasing stays allowed)
    d = base_doc([base_paper(
        relevance_to_current_results="OUR INTERPRETATION: this shows our system is clinically validated.")])
    d_ok = base_doc([base_paper(claim_boundaries=[
        "This result is not clinically validated and no deployment claim is made."])])
    check("P20 clinical overclaim rejected",
          has_err(d, "clinical/deployment claim") and not errs(d_ok))

    # P21: excessive verbatim quotation rejected
    d = base_doc([base_paper(paper_contribution_summary="lorem ipsum " * 120)])
    check("P21 excessive verbatim quotation rejected", has_err(d, "long verbatim extracts"))

    # P22: defense-line mapping validates; invalid labels rejected
    d_ok = base_doc([base_paper(defense_line_tags=["D1", "D9", "D14"])])
    d_bad = base_doc([base_paper(defense_line_tags=["D99"])])
    check("P22 defense-line mapping validates",
          not errs(d_ok) and has_err(d_bad, "invalid defense-line label"))

    # P23: no PDF existence requirement (validator source has no PDF check; record needs no file)
    src = (Path(vpr.__file__)).read_text(encoding="utf-8")
    check("P23 no PDF existence requirement",
          ".pdf" not in src.lower() and not errs(base_doc()))

    # P24: local-source-only registry validates without network (no network imports/calls)
    check("P24 local-source-only validates without network",
          not re.search(r"\b(requests|urllib|http\.client|socket)\b", src)
          and not real_errors)

    # P25: registry ordering / validator output is deterministic
    buf1, buf2 = io.StringIO(), io.StringIO()
    with redirect_stdout(buf1):
        rc1 = vpr.main([])
    with redirect_stdout(buf2):
        rc2 = vpr.main([])
    check("P25 registry ordering is deterministic",
          rc1 == rc2 == 0 and buf1.getvalue() == buf2.getvalue())

    # extra: validator never mutates inputs
    d = base_doc()
    snapshot = copy.deepcopy(d)
    vpr.validate(d, GOALS_DOC)
    check("extra: validate() is pure (input unmutated)", d == snapshot)

    # extra: malformed root rejected without crash
    check("extra: non-mapping root rejected", vpr.validate([1, 2], GOALS_DOC) != [])

    # extra: scope policy enforced
    d = base_doc()
    d["registry_scope"]["clinical_claims_allowed"] = True
    check("extra: clinical_claims_allowed=true rejected",
          has_err(d, "clinical_claims_allowed must be false"))

    print()
    print(f"RESULT: {'ALL PASS' if FAILED == 0 else 'FAILURES'} ({PASSED}/{PASSED + FAILED})")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
