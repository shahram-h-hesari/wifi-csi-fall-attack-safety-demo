## Standing rule — end every response with a next-task + model recommendation

End EVERY response with a short **Next task** block containing:
1. The single best next action (one line, concrete).
2. A recommended Claude model AND reasoning-effort level for that task, with one-line reasoning:
   - **haiku · low** — mechanical work: renames, file moves, formatting, trivial scripts, bulk data plumbing
   - **sonnet · low–medium** — routine, well-specified coding: single-file changes with clear acceptance criteria
   - **opus · medium–high** — multi-file implementation, debugging, refactors of verified automation code
   - **fable · high–max** — deep reasoning: research design, evidence audits, feasibility analysis, thesis/grant framing

Model and effort are independent knobs — recommend them separately when they diverge (e.g.,
**fable · low** for a quick claim-boundary sanity check; **sonnet · high** for a fiddly but
well-specified parser). Anything touching claim boundaries, frozen protocols, test-split policy,
or threshold selection is ALWAYS fable, regardless of how small the edit looks — the risk is
scientific, not mechanical.

## Standing rule — human review of paper records is a guided claim-by-claim walkthrough

Whenever a paper record (`paper_record_draft.md` or equivalent) needs human review before
`human_verified`, drive it as a guided walkthrough, not a "go read the file" pointer:
1. Work through `claim_provenance.important_claims` one at a time (or in small batches).
2. For each claim, show the claim text side-by-side with the actual source passage from the
   PDF/raw conversion at the cited page/section — quote the passage, don't just cite the page
   number.
3. Ask the user to approve/reject/flag each claim (use AskUserQuestion when it fits the 1-4
   question format; otherwise a clear inline table with a decision column).
4. Record the outcome per claim (approved / rejected / needs edit) rather than a single
   whole-record verdict — a record can be partially verified.
5. Surface any claim I already spot-checked and found surprising or borderline first (highest
   information value), not necessarily in file order.

## Standing rule — always hand over a Codex prompt for Codex work

Any time I recommend that a task be done in Codex (the "model: Codex (local, $0)" recommendation,
or any Next-task line naming Codex), I must also write out the actual, self-contained Codex
prompt in the same response — not just describe the task. The prompt must include: the exact
repo path, which files to read first (design docs, existing skills, schemas), the exact
CLIs/commands to run in order, the exact stop conditions (duplicates, missing data), and the
exact report-back format I need. The user pastes it directly into Codex; they should never have
to write their own Codex prompt from my description.

## Standing rule — Research OS is no longer embedded here

This repo is the experiment/evidence layer. The embedded Research OS copy has been retired;
see `RESEARCH_OS_MOVED.md`.

Rules:
1. Use `C:\Users\Hesar\Documents\GitHub\research-os` on `main` for Research OS dashboards,
   registries, receipts, acceptance contracts, roadmap state, and Research OS automation.
2. Do not recreate `automation/`, `RESEARCH_DASHBOARD.md`, dashboard-refresh skills, or
   Research OS automation scripts in this repository.
3. This repository remains authoritative for experiment code, results, figures, checkpoints,
   thesis artifacts, experiment-specific agents/skills, and the local safety hook.
4. The live test-split safeguard remains here and must stay operational:
   `.claude/settings.json` invokes `scripts/automation/test_split_guard.py`, with cases in
   `scripts/automation/test_split_guard_cases.py`.
5. If Research OS state needs to reflect an experiment-repo change, update and verify it from
   the canonical `research-os` repository; treat this repo as the external experiment/evidence
   source.

## Standing rule — the artifact family shares facts through a manifest, not memory

Four claude.ai artifacts form one cross-linked family: Research OS Control Center (the hub),
Verifiable Literature Review, CSI Sentinel, and Thesis Chapter View. (Three siblings — Research
OS Architecture, Research Intelligence Workflow, and the Combined Architecture and Operational
Workstreams Map — were consolidated into the Control Center and deleted 2026-07-20; do not
re-add rows for them.) They are static published HTML — there is no live sync between them — so
every number, URL, or term that appears in more than one is tracked in
`research-os/ARTIFACT_CROSS_REFERENCE_MANIFEST.md`.

Rules:
1. Before editing any of these four artifacts, grep the manifest for every fact you're about to
   touch (paper counts, test counts, benchmark numbers, terminology, artifact URLs).
2. The manifest's "Appears in" column is the blast radius — if a shared fact changes, edit and
   republish every artifact listed, in the same turn. Don't leave siblings stale.
3. Run the manifest's grep-based consistency checks (doubled-word typos, retired terminology,
   known-bad numbers like "50 pending", missing `target="_blank" rel="noopener noreferrer"`)
   before republishing any of the four.
4. If a genuinely new cross-artifact fact gets introduced, add it as a manifest row — don't let
   it live only in conversation memory, which is exactly how the "50 pending" bug and the
   doubled "source-source-statement-verified" typo happened.
5. A periodic full re-read of all four artifacts (not just the one being edited) catches drift
   that per-edit grepping misses — do one whenever asked, or proactively after a run of several
   consecutive edits to the same artifact family.

## Standing rule — Research OS updates happen from the canonical repo

The Research OS Control Center artifact (`f155b23f-cb75-4710-ab64-5da8b52b1931`) is still the
canonical "what's the current state" surface for Goals, Plan & Tasks, Literature Evidence,
Experiments, Results, Decisions, Thesis Outputs, and Human Approval. Its source and render
pipeline now live in `C:\Users\Hesar\Documents\GitHub\research-os`, not in this experiment
repository.

Trigger this rule whenever a turn does any of the following in this repo or research-os:
- Starts, plans, or approves a new experiment (candidate promoted, experiment kicked off, seed
  run launched)
- Changes an experiment's status (running → complete, complete → superseded, etc.)
- Records a new result, decision, or human-approval event
- Adds/completes/reprioritizes a roadmap or plan task
- Produces a new thesis output (chapter draft, figure, table)

Do, in the same turn:
1. Update the experiment artifact in this repo first when the change is experiment evidence.
2. Switch to `research-os` to update Research OS ledgers, receipts, dashboards, and artifacts.
3. If the change also affects a shared fact (see the artifact-family manifest rule above), update
   the manifest and sibling artifact sources from `research-os`.
4. If I forget and the user has to ask "does the Control Center reflect X yet?", that is a sign
   this rule was skipped — treat it as a miss, not a reasonable follow-up ask.

This does not require re-publishing on every trivial edit (a typo fix, a comment) — it applies to
state changes a user would actually check the Control Center to see.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
