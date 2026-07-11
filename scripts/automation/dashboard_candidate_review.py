#!/usr/bin/env python
"""Dashboard candidate-review rendering (DASH-NEXT-EXP-REVIEW) for RESEARCH_DASHBOARD.md.

Renders a single generated section (BEGIN/END AUTO:NEXT-EXPERIMENT-REVIEW markers) that DISPLAYS
the already-accepted, already-generated Next Experiment Brainstorm review verbatim.

Architectural authority rule (do not violate): this module is a VIEW of a VIEW, never a verdict
engine. The Brainstorm Checker (scripts/automation/next_experiment_brainstorm_checker.py) owns
verdict derivation, ranking, and material-difference determination; this module never
recalculates, reinterprets, reranks, or overrides any of it. It reads
automation/reviews/next_experiment_review.yaml ONLY, and only its already-computed fields
(candidate_id, rank, derived_verdict, verdict_reasons, blockers, required_human_actions,
material_difference_requirement, summary counts, review_id, source_fingerprint). If that file is
missing, unparsable, or structurally inconsistent (duplicate/missing candidate_id, non-contiguous
ranks, summary counts that disagree with its own entries), this module renders a visible integrity
warning instead of silently omitting the section or fabricating data.

Deterministic and idempotent: identical review file -> byte-identical output. Read-only: never
writes outside the caller-supplied return string; never runs a subprocess; never touches results/,
checkpoints/, the experiment queue, or a --split command.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

BEGIN_MARK = "<!-- BEGIN AUTO:NEXT-EXPERIMENT-REVIEW -->"
END_MARK = "<!-- END AUTO:NEXT-EXPERIMENT-REVIEW -->"

VERDICT_BADGE = {"GO": "🟢 GO", "REVIEW": "🟡 REVIEW", "NO-GO": "🔴 NO-GO"}
VALID_VERDICTS = set(VERDICT_BADGE)


# ---------------------------------------------------------------------------- read-only loading
def _load_review(sources):
    """Read-only load + structural-integrity check of the already-generated review. Returns
    (doc_or_None, warning_or_None) -- never recomputes a verdict, only checks internal consistency
    of what the Brainstorm Checker already wrote."""
    path = sources.get("next_experiment_review_yaml")
    if not path:
        return None, "no next_experiment_review_yaml source configured"
    p = Path(path)
    if not p.exists():
        return None, ("automation/reviews/next_experiment_review.yaml not found — the Brainstorm "
                       "Checker has not been run")
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None, "automation/reviews/next_experiment_review.yaml is malformed/unparseable YAML"
    if not isinstance(doc, dict):
        return None, "automation/reviews/next_experiment_review.yaml root is not a mapping"

    entries = doc.get("entries")
    if not isinstance(entries, list) or not entries:
        return None, "automation/reviews/next_experiment_review.yaml has no entries"

    seen_ids = set()
    for e in entries:
        if not isinstance(e, dict):
            return None, "an entry in next_experiment_review.yaml is not a mapping"
        cid = e.get("candidate_id")
        if not cid:
            return None, "an entry in next_experiment_review.yaml has no candidate_id"
        if cid in seen_ids:
            return None, f"duplicate candidate_id in next_experiment_review.yaml: {cid!r}"
        seen_ids.add(cid)
        if e.get("rank") is None:
            return None, f"entry {cid!r} has no rank"
        if e.get("derived_verdict") not in VALID_VERDICTS:
            return None, f"entry {cid!r} has an invalid derived_verdict {e.get('derived_verdict')!r}"

    ranks = sorted(e.get("rank") for e in entries)
    if ranks != list(range(1, len(entries) + 1)):
        return None, f"next_experiment_review.yaml ranks are not contiguous 1..{len(entries)}: {ranks}"

    s = doc.get("summary") or {}
    actual = (sum(1 for e in entries if e.get("derived_verdict") == "GO"),
              sum(1 for e in entries if e.get("derived_verdict") == "REVIEW"),
              sum(1 for e in entries if e.get("derived_verdict") == "NO-GO"))
    recorded = (s.get("go_count"), s.get("review_count"), s.get("no_go_count"))
    if recorded != actual:
        return None, ("next_experiment_review.yaml summary counts "
                       f"{recorded} do not match its own entries {actual}")
    if doc.get("candidate_count") != len(entries):
        return None, (f"next_experiment_review.yaml candidate_count {doc.get('candidate_count')} "
                       f"!= its own entries length {len(entries)}")

    return doc, None


# ---------------------------------------------------------------------------- rendering
def render_candidate_review(sources):
    """Build the whole generated section (deterministic, idempotent for an identical review
    file). Displays the accepted review verbatim; never recalculates a verdict, rank, or
    material-difference status."""
    out = ["## 2b. Next-Experiment Candidate Review — Human Decision Required", ""]
    doc, warning = _load_review(sources)
    if warning:
        out.append(f"⚠️ **INTEGRITY WARNING — candidate review unavailable:** {warning}")
        out.append("")
        out.append("No candidate-review data is shown until "
                   "`scripts/automation/next_experiment_brainstorm_checker.py` has produced a "
                   "structurally valid `automation/reviews/next_experiment_review.yaml`.")
        body = "\n".join(out)
        return f"{BEGIN_MARK}\n\n{body}\n\n{END_MARK}\n"

    entries = sorted(doc["entries"], key=lambda e: e["rank"])
    s = doc.get("summary") or {}
    fp = str(doc.get("source_fingerprint") or "")
    out.append(f"**Human decision required.** Review `{doc.get('review_id')}` · "
               f"source_fingerprint `{fp[:12]}…` · {doc.get('candidate_count')} candidates.")
    out.append("")
    out.append(f"- **GO:** {s.get('go_count', 0)} · **REVIEW:** {s.get('review_count', 0)} · "
               f"**NO-GO:** {s.get('no_go_count', 0)}")
    if entries:
        top = entries[0]
        out.append(f"- **Highest-ranked planning candidate:** `{top['candidate_id']}` — "
                   f"{VERDICT_BADGE.get(top['derived_verdict'], top['derived_verdict'])}")
    out.append("")
    out.append("> ⚠️ No verdict below authorizes running an experiment, entering the experiment "
               "queue, using a frozen protocol, or accessing held-out test data. **GO means "
               "suitable for human planning review only.**")
    out.append("")
    out.append("| Rank | Candidate | Verdict | Material difference |\n|---|---|---|---|")
    for e in entries:
        md = (e.get("material_difference_requirement") or {}).get("status", "—")
        out.append(f"| {e['rank']} | `{e['candidate_id']}` | "
                   f"{VERDICT_BADGE.get(e['derived_verdict'], e['derived_verdict'])} | {md} |")
    out.append("")
    out.append("**Per-candidate reasons, blockers, and required human actions:**")
    out.append("")
    for e in entries:
        out.append(f"- **#{e['rank']} `{e['candidate_id']}`** "
                   f"({VERDICT_BADGE.get(e['derived_verdict'], e['derived_verdict'])})")
        for r in (e.get("verdict_reasons") or []):
            out.append(f"  - reason: {r}")
        for b in (e.get("blockers") or []):
            out.append(f"  - blocker: {b}")
        for a in (e.get("required_human_actions") or []):
            out.append(f"  - action: {a}")
    body = "\n".join(out)
    return f"{BEGIN_MARK}\n\n{body}\n\n{END_MARK}\n"
