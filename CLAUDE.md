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

## Standing rule — two dashboards, keep both views fresh

This repo is the experiment/evidence layer of a larger program tracked in
`C:\Users\Hesar\Documents\GitHub\research-os` (program stages 0–6; its `automation/status.json` +
`PROGRAM_STATUS.md` render a stage dashboard). Mapping: Stage 3A = this repo's candidate
registry/checker/candidate-review skill · Stage 3B = the paper-intelligence lane (research-os repo) ·
Stage 4 is BLOCKED on this repo's val-pilot-gate.

Rules:
1. When recommending the next task, consider BOTH plans: this repo's `automation/roadmap.yaml`
   AND the research-os program dashboard's current active item. Name which plan each candidate
   task comes from.
2. After completing any roadmap/skill task in this repo, refresh BOTH views in the same turn:
   run `update_dashboard.py` AND republish the CSI Sentinel agent-view artifact
   (https://claude.ai/code/artifact/0f907387-ae53-4736-a839-9e23913eba62) so the skills board
   and pickup point never go stale. A second artifact exists for the startup lane —
   Startup Architecture (https://claude.ai/code/artifact/c101de51-1b75-408d-b328-7b68889ee838):
   republish it on MILESTONES only (a card changes column: proposed→designed→built), not every
   change; its live counterpart is the auto-syncing section on the research-os HTML dashboard.
3. The program dashboard embeds a copy of this repo's weekly status; after meaningful dashboard
   changes here, remind the user it needs a resync (its render script lives in research-os).
4. Rule #2's "refresh both views" applies to research-os-repo work too, not just wifi-csi-repo
   work — a whole selector/benchmark workstream went ~15 turns unlogged (no receipt, no
   lane-note entry) because this was only being checked for wifi-csi tasks. Every task in
   EITHER repo needs a receipt + lane-note decision-log entry + both artifacts refreshed.
5. Every artifact must have a local-file source of truth Codex can read (a markdown mirror in
   the relevant repo), not just a claude.ai artifact — CSI Sentinel had none until 2026-07-17,
   making it impossible to share with Codex. Startup Architecture's lane note already served
   this role; CSI Sentinel now has `wifi-csi-fall-attack-safety-demo/CSI_SENTINEL_AGENT_VIEW.md`.
   Keep both mirrors updated alongside their artifacts.

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

## Standing rule — the Control Center artifact updates the same turn as the plan/experiment it reflects

The Research OS Control Center artifact (`f155b23f-cb75-4710-ab64-5da8b52b1931`) is the canonical
"what's the current state" surface for Goals, Plan & Tasks, Literature Evidence, Experiments,
Results, Decisions, Thesis Outputs, and Human Approval. It is static published HTML — nothing in
it updates unless I republish it — so it will silently drift stale unless refreshing it is part
of the same turn as the underlying change, not a separate follow-up task.

Trigger this rule whenever a turn does any of the following in this repo or research-os:
- Starts, plans, or approves a new experiment (candidate promoted, experiment kicked off, seed
  run launched)
- Changes an experiment's status (running → complete, complete → superseded, etc.)
- Records a new result, decision, or human-approval event
- Adds/completes/reprioritizes a roadmap or plan task
- Produces a new thesis output (chapter draft, figure, table)

Do, in the same turn:
1. Update the underlying source of truth first (roadmap.yaml, status.json, results/ files,
   decision log, receipts) — the artifact must reflect real state, never be edited ahead of it.
2. Re-open the relevant section of `research-os-control-center.html` in the scratchpad, update
   the affected card/row/detail panel with the new fact, and republish to the same URL
   (`f155b23f-cb75-4710-ab64-5da8b52b1931`) so the link never changes.
3. If the change also affects a shared fact (see the artifact-family manifest rule above), update
   `ARTIFACT_CROSS_REFERENCE_MANIFEST.md` and any sibling artifact in the same turn.
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
