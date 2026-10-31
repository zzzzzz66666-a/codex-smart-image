# Pre-implementation and Release Risk Checklist

Use this checklist to find related problems before coding. Mark each item yes, no, or not applicable, and explain every no.

## Requirements and scope

- Is the primary user outcome measurable?
- Are actor, starting state, trigger, and end state explicit?
- Are success, failure, cancellation, retry, duplicate action, and timeout defined?
- Are all limits quantified: size, count, duration, rate, storage, concurrency?
- Are first-version exclusions explicit?
- Are terms and statuses used consistently?
- Is every rule tagged as confirmed, proposed, assumed, open, or out of scope?
- Does every numeric limit, timeout, compatibility claim, and performance target cite its source?
- Could any proposed default silently change data, protocol, security, permissions, or acceptance?

## State and lifecycle

- Can every state be reached, left, restored, or expired?
- What happens during close, force close, crash, restart, sleep, wake, and OS shutdown?
- Can two operations race or be triggered twice?
- Who owns each transition across devices, user sessions and processes?
- Are active, paused, cancelled, failed, resumable, completed, and expired states distinguishable?

## Data and persistence

- Is every field typed, defaulted, versioned, and owned?
- Are writes atomic and safe under concurrent access?
- Is corruption detected and is backup recovery deterministic?
- Are temporary, partial, history, settings, pairing, and user files separated?
- Does uninstall remove only intended app data and preserve user data?
- Is migration tested from the oldest supported format?

## Network and compatibility

- Are discovery, addressing, ports, firewall profiles, and network changes defined?
- Does both sides discover and display the same relationship state?
- Are handshake, authorization, expiry, replay, spoofing, and wrong-code cases covered?
- Are messages bounded, validated, versioned, ordered, and idempotent?
- What happens on disconnect at every transfer phase?
- Can old and new versions interoperate, and is fallback explicit and safe?
- Are large files streamed without integer overflow, buffering, or UI blocking?

## Security and privacy

- What can an untrusted device on the same network do?
- Can a filename escape the destination directory or overwrite an existing file?
- Can repeated requests exhaust CPU, memory, disk, sockets, or dialogs?
- Are tokens, paths, IP addresses, and file names logged appropriately?
- Are permissions and firewall changes least-privilege and reversible?

## UI and accessibility

- Does every action expose disabled/busy/error/completed feedback?
- Does the user have a recovery action after each failure?
- Do text, controls, dialogs, progress, and status remain usable at minimum size and DPI?
- Are keyboard navigation, focus, contrast, localization, and screen-reader names adequate?
- For visual-only changes, are bindings, names, handlers, and data untouched?

## Performance and release

- Are throughput, latency, launch, memory, CPU, and disk targets measured on stated hardware?
- Is UI work decoupled from large I/O and network loops?
- Are retries/backoff bounded and observable?
- Does the build use the current source commit and correct target architecture?
- Is the installer input directory complete and free of stale binaries?
- Are install, upgrade, launch, firewall, uninstall, and data-preservation checks performed?
- Is the final artifact path, size, version, checksum, and known limitation recorded?

## Rework prevention

- Was a design pre-mortem completed before implementation?
- Are the highest-cost uncertainties resolved before data and protocol contracts are coded?
- Does every major decision record rejected alternatives and verification method?
- Can each requirement be traced to code ownership and a detecting test?
- Are assumptions prevented from becoming implementation requirements without explicit confirmation?
