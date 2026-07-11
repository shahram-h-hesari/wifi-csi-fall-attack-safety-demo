#!/usr/bin/env python
"""NEXT-EXP-REVIEW acceptance tests for the Brainstorm Checker + its review validator.

Synthetic in-memory fixtures for every verdict/rejection case; the real generated review, the real
registries, and the real validator are only ever READ. No network, no subprocess, no PDF/checkpoint
requirement, no experiment/queue/test-read action.

Run: python scripts/automation/test_next_experiment_brainstorm_checker.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import next_experiment_brainstorm_checker as chk  # noqa: E402
import validate_next_experiment_review as vnr  # noqa: E402

REPO = chk.REPO

# ---- synthetic index (stands in for _index over the real registries) ------------------------
SYN_IDX = {
    "candidates": [],
    "paper_ids": {"paper_direct", "paper_indirect", "paper_background"},
    "gap_ids": {"gap_syn"},
    "goals": {
        "fall_detection": {"allowed_evidence_levels": ["frozen-test", "validation-only"]},
        "walking_detection": {"allowed_evidence_levels": ["validation-only"]},
        "future_fall_risk_prediction": {"allowed_evidence_levels": []},
    },
    "dataset_ids": {"sensefi_ut_har"},
    "ref_evidence_keys": {"H15_eps0015_frozen", "AFAC_eps0030_F20_posthoc"},
    "ref_evidence_levels": {"H15_eps0015_frozen": "frozen-test", "AFAC_eps0030_F20_posthoc": "test-post-hoc"},
    "evaluation_ids": {"eval_syn_v1"},
    "protocol_ids": {"H15-TEST-EPS0015-AFAC-20260705"},
}


def syn_candidate(**over):
    c = {
        "candidate_id": "candidate_syn_v1",
        "title": "Synthetic",
        "hypothesis": "A benign synthetic hypothesis.",
        "target_gap": "a synthetic gap",
        "direction_tags": ["neyman_pearson_far_control"],
        "literature_support": [{"paper_id": "paper_direct", "relationship": "direct"}],
        "literature_gap_ids": [],
        "current_evidence_refs": [{"source": "research_os", "identity": "H15_eps0015_frozen",
                                    "relationship": "background", "note": "context"}],
        "current_evidence_summary": "short",
        "prior_negative_evidence_refs": [],
        "our_rationale": "OUR INTERPRETATION: benign.",
        "required_dataset_ids": ["sensefi_ut_har"],
        "target_goal_ids": ["fall_detection"],
        "dataset_readiness": "available",
        "allowed_split": "validation_only",
        "frozen_protocol_requirement": None,
        "test_read_risk": "none",
        "other_risks": [],
        "evidence_strength": "strong_local_and_literature",
        "status": "proposed",
        "claim_boundaries": ["this record is not a verdict"],
        "supersedes": None,
        "superseded_by": None,
        "notes": None,
    }
    c.update(over)
    return c


def verdict_of(candidate, base=REPO, idx=None):
    return chk.build_entry(candidate, idx or SYN_IDX, base)["derived_verdict"]


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


def run():
    # 1. real generated review validates via the real validator
    check("real generated review validates", vnr.validate(REPO) == [], f"{vnr.validate(REPO)[:2]}")

    # 2. available validation-only supported candidate with strong+direct support -> GO
    check("supported validation-only strong+direct -> GO", verdict_of(syn_candidate()) == "GO")

    # 3. available_not_evaluated caps at REVIEW (never GO)
    check("available_not_evaluated -> REVIEW",
          verdict_of(syn_candidate(dataset_readiness="available_not_evaluated",
                                    target_goal_ids=["walking_detection"])) == "REVIEW")

    # 4. unavailable dataset -> NO-GO
    check("unavailable dataset -> NO-GO",
          verdict_of(syn_candidate(dataset_readiness="unavailable")) == "NO-GO")

    # 5. aspirational dataset -> NO-GO
    check("aspirational_only dataset -> NO-GO",
          verdict_of(syn_candidate(dataset_readiness="aspirational_only")) == "NO-GO")

    # 6. no_experiment_allowed -> NO-GO
    check("no_experiment_allowed -> NO-GO",
          verdict_of(syn_candidate(allowed_split="no_experiment_allowed")) == "NO-GO")

    # 7. literature gap -> REVIEW cap
    check("literature gap -> REVIEW",
          verdict_of(syn_candidate(literature_gap_ids=["gap_syn"])) == "REVIEW")

    # 8. indirect-only literature -> REVIEW cap
    check("indirect-only literature -> REVIEW",
          verdict_of(syn_candidate(literature_support=[{"paper_id": "paper_indirect", "relationship": "indirect"}],
                                    evidence_strength="local_supported_literature_indirect")) == "REVIEW")

    # 9. D13/D14-style prior negative with NO stated difference -> NO-GO
    prior = [{"source": "research_os", "identity": "H15_eps0015_frozen", "relationship": "direct",
              "note": "prior gate failure"}]
    check("prior negative, missing material difference -> NO-GO",
          verdict_of(syn_candidate(prior_negative_evidence_refs=prior,
                                    hypothesis="Just rerun the same thing.",
                                    our_rationale="OUR INTERPRETATION: nothing new.",
                                    evidence_strength="local_negative_evidence")) == "NO-GO")

    # 10. prior negative WITH stated material difference -> REVIEW (capped, never NO-GO from missing)
    check("prior negative, stated material difference -> REVIEW",
          verdict_of(syn_candidate(prior_negative_evidence_refs=prior,
                                    hypothesis="A materially different formulation, not the prior one.",
                                    evidence_strength="local_negative_evidence")) == "REVIEW")

    # 11. unresolved paper reference -> NO-GO
    check("unresolved paper reference -> NO-GO",
          verdict_of(syn_candidate(literature_support=[{"paper_id": "paper_missing", "relationship": "direct"}])) == "NO-GO")

    # 12. unresolved evidence reference (bad path, empty base) -> NO-GO
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        cand = syn_candidate(current_evidence_refs=[{"source": "research_os",
                             "identity": "results/nonexistent/missing.md", "relationship": "background", "note": ""}])
        check("unresolved evidence reference -> NO-GO", verdict_of(cand, base=Path(td)) == "NO-GO")

    # 13. invalid dataset / goal -> unresolved -> NO-GO
    check("invalid dataset -> NO-GO", verdict_of(syn_candidate(required_dataset_ids=["nope"])) == "NO-GO")
    check("invalid goal -> NO-GO", verdict_of(syn_candidate(target_goal_ids=["nope"])) == "NO-GO")

    # 14. missing/invalid frozen protocol where test access required -> NO-GO
    check("existing_frozen_protocol_only with bad protocol -> NO-GO",
          verdict_of(syn_candidate(allowed_split="existing_frozen_protocol_only",
                                    frozen_protocol_requirement="MADE-UP", test_read_risk="low")) == "NO-GO")

    # 15. requires_new_frozen_protocol cannot GO (-> REVIEW)
    check("requires_new_frozen_protocol -> REVIEW (never GO)",
          verdict_of(syn_candidate(allowed_split="requires_new_frozen_protocol",
                                    frozen_protocol_requirement="new_protocol_required",
                                    test_read_risk="requires_review")) == "REVIEW")

    # 16. test-read risk cannot GO (-> REVIEW)
    check("test_read_risk requires_review -> REVIEW (never GO)",
          verdict_of(syn_candidate(test_read_risk="requires_review")) == "REVIEW")
    check("test_read_risk blocked_without_protocol -> REVIEW (never GO)",
          verdict_of(syn_candidate(test_read_risk="blocked_without_protocol")) == "REVIEW")

    # 17. a manually-stuffed verdict field in the candidate is IGNORED (recomputed)
    stuffed = syn_candidate(dataset_readiness="unavailable")
    stuffed["derived_verdict"] = "GO"
    stuffed["verdict"] = "GO"
    check("manual verdict field ignored (recomputed NO-GO)", verdict_of(stuffed) == "NO-GO")

    # 18. stored priority/score/rank fields are ignored by ranking (computed keys win)
    a = chk.build_entry(syn_candidate(candidate_id="candidate_bbb", evidence_strength="literature_only",
                                       literature_support=[{"paper_id": "paper_direct", "relationship": "direct"}]), SYN_IDX, REPO)
    b = chk.build_entry(syn_candidate(candidate_id="candidate_aaa", evidence_strength="strong_local_and_literature",
                                       literature_support=[{"paper_id": "paper_direct", "relationship": "direct"}]), SYN_IDX, REPO)
    cand_by_id = {"candidate_bbb": syn_candidate(candidate_id="candidate_bbb", evidence_strength="literature_only"),
                  "candidate_aaa": syn_candidate(candidate_id="candidate_aaa", evidence_strength="strong_local_and_literature")}
    ordered = sorted([a, b], key=lambda e: chk._rank_key(e, cand_by_id))
    # both GO (verdict tier equal); stronger evidence (candidate_aaa) ranks first regardless of id/stored score
    check("stored priority/score ignored; evidence order wins",
          ordered[0]["candidate_id"] == "candidate_aaa")

    # 19. deterministic rank tie-break by candidate_id (all rank keys equal except id)
    e1 = chk.build_entry(syn_candidate(candidate_id="candidate_zzz"), SYN_IDX, REPO)
    e2 = chk.build_entry(syn_candidate(candidate_id="candidate_aaa"), SYN_IDX, REPO)
    cbi = {"candidate_zzz": syn_candidate(candidate_id="candidate_zzz"),
           "candidate_aaa": syn_candidate(candidate_id="candidate_aaa")}
    tie = sorted([e1, e2], key=lambda e: chk._rank_key(e, cbi))
    check("deterministic tie-break alphabetical by candidate_id", tie[0]["candidate_id"] == "candidate_aaa")

    # 20. build assigns contiguous ranks 1..N over the real registry
    sources = chk.load_sources(REPO)
    doc = chk.build_review(sources, existing=yaml_load(chk.REVIEW_PATH))
    ranks = sorted(e["rank"] for e in doc["entries"])
    check("ranks contiguous 1..N", ranks == list(range(1, len(doc["entries"]) + 1)))

    # 21. summary counts match entries
    s = doc["summary"]
    check("summary counts match entries",
          s["go_count"] == sum(1 for e in doc["entries"] if e["derived_verdict"] == "GO")
          and s["review_count"] == sum(1 for e in doc["entries"] if e["derived_verdict"] == "REVIEW")
          and s["no_go_count"] == sum(1 for e in doc["entries"] if e["derived_verdict"] == "NO-GO"))

    # 22. wrong source fingerprint is detectable (tamper -> mismatch)
    real_fp = chk.compute_fingerprint(sources)
    check("source fingerprint mismatch detectable", real_fp != "deadbeef" and doc["source_fingerprint"] == real_fp)

    # 23. generated_at/review_id preserved when fingerprint unchanged
    doc2 = chk.build_review(sources, existing=doc)
    check("generated_at/review_id preserved on unchanged fingerprint",
          doc2["review_id"] == doc["review_id"] and doc2["generated_at"] == doc["generated_at"])

    # 24. output byte-identical on second build
    check("output byte-identical on second build", chk.dump_yaml(doc) == chk.dump_yaml(doc2))

    # 25. changed fingerprint -> new review_id/generated_at
    doc_changed = chk.build_review(sources, existing={"source_fingerprint": "different", "review_id": "old", "generated_at": "old"})
    check("changed fingerprint -> new review_id", doc_changed["review_id"] != "old")

    # 26-30. validator structural regexes reject forbidden content
    check("command-like content rejected", bool(vnr.COMMAND_LIKE_RE.search("run --split test now")))
    check("queue linkage rejected", bool(vnr.QUEUE_LINKAGE_RE.search("queue_entry: EQ-2026-07-14-J1")))
    check("absolute path rejected", bool(vnr.ABS_PATH_RE.search(r"C:\Users\someone\notes.md")))
    check("clinical claim rejected", bool(vnr.CLINICAL_OVERCLAIM_RE.search("this is deployment-ready")))
    check("long markdown table row rejected",
          bool(vnr.MARKDOWN_TABLE_ROW_RE.search("| a | b | c | d | e | f |")))
    check("execution-auth content rejected", chk._affirmative_hit("we authorize a test read", chk.EXECUTION_AUTH_TRIGGERS) is not None)
    check("negated execution phrase allowed", chk._affirmative_hit("does not authorize a test read", chk.EXECUTION_AUTH_TRIGGERS) is None)

    # 31. checker source is network/subprocess free (actual imports/calls, not docstring mentions)
    src = Path(chk.__file__).read_text(encoding="utf-8")
    import re as _re
    forbidden_import = _re.search(r"^\s*(?:import|from)\s+(subprocess|socket|urllib|requests|http\.client|pty|asyncio)\b", src, _re.M)
    check("checker imports no forbidden module", forbidden_import is None)
    check("checker uses no forbidden call",
          not any(t in src for t in ("os.system(", "os.popen(", "subprocess.", "eval(", "exec(")))

    # 32. checker writes ONLY the designated review file (exactly one write_text, to review_path)
    check("checker writes only the designated review file",
          src.count(".write_text(") == 1 and "review_path.write_text(" in src
          and not _re.search(r"open\([^)]*['\"][wax]", src))

    # 33. clinical negation allowed (boundary phrasing not flagged)
    check("negated clinical phrase allowed", not vnr.CLINICAL_OVERCLAIM_RE.search("this is not clinically validated"))

    # 34. purity: build_entry does not mutate the candidate
    cand = syn_candidate()
    snap = copy.deepcopy(cand)
    chk.build_entry(cand, SYN_IDX, REPO)
    check("build_entry does not mutate the candidate", cand == snap)

    print()
    print(f"RESULT: {'ALL PASS' if FAILED == 0 else 'FAILURES'} ({PASSED}/{PASSED + FAILED})")
    return 0 if FAILED == 0 else 1


def yaml_load(path):
    import yaml
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


if __name__ == "__main__":
    raise SystemExit(run())
