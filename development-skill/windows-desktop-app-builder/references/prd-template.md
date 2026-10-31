# Windows Desktop App PRD Template

Replace bracketed text. Remove guidance text only after the decision it describes has been recorded elsewhere in the document.

## Contents

1. Document control and provenance
2. Product goal and context
3. Scope
4. Product vocabulary and rules
5. System boundary and architecture fit
6. Page, window, and navigation structure
7. Detailed feature specifications
8. Persistent data and lifecycle
9. Network and protocol contract
10. Security and privacy
11. Performance and reliability targets
12. Compatibility, migration, updates, and uninstall
13. Test and acceptance specification
14. Risks, decisions, open questions, and pre-mortem
15. Traceability

## 1. Document control

- Product name:
- PRD version and date:
- Owner and reviewers:
- Status: draft / awaiting confirmation / approved / superseded
- Related repository, branch, and baseline commit:
- Decision log location:

### 1.1 Requirement provenance legend

Tag every rule and numeric value:

- `[CONFIRMED]`: explicitly confirmed by the user or an approved source.
- `[PROPOSED]`: recommended default awaiting confirmation.
- `[ASSUMPTION]`: temporary premise needed for analysis; not authorized for implementation.
- `[OPEN]`: unanswered question that may change behavior or design.
- `[OUT]`: explicitly excluded from this release.

Maintain a requirement ledger with columns: ID, rule, tag, source/evidence, affected UI/data/protocol/tests, confirmation date, and owner. Do not remove the tag merely because a draft PRD reads smoothly.

## 2. Product goal and context

### 2.1 Problem

State the user problem, who experiences it, and why existing tools are insufficient.

### 2.2 Goal and measurable outcome

State the first-version outcome and how it will be measured. Avoid vague verbs such as “support” without a testable meaning.

### 2.3 Users and scenarios

For each primary scenario, record actor, starting state, trigger, steps, expected result, alternate path, failure path, and end state.

### 2.4 Constraints and assumptions

Record OS versions, CPU architecture, runtime prerequisites, network conditions, storage limits, permissions, offline requirements, privacy expectations, and assumptions awaiting confirmation.

## 3. Scope

### 3.1 Version-one must-have

Give each item an ID, status tag, source, user value, priority, dependencies, and acceptance criterion.

### 3.2 Version-one deferred or excluded

State what is not being built and why. Include tempting adjacent features that must not enter implementation accidentally.

## 4. Product vocabulary and rules

Define terms, identifiers, ownership, time units, size units, status names, error categories, and rules that must remain consistent across UI, data, and protocol.

## 5. System boundary and architecture fit

Describe processes, modules, ownership boundaries, external OS services, network participants, storage locations, runtime dependencies, and data flow. Identify what remains unchanged in an existing application.

## 6. Page, window, and navigation structure

For every window/page/module:

- Purpose and user goal.
- Entry points and exit paths.
- Inputs and outputs.
- Required controls and stable identifiers.
- Normal, empty, loading, disabled, error, offline, partial, cancelled, and completed states.
- Relationship to other modules and source of truth for displayed data.
- Resize, DPI, keyboard, accessibility, and localization expectations.

Include a simple navigation map and a feature dependency map.

## 7. Detailed feature specifications

For each feature, document:

- User story and non-goals.
- Preconditions and permissions.
- Exact step-by-step behavior.
- Validation and duplicate-action behavior.
- State transitions and events.
- Success, timeout, retry, cancel, pause, resume, crash, restart, and recovery behavior.
- Notifications, progress, logs/history, and user actions after failure.
- Dependencies and affected modules.

## 8. Persistent data and lifecycle

Provide a field-level table with: entity, field, type/shape, required/default, owner, read/write locations, update trigger, consistency rule, migration/versioning, backup/restore behavior, retention, deletion, and privacy sensitivity.

Specify:

- File/database format and atomic-write strategy.
- Locking/concurrency behavior.
- Backup frequency, location, rotation, corruption detection, and recovery precedence.
- Behavior after crash, forced close, upgrade, downgrade, and uninstall.
- Whether user-created files are separated from app metadata and protected from cleanup.

## 9. Network and protocol contract

For every message or API, document sender, receiver, purpose, fields and types, version, validation, authentication/authorization or trust assumption, timeout, retry, idempotency, maximum size, ordering, cancellation, and error response.

Include discovery, pairing/handshake, transfer, progress, pause/resume, cancel, disconnect/reconnect, mixed-version behavior, firewall/port requirements, and network-change behavior where applicable.

## 10. Security and privacy

Describe trust boundaries, local-network threats, code/token entropy and lifetime, replay/spoofing protection, file path validation, overwrite rules, resource exhaustion limits, sensitive logs, permissions, and user-visible security warnings. Record residual risks and accepted tradeoffs.

## 11. Performance and reliability targets

Define measurable targets for launch time, UI responsiveness, memory, CPU, disk I/O, throughput, latency, file sizes, item counts, concurrent operations, retry duration, and recovery time. State whether each value is confirmed, proposed, or measured. Record the test environment and measurement method. Do not convert a desired target into a verified capability before testing it.

## 12. Compatibility, migration, updates, and uninstall

Provide a matrix for OS versions, architectures, runtime availability, old/new app versions, old/new data, and protocol versions. Define feature negotiation, update prompt, fallback behavior, migration, rollback, uninstall cleanup, user-data preservation, and firewall/service cleanup.

## 13. Test and acceptance specification

For each requirement, provide an ID, setup, action, expected result, evidence, automation/manual method, and priority. Cover happy path, invalid input, duplicate action, interruption, restart, offline, disk full, permission denied, corrupted data, mixed versions, large inputs, and UI states. Include release smoke checks and packaging verification.

## 14. Risks, decisions, and open questions

Use tables for risk ID, description, likelihood, impact, mitigation, owner, detection test, and residual risk. Record confirmed decisions, rejected alternatives, rationale, and date. Maintain a separate uncertainty register for proposed defaults and assumptions. Do not hide unresolved questions in prose.

Add a pre-mortem table with: imagined release failure, likely cause, affected user journey, preventive design rule, earliest detecting test, and remaining risk.

## 15. Traceability

Map goal -> requirement -> module -> data/protocol contract -> test -> acceptance evidence. A requirement without a test or evidence is incomplete.
