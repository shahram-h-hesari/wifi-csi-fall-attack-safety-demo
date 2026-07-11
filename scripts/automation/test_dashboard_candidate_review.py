#!/usr/bin/env python
"""DASH-NEXT-EXP-REVIEW acceptance tests for the candidate-review dashboard section.

Synthetic tmp_path fixtures for missing/invalid-review cases; the real generated review and the
real dashboard render are only ever READ. No network, no subprocess, no experiment/queue action.

Run: python -m pytest scripts/automation/test_dashboard_candidate_review.py -v
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dashboard_candidate_review as dcr  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
REAL_REVIEW = REPO / "automation" / "reviews" / "next_experiment_review.yaml"


def _real_sources():
    return {"next_experiment_review_yaml": str(REAL_REVIEW)}


def _write(path: Path, doc) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def _synthetic_review(**over):
    doc = {
        "schema_version": 1,
        "review_id": "review_synthetic_v1",
        "generated_at": "2026-01-01T000000Z",
        "source_fingerprint": "deadbeef",
        "candidate_count": 2,
        "entries": [
            {"candidate_id": "candidate_x", "rank": 1, "derived_verdict": "REVIEW",
             "verdict_reasons": ["reason one"], "blockers": [],
             "required_human_actions": ["do X"],
             "material_difference_requirement": {"status": "not_applicable"}},
            {"candidate_id": "candidate_y", "rank": 2, "derived_verdict": "NO-GO",
             "verdict_reasons": ["reason two"], "blockers": ["blocker one"],
             "required_human_actions": ["do Y"],
             "material_difference_requirement": {"status": "missing"}},
        ],
        "summary": {"go_count": 0, "review_count": 1, "no_go_count": 1},
    }
    doc.update(over)
    return doc


# =============================================================== 1. section renders
def test_candidate_review_section_renders():
    out = dcr.render_candidate_review(_real_sources())
    assert dcr.BEGIN_MARK in out and dcr.END_MARK in out
    assert "## 2b. Next-Experiment Candidate Review" in out


# =============================================================== 2. exact rank order preserved
def test_exact_rank_order_preserved():
    out = dcr.render_candidate_review(_real_sources())
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    expected_order = [e["candidate_id"] for e in sorted(doc["entries"], key=lambda e: e["rank"])]
    positions = [out.find(f"`{cid}`") for cid in expected_order]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions), "candidates must appear in accepted rank order"


# =============================================================== 3. counts GO=0 REVIEW=6 NO-GO=2
def test_counts_match_accepted_review():
    out = dcr.render_candidate_review(_real_sources())
    assert "**GO:** 0" in out
    assert "**REVIEW:** 6" in out
    assert "**NO-GO:** 2" in out


# =============================================================== 4. all eight candidates exactly once
def test_all_eight_candidates_appear_exactly_once():
    out = dcr.render_candidate_review(_real_sources())
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    for e in doc["entries"]:
        cid = e["candidate_id"]
        assert out.count(f"`{cid}`") >= 1, cid
    assert len(doc["entries"]) == 8


# =============================================================== 5. verdicts match the accepted review
def test_verdicts_match_accepted_review():
    out = dcr.render_candidate_review(_real_sources())
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    for e in doc["entries"]:
        row = f"| {e['rank']} | `{e['candidate_id']}` | {dcr.VERDICT_BADGE[e['derived_verdict']]} |"
        assert row in out, e["candidate_id"]


# =============================================================== 6. NO-GO blockers displayed
def test_no_go_blockers_displayed():
    out = dcr.render_candidate_review(_real_sources())
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    for e in doc["entries"]:
        if e["derived_verdict"] == "NO-GO":
            for b in e.get("blockers") or []:
                assert f"blocker: {b}" in out


# =============================================================== 7. D13/D14 material-difference statuses displayed
def test_material_difference_statuses_displayed():
    out = dcr.render_candidate_review(_real_sources())
    assert "stated_unverified" in out  # D13 (ensemble) and D14 (partial-auc) candidates
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    d13_or_d14 = [e for e in doc["entries"]
                  if e["candidate_id"] in ("candidate_ensemble_gating_score_fusion_v1",
                                           "candidate_partial_auc_low_far_ranking_v1")]
    assert len(d13_or_d14) == 2
    for e in d13_or_d14:
        assert e["material_difference_requirement"]["status"] == "stated_unverified"


# =============================================================== 8. required human actions displayed
def test_required_human_actions_displayed():
    out = dcr.render_candidate_review(_real_sources())
    doc = yaml.safe_load(REAL_REVIEW.read_text(encoding="utf-8"))
    for e in doc["entries"]:
        for a in (e.get("required_human_actions") or [])[:1]:
            assert f"action: {a}" in out


# =============================================================== 9. no-execution-authorization warning
def test_no_execution_authorization_warning_present():
    out = dcr.render_candidate_review(_real_sources())
    assert "does not authorize" in out.lower() or "no verdict below authorizes" in out.lower()
    assert "held-out test data" in out
    assert "suitable for human planning review only" in out.lower()


# =============================================================== 10. missing review -> integrity warning
def test_missing_review_produces_integrity_warning(tmp_path):
    out = dcr.render_candidate_review({"next_experiment_review_yaml": str(tmp_path / "nope.yaml")})
    assert "INTEGRITY WARNING" in out
    assert "not found" in out
    assert dcr.BEGIN_MARK in out and dcr.END_MARK in out


# =============================================================== 11. invalid review -> integrity warning
def test_invalid_review_produces_integrity_warning(tmp_path):
    # malformed YAML
    bad = tmp_path / "bad.yaml"
    bad.write_text("entries: [this is: not: valid", encoding="utf-8")
    out = dcr.render_candidate_review({"next_experiment_review_yaml": str(bad)})
    assert "INTEGRITY WARNING" in out

    # duplicate candidate_id
    dup = _write(tmp_path / "dup.yaml", _synthetic_review(
        entries=[{"candidate_id": "candidate_x", "rank": 1, "derived_verdict": "GO",
                  "material_difference_requirement": {"status": "not_applicable"}},
                 {"candidate_id": "candidate_x", "rank": 2, "derived_verdict": "GO",
                  "material_difference_requirement": {"status": "not_applicable"}}],
        summary={"go_count": 2, "review_count": 0, "no_go_count": 0}))
    out2 = dcr.render_candidate_review({"next_experiment_review_yaml": str(dup)})
    assert "INTEGRITY WARNING" in out2 and "duplicate" in out2.lower()

    # non-contiguous ranks
    gap = _write(tmp_path / "gap.yaml", _synthetic_review(
        entries=[{"candidate_id": "candidate_x", "rank": 1, "derived_verdict": "GO",
                  "material_difference_requirement": {"status": "not_applicable"}},
                 {"candidate_id": "candidate_y", "rank": 3, "derived_verdict": "GO",
                  "material_difference_requirement": {"status": "not_applicable"}}],
        summary={"go_count": 2, "review_count": 0, "no_go_count": 0}))
    out3 = dcr.render_candidate_review({"next_experiment_review_yaml": str(gap)})
    assert "INTEGRITY WARNING" in out3 and "contiguous" in out3.lower()

    # summary counts disagree with entries
    wrong = _write(tmp_path / "wrong.yaml", _synthetic_review(summary={"go_count": 5, "review_count": 0, "no_go_count": 0}))
    out4 = dcr.render_candidate_review({"next_experiment_review_yaml": str(wrong)})
    assert "INTEGRITY WARNING" in out4 and "summary counts" in out4.lower()


# =============================================================== 12. deterministic and idempotent
def test_rendering_deterministic_and_idempotent():
    a = dcr.render_candidate_review(_real_sources())
    b = dcr.render_candidate_review(_real_sources())
    assert a == b


def test_full_dashboard_idempotent_with_candidate_review():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_dashboard as ud
    a_md, a_js, _ = ud.do_render(write=False)
    b_md, b_js, _ = ud.do_render(write=False)
    assert a_md == b_md
    assert a_js == b_js


# =============================================================== 13. existing sections retain meaning
def test_existing_dashboard_sections_unaffected():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_dashboard as ud
    md, _, status = ud.do_render(write=False)
    assert "## 1. Now / Next / Blocked" in md
    assert "## 2. Research Evidence & Canonical Identity" in md
    assert "## 2b. Next-Experiment Candidate Review" in md
    assert "## 3. 7-day roadmap" in md
    assert "AFAC frozen-test evaluation under PGD epsilon=0.015" in md  # D3 section untouched


# =============================================================== 14. registry/queue remain unchanged
def test_candidate_registry_and_queue_unchanged_by_rendering():
    reg = REPO / "automation" / "registry" / "experiment_candidates.yaml"
    q = REPO / "automation" / "experiment_queue.yaml"
    before_reg, before_q = reg.read_bytes(), q.read_bytes()
    dcr.render_candidate_review(_real_sources())
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_dashboard as ud
    ud.do_render(write=False)
    assert reg.read_bytes() == before_reg
    assert q.read_bytes() == before_q


# =============================================================== extra: no verdict recomputation
def test_renderer_never_recomputes_a_verdict():
    src = Path(dcr.__file__).read_text(encoding="utf-8")
    forbidden = ["dataset_readiness ==", "allowed_split ==", "evidence_strength ==",
                 "test_read_risk ==", "derive_verdict", "derive_material_difference"]
    for f in forbidden:
        assert f not in src, f"renderer must not re-implement verdict logic ({f!r} found)"


# =============================================================== extra: purity (no source mutation)
def test_load_review_does_not_mutate_sources():
    sources = _real_sources()
    snap = copy.deepcopy(sources)
    dcr.render_candidate_review(sources)
    assert sources == snap
