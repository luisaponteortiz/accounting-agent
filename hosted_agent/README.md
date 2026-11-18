# Hosted accounting agent (development build)

The agent that runs by itself on a host and brings people only the exceptions.
Opened by owner decision D-040 (17 November 2026). Every company in this build
is fictional; nothing here connects to a real client's books.

## What it does today

One run per client (`python3 -m hosted_agent run`, the job a scheduler calls):

1. **Company check.** The company the ledger returns must be the one the client was set up with. Checked before the run and again before every posting. The ledger has no "current company": every call names it.
2. **Observe.** If a person handled a waiting line directly in the books, record whether they did what the agent proposed.
3. **Propose.** Each new bank line gets a class, a proposed treatment and the evidence for it.
4. **Route.** A line posts unattended only when all of these hold: no hard stop (closed period, before the fiscal year, future date, Opening Balance Equity), a class that may be automated, enough confidence, under the client's unattended limit, the client is in `post standing` mode, and a person has granted a standing approval for this client, this class and this exact treatment, within its amount limit. A fixed share of those still goes to a person as a spot check.
5. **Post and read back.** What was posted is read back from the books and compared. A posting that cannot be verified goes to a person and is never retried unattended.
6. **Queue the rest**, each with the reason it is there.

People decide waiting items (approve, change, reject with a reason), grant and end standing approvals, and set each client's mode. The agent can do none of those. A standing approval needs five agreements in a row on record, or the owner's stated reason. One disagreement ends it.

| Mode | What can reach the books |
| --- | --- |
| `prepare only` | Nothing. Proposals and the record of agreement only. |
| `post approved` | Items a person approved or changed, one decision each. |
| `post standing` | The above, plus classes covered by a standing approval. |

## Run it

```sh
python3 -m hosted_agent demo                               # review page on http://127.0.0.1:8770, sign-in links printed
python3 -m unittest discover -s hosted_agent/tests -t .     # 58 review tests
```

## What is not built yet

- **Claude is a first cut.** With `ANTHROPIC_API_KEY` set, `ClaudeBrain` asks Claude only about lines the books cannot settle, and its suggestions are always reviewed by a person (class `model suggestion` can never get a standing approval). Its instructions are a short list of the firm's rules written into `claude_brain.py`; the owner's skill library is not loaded yet. Set `AGENT_BRAIN=baseline` to switch it off, `AGENT_MODEL` to change the model.
- **QuickBooks is connected read-only, to a sandbox.** With `INTUIT_CLIENT_ID` and `INTUIT_CLIENT_SECRET` set, the owner can connect one Intuit sandbox company and the page shows what the agent can read from it. `qbo.py` can reach only the sandbox host and writes nothing. The agent's runs still use `FakeLedger`. Whether the bank feed's unreviewed lines can be read this way is not yet known.
- **Only the bank feed job.** Cards, documents, close and the other jobs follow the same frame.
- **Sign-in is a link with a token**, good enough for fictional data and not for go-live. Storage is SQLite.
- The page has been exercised in a headless browser, not reviewed by a person.
