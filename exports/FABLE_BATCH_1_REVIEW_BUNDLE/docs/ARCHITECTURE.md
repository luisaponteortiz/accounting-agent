# General Accounting Agent OS — Batch 1

This remains a local, fictional-data accounting preparation platform. The shared runner supports modular GL, AP, AR, banking/reconciliation, close and reporting/analysis contracts. Only card preparation, mechanical journal validation and document-presence close readiness execute. No Batch 2 accounting capability has been added.

## State and inputs

Organization/client/environment scope applies to profiles, periods, evidence, occurrences, runs, artifacts, decisions and exports. SQLite migrations 2–5 preserve immutable evidence/artifact/decision/audit bytes and relationships. The original schema is retained as a regression fixture. Startup migrations are serialized and recheck their version under the database writer lock.

Periods are records, not profile fields. Human reviewer-role actors open periods; locking/reopening additionally excludes people who prepared runs or supplied evidence in that period. Status history is append-only. A lock preserves the currently completed preparations through frozen run references and refuses further enqueue. New or revised locked-period evidence is retained with LATE_ACTIVITY_IN_LOCKED_PERIOD; reopening explicitly admits it for renewed preparation. A lock is not final-close sign-off or package finalization.

Dated evidence belongs to the period containing its fixture accounting date. Unconfigured dates are quarantined as UNASSIGNED_ACCOUNTING_PERIOD. Undated documents use an explicit packet period, or the sole configured period. They are not silently reused across months.

Each capability declares source kinds, profile sections and bound-period lookback. Runs persist the union manifest for their workflow; handlers receive only their declared inputs and declared upstream outputs. Receipt changes affect card preparation, not journals; journal documents do not invalidate cards. Invalidation remains conservative within a workflow/period population. Lineage includes capability versions and core.py/modules.py hashes; HTTP, CLI and UI changes do not stale accounting work. Locked snapshots stay frozen. Finalized packages and finer per-item dependency optimization remain deferred.

## Authority and governing work

Trusted local transport supplies Actor.kind (human/service) and role. Hashed envelopes record contributors: run enqueuer, committing worker, mandate issuer, applicable profile registrant and suppliers of the workflow manifest's source versions. A contributor cannot review that artifact under another role. Review requires a non-contributing human reviewer; name prefixes have no authority. Real identity verification and client authority matrices remain unavailable.

Identical governing preparations reuse an immutable artifact through artifact_runs links. Its originating run_id remains historical; run_ids lists every linked execution. The newest completed preparation governs each client/workflow/period/item. State/export expose one governing review state plus all history. Pending can become approve/reject; approve can become revoke. Duplicate decisions return 409. Opposing decisions by different reviewers create disputed, never last-write-wins approval. Only an explicit third independent human reviewer resolution can resolve a synthetic dispute. Real resolution authority is not configured.

Envelopes bind scope, period ID, workflow/capability/control versions, contributors, dependency content hashes, input fingerprint and module output. Legal entity/book identity, a shared proposed-entry contract, independent policy approval and formal review-policy binding are not implemented (Batch 2). Mechanical validation does not establish recognition or tax correctness.

## Recurring execution

Only a human preparer can issue a synthetic mandate; this remains a demo privilege, not independently approved standing client authority. Occurrences are unique business slots, separate from retryable execution runs. A database constraint permits one completed run per occurrence. Stale held attempts can be re-dispatched while authority remains valid; missed slots are skipped_no_catch_up records; an unfit mandate is held independently. The synthetic occurrence date selects its configured calendar period. Explicit client period rules, evidence freshness and independent mandate approval remain Batch 2.

The worker retains expiring leases, three-attempt limits and atomic checkpoints. Live schedules, model/connector calls, ledger writes, payments and deployment remain disabled. package.manifest records provenance/external-state metadata; it performs no accounting readiness validation.

## Remaining limits

Profiles still activate through synthetic preparer registration. Shared approved rules, exception dispositions, source revision ordering/removals, stronger journal support/duplicate/no-effect controls, statement population identity and outcome-aware close readiness remain unresolved. Export still reads in two transactions with a source-change guard; it is not an atomic finalized package. Audit hashes are not an externally anchored/WORM guarantee. Production identity, persistence, secrets, retention and recovery remain unverified.

Python standard library, SQLite and static HTML/JS are retained. No production stack rewrite or live access was introduced.
