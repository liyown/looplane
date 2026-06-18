# Linear Agent Team System v1

## 1. Purpose

This spec defines a generic Linear-driven local agent team. It can initialize an
empty Linear workspace, process natural-language issues without requiring users to
name repositories, read repositories before planning implementation, and tolerate
manual Linear changes, GitHub/PR automation, unfinished prior runs, and multiple
local executors. Runtime control state lives under `~/.linear-loop`; issue evidence
lives on Linear issues; long-lived experience memory lives in Linear Project docs.
This repository keeps the prompt files, operating docs, and examples. The files under
`prompts/` are the prompts users copy into their agent runtime.

The v1 default optimizes for first use: few visible statuses, few labels, independent
state loops that write their own results, and one Coordinator loop for exceptions.
Normal state progression is owned by the loop responsible for the current Linear
state.

## 2. External Practices Incorporated

The design follows patterns seen in current Linear and agent workflows:

- Linear's default workflow is simple: `Backlog > Todo > In Progress > Done >
  Canceled`, with Duplicate as a reserved status.
- Linear Triage is a special inbox for accepting, declining, or marking incoming
  issues as duplicates before they enter the team workflow.
- Linear label groups are useful but should not become a high-cardinality repository
  database for large teams.
- GitHub/PR integrations can update Linear issue state automatically, so local agents
  must reconcile instead of overwriting.
- Existing agent integrations such as Devin and Factory use Linear as the user-visible
  control plane while scoping, planning, coding, testing, and reporting progress in
  context.

References:

- https://linear.app/docs/configuring-workflows
- https://linear.app/docs/triage
- https://linear.app/docs/labels
- https://linear.app/docs/github-integration
- https://linear.app/integrations/devin
- https://linear.app/integrations/factory

## 3. Core Principles

1. **Linear is the collaboration source of truth.**
   It stores issue state, labels, project, priority, comments, decisions, acceptance
   criteria, review findings, and delivery evidence.

2. **Do not create a second database.**
   Linear issues store issue-bound facts. Linear Project docs store long-lived
   experience memory. Local Loop Space stores only runtime control state such as
   fingerprints, active runs, leases, locks, cooldowns, lesson candidates, and cache.

3. **Todo means evidence-backed.**
   A code-backed issue cannot enter Todo only from issue text. It needs a fresh
   read-only `[Discovery]` block on the Linear issue.

4. **Users do not have to declare repositories.**
   The system infers an execution target from Linear Project settings, area labels,
   issue templates, linked branches/PRs, and historical similarity. It asks for help
   only when confidence is low or conflicting.

5. **State loops own normal progression.**
   Each visible state has a loop that may scan, claim, process, and apply allowed
   transitions for issues currently in that state.

6. **Every apply is compare-and-set.**
   A state loop must echo the snapshot it claimed and re-read Linear and local state
   before applying. If state, updatedAt, fingerprint, run reservation, or relevant
   lease/lock data changed, it must not apply and should escalate to Coordinator.

7. **Coordinator handles exceptions, not routine work.**
   Coordinator owns stale-run handling, duplicate executor reconciliation, illegal or
   unknown states, human/automation drift, multi-repo coordination, and global
   invariants.

8. **Keep visible workflow small.**
   Discovery is a mandatory internal gate, not a default Linear status. Teams may opt
   into an explicit Discovery status, but the default board remains easy to understand.

## 4. Default Visible Workflow

Default Linear workflow:

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
Canceled / Duplicate
```

State meanings:

```text
Triage      Intake inbox. Accept, decline, duplicate, or ask one clarification.
Backlog     Accepted but not yet execution-ready.
Todo        Target resolved and required evidence exists.
In Progress Implementation or approved execution is active.
In Review   Work is complete and being verified.
Done        Accepted as complete.
Canceled    Explicitly not doing this issue.
Duplicate   Duplicate of another issue.
```

Allowed default transitions:

```text
Triage -> Backlog | Canceled | Duplicate
Backlog -> Todo | Canceled | Duplicate
Todo -> In Progress | Backlog
In Progress -> In Review | Todo | Backlog
In Review -> Done | In Progress | Todo | Backlog
Done -> Done
Canceled -> Canceled
Duplicate -> Duplicate
```

Optional advanced mode:

- Teams that want agent-internal discovery visible on the Linear board may add
  `Discovery` between Backlog and Todo.
- In default mode, Discovery remains an internal worker/gate and is reported through a
  structured Linear issue comment or block.

## 5. Components

### 5.1 Initial Setup Prompt

Runs once to initialize Linear and local system state before the scheduled loops start:

- Confirms the default workflow and optionally adds In Review.
- Enables or documents Triage setup.
- Creates the default label set.
- Creates operating docs and issue templates.
- Creates Linear Project agent settings, Project docs, and minimal local state
  directories.
- Creates a no-code healthcheck issue.
- Returns user-facing start instructions for schedules, service handoffs, and manual
  setup gaps.

Initial setup does not own a recurring Linear state and must not be configured as a
scheduled loop. If API/tooling cannot create statuses or Triage settings, it returns
a manual checklist instead of claiming success.

### 5.2 State Loops

State loops own normal progression for their source states:

- Scan only the Linear state they own.
- Create or reuse active run reservations for claimed issues.
- Build their own context from Linear, Linear Project settings, Project docs, and
  local state.
- Enforce their state-specific gates.
- Re-read Linear and local state before applying changes.
- Apply only allowed transitions when the observed snapshot still matches.
- Escalate CAS conflicts, illegal states, duplicate runs, and cross-loop issues to
  Coordinator.

Default state loops are Triage, Backlog, Todo, In Progress, In Review, Done,
Canceled, and Duplicate. Discovery is an internal worker by default rather than a
visible board state.

### 5.3 Coordinator Loop

Coordinator handles exceptions and global invariants:

- Reconciles stale, expired, superseded, and duplicate runs.
- Resolves CAS conflicts reported by state loops.
- Handles human state/label changes and GitHub/PR automation drift.
- Handles unknown or illegal Linear states.
- Coordinates multi-repo parent/child issue splitting.
- Decides whether stale read-only evidence can be safe-merged.
- Routes expired leases and repo/worktree conflicts through Repo Manager.
- Suppresses repeated blocked/no-op work through cooldowns.

### 5.4 Internal Discovery Worker

Discovery is an internal worker, not a default Linear state:

- Gets a read lease through Repo Manager.
- Performs read-only repo/document inspection.
- Records the minimum evidence needed for Todo on the Linear issue.
- Produces the `[Discovery]` block required before code-backed Todo.

### 5.5 Repo Manager

Repo Manager owns local Git/filesystem safety:

- Resolves repositories from Linear Project agent settings.
- Clones missing repositories only from project-declared origins.
- Fetches canonical checkouts.
- Grants read leases for Discovery.
- Creates issue-scoped worktrees for implementation.
- Grants write locks for In Progress.
- Records baseline verification results.
- Safely fails with `needs-access`.

### 5.6 Memory/Reconcile Loop

Memory/Reconcile detects drift:

- Computes fingerprints.
- Tracks active, expired, superseded, and applied runs.
- Suppresses repeated blocked/no-op work.
- Detects stale loop outputs and stale discovery reports.
- Reconciles human state/label changes.
- Reconciles GitHub/PR automation changes.

## 6. Execution Target Model

Every issue gets a v1 execution target before Todo:

```yaml
target:
  kind: unknown | no-code | parent | code
  status: unresolved | inferred | confirmed
  repo: product-a-app
  confidence: low | medium | high
  evidence:
    - source: project-default
      detail: Product A maps to product-a-app.
```

Target rules:

- `unknown`: stays in Backlog until clarified or inferred.
- `no-code`: may enter Todo without repo discovery.
- `parent`: coordinates child issues and should not enter In Progress directly.
- `code`: requires a repo slug and fresh `[Discovery]` block before Todo.

Advanced target kinds such as research, multi-repo, or external-service can be mapped
onto v1 defaults:

```text
research         -> no-code unless repo evidence is required
multi-repo       -> parent plus child issues, each child is code or no-code
external-service -> no-code with needs-access when credentials/tools are missing
```

Target resolution order:

1. Explicit `Target/*`, optional `Repo/*`, or issue metadata.
2. Linear Project default target in Agent Project Settings.
3. Area/component mapping in Agent Project Settings.
4. Issue template defaults.
5. Linked branch, PR, or commit metadata.
6. Historical similar issues as advisory evidence only.
7. Human decision recorded by Coordinator or the owning state loop.

Only low-confidence or conflicting target resolution should interrupt the user.

## 7. Labels

Use label groups for low-cardinality dimensions:

```text
Type/Bug
Type/Feature
Type/Improvement
Type/Docs
Type/Chore
Type/Spike

Area/Frontend
Area/Backend
Area/API
Area/Data
Area/Infra
Area/Docs
Area/Testing
Area/Unknown

Risk/Low
Risk/Medium
Risk/High

Size/XS
Size/S
Size/M
Size/L
Size/XL

Mode/Auto
Mode/Human
Mode/Hybrid

Target/Unknown
Target/No-Code
Target/Parent
Target/Repo
```

`Target/Repo` maps to internal `target.kind: code`. The label stays user-facing
because it tells humans that repository evidence is required.

Optional for small workspaces:

```text
Repo/<repo-slug>
```

Default control labels:

```text
needs-info
needs-repo
needs-access
needs-review
blocked
security-sensitive
multi-repo
baseline-failing
```

Advanced control labels such as `needs-env`, `needs-decision`, `needs-discovery`,
`needs-reconcile`, `stale-worker`, `discovery-stale`, `flaky-test`, `release-note`,
`ready`, and `no-code` are optional. In v1 default, those details live in local state,
Project docs, and Linear comments unless the team explicitly wants more visible board
metadata.

Label ownership:

```text
Human-owned: Type/*, Area/*, Risk/*, Size/*, Mode/*, needs-*, blocked
System-owned: baseline-failing
Shared: Target/*, Repo/*, security-sensitive, multi-repo
```

If a human removes a human-owned label, the system must not immediately re-add it.
If a gate still fails, the owning state loop writes one concise comment and uses the
smallest blocking label that already exists in the default set.

## 8. Linear Project Agent Settings

Each managed Linear Project should contain an `Agent Project Settings` section or
linked document. This is the default place for target and repository configuration.
Use a fenced YAML block so each loop can parse it consistently:

```yaml
agent:
  version: 1
  defaultTarget:
    kind: code
    repo: product-a-app
    confidence: high
  repos:
    product-a-app:
      origin: git@github.com:org/product-a.git
      defaultBranch: main
      verify:
        test: pnpm test
  componentMap:
    Area/Frontend:
      kind: code
      repo: product-a-app
      confidence: high
```

Linear Project agent settings are the source for repository origin URLs. Agents never
infer clone URLs.

Optional project settings can define component maps, branch patterns, package
managers, and verification command sets. Local worktree roots and lease durations are
local loop configuration, not Linear project data.

## 9. Discovery Report

Code-backed Todo requires a fresh `[Discovery]` block on the Linear issue. The minimum
v1 report is:

```json
{
  "issueId": "ABC-123",
  "target": {
    "kind": "code",
    "status": "confirmed",
    "repo": "product-a-app",
    "confidence": "high"
  },
  "repoHead": "abc123",
  "baseBranch": "main",
  "inspectedPaths": ["package.json", "src/modules/billing"],
  "likelyChangeAreas": ["src/modules/billing"],
  "verificationCandidates": ["pnpm test -- billing"],
  "unknowns": [],
  "createdAt": "2026-06-17T18:30:00+08:00",
  "freshness": {
    "issueFingerprint": "sha256:...",
    "projectConfigVersion": 1
  }
}
```

Optional fields such as commands run, architecture facts, dependency notes, and risk
analysis are useful, but not required for v1.

Discovery is stale when issue description, acceptance criteria, target, project
configuration version, relevant repo HEAD, or human labels changed enough to
invalidate evidence.

## 10. Memory and Concurrency Model

Default local Loop Space structure:

```text
~/.linear-loop/config.yaml
~/.linear-loop/state/issues/{issueId}.json
~/.linear-loop/state/locks/{repoSlug}.json
~/.linear-loop/state/cooldowns/{issueId}.json
~/.linear-loop/state/lesson-candidates.jsonl
~/.linear-loop/runtime-issues/{YYYY-MM}.jsonl
~/.linear-loop/repos/{repoSlug}/
~/.linear-loop/worktrees/{issueId}-{repoSlug}/
```

Issue memory example:

```json
{
  "issueId": "ABC-123",
  "lastState": "Backlog",
  "lastLoop": "backlog",
  "fingerprint": "sha256...",
  "cooldown": {
    "reason": "needs-repo",
    "nextEligibleAt": "2026-06-18T10:00:00+08:00"
  },
  "target": {
    "kind": "code",
    "status": "inferred",
    "confidence": "low"
  },
  "activeRuns": {},
  "handoffMarkers": []
}
```

Runtime issues are append-only records for system problems found while loops run. They
are not product issue requirements. Each loop appends one JSON object per line to
`~/.linear-loop/runtime-issues/YYYY-MM.jsonl` with timestamp, source, severity,
summary, detail, suggested change, and optional issue/run evidence. Coordinator or
Memory/Reconcile uses repeated records as iteration input for prompts, loop rules,
loop runtime behavior, Linear setup, or repo access.

Fingerprint inputs:

```text
issue id
issue updatedAt
state
labels
title/description hash
project id
target kind/status/repo
project configuration version
repo HEAD, if relevant
discovery report hash, if present
memory version
```

If fingerprint is unchanged and previous result was `blocked` or `no_op`, the owning
state loop does not retry until cooldown expires.

### 10.1 Run Reservation

Before processing an issue, the owning state loop creates or reuses a run reservation:

```json
{
  "runId": "run-20260617-abc123",
  "runKey": "ABC-123:backlog:sha256...",
  "issueId": "ABC-123",
  "loop": "backlog",
  "shard": null,
  "workerId": "local-agent-1",
  "fingerprint": "sha256...",
  "stateAtClaim": "Backlog",
  "status": "active",
  "startedAt": "2026-06-17T18:30:00+08:00",
  "heartbeatAt": "2026-06-17T18:35:00+08:00",
  "expiresAt": "2026-06-17T19:00:00+08:00",
  "leaseIds": []
}
```

The default idempotency key is:

```text
issueId + loopName + fingerprint
```

For code-writing work, the key also includes repo slug and worktree/branch identity.

### 10.2 Previous Loop Not Finished When Next Cycle Starts

When a scheduler cycle starts and finds an unfinished run:

```text
same runKey, active, heartbeat fresh:
  Do not start another executor. Poll or wait.

same runKey, active, heartbeat expired:
  Route to Memory/Reconcile or Coordinator. It may recommend resuming the same run,
  marking it expired, or allowing a replacement run after checking leases and
  worktree state.

different fingerprint:
  Mark the older run superseded. The owning state loop may retry from the current
  Linear snapshot. Old output can only be safe-merged if it is read-only evidence or
  a non-conflicting comment and still matches current gates.

terminal Linear state:
  Terminal state wins. Mark all active runs stale.
```

### 10.3 Multiple Executors for One Loop

Default policy is one primary executor per `issueId + loop + fingerprint`.

If two executors start anyway:

- Each executor must compare against its observed claim snapshot before writing.
- Only the first executor whose reservation and current Linear snapshot still match
  may apply changes.
- Later matching executors become no-op unless they add non-conflicting evidence.
- Any executor with a non-active run, old fingerprint, old state, or expired write
  lock is stale.

Read-only loops may use multiple executors only when the owning loop or Coordinator
creates explicit shards, for example `discovery:frontend` and `discovery:tests`.
Coordinator or the owning loop merges shard evidence into one `[Discovery]` block. In
Progress remains single-writer per repo/worktree by default.

### 10.4 Leases and Locks

- Read leases may coexist for read-only Discovery.
- Write locks are exclusive per repo/worktree and required before product files
  change.
- Expired locks are not reclaimed by workers directly. Memory/Reconcile or
  Coordinator reconciles memory, Git state, branch, and Linear state before resuming
  or replacing the worker.

## 11. v1 Claim and Apply Protocol

State loops apply their own allowed changes after fresh compare-and-set checks.
Coordinator applies only exceptional reconciliation actions.

Observed snapshots are local control state. A claim record should include the issue
id, run id, loop name, optional shard, fingerprint, Linear updatedAt, Linear state,
description/comment hash, memory version, and lease or lock id.

Handoffs are durable state. Use the place the next loop can read:

- Linear issue comments or blocks for issue-bound evidence and requests.
- Labels for human-visible blockers.
- `~/.linear-loop/state/issues/` for issue-local handoff markers.
- `~/.linear-loop/state/locks/` for leases and write locks.
- `~/.linear-loop/runtime-issues/YYYY-MM.jsonl` for system problems.

Apply process:

1. State loop claims an issue in its owned source state and records the observed
   snapshot.
2. State loop performs its own allowed work.
3. State loop re-reads Linear and local state immediately before apply.
4. State loop checks active run reservation, fingerprint, state, updatedAt, and
   relevant lease/lock status.
5. If all compare-and-set checks pass, the state loop applies allowed state, label,
   comment, GitHub, filesystem, and local state changes.
6. If any check fails, the state loop does not apply. It marks the run stale/no-op or
   records a Coordinator-facing handoff marker.
7. If a final summary is useful, the loop writes a short Markdown `Run Note` for
   humans. Later loops must not depend on that note.
8. Coordinator handles only reconciliation, safe evidence merges, stale markings,
   illegal state reroutes, and cross-loop coordination.

## 12. Human and Automation Reconciliation Matrix

```text
Human moved issue to Done/Canceled/Duplicate:
  Treat as authoritative. Mark active runs stale unless Coordinator explicitly reopens.

Human moved issue backward:
  Treat as rollback. Prefer earlier state and re-run gates.

Human moved issue forward:
  Check gates. If gates fail, keep human state visible when possible, add the smallest
  blocker label, and explain missing evidence in one comment.

Human added needs-* or blocked:
  Block forward progress and route to the loop that can resolve it.

Human removed needs-* or blocked:
  Treat as unblock signal. Re-run gates; do not blindly restore the old blocker.

Human changed target/repo labels:
  Mark current discovery/worktree assumptions stale. Re-resolve target.

Human changed description or acceptance criteria:
  Recompute fingerprint. If code-backed, require fresh Discovery if impacted.

GitHub/PR automation changed state:
  Treat as external signal. Reconcile instead of overwriting; choose the safer
  non-terminal state when evidence conflicts.
```

## 13. Gates

### Triage -> Backlog

- Issue is understandable enough to accept.
- It is not an obvious duplicate.
- It is not explicitly out of scope.
- Type label is assigned or `Type/Spike` is used.

### Backlog -> Todo

- Target is resolved.
- Acceptance criteria exist.
- Scope is bounded or split.
- No blocking `needs-*` or `blocked` label remains.
- If target is `code`, a fresh `[Discovery]` block exists.
- If target is `no-code` or `parent`, required non-repo evidence exists.

When the only missing gate is a fresh `[Discovery]` block, Backlog remains the visible
state in default mode. The Backlog worker should record a Discovery handoff marker
rather than requesting a visible Discovery state.

### Todo -> In Progress

- Execution brief cites the Linear issue `[Discovery]` block for code-backed work.
- Verification path is known or explicitly unavailable.
- Target remains valid.
- Dependencies and blockers are resolved.
- Repo Manager has granted a write lock if product files will change.
- No active In Progress run already owns the same repo/worktree.

### In Progress -> In Review

- Implementation or approved non-code execution is complete.
- Baseline and verification evidence are recorded.
- Progress comment includes summary, target, branch/worktree when applicable, and
  verification results.

### In Review -> Done

- Acceptance criteria are met.
- Diff or artifact is scoped to the issue.
- Verification evidence is credible.
- Human review is complete when required.
- Delivery links and final summary are present.

## 14. Edge Cases

### Missing Repository

Only applies after target is known to be code-backed and no repository can be resolved.
Add `needs-repo`, keep in Backlog, ask one minimal question.

### Target Conflict

If multiple repos or target kinds are plausible, add `needs-info` and present the
smallest concrete choice.

### Missing Discovery

Do not move code-backed work to Todo. Keep in Backlog, record an internal Discovery
handoff marker, and explain that Todo requires repository evidence.

### Stale Discovery

Re-run Discovery and do not let Todo rely on old evidence. In v1 this is normally a
memory/comment event, not a visible label.

### Multi-Repo Work

Default to parent issue plus child issues, one child per repo. The parent coordinates
acceptance and should not directly enter In Progress.

### Missing Access or Environment

Add `needs-access`. Store exact missing capability without secrets. Suppress repeat
attempts until cooldown or input changes.

### Baseline Already Failing

Record baseline failure before edits, add `baseline-failing`, and continue only with
focused verification or Coordinator approval.

### Long-Running Work

Use active run reservations, heartbeat, and write-lock leases. Expired leases require
Memory/Reconcile before any worker can resume.

### Duplicate Scheduler or Worker

Use the run reservation rules. Same runKey means wait or merge evidence; changed
fingerprint means supersede older runs; terminal state always wins.

### Security-Sensitive Work

Add `security-sensitive`, require `Mode/Human` or `Mode/Hybrid`, and block Done until
human review is recorded.

## 15. Prompt Set

`prompts/` is the runtime prompt layer. Initial setup is run manually once. Scheduled
state and service loops are pasted into schedules from these files.

```text
prompts/initial-setup.md
prompts/coordinator-loop.md
prompts/repo-manager.md
prompts/memory-reconcile-loop.md
prompts/triage-loop.md
prompts/backlog-loop.md
prompts/discovery-loop.md
prompts/todo-loop.md
prompts/in-progress-loop.md
prompts/in-review-loop.md
prompts/done-loop.md
prompts/canceled-loop.md
prompts/duplicate-loop.md
```

`prompts/discovery-loop.md` is an internal worker prompt by default. If advanced mode
enables a visible Discovery state, the same prompt can be attached to that state.

## 16. Completion Criteria

The v1 system is ready when:

- Empty Linear initialization is documented.
- Default visible states stay simple.
- Default labels stay small.
- Execution target resolution works without per-issue repo declarations.
- Code-backed Todo requires a fresh `[Discovery]` block on the Linear issue.
- Loops record observed run context for compare-and-set checks.
- State loops re-read Linear and local state before applying allowed transitions.
- Coordinator handles conflicts, stale runs, and exceptional routing.
- Unfinished prior runs and duplicate executors have deterministic handling.
- Manual edits and GitHub automation have deterministic reconciliation behavior.
- Examples explain the v1 default profile without requiring a machine-readable run
  result.
