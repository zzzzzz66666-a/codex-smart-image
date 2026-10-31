# Public release and installation handoff

Use this reference when the user requests a GitHub upload, a public repository, or a distributable plugin. It extends the development workflow through a verifiable handoff.

## Scope and authorization

Resolve the correct plugin from its manifest and source, the target GitHub repository, visibility, and requested local delivery directory. Existing user authorization to publish is sufficient; ask only about an unresolved decision that changes the result. A directory named for another plugin may be a delivery destination: preserve its existing contents and use distinct document names.

## Build a sanitized candidate

Use an explicit source allowlist or a reviewed manifest. Include implementation, manifests, installation scripts, tests and required documentation. Exclude local runtime configuration, API keys, private service addresses, credential stores, generated absolute-path manifests, logs, prompts, generated images, caches and unrelated projects. Put service endpoint and model choices in local editable settings; an empty required endpoint must fail clearly before any network request.

Inventory old archives before packaging: rebuilding a safe source tree does not sanitize an old ZIP. Build fresh versioned archives from the candidate, extract them and run the documented startup/install checks. Include a human installation guide and a separate AI installation Skill in both the repository and the appropriate distribution. Check the contents inside archives, not only filenames. Keep private deny terms in a local file outside the candidate, and report matched file/rule names without echoing sensitive values.

## Check Git and publication

Review source text, binary resources, archive entries, staged Git blobs, commit author/committer metadata and all history to be uploaded. A later deletion does not remove a leak from an earlier commit. If a new repository is appropriate, export reviewed source into a clean repository with generic maintainer metadata and no private history. Do not overwrite an existing repository or rewrite its history without the user's authorization.

Run regression tests and package smoke checks, then record a manifest hash for the exact reviewed candidate. Recompute it immediately before publication; any changed byte requires renewed audit. Verify the committed tree matches the staged files and allowlist, and that no local configuration is tracked. Keep authenticated API headers and tokens in memory or protected credential tooling, never in source, terminal output, process arguments or commit messages.

Publish only to the authorized repository and visibility. Preserve existing assets unless replacement is requested. After a partial failure, inspect remote state and resume missing operations; do not blindly recreate releases, force-push or duplicate uploads. Read back repository visibility, branch commit, release tag and asset SHA256 digests. If the server omits a digest, download the public artifact and compare its bytes locally.

## Installation documents and local delivery

The human guide must cover prerequisites, download and integrity checks, installation, private local configuration, usage, update, uninstall, common failures and actual verification limits. Use placeholders or interactive local input instead of a developer's personal account, computer path, service URL or key.

The AI Skill must define when to install, locate the correct package, inspect scripts and prerequisites, preserve existing configuration, keep credentials out of chat and public output, perform the installation within current permissions, and verify the result. Distinguish local readiness, model listing, real provider generation and automatic chat invocation. Do not claim one proves another. Paid generation needs task authorization; uncertain submissions must not be automatically retried with a new request identifier.

Copy both final installation files to the user's requested folder, preserve unrelated files, and compare SHA256 with the source documents. Request sandbox access for destinations outside writable roots. Add this handoff procedure to the reusable development Skill itself using generic instructions and references. Verify the original Skill and packaged copy contain the same update.

The final handoff reports public repository/release links, local document locations, test results, privacy audit outcome and remaining real-environment checks. Do not paste private identifiers, endpoint values or credential output into that report.
