# Primary Product Sources

Checked for this handoff on November 14, 2026. Reverify dynamic product details when implementing connections. These sources support specific product capabilities and limits; the organizational design, proposed stack, operating policies, acceptance criteria and synthetic examples are recommendations derived from Luis's requirements.

## S1 Anthropic runtime choices

https://platform.claude.com/docs/en/cli-sdks-libraries/overview

Distinguishes API clients from the Agent SDK, which runs in a process the developer operates, and Managed Agents, which supplies a managed runtime. The plan uses a provider interface and application-owned orchestration.

https://code.claude.com/docs/en/agent-sdk/overview

Describes tool execution, permissions, sessions and subagents in the SDK. Its developer guidance directs third-party applications to API authentication. This plan does not depend on subscription-session credentials.

## S2 Render background workers

https://render.com/docs/background-workers

Documents continuously running background processes that consume queued work and can call third-party APIs, including AI models. Hosting and model usage remain distinct services.

## S3 Render Blueprints

https://render.com/docs/infrastructure-as-code

Documents multi-resource configuration in a YAML Blueprint and manual control of synchronization. The implementation should generate a reviewable configuration and verify its current schema; this handoff does not authorize applying it.

## S4 PostgreSQL queue locking

https://www.postgresql.org/docs/current/sql-select.html

Documents row locking and SKIP LOCKED for queue-like consumers. Use it for job claiming with short transactions. It is not a general solution for consistent business reporting or exactly-once external effects.

## S5 Claude Team API credits

https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers

https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans

Documents the pooled Team benefit, owner-managed linking to one Console organization, credit expiry, and separation from normal app usage limits. The office's actual claim status and available balance are not known.

## S6 Console workspace scope and cost management

https://platform.claude.com/docs/en/manage-claude/workspaces

https://support.claude.com/en/articles/9796807-create-and-manage-workspaces-in-the-claude-console

Documents workspace-scoped access/resources and centralized organization billing, with workspace usage limits. A workspace does not establish a separately owned share of the team's credits.

## S7 QBO pending bank-feed limitations

https://help.developer.intuit.com/s/question/0D5TR00001a1LyM0AU/can-you-confirm-the-supported-api-to-fetch-and-post-banking-for-review-pending-bank-feed-transactions-our-automation-pulls-gl-posted-txns-then-needs-to-acceptmatchcategorize-pending-feed-items-and-create-posted-expensetransferdeposit-records

Intuit Developer Support states that pending Banking For Review retrieval, acceptance, matching and categorization are not supported by the public QBO Accounting API. Do not label a ledger write as a completed bank-feed action.

## S8 QBO cleared and reconciled status

https://help.developer.intuit.com/s/question/0D5TR00001ad0W30AI/does-qbo-provide-a-supported-api-to-mark-an-existing-bankaccount-transaction-as-clearedreconciledthe-green-check-in-reconcileafter-our-app-finds-one-unique-100-match-if-not-is-there-a-partner-api-or-approved-alternative

Intuit Developer Support distinguishes reading reported status from setting Cleared/Reconciled status, and identifies the QuickBooks UI as the supported status-setting workflow. A reconciliation workpaper does not by itself complete that external workflow.

## S9 Render billing and team access

https://render.com/docs/render-dashboard

https://render.com/docs/team-members

https://render.com/articles/how-paas-billing-works

Documents payment-method management, workspace member roles/plan requirements, and the components of hosting cost. Determine the complete configuration cost before deployment instead of quoting one instance as the total.

## S10 Claude API billing

https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage

Documents prepaid credits, auto-reload, invoicing arrangements, and payment-method changes. Actual billing permissions and arrangements must be checked before any purchase.

## S11 Render projects and environments

https://render.com/docs/projects.md

Documents staging/production grouping, environment-scoped secrets and private-network controls. Network isolation does not remove public web access. Blueprint/repository permissions also matter for protected resources. Verify current plan entitlements before relying on a control.

## S12 Render deployment controls

https://render.com/docs/deploys.md

Documents manual deployment, deployment of a selected commit, and automatic-deploy settings. This plan proposes explicit release approval; a code rollback must be evaluated separately from database migration or data recovery.

## S13 NIST Generative AI Profile

https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

Voluntary AI risk-management guidance covering governance, content provenance, pre-deployment testing and incident handling. Used as background for the proposed testing/governance approach, not as a statement of binding legal requirements or company compliance.

## S14 Agent orchestration and durable work

https://www.anthropic.com/research/building-effective-agents

Describes orchestrator/worker and evaluator/optimizer patterns, tool feedback, human checkpoints and stopping conditions. Used for architectural patterns rather than current SDK names or unmeasured claims of business autonomy.

https://www.anthropic.com/research/managed-agents

Describes separating durable session records, the model loop and execution tools so work can recover across failures. The handoff retains its application-owned runtime; this source does not require a switch to a hosted agent product or prove this pilot's competence.

## S15 Direct QuickBooks application integration

https://static.developer.intuit.com/output_html/qbo/docs/learn/rest-api-features.html

https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0

Documents application REST requests, company identifiers and OAuth authorization. The application can call supported operations directly; a model is not an API transport requirement. Verify the actual edition, company and capabilities before enabling a connector.

## S16 Application-executed model tools

https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works

Documents model-generated tool requests and application execution of client tools. This supports separating optional reasoning from the trusted accounting adapter and its validation/authorization. Deterministic code paths need not make a model request.

## Implementation source practice

Record official documentation URLs, access date, supported operation, account-specific test result and limitations for each live capability. Do not treat a public endpoint description as proof that the company's account has that entitlement. Current HubSpot, BILL, Sage, identity and document-provider schemas must be researched when those integrations are selected; this handoff does not claim their account capabilities are verified.
