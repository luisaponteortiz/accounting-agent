# Owner clarification resolved — D-029

On 16 November 2026 the owner answered the question about a second claim against a row already approved inside its own locked period: **"Preserve frozen approval; block new version"**.

D-029 appends that clarification without rewriting the verbatim D-026 contract or the historical D-028 question. The existing frozen approval remains protected; the incoming version stays quarantined until an authorized reopen. After reopen, the contested-claim blocker remains and no approval is created automatically. The existing refusal to disposition an incoming source inside its own locked period remains until reopen. No schema or frozen-approval behavior change was required.

The portable check is `python3 docs/corrections_re/locked_second_claim_reproduction.py`. `owner-clarification-probe.*` records exit 0: both claims recorded, frozen approval preserved, incoming version held, audit valid; after reopen, the contested blocker remains and the current version is not approved.

Historical evidence is retained in `locked-second-claim-contract-check.*`, `final-locked-home-boundary.*` and `verified-locked-home-boundary.*`. The latter two returned exit 1 while the literal clause-7 question was unresolved; they are not current failures under the owner's clarified scope. The exact diagnostic sources are retained in `locked-second-claim-original-source.txt` and `locked-second-claim-before-clarification-source.txt`.

Independent verification must exercise D-026 together with D-029. No implementation state or readiness gate is raised by this owner clarification or the passing developer check.
