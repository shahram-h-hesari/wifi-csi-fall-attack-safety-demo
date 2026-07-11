#!/usr/bin/env python
"""Next Experiment Brainstorm Checker (NEXT-EXP-REVIEW) — read-only planning-review generator.

Design contract: automation/acceptance/next-experiment-review.yaml (accepted, hash-bound, NEVER
modified by this script). Reads the accepted registries, RE-RESOLVES every reference, derives a
deterministic GO/REVIEW/NO-GO verdict per candidate purely from structured fields, ranks
deterministically, and writes ONE file: automation/reviews/next_experiment_review.yaml.

Hard safety properties (statically asserted by the test suite):
  - stdlib + yaml only; NO subprocess, NO os.system/exec, NO socket/urllib/requests/http, NO
    network of any kind.
  - the ONLY path this module ever opens for writing is automation/reviews/next_experiment_review.yaml.
  - never constructs a runnable experiment command, never reads/writes a held-out test split,
    never authorizes a frozen-test read, never modifies any registry or the experiment queue.
  - GO is defined as "Suitable for human planning review only." -- never permission to run, queue,
    read test data, or use a frozen protocol.

Idempotency: the output records a source_fingerprint (digest of every authoritative input's bytes
plus this checker's policy+implementation version). Re-running with an unchanged fingerprint
preserves the existing review_id and generated_at and re-emits byte-identical YAML.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parents[2]
REVIEW_PATH = REPO / "automation" / "reviews" / "next_experiment_review.yaml"

SCHEMA_VERSION = 1
# policy_version tracks the section-6/8 rules in the acceptance contract; impl_version tracks this file.
POLICY_VERSION = "next-experiment-review-policy-v1"
IMPL_VERSION = "next-experiment-brainstorm-checker-v1"
RANKING_POLICY = "verdict > data_readiness > allowed_split > evidence_strength > candidate_id (see acceptance/next-experiment-review.yaml section 8)"

# Authoritative read-only inputs, in a FIXED sorted order so the fingerprint is deterministic.
AUTHORITATIVE_SOURCES = tuple(sorted([
    "automation/registry/experiment_candidates.yaml",
    "automation/literature/paper_registry.yaml",
    "automation/frontier.yaml",
    "automation/registry/goals.yaml",
    "automation/registry/datasets.yaml",
    "automation/registry/reference_evidence.yaml",
    "automation/registry/experiment_identity.yaml",
    "automation/artifact_manifest.csv",
    "automation/acceptance/protocol-freeze.yaml",  # accepted protocol-freeze record (present)
]))

# ----------------------------------------------------------------- deterministic ordering keys
VERDICT_ORDER = {"GO": 0, "REVIEW": 1, "NO-GO": 2}
DATA_READINESS_ORDER = {"available": 0, "available_not_evaluated": 1, "unavailable": 2, "aspirational_only": 3}
ALLOWED_SPLIT_ORDER = {"training_and_validation": 0, "validation_only": 1, "existing_frozen_protocol_only": 2,
                       "requires_new_frozen_protocol": 3, "no_experiment_allowed": 4}
EVIDENCE_STRENGTH_ORDER = {"strong_local_and_literature": 0, "local_supported_literature_indirect": 1,
                          "literature_only": 2, "literature_gap": 3, "local_negative_evidence": 4,
                          "dataset_blocked": 5}
RELATIONSHIP_STRENGTH = {"direct": 3, "indirect": 2, "background": 1, "not_established": 0}

GO_WORDING = "Suitable for human planning review only."

# Markers (case-insensitive) indicating a candidate states a materially different hypothesis.
MATERIAL_DIFFERENCE_MARKERS = (
    "materially different", "material difference", "materially-different",
    "different formulation", "different specialist set", "different combination rule",
    "different training objective",
)
# Affirmative casual-test-tuning triggers (negation-aware scan; see _affirmative_hit).
CASUAL_TEST_TUNING_TRIGGERS = (
    "tune on test", "tuning on test", "tune on the test", "tuning on the test",
    "select a threshold on test", "select threshold on test", "sweep threshold on test",
    "compare candidates on test", "compare on the test", "held-out test tuning",
    "test-set tuning", "casual test", "casually tune", "casually compare",
)
# Affirmative execution / test-read authorization triggers (negation-aware).
EXECUTION_AUTH_TRIGGERS = (
    "authorize a test read", "authorizes a test read", "authorize execution",
    "authorizes execution", "approved to run", "cleared to run", "authorize the frozen read",
    "enqueue this candidate", "add to the experiment queue",
)
NEGATION_WINDOW = 32
NEGATION_WORDS = ("not ", "never ", "no ", "without ", "must not", "cannot ", "can never", "does not")


def _affirmative_hit(text, triggers):
    """Return the first trigger substring present WITHOUT a negation in the preceding window, or None."""
    low = (text or "").lower()
    for trig in triggers:
        start = 0
        while True:
            i = low.find(trig, start)
            if i < 0:
                break
            preceding = low[max(0, i - NEGATION_WINDOW):i]
            if not any(neg in preceding for neg in NEGATION_WORDS):
                return trig
            start = i + 1
    return None


# --------------------------------------------------------------------------- loading (read-only)
def load_sources(base=REPO):
    """Read every authoritative input's raw bytes (for fingerprinting) and parsed content."""
    raw = {}
    parsed = {}
    for rel in AUTHORITATIVE_SOURCES:
        p = base / rel
        raw[rel] = p.read_bytes() if p.exists() else b""
        if rel.endswith(".yaml") and p.exists():
            parsed[rel] = yaml.safe_load(raw[rel].decode("utf-8")) or {}
        else:
            parsed[rel] = None  # csv/manifest read for fingerprint + path-existence only
    return {"base": base, "raw": raw, "parsed": parsed}


def compute_fingerprint(sources):
    """Deterministic digest over each authoritative file's sha256 (in fixed sorted order) plus the
    checker's policy and implementation versions."""
    h = hashlib.sha256()
    for rel in AUTHORITATIVE_SOURCES:  # already sorted
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(hashlib.sha256(sources["raw"][rel]).hexdigest().encode("utf-8"))
        h.update(b"\x00")
    h.update(POLICY_VERSION.encode("utf-8"))
    h.update(b"\x00")
    h.update(IMPL_VERSION.encode("utf-8"))
    return h.hexdigest()


def source_hashes(sources):
    return [{"path": rel, "sha256": hashlib.sha256(sources["raw"][rel]).hexdigest()}
            for rel in AUTHORITATIVE_SOURCES]


# ----------------------------------------------------------------------------- index helpers
def _index(sources):
    p = sources["parsed"]
    cand = p["automation/registry/experiment_candidates.yaml"] or {}
    papers = p["automation/literature/paper_registry.yaml"] or {}
    goals = p["automation/registry/goals.yaml"] or {}
    datasets = p["automation/registry/datasets.yaml"] or {}
    ref_ev = p["automation/registry/reference_evidence.yaml"] or {}
    identity = p["automation/registry/experiment_identity.yaml"] or {}
    frontier = p["automation/frontier.yaml"] or {}
    return {
        "candidates": cand.get("candidates") or [],
        "paper_ids": {x.get("paper_id") for x in (papers.get("papers") or [])},
        "gap_ids": {g.get("gap_id") for g in (papers.get("literature_gaps") or [])},
        "goals": {g.get("id"): g for g in (goals.get("goals") or [])},
        "dataset_ids": {d.get("id") for d in (datasets.get("datasets") or [])},
        "ref_evidence_keys": {e.get("key") for e in (ref_ev.get("reference_results") or [])},
        "ref_evidence_levels": {e.get("key"): e.get("evidence_level") for e in (ref_ev.get("reference_results") or [])},
        "evaluation_ids": {e.get("evaluation_id") for e in (identity.get("evaluations") or [])},
        "protocol_ids": {fp.get("protocol_id") for fp in (frontier.get("frozen_protocol_registry") or [])},
    }


# ----------------------------------------------------------------------------- reference resolution
def resolve_references(candidate, idx, base):
    """Re-resolve EVERY reference the candidate makes. Returns a sorted list of unresolved-reference
    strings (empty == all resolved). An unresolved required reference is a blocker (-> NO-GO)."""
    unresolved = []
    for ls in candidate.get("literature_support") or []:
        if ls.get("paper_id") not in idx["paper_ids"]:
            unresolved.append(f"paper_id {ls.get('paper_id')!r} not in paper_registry.yaml")
    for gid in candidate.get("literature_gap_ids") or []:
        if gid not in idx["gap_ids"]:
            unresolved.append(f"literature_gap_id {gid!r} not in paper_registry.yaml literature_gaps")
    for did in candidate.get("required_dataset_ids") or []:
        if did not in idx["dataset_ids"]:
            unresolved.append(f"dataset_id {did!r} not in datasets.yaml")
    for gid in candidate.get("target_goal_ids") or []:
        if gid not in idx["goals"]:
            unresolved.append(f"goal_id {gid!r} not in goals.yaml")
    fpr = candidate.get("frozen_protocol_requirement")
    if fpr and fpr != "new_protocol_required" and fpr not in idx["protocol_ids"]:
        unresolved.append(f"frozen_protocol_requirement {fpr!r} not in frontier.yaml frozen_protocol_registry")
    for kind in ("current_evidence_refs", "prior_negative_evidence_refs"):
        for ref in candidate.get(kind) or []:
            ident = ref.get("identity")
            if ident is None:
                unresolved.append(f"{kind} entry has no identity")
                continue
            if (ident in idx["ref_evidence_keys"] or ident in idx["evaluation_ids"]
                    or ident in idx["protocol_ids"] or ident in idx["dataset_ids"]):
                continue
            # otherwise it must be an existing repository-relative path
            if (base / ident).exists():
                continue
            unresolved.append(f"{kind} identity {ident!r} does not resolve to a known id or repo-relative path")
    return sorted(unresolved)


# ------------------------------------------------------------------------- material difference
def derive_material_difference(candidate):
    """DERIVED at generation time (never a candidate field). See acceptance contract section 5."""
    priors = candidate.get("prior_negative_evidence_refs") or []
    if not priors:
        return {"required": False, "status": "not_applicable", "basis_refs": [],
                "explanation": "no prior negative evidence applies to this candidate"}
    basis = sorted(str(r.get("identity")) for r in priors if r.get("identity"))
    text = " ".join(str(candidate.get(f) or "") for f in ("hypothesis", "our_rationale"))
    text += " " + " ".join(str(x) for x in (candidate.get("other_risks") or []))
    text += " " + str(candidate.get("notes") or "")
    if any(m in text.lower() for m in MATERIAL_DIFFERENCE_MARKERS):
        return {"required": True, "status": "stated_unverified", "basis_refs": basis,
                "explanation": "prior negative evidence exists and a materially different hypothesis is "
                               "stated; a human must judge whether the stated difference is sufficient "
                               "(the checker never certifies this)"}
    return {"required": True, "status": "missing", "basis_refs": basis,
            "explanation": "prior negative evidence exists but no materially different hypothesis is stated"}


# ------------------------------------------------------------------------------- dimensions
def derive_dimensions(candidate):
    lit = candidate.get("literature_support") or []
    best = max((RELATIONSHIP_STRENGTH.get(x.get("relationship"), -1) for x in lit), default=-1)
    scientific_promise = {3: "direct_literature", 2: "indirect_literature",
                          1: "background_literature"}.get(best, "no_established_literature")

    md = derive_material_difference(candidate)
    if md["status"] == "not_applicable":
        practical_readiness = "no_prior_blockers"
    elif md["status"] == "missing":
        practical_readiness = "blocked_by_unaddressed_prior_negative"
    else:
        practical_readiness = "needs_material_difference_review"

    data_readiness = {"available": "data_ready", "available_not_evaluated": "data_ready_unevaluated",
                      "unavailable": "data_unavailable", "aspirational_only": "data_aspirational"}.get(
        candidate.get("dataset_readiness"), "data_unknown")

    split = candidate.get("allowed_split")
    risk = candidate.get("test_read_risk")
    fpr = candidate.get("frozen_protocol_requirement")
    if split == "no_experiment_allowed":
        split_safety = "no_experiment"
    elif split == "validation_only" and risk == "none" and not fpr:
        split_safety = "validation_only_safe"
    elif split == "training_and_validation" and risk == "none" and not fpr:
        split_safety = "train_val_safe"
    elif split == "existing_frozen_protocol_only":
        split_safety = "existing_frozen_protocol_review"
    elif split == "requires_new_frozen_protocol":
        split_safety = "requires_new_frozen_protocol_review"
    else:
        split_safety = "review_required"
    return {"scientific_promise": scientific_promise, "practical_readiness": practical_readiness,
            "data_readiness": data_readiness, "split_safety": split_safety, "_material": md}


# ---------------------------------------------------------------------------- verdict derivation
def derive_verdict(candidate, idx, unresolved, material):
    """Returns (verdict, no_go_reasons, review_reasons, blockers). Implements acceptance section 6."""
    no_go, review, blockers = [], [], []

    def blk(msg):
        no_go.append(msg)
        blockers.append(msg)

    readiness = candidate.get("dataset_readiness")
    split = candidate.get("allowed_split")
    strength = candidate.get("evidence_strength")
    risk = candidate.get("test_read_risk")
    fpr = candidate.get("frozen_protocol_requirement")

    # -------- force NO-GO
    if unresolved:
        for u in unresolved:
            blk(f"unresolved/stale reference forces NO-GO: {u}")
    if readiness == "unavailable":
        blk("dataset_readiness is unavailable")
    if readiness == "aspirational_only":
        blk("dataset_readiness is aspirational_only")
    if split == "no_experiment_allowed":
        blk("allowed_split is no_experiment_allowed")
    if strength == "dataset_blocked":
        blk("evidence_strength is dataset_blocked")
    for gid in candidate.get("target_goal_ids") or []:
        goal = idx["goals"].get(gid) or {}
        if goal and not (goal.get("allowed_evidence_levels") or []):
            blk(f"target goal {gid!r} has an empty allowed_evidence_levels list")
    if material["status"] == "missing":
        blk("prior negative evidence exists and the required material difference is missing")
    # casual held-out-test tuning/comparison implied by the candidate's own text
    ctext = " ".join(str(candidate.get(f) or "") for f in ("hypothesis", "target_gap", "our_rationale",
                     "current_evidence_summary"))
    ctext += " " + " ".join(str(x) for x in (candidate.get("other_risks") or []))
    ctext += " " + " ".join(str((r or {}).get("note") or "") for r in (candidate.get("current_evidence_refs") or []))
    hit = _affirmative_hit(ctext, CASUAL_TEST_TUNING_TRIGGERS)
    if hit:
        blk(f"candidate text implies casual held-out-test tuning/comparison ({hit!r})")
    # required frozen protocol absent or invalid where test access is required
    if split in ("existing_frozen_protocol_only", "requires_new_frozen_protocol"):
        if split == "existing_frozen_protocol_only" and fpr not in idx["protocol_ids"]:
            blk("existing_frozen_protocol_only but frozen_protocol_requirement is absent/invalid")
        if split == "requires_new_frozen_protocol" and fpr != "new_protocol_required":
            blk("requires_new_frozen_protocol but frozen_protocol_requirement is not 'new_protocol_required'")
    # candidate attempts to authorize execution or a test read
    ahit = _affirmative_hit(ctext + " " + " ".join(str(x) for x in (candidate.get("claim_boundaries") or [])),
                            EXECUTION_AUTH_TRIGGERS)
    if ahit:
        blk(f"candidate attempts to authorize execution or a test read ({ahit!r})")

    # -------- cap at REVIEW
    lit = candidate.get("literature_support") or []
    best = max((RELATIONSHIP_STRENGTH.get(x.get("relationship"), -1) for x in lit), default=-1)
    if lit and best <= RELATIONSHIP_STRENGTH["indirect"]:
        review.append("literature support is only indirect/background/not_established")
    if candidate.get("literature_gap_ids"):
        review.append(f"a literature gap applies: {', '.join(candidate['literature_gap_ids'])}")
    if strength in ("literature_only", "literature_gap"):
        review.append(f"evidence_strength is {strength}")
    if material["status"] == "stated_unverified":
        review.append("prior negative evidence exists and the material difference is stated_unverified "
                      "(human scientific review required)")
    if split == "requires_new_frozen_protocol":
        review.append("allowed_split is requires_new_frozen_protocol (protocol-freeze gate required)")
    if risk in ("requires_review", "blocked_without_protocol"):
        review.append(f"test_read_risk is {risk}")
    if readiness == "available_not_evaluated":
        review.append("dataset_readiness is available_not_evaluated")
    if candidate.get("prior_negative_evidence_refs"):
        review.append("prior local negative evidence exists")
    if strength == "local_negative_evidence":
        review.append("evidence_strength is local_negative_evidence")

    # -------- verdict (precedence: NO-GO > REVIEW > GO)
    if no_go:
        verdict = "NO-GO"
        reasons = no_go + review
    elif review:
        verdict = "REVIEW"
        reasons = review
    else:
        verdict = "GO"
        reasons = [f"all GO conditions satisfied — {GO_WORDING}"]
    return verdict, verdict_dedup(reasons), sorted(set(blockers))


def verdict_dedup(reasons):
    seen, out = set(), []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ------------------------------------------------------------------------- required human actions
def required_human_actions(candidate, verdict, material, blockers):
    acts = []
    if verdict == "GO":
        acts.append(f"{GO_WORDING} Not approved to run, queue, read test data, or use a frozen protocol.")
    if verdict == "REVIEW":
        acts.append("Human planning review required before this direction is considered further "
                    "(not approved to run).")
    if verdict == "NO-GO":
        acts.append("Not actionable as a model experiment in its current form.")
    if material["status"] == "stated_unverified":
        acts.append("Human scientific review: judge whether the STATED material difference vs "
                    f"{', '.join(material['basis_refs'])} is scientifically sufficient (checker does not certify it).")
    if material["status"] == "missing":
        acts.append("State a materially different hypothesis vs the prior negative evidence, or drop this direction.")
    if candidate.get("literature_gap_ids"):
        acts.append(f"Close the literature gap(s) {', '.join(candidate['literature_gap_ids'])} "
                    "(future D4a-2 external verification) or accept the recorded limitation.")
    if candidate.get("dataset_readiness") in ("unavailable", "aspirational_only"):
        acts.append("Acquire the required dataset before this direction can become actionable.")
    if candidate.get("allowed_split") == "requires_new_frozen_protocol":
        acts.append("Any test involvement requires a separate, human-run protocol-freeze (AUT-PF) step.")
    return acts


# --------------------------------------------------------------------------------- summaries
def _short_pointer_summaries(candidate):
    lit = candidate.get("literature_support") or []
    if lit:
        best = max((RELATIONSHIP_STRENGTH.get(x.get("relationship"), -1) for x in lit), default=-1)
        best_lbl = {3: "direct", 2: "indirect", 1: "background", 0: "not_established"}.get(best, "none")
        ptrs = ", ".join(f"{x.get('paper_id')}({x.get('relationship')})" for x in lit)
        lit_sum = f"{len(lit)} paper(s), best relationship {best_lbl}: {ptrs}"
    else:
        lit_sum = "no literature support cited"
    if candidate.get("literature_gap_ids"):
        lit_sum += f"; gaps: {', '.join(candidate['literature_gap_ids'])}"

    cur = candidate.get("current_evidence_refs") or []
    cur_sum = ("; ".join(f"{r.get('identity')}({r.get('relationship')})" for r in cur)
               if cur else "no current-evidence references")
    neg = candidate.get("prior_negative_evidence_refs") or []
    neg_sum = ("; ".join(f"{r.get('identity')}({r.get('relationship')})" for r in neg)
               if neg else "no prior negative evidence")
    return lit_sum, cur_sum, neg_sum


def _target_gap_pointer(candidate):
    gaps = candidate.get("literature_gap_ids") or []
    dirs = candidate.get("direction_tags") or []
    if gaps:
        return f"gap {', '.join(gaps)} (direction: {', '.join(dirs)})"
    return f"direction: {', '.join(dirs)} (see candidate target_gap in experiment_candidates.yaml)"


# ------------------------------------------------------------------------------- entry building
def build_entry(candidate, idx, base):
    unresolved = resolve_references(candidate, idx, base)
    dims = derive_dimensions(candidate)
    material = dims.pop("_material")
    verdict, reasons, blockers = derive_verdict(candidate, idx, unresolved, material)
    lit_sum, cur_sum, neg_sum = _short_pointer_summaries(candidate)
    return {
        "candidate_id": candidate.get("candidate_id"),
        "rank": None,  # assigned after ranking
        "target_gap": _target_gap_pointer(candidate),
        "direction_tags": list(candidate.get("direction_tags") or []),
        "scientific_promise": dims["scientific_promise"],
        "practical_readiness": dims["practical_readiness"],
        "data_readiness": dims["data_readiness"],
        "split_safety": dims["split_safety"],
        "literature_support_summary": lit_sum,
        "current_evidence_summary": cur_sum,
        "prior_negative_evidence_summary": neg_sum,
        "dataset_readiness": candidate.get("dataset_readiness"),
        "allowed_split": candidate.get("allowed_split"),
        "test_read_risk": candidate.get("test_read_risk"),
        "frozen_protocol_requirement": candidate.get("frozen_protocol_requirement"),
        "blockers": blockers,
        "material_difference_requirement": material,
        "derived_verdict": verdict,
        "verdict_reasons": reasons,
        "required_human_actions": required_human_actions(candidate, verdict, material, blockers),
        "claim_boundaries": list(candidate.get("claim_boundaries") or []),
    }


def _rank_key(entry, candidate_by_id):
    c = candidate_by_id[entry["candidate_id"]]
    return (
        VERDICT_ORDER.get(entry["derived_verdict"], 9),
        DATA_READINESS_ORDER.get(c.get("dataset_readiness"), 9),
        ALLOWED_SPLIT_ORDER.get(c.get("allowed_split"), 9),
        EVIDENCE_STRENGTH_ORDER.get(c.get("evidence_strength"), 9),
        entry["candidate_id"],
    )


def build_review(sources, existing=None):
    idx = _index(sources)
    base = sources["base"]
    candidate_by_id = {c.get("candidate_id"): c for c in idx["candidates"]}
    entries = [build_entry(c, idx, base) for c in idx["candidates"]]
    entries.sort(key=lambda e: _rank_key(e, candidate_by_id))
    for i, e in enumerate(entries, start=1):
        e["rank"] = i

    fingerprint = compute_fingerprint(sources)
    go = sum(1 for e in entries if e["derived_verdict"] == "GO")
    rev = sum(1 for e in entries if e["derived_verdict"] == "REVIEW")
    nogo = sum(1 for e in entries if e["derived_verdict"] == "NO-GO")
    unresolved_count = sum(1 for e in entries for b in e["blockers"] if b.startswith("unresolved/stale reference"))

    # idempotency: preserve review_id/generated_at when the fingerprint is unchanged
    if existing and existing.get("source_fingerprint") == fingerprint:
        review_id = existing.get("review_id")
        generated_at = existing.get("generated_at")
    else:
        generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        review_id = f"review_{generated_at}"

    return {
        "schema_version": SCHEMA_VERSION,
        "review_id": review_id,
        "generated_at": generated_at,
        "source_fingerprint": fingerprint,
        "policy_version": POLICY_VERSION,
        "impl_version": IMPL_VERSION,
        "authoritative_sources": source_hashes(sources),
        "candidate_count": len(entries),
        "ranking_policy": RANKING_POLICY,
        "entries": entries,
        "summary": {
            "go_count": go,
            "review_count": rev,
            "no_go_count": nogo,
            "unresolved_reference_count": unresolved_count,
        },
        "notice": ("GO means 'Suitable for human planning review only.' No verdict authorizes running an "
                   "experiment, entering the experiment queue, reading held-out test data, or using a "
                   "frozen protocol. This file is generated; edit the source registries, not this file."),
    }


def dump_yaml(doc):
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, allow_unicode=True, width=100)


def write_review(base=REPO):
    sources = load_sources(base)
    review_path = base / "automation" / "reviews" / "next_experiment_review.yaml"
    existing = None
    if review_path.exists():
        try:
            existing = yaml.safe_load(review_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            existing = None
    doc = build_review(sources, existing=existing)
    text = dump_yaml(doc)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    changed = (not review_path.exists()) or (review_path.read_text(encoding="utf-8") != text)
    if changed:
        review_path.write_text(text, encoding="utf-8")
    return doc, changed


def main(argv):
    ap = argparse.ArgumentParser(description="Next Experiment Brainstorm Checker (read-only planning review).")
    ap.add_argument("--check", action="store_true",
                    help="build the review in memory and report the verdict summary; do NOT write")
    args = ap.parse_args(argv)
    if args.check:
        sources = load_sources(REPO)
        existing = None
        if REVIEW_PATH.exists():
            existing = yaml.safe_load(REVIEW_PATH.read_text(encoding="utf-8")) or {}
        doc = build_review(sources, existing=existing)
        s = doc["summary"]
        print(f"[checker] candidates={doc['candidate_count']} GO={s['go_count']} REVIEW={s['review_count']} "
              f"NO-GO={s['no_go_count']} unresolved_refs={s['unresolved_reference_count']}")
        for e in doc["entries"]:
            print(f"  #{e['rank']} {e['candidate_id']} -> {e['derived_verdict']}")
        print(f"[checker] source_fingerprint={doc['source_fingerprint']}")
        return 0
    doc, changed = write_review(REPO)
    s = doc["summary"]
    print(f"[checker] wrote {REVIEW_PATH.relative_to(REPO)} (changed={changed}); "
          f"GO={s['go_count']} REVIEW={s['review_count']} NO-GO={s['no_go_count']} "
          f"unresolved_refs={s['unresolved_reference_count']}; fingerprint={doc['source_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
