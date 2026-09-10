#!/usr/bin/env python
"""Dashboard val-pilot-gate rendering (design VAL_PILOT_GATE_DESIGN.md §7/§10 step 4) for
RESEARCH_DASHBOARD.md.

Renders a single generated section (BEGIN/END AUTO:VAL-PILOT-GATE markers) that DISPLAYS whatever
pilot receipts already exist in automation/val_pilot_receipts/ (written only by
val_pilot_scan.py --write-receipts, one per VERIFIED pilot — see design §7).

Architectural authority rule (do not violate), same as dashboard_candidate_review.py: this module
is a VIEW, never a verdict engine. val_pilot_gate_lib.py owns pilot verification and gate-verdict
computation; val_pilot_scan.py owns deciding which pilots are VERIFIED and writing their receipts.
This module only reads already-written receipt JSON files and displays their already-computed
fields. It never re-verifies a pilot, never recomputes a gate_verdict, never walks results/, and
never runs a subprocess or a --split command.

CLAIMED / VERIFIED / ACCEPTED (design §7):
  - A pilot receipt existing in automation/val_pilot_receipts/ IS the VERIFIED state — the scanner
    only ever writes one after its own read-only verification already found the pilot complete
    (§2/§3). There is no separate on-disk CLAIMED state for these receipts to display.
  - ACCEPTED is the receipt's own `acceptance` field being non-null. As of this module's creation
    (design §10 step 4) nothing yet WRITES that field -- promoting a pilot receipt to ACCEPTED is
    deliberately left as separate, later, explicitly-approved work (the same "each step gated on
    user approval" discipline as the rest of this design). Today every receipt therefore renders
    as VERIFIED; the ACCEPTED column exists so it activates automatically once that mechanism is
    built, with no renderer change required.

Deterministic and idempotent: identical receipt files -> byte-identical output (aside from the
"scanned N receipts" count, which is just len(receipts)). Read-only.
"""
from __future__ import annotations

import json
from pathlib import Path

BEGIN_MARK = "<!-- BEGIN AUTO:VAL-PILOT-GATE -->"
END_MARK = "<!-- END AUTO:VAL-PILOT-GATE -->"

REQUIRED_RECEIPT_FIELDS = (
    "receipt_version", "run_name", "seed", "epsilon", "split", "metrics", "gate_verdict",
)


# ---------------------------------------------------------------------------- read-only loading
def _load_receipts(sources):
    """Read-only load of every pilot receipt under val_pilot_receipts_dir. Returns
    (receipts, warnings) -- a malformed individual file is skipped and named in `warnings`, it
    never aborts the whole section (unlike the single-source candidate-review renderer, this is a
    directory of independently-written files: one bad file should never hide all the good ones)."""
    dir_path = sources.get("val_pilot_receipts_dir")
    if not dir_path:
        return [], ["no val_pilot_receipts_dir source configured"]
    d = Path(dir_path)
    if not d.exists():
        return [], []  # not an error -- just means the scanner hasn't written any receipt yet

    receipts, warnings = [], []
    for p in sorted(d.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            warnings.append(f"{p.name}: unreadable/malformed JSON, skipped")
            continue
        if not isinstance(doc, dict):
            warnings.append(f"{p.name}: root is not a JSON object, skipped")
            continue
        missing = [f for f in REQUIRED_RECEIPT_FIELDS if f not in doc]
        if missing:
            warnings.append(f"{p.name}: missing required field(s) {missing}, skipped")
            continue
        doc["_file"] = p.name
        receipts.append(doc)
    return receipts, warnings


# ---------------------------------------------------------------------------- rendering
def render_val_pilot_gate(sources):
    """Build the whole generated section. Displays already-written pilot receipts verbatim; never
    recomputes a verdict or a provenance decision."""
    out = ["## 7b. Validation-pilot gate — CLAIMED / VERIFIED / ACCEPTED pilots", ""]
    receipts, warnings = _load_receipts(sources)

    for w in warnings:
        out.append(f"⚠️ {w}")
    if warnings:
        out.append("")

    if not receipts:
        out.append(
            "No pilot receipts yet — `automation/val_pilot_receipts/` is empty or does not exist. "
            "A receipt appears here only after `val_pilot_scan.py --write-receipts` finds a pilot "
            "that is complete under design §2/§3 (metadata JSON present, checkpoint hash-bindable, "
            "core metrics available). Run the scanner to see why any given axis isn't there yet."
        )
        out.append("")
        out.append(
            "> ⚠️ A receipt here is evidence a validation pilot is complete and its metrics are "
            "computed — it is never authorization for a frozen test read (design §9)."
        )
        body = "\n".join(out)
        return f"{BEGIN_MARK}\n\n{body}\n\n{END_MARK}\n"

    accepted = [r for r in receipts if r.get("acceptance")]
    verified_only = [r for r in receipts if not r.get("acceptance")]
    out.append(
        f"**{len(receipts)}** pilot receipt(s) on file — **{len(verified_only)}** VERIFIED, "
        f"**{len(accepted)}** ACCEPTED."
    )
    out.append("")
    out.append(
        "> ⚠️ No verdict below authorizes a frozen test read. STRONG-GO is a proposal, never an "
        "authorization (design §5.2, §9); only ACCEPTED + STRONG-GO pilots would ever be cited in "
        "a future test-protocol proposal, and even that requires a separate protocol-freeze step."
    )
    out.append("")

    # Validation-read count per candidate (run_name) -- visibility against val-split overfitting,
    # the quieter cousin of test-split leakage (design §7).
    by_run = {}
    for r in receipts:
        by_run.setdefault(r["run_name"], []).append(r)
    out.append("**Validation-read count per candidate:**")
    out.append("")
    for run_name in sorted(by_run):
        out.append(f"- `{run_name}`: {len(by_run[run_name])} recorded validation read(s)")
    out.append("")

    out.append(
        "| Candidate | Seed | ε | Status | Verdict | AUROC | recall@FAR10 | recall@FAR20 | "
        "Clean-degrade (pp) |\n|---|---|---|---|---|---|---|---|---|"
    )
    for r in sorted(receipts, key=lambda r: (r["run_name"], r["seed"], r["epsilon"])):
        m = r.get("metrics") or {}
        status = "🟢 ACCEPTED" if r.get("acceptance") else "🟡 VERIFIED"
        out.append(
            f"| `{r['run_name']}` | {r['seed']} | {r['epsilon']} | {status} | "
            f"{r.get('gate_verdict', '—')} | {m.get('auroc', '—')} | "
            f"{m.get('rfall_at_far_010', '—')} | {m.get('rfall_at_far_020', '—')} | "
            f"{m.get('clean_recall_degradation_pp', '—')} |"
        )

    body = "\n".join(out)
    return f"{BEGIN_MARK}\n\n{body}\n\n{END_MARK}\n"
