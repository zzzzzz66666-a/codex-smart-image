---
name: windows-desktop-app-builder
description: Structured requirements analysis, PRD design, implementation planning, staged testing, packaging, and delivery for Windows desktop applications. Use when a user wants to design, build, modify, debug, test, package, or release a Windows app, especially when local storage, networking, pairing, background behavior, installation, updates, uninstall, compatibility, or persistent state are involved.
---

# Windows Desktop App Builder

Use this skill to move a Windows desktop application from an idea to a verifiable release while reducing late requirement changes and preventable bugs. Treat analysis, state modeling, feasibility, and acceptance criteria as engineering work, not as documentation afterthoughts.

## Non-negotiable operating rules

1. Inspect the repository and environment before proposing implementation details. Preserve existing architecture and user changes unless the user explicitly authorizes a change.
2. Before code changes, resolve ambiguity in ordinary language. Ask exactly one question per turn. Prefer questions that can invalidate architecture, data design, protocol design, permissions, or acceptance criteria.
3. Do not start coding, scaffolding, refactoring, installing dependencies, changing configuration, or creating build artifacts until the user confirms the scope and implementation direction. Read-only inspection is allowed.
4. After each answer, update the known decisions, assumptions, risks, and remaining questions. Do not ask questions whose answers are already established.
5. Treat every feature as a stateful workflow. Define states, events, transitions, failure behavior, restart behavior, cancellation behavior, and ownership before implementation.
6. Never make a test pass by deleting tests, weakening assertions, skipping a phase, hiding errors, or lowering an acceptance threshold. Fix the cause or report a real blocker.
7. Keep functional changes separate from visual-only changes. For a visual-only request, preserve names, bindings, handlers, routes, data, settings, permissions, and business logic.
8. Do not commit, push, publish, install software, or delete data unless the user requests that action. Before destructive actions, resolve exact targets and explain the impact.
9. Tag every product rule as `[CONFIRMED]`, `[PROPOSED]`, `[ASSUMPTION]`, `[OPEN]`, or `[OUT]`. Never present a proposed timeout, size limit, port, platform, security rule, performance target, or fallback as user-confirmed.
10. Separate desired targets from verified capabilities. A benchmark, compatibility claim, or packaging claim is verified only when supported by repository evidence, platform documentation, or a repeatable test result.

## Workflow and phase gates

Maintain a short visible checklist and mark only one phase as active. Do not cross a gate until its exit condition is true.

### Phase 0: Understand the request

- Restate the product goal, users, environment, constraints, success definition, and explicit non-goals in plain language.
- Identify whether the request is new construction, an additive change, a bug fix, a visual-only change, packaging, or release work.
- Inspect repository structure, existing docs, project files, build scripts, tests, runtime targets, and local modifications.
- Record facts separately from assumptions. Treat screenshots, logs, and user statements as evidence, not as complete specifications.
- Build a requirement ledger containing ID, rule, provenance, status tag, affected contracts, and confirmation date.

Gate: the user confirms the restatement and the scope of work.

### Phase 1: Close requirement gaps

Ask one question at a time, in this order of risk:

1. Which user and business outcome must work first?
2. What is the exact target OS/version/architecture, runtime prerequisite, and deployment environment?
3. What is local versus remote, online versus offline, account-free versus authenticated?
4. What are the limits: size, count, duration, throughput, concurrent users/devices, storage, and resource usage?
5. What happens on restart, crash, sleep, network change, timeout, duplicate action, partial completion, or insufficient disk space?
6. What must be confirmed by one or both operators, and who owns each decision?
7. What is the lifecycle of data: creation, update, retention, backup, restore, migration, deletion, and uninstall?
8. What compatibility and version negotiation rules apply to old and new clients?
9. What are the security and privacy expectations on a local network?
10. What must be visible to the user: status, progress, errors, recovery actions, and audit/history?

Use a question only when its answer changes behavior, data, architecture, tests, or acceptance. If a safe default exists, state it explicitly and ask for confirmation rather than silently inventing a product rule.

When many gaps exist, show a compact risk-ranked gap list, but ask only the single highest-impact question. Do not make lower-priority choices on the user's behalf while waiting.

Gate: no unresolved question may affect a first-version acceptance criterion, persistent data shape, network/protocol contract, permission model, or destructive action.

### Phase 2: Analyze related problems before design

For every requested feature, produce:

- Direct behavior: what the user does and sees.
- Preconditions: required state, permission, connectivity, files, or settings.
- Downstream consumers: pages, services, data, protocol messages, notifications, and tests affected.
- Adjacent workflows: first run, repeat use, duplicate actions, cancel/pause/resume, close/reopen, restart, upgrade, downgrade, uninstall, and recovery.
- Failure modes: technical failures and understandable user-facing responses.
- Compatibility impact: old data, old protocol, old executable, OS variants, and mixed-version peers.
- Security impact: trust boundaries, spoofing, disclosure, tampering, abuse, and local-network assumptions.
- Performance impact: latency, throughput, memory, disk I/O, UI responsiveness, and large-input behavior.

Required artifacts before coding:

- Feature dependency map.
- State/event transition table for each stateful workflow.
- Data lifecycle table.
- Failure and recovery matrix.
- Compatibility matrix.
- Risk register with likelihood, impact, mitigation, and a test that detects regression.
- Decision log recording confirmed choices and rejected alternatives.
- Uncertainty register showing every proposed or assumed rule, its decision deadline, and the rework it could cause.

Use `references/risk-checklist.md` for the minimum review questions. For networked or persistent apps, do not omit it even when the initial request appears simple.

Gate: each high-risk path has an explicit behavior and an executable or manually checkable acceptance criterion.

### Phase 3: Feasibility and architecture fit

Evaluate proposed behavior against the actual repository and target platform:

- Confirm framework, language/runtime, project layout, packaging technology, signing needs, and OS APIs.
- Confirm whether required runtime packages, SDKs, compilers, and build tools are available locally.
- Check whether a proposed feature conflicts with the existing architecture or can be implemented at the correct ownership boundary.
- Identify network constraints, firewall rules, permissions, ports, sleep/wake behavior, and Windows version differences.
- Estimate large-file, concurrent-operation, and crash-recovery behavior with concrete numbers.
- Identify migration, compatibility, and rollback strategy before changing persistent formats or protocols.
- Prefer proven libraries and existing local abstractions for protocol, parsing, storage, and platform integration.

Every major decision must include: chosen approach, reason, rejected alternative, known tradeoff, and verification method. Mark anything not verified as an assumption.

Run a design pre-mortem: assume the first release failed in production, list the most plausible causes, map each cause to a preventive design rule and an early test, and add unresolved causes to the risk register.

Gate: the design is implementable with available technology and dependencies, or the exact external prerequisite is documented as a blocker.

### Phase 4: Write and review the PRD

Create `PRD.md` using `references/prd-template.md`. It must be specific enough that another developer can implement without guessing. Include behavior, not only headings or aspirations.

Run a completeness review:

- Every user-visible action has a success, failure, cancel, duplicate, and restart behavior.
- Every persistent field has an owner, type/shape, default, update trigger, migration rule, backup rule, and deletion rule.
- Every network interaction has participants, message purpose, validation, timeout, retry, version handling, and failure response.
- Every page/module states its purpose, inputs, outputs, controls, empty/loading/error states, and links to other modules.
- Every first-version item has a checkable acceptance criterion.
- Every out-of-scope item is explicit so it cannot silently enter implementation.
- Open questions are either resolved or explicitly excluded from version one.
- Every numeric value and compatibility statement has a source or a non-confirmed status tag.
- No `[PROPOSED]`, `[ASSUMPTION]`, or `[OPEN]` item that changes data, protocol, security, permissions, destructive behavior, or first-version acceptance may pass the PRD gate.

Show the user the plain-language summary and the unresolved decisions. Wait for confirmation before moving to page/interaction design or code.

Gate: the user confirms the PRD, scope, and out-of-scope list.

### Phase 5: Page and interaction design

For desktop apps, describe window hierarchy, sizing constraints, navigation, module relationships, control states, keyboard/mouse behavior, dialogs, notifications, and responsive behavior. Do not create new functionality merely because a visual reference contains it.

For each control, preserve or define: stable identifier, purpose, enabled/disabled rule, click/input result, validation, busy state, error state, and return path. For visual-only work, compare control names, bindings, handlers, and routes before and after.

Gate: the interaction map covers normal, empty, loading, error, offline, partial, cancelled, and completed states.

### Phase 6: Produce an executable development plan

Order work by dependency and risk, not by file order. Each stage must state:

- Goal and exact files/modules allowed to change.
- Preconditions and expected outputs.
- Implementation steps.
- Tests to add or run before proceeding.
- Manual acceptance checks where automation cannot prove behavior.
- Rollback or recovery approach.
- Exit criteria.

Separate foundational data/state/protocol work from UI work. Make cross-cutting contracts explicit before consumers. Limit each change to one coherent behavior so failures are easy to locate.

Gate: the user confirms the plan, stage order, test strategy, and release target.

### Phase 7: Implement incrementally

For each stage: inspect relevant code, make the smallest coherent change, add focused tests, run those tests, diagnose failures to root cause, fix, rerun, then continue. Keep a change log and do not silently expand scope.

Use subagents only for disjoint, bounded analysis or verification tasks. Give each a separate write set; never let multiple agents edit the same contract or file concurrently. Review all delegated output against the PRD and current repository before integrating it.

### Phase 8: Verify and release

Run focused tests after every stage, then the complete suite. Include build, launch/smoke, persistence/restart, upgrade/compatibility, failure/recovery, performance, and packaging checks appropriate to the PRD. Exercise both sides of network workflows when applicable.

Before packaging, verify the published input directory is built from the current commit, the installer script points to that directory, the output path is known, and the package contains the expected executable and dependencies. Report any unavailable network, SDK, compiler, signing, or installer prerequisite instead of claiming success.

Final report: summarize changes, files, tests and results, known limitations, produced artifacts and checksums, uncommitted changes, and the exact next action if something remains blocked.

### Phase 9: Public publication and installation handoff

When the user requests GitHub publication or a shareable release, read `references/public-release.md`. Respect the repository visibility and publication scope already authorized in the conversation; do not ask again for an established decision.

For release-only or documentation-only work on an existing implementation, enter this phase directly after inspecting the source and verification evidence. Earlier PRD/design approval gates apply only to new or changed product behavior, not to replaying established decisions.

Required handoff artifacts are the sanitized source, a human installation guide, an AI installation `SKILL.md`, versioned packages with checksums, and a verified repository/release link. Copy both installation documents to the user's requested delivery directory and compare their hashes, preserving unrelated files. Keep private configuration, service URLs, personal paths, credentials, and local audit denylists outside all public artifacts and Git history.

Gate: source, archives, staged Git blobs and commit metadata pass the privacy review; the remote visibility, commit and assets match the approved release; requested local copies match their source documents. Report any blocked step separately from completed work.

## Change requests after confirmation

When new requirements arrive after coding has started, pause implementation. Classify the change as data, protocol, lifecycle, UI, packaging, security, performance, or documentation. Trace affected artifacts, tests, migrations, compatibility, and acceptance criteria. Ask one question if behavior is ambiguous, then update the PRD and plan and obtain confirmation before editing code.

## Resource routing

- Read `references/prd-template.md` when creating or revising a PRD.
- Read `references/risk-checklist.md` during discovery, design review, and before release.
- Read `references/public-release.md` for GitHub publication, public packages, or human/AI installation-document delivery.
- Use repository-native tests, scripts, and helpers before creating new test infrastructure.
