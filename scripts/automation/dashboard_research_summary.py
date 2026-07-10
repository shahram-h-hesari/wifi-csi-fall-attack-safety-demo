#!/usr/bin/env python
"""D3 — Markdown research-evidence rendering for RESEARCH_DASHBOARD.md.

Renders a single generated section (BEGIN/END AUTO:RESEARCH-EVIDENCE markers) covering verified
scientific evidence, canonical experiment identity, goal/dataset readiness, and safety warnings.

Architectural authority rule (do not violate): this module is a VIEW, never a second ledger.
  - scientific metrics + provenance          -> scripts/automation/result_explorer.py (run_query)
  - canonical evaluation identity            -> the experiment_identity block Result Explorer
                                                 attaches to a curated row (never re-matched here)
  - which reference keys to render           -> automation/registry/reference_evidence.yaml,
                                                 read ONLY for (key, goal) routing pairs — never
                                                 for metrics, thresholds, or aliases
  - goal/dataset readiness                   -> automation/registry/goals.yaml,
                                                 automation/registry/datasets.yaml (their own
                                                 `status` / capability fields, read verbatim)
  - target comparator rules (F20/R90F10)     -> parsed from goals.yaml success_targets[*].rule
                                                 text, never a silently-changed operator/threshold

This module must never hardcode a TP/FN/FP/TN, Rfall, FAR, threshold, canonical evaluation ID,
canonical display name, or alias value as a data constant — every one of those is read at render
time from Result Explorer's own return value or a registry's own field. See
scripts/automation/test_dashboard_research_summary.py::test_d3_13_* for the static proof.

Deterministic and idempotent: identical sources -> byte-identical output. Read-only: never writes
outside the caller-supplied return string; never runs a subprocess; never touches results/,
checkpoints/, or a --split command.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import result_explorer  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

BEGIN_MARK = "<!-- BEGIN AUTO:RESEARCH-EVIDENCE -->"
END_MARK = "<!-- END AUTO:RESEARCH-EVIDENCE -->"

# Registry `status` enum -> readiness phrase. Generic vocabulary translation, not a per-goal fact:
# every current/future goal's `status` field (goals.yaml) is one of these four values.
STATUS_LABELS = {
    "ACTIVE_THESIS_PRIMARY": "supported and evaluated",
    "DATA_AVAILABLE_NOT_EVALUATED": "dataset-supported but not yet evaluated",
    "NO_DATA": "data needed — no supporting dataset locally",
    "NO_DATA_ASPIRATIONAL": "data needed / aspirational — no current longitudinal support",
}

# Glossary prose for terms Result Explorer's WARN_TEXT does not itself carry (frozen-test is a
# "good" evidence level and never appears in a warning; identity/provenance states are dashboard-
# level concepts). Descriptive text only — not a scientific value.
LEGEND_EXTRA = {
    "frozen-test": "a one-shot, protocol-gated held-out test read — the strongest evidence level this repo produces",
    "provenance_mismatch": "a curated reference entry's provenance path disagreed with (or was missing from) the artifact manifest — metrics withheld entirely",
    "identity_unavailable": "no canonical identity mapping could be resolved for this result — the scientific evidence stands on its own; no canonical ID/display name is shown",
    "identity_mismatch": "a canonical identity mapping exists but conflicts with (or is ambiguous against) the scientific result — the scientific evidence stands on its own; no canonical ID/display name is shown",
    "research-only": "descriptive / internal finding — not a clinical, deployment, or certified claim",
}


# ---------------------------------------------------------------------------- read-only loading
def _load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _curated_reference_keys(sources):
    """Read ONLY the ordered (key, goal) routing pairs from the curated reference-evidence
    registry — never metrics, thresholds, or aliases. Result Explorer resolves everything else."""
    path = sources.get("reference_evidence_yaml")
    if not path or not Path(path).exists():
        return []
    doc = _load_yaml(path)
    return [(e.get("key"), e.get("goal")) for e in (doc.get("reference_results") or []) if e.get("key")]


# ---------------------------------------------------------------------------- target comparators
_OP_FN = {
    ">": lambda v, t: v > t,
    ">=": lambda v, t: v >= t,
    "<": lambda v, t: v < t,
    "<=": lambda v, t: v <= t,
}
_RULE_RE = re.compile(r"(Rfall|FAR)\s*(>=|<=|>|<)\s*([\d.]+)")


def _parse_rule(rule_text):
    """Extract (metric, operator, threshold) triples from a goals.yaml success_targets rule
    string, in the order they appear. Operators/thresholds are never hardcoded elsewhere —
    changing the registry's rule text changes this module's behavior automatically."""
    return [(m.group(1), m.group(2), float(m.group(3))) for m in _RULE_RE.finditer(rule_text or "")]


def _at_boundary(value, op, threshold, tol=1e-9):
    # Only an inclusive comparator (>=, <=) can be exactly "at" its own passing threshold; a
    # strict comparator (>, <) that lands exactly on the threshold has FAILED, not boundary-passed.
    return op in (">=", "<=") and abs(value - threshold) <= tol


def assess_target(target_id, rule_text, metrics, evidence_level, epsilon):
    """Evaluate one goals.yaml success_targets rule against a Result-Explorer-returned metrics
    dict. Returns {target_id, status, boundary, text, checks}. `text` is the human-readable,
    evidence-qualified assessment string; never a bare pass/fail badge."""
    components = _parse_rule(rule_text)
    if not components:
        return {"target_id": target_id, "status": "unavailable",
                "text": f"{target_id}: no parseable comparator rule", "checks": []}
    checks = []
    for metric_name, op, threshold in components:
        value = metrics.get(metric_name)
        if value is None:
            return {"target_id": target_id, "status": "unavailable",
                    "text": f"{target_id}: metric {metric_name} not present in this result",
                    "checks": []}
        ok = _OP_FN[op](value, threshold)
        checks.append({"metric": metric_name, "op": op, "threshold": threshold, "value": value,
                        "ok": ok, "boundary": _at_boundary(value, op, threshold)})
    all_ok = all(c["ok"] for c in checks)
    if all_ok:
        boundary = any(c["boundary"] for c in checks)
        label = f"{target_id} boundary" if boundary else f"{target_id} reached"
        text = f"{label}, {evidence_level}"
    else:
        parts = []
        for c in checks:
            comp_label = (f"R{int(round(c['threshold'] * 100))} recall"
                          if c["metric"] == "Rfall" else c["metric"])
            parts.append(f"{comp_label} component {'reached' if c['ok'] else 'not reached'}")
        eps_txt = f"; {evidence_level} at ε={epsilon}" if epsilon is not None else f"; {evidence_level}"
        text = ", ".join(parts) + eps_txt
    return {"target_id": target_id, "status": "reached" if all_ok else "not_reached",
            "boundary": all_ok and any(c["boundary"] for c in checks), "text": text, "checks": checks}


# ---------------------------------------------------------------------------- section B: per-entry rendering
def _fmt_alias_line(alias):
    val = alias.get("value")
    status = alias.get("meaning_status") or "unknown"
    meaning = alias.get("meaning")
    line = f"  - `{val}` — {status}"
    line += f": {meaning}" if meaning else " (expansion unverified)"
    note = (alias.get("note") or "").strip().splitlines()
    if note:
        line += f" _( {note[0]} )_"
    return line


def _render_matched_row(row, ei):
    lines = [f"### {ei.get('display_name') or ei.get('evaluation_id')}", ""]
    lines.append(f"- Canonical evaluation: `{ei.get('evaluation_id')}`")
    if ei.get("run_id"):
        run_bit = f" — {ei['run_display_name']}" if ei.get("run_display_name") else ""
        lines.append(f"- Canonical run: `{ei['run_id']}`{run_bit}")
    aliases = ei.get("legacy_aliases") or []
    if aliases:
        lines.append("- Legacy aliases:")
        for a in aliases:
            lines.append(_fmt_alias_line(a))
    lines.append("")
    lines.append(f"Goal `{row.get('goal')}` · dataset `{row.get('dataset')}` · attack `{row.get('attack')}` · "
                 f"epsilon `{row.get('epsilon')}` · split `{row.get('split')}` · evidence `{row.get('evidence_level')}`")
    m = row.get("metrics") or {}
    lines.append("")
    lines.append(f"Metrics: TP {m.get('TP')} / FN {m.get('FN')} / FP {m.get('FP')} / TN {m.get('TN')} "
                 f"· Rfall {m.get('Rfall')} · FAR {m.get('FAR')} · threshold {row.get('threshold')}")
    prov = row.get("provenance") or {}
    lines.append(f"Manifest cross-check: `{prov.get('manifest_cross_check', '?')}`" +
                 (f" · source `{row['source_file']}`" if row.get("source_file") else ""))
    wb = row.get("warning_band") or []
    if wb:
        lines.append("")
        lines.append("Warnings:")
        for w in wb:
            lines.append(f"- {w}")
    return "\n".join(lines)


def _render_scientific_block(row):
    m = row.get("metrics") or {}
    lines = [
        f"Goal `{row.get('goal')}` · dataset `{row.get('dataset')}` · attack `{row.get('attack')}` · "
        f"epsilon `{row.get('epsilon')}` · split `{row.get('split')}` · evidence `{row.get('evidence_level')}`",
        "",
        f"Metrics: TP {m.get('TP')} / FN {m.get('FN')} / FP {m.get('FP')} / TN {m.get('TN')} "
        f"· Rfall {m.get('Rfall')} · FAR {m.get('FAR')} · threshold {row.get('threshold')}",
    ]
    wb = row.get("warning_band") or []
    if wb:
        lines.append("")
        lines.append("Warnings:")
        for w in wb:
            lines.append(f"- {w}")
    return "\n".join(lines)


def _render_unavailable_row(key, row, ei):
    lines = [f"### {key}", ""]
    lines.append(f"**Identity unavailable:** {ei.get('reason')}")
    lines.append("")
    lines.append(_render_scientific_block(row))
    return "\n".join(lines)


def _render_mismatch_row(key, row, ei):
    lines = [f"### {key}", ""]
    lines.append(f"**Identity mismatch — canonical identity suppressed:** {ei.get('reason')}")
    lines.append("")
    lines.append(_render_scientific_block(row))
    return "\n".join(lines)


def _render_scientific_only(key, row):
    lines = [f"### {key}", ""]
    lines.append(_render_scientific_block(row))
    return "\n".join(lines)


def _render_reference_entry(key, result):
    status = result.get("status")
    if status == "refused":
        return (f"### {key} — REFUSED\n\n"
                f"**{result.get('state_id')}:** {result.get('message')}")
    if status != "ok" or not result.get("rows"):
        return f"### {key} — no result\n\n{result.get('message')}"
    row = result["rows"][0]
    ei = row.get("experiment_identity")
    if ei is None:
        return _render_scientific_only(key, row)
    state = ei.get("state")
    if state == "matched":
        return _render_matched_row(row, ei)
    if state == "unavailable":
        return _render_unavailable_row(key, row, ei)
    if state == "mismatch":
        return _render_mismatch_row(key, row, ei)
    return _render_scientific_only(key, row)


def _resolve_reference_results(sources):
    """Run every curated reference key through Result Explorer exactly once. Returns an ordered
    list of (key, goal, result) so the snapshot/evaluations/target sections stay consistent within
    a single render pass (never re-queried per section, never cached across renders)."""
    out = []
    for key, gid in _curated_reference_keys(sources):
        result = result_explorer.run_query({"goal": gid, "reference_evidence_query": key}, sources)
        out.append((key, gid, result))
    return out


# ---------------------------------------------------------------------------- section A
def render_snapshot(resolved, goals_doc):
    out = ["### A. Research Evidence Snapshot", ""]
    goal = next((g for g in goals_doc.get("goals", []) if g.get("status") == "ACTIVE_THESIS_PRIMARY"), None)
    if goal is None:
        out.append("_(no active primary goal registered)_")
        return "\n".join(out) + "\n"
    out.append(f"- **Active primary goal:** `{goal['id']}` — {goal.get('display_name')}")
    out.append(f"- **Datasets:** {', '.join(goal.get('datasets_available') or []) or 'none'}")
    targets = goal.get("success_targets") or {}
    if "F20" in targets:
        out.append(f"- **Proposal target (F20):** {targets['F20'].get('rule')}")
    if "R90F10" in targets:
        out.append(f"- **Aspirational final target (R90F10):** {targets['R90F10'].get('rule')}")
    out.append("")
    out.append("**Current honest state:**")
    goals_by_id = {g["id"]: g for g in goals_doc.get("goals", [])}
    any_line = False
    for key, gid, result in resolved:
        if result.get("status") != "ok" or not result.get("rows"):
            continue
        row = result["rows"][0]
        gdef = goals_by_id.get(gid) or {}
        tdefs = gdef.get("success_targets") or {}
        for tid in ("F20", "R90F10"):
            tdef = tdefs.get(tid)
            if not tdef:
                continue
            a = assess_target(tid, tdef.get("rule"), row.get("metrics") or {},
                               row.get("evidence_level"), row.get("epsilon"))
            out.append(f"- `{key}` — {a['text']}")
            any_line = True
    if not any_line:
        out.append("- _(no target-comparable evidence resolved)_")
    out.append("- No clinical or deployment claim is made by this dashboard.")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------- section B
def render_reference_evaluations(resolved):
    out = ["### B. Canonical Reference Evaluations", ""]
    if not resolved:
        out.append("_(no curated reference-evidence entries registered)_")
        return "\n".join(out) + "\n"
    for key, _gid, result in resolved:
        out.append(_render_reference_entry(key, result))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------- section C
def render_target_assessment(resolved, goals_doc):
    out = ["### C. Target Assessment", ""]
    if not resolved:
        out.append("_(no curated reference-evidence entries registered)_")
        return "\n".join(out) + "\n"
    goals_by_id = {g["id"]: g for g in goals_doc.get("goals", [])}
    out.append("| Reference | Target | Status |\n|---|---|---|")
    any_row = False
    for key, gid, result in resolved:
        if result.get("status") != "ok" or not result.get("rows"):
            out.append(f"| `{key}` | — | no scientific result "
                       f"({result.get('state_id') or result.get('status')}) |")
            any_row = True
            continue
        row = result["rows"][0]
        targets = (goals_by_id.get(gid) or {}).get("success_targets") or {}
        for target_id in ("F20", "R90F10"):
            tdef = targets.get(target_id)
            if not tdef:
                continue
            a = assess_target(target_id, tdef.get("rule"), row.get("metrics") or {},
                               row.get("evidence_level"), row.get("epsilon"))
            out.append(f"| `{key}` | {target_id} | {a['text']} |")
            any_row = True
    if not any_row:
        out.append("| _(none)_ | — | — |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------- section D
def render_readiness(goals_doc, datasets_doc):
    out = ["### D. Goal and Dataset Readiness", ""]
    ds_names = {d.get("id"): d.get("name") or d.get("id") for d in (datasets_doc.get("datasets") or [])}
    out.append("| Goal | Readiness |\n|---|---|")
    for g in goals_doc.get("goals", []):
        label = STATUS_LABELS.get(g.get("status"), g.get("status") or "unknown")
        ds = ", ".join(ds_names.get(d, d) for d in (g.get("datasets_available") or []))
        needs = ", ".join(g.get("data_needs") or [])
        detail = label
        if ds:
            detail += f" (dataset: {ds})"
        elif needs:
            detail += f" — needs: {needs}"
        out.append(f"| `{g['id']}` | {detail} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------- section E
def render_legend():
    out = ["### E. Safety and Evidence Legend", ""]
    for level in ("validation-only", "test-post-hoc", "diagnostic-internal"):
        out.append(f"- **{level}** — {result_explorer.WARN_TEXT[level]}")
    out.append(f"- **frozen-test** — {LEGEND_EXTRA['frozen-test']}")
    out.append(f"- **provenance mismatch** — {LEGEND_EXTRA['provenance_mismatch']}")
    out.append(f"- **identity unavailable** — {LEGEND_EXTRA['identity_unavailable']}")
    out.append(f"- **identity mismatch** — {LEGEND_EXTRA['identity_mismatch']}")
    out.append(f"- **not R90F10** — {result_explorer.WARN_TEXT['not_r90f10']}")
    out.append(f"- **research-only / not clinical evidence** — {LEGEND_EXTRA['research-only']}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------- top-level entry point
def render_research_evidence(sources):
    """Build the whole generated section (deterministic, idempotent for identical sources)."""
    goals_doc = _load_yaml(sources["goals_yaml"])
    datasets_doc = _load_yaml(sources["datasets_yaml"])
    resolved = _resolve_reference_results(sources)
    parts = [
        "## 2. Research Evidence & Canonical Identity\n",
        render_snapshot(resolved, goals_doc),
        render_reference_evaluations(resolved),
        render_target_assessment(resolved, goals_doc),
        render_readiness(goals_doc, datasets_doc),
        render_legend(),
    ]
    body = "\n\n".join(p.strip() for p in parts if p.strip())
    return f"{BEGIN_MARK}\n\n{body}\n\n{END_MARK}\n"
