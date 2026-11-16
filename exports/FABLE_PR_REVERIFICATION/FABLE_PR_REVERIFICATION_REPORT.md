# Fable re-verification of the product-register corrections (PR-01 to PR-17)

16 November 2026. Reviewed: `docs/PRODUCT_REQUIREMENTS.md` (88 records, SHA-256 `4b62c91b…3b1f49`), `AGENTS.md`, `DECISIONS.md`, `PROGRESS.md`, `scripts/check_product_requirements.py`, `scripts/check.py` and `docs/corrections_rb/PR_DISPOSITION.md`, all from bundle `00a13d93…be001d`.

This review changes no file of the bundle. A product decision recorded in the register is not implementation authority, client-policy approval or operating readiness, and nothing here opens a gate. The original findings in `exports/FABLE_PRODUCT_REQUIREMENTS/` are unchanged (byte-identical to the returned response ZIP).

## Verdict

**The register corrections are accepted.** All 17 findings are answered; 16 are corrected as specified and PR-11 is documented but needs your explicit confirmation. No future feature is described as built, and no proposal is described as approved.

Three things remain:

1. The register must now record this review (PRV-01, P2). Three records stay failed for new reasons; four may be raised.
2. Nine small gaps, mostly in how strictly the register check enforces its own rules (PRV-02 to PRV-10, P3).
3. Six product decisions that only the owner can make. One is time-critical.

## Verification conclusions for the seven failed records

Source checkpoint: bundle SHA-256 `00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d`. Scope of every conclusion: synthetic local preparation controls exercised by the named probes and the retained gates. Not client policy, connected operation, reconciliation completion or close.

| Record | Conclusion | Basis |
| --- | --- | --- |
| AAOS-KNO-04 | May be recorded Independently verified | RB-03 accepted: R02a, R02b, N03a, N03b, N03c |
| AAOS-CTL-01 | May be recorded Independently verified | RB-03 accepted; acceptance actors of a prior-statement revision are contributors (N04a) |
| AAOS-BNK-02 | May be recorded Independently verified | RB-02 and RB-04 accepted: R04a–R04c, N02b, N04a–N04d. Note UC-11 in the scope note. |
| AAOS-CTL-09 | May be recorded Independently verified | RB-02 and RB-04 accepted: R03a, R03b, N02a, N02b. Note UC-10 in the scope note. |
| AAOS-BNK-03 | **Remains Verification failed** | N01b, N01c, N01d: one charge approved in two periods (RC-01 to RC-03) |
| AAOS-CTL-04 | **Remains Verification failed** | Same |
| AAOS-GOV-03 | **Remains Verification failed** | "Known repaired defects must pass": RB-01 is not accepted |

The developer was right to leave all seven at Verification failed. Developer passes were not presented as independent acceptance anywhere I looked.

## Finding by finding

| Finding | Verdict | What remains |
| --- | --- | --- |
| PR-01 | Corrected | Records stay failed and must cite RC-01 to RC-03 (PRV-01). |
| PR-02 | Corrected | Both records may be raised. |
| PR-03 | Corrected | Both records may be raised. |
| PR-04 | Corrected, with gaps in the check | Evidence rule and promotion guard are weak (PRV-02, PRV-03). |
| PR-05 | Corrected | Owner decides the order of unassigned work. |
| PR-06 | Corrected as Proposed records | Owner ratifies AAOS-ONB-01 and ONB-02. Approved records "depend on" them (PRV-05). |
| PR-07 | Corrected | Optional hardening of the check (PRV-10). |
| PR-08 | Corrected as a Proposed record | Owner ratifies AAOS-INT-07 (PRV-05). |
| PR-09 | Corrected as Proposed records | Owner decides AAOS-GL-06, BNK-07, RPT-03. |
| PR-10 | Corrected | Owner confirms each exclusion. "Reserved" lives only in an unchecked table (PRV-07). |
| PR-11 | **Documented; owner confirmation required** | See below. |
| PR-12 | Corrected, one residual | Two tested records depend on a Not started record (PRV-06); punctuation (PRV-08). |
| PR-13 | Corrected | None. |
| PR-14 | Corrected | Parameter values are owner decisions before the named gates. |
| PR-15 | Corrected in the service | The shared web page still names the first client (PRV-04). |
| PR-16 | Corrected | None. Deferred, correctly not built. |
| PR-17 | Corrected | Same check gaps as PR-04. |

Details and the exact checks behind each row are in `FABLE_PR_REVERIFICATION_CORRECTIONS.json`.

## What I checked mechanically

My own parser, independent of the project's checker (`evidence/register_checks_output.txt` in `FABLE_RB_ACCEPTANCE`):

- 88 records, 88 unique IDs, all 12 fields present exactly once in every record.
- All 76 original IDs retained with unchanged titles. 12 new: ONB-01, ONB-02, INT-07, GL-06, BNK-07, RPT-03, BB-08, EXC-01 to EXC-05.
- Product decision: 77 Approved, 9 Proposed, 2 Rejected. Implementation state: 36 Deferred, 25 Not started, 20 Developer-tested, 7 Verification failed. The project script reproduces the same counts.
- Every dependency names an existing record. No self-dependency, no cycle. All 27 backlog tickets appear once in the crosswalk and name existing records.
- All 27 records in a tested or failed state cite a test file that exists.
- The first client is named in shared records only in AAOS-GOV-01, AAOS-ARC-04 and AAOS-KNO-01, the three boundary records the original finding allowed.

Fault injection against the checker, 37 cases (`evidence/register_fault_tests_output.txt`): 27 behave as a sound gate should. It rejects duplicate and lost IDs, missing, repeated and empty fields, unknown, self and cyclic dependencies, missing, duplicated and empty crosswalk rows, unsupported and mixed states, missing evidence, broken links, the first client's name in shared criteria and target stages, and unconditional Deferred dependencies. `make check` exits non-zero for each of the five faults PR-17 named, and for the client name in a shared Python module.

The 10 it accepts are the basis of PRV-02, PRV-03, PRV-06, PRV-07 and PRV-10.

## The gaps, in order

**PRV-01 (P2). Record this review.** Keep AAOS-BNK-03, CTL-04 and GOV-03 failed and cite RC-01 to RC-03; extend their criteria with the three arrival orders that still fail; raise the four records above with this report, the bundle hash and the probes as evidence; update the Current evidence section.

**PRV-02 (P3). Evidence rule.** A Developer-tested record passes with a test path that does not exist, with "See PR-04", or with any token starting with R and a digit.

**PRV-03 (P3). Promotion guard.** Changing AAOS-BNK-03 from Verification failed to Developer-tested passes the check. Independently verified passes with the words "independent review" and any 64 hexadecimal characters. AGENTS.md states both rules; nothing enforces them.

**PRV-04 (P3, code). Shared web page.** `accounting_agent/web/index.html` line 12 reads "Bird Bowl — fictional sandbox" for every client. The `make check` guard covers `*.py` only. Residual of PR-15, whose ticket named only `service.py`.

**PRV-05 (P3). Approved depends on Proposed.** 13 Approved records list a Proposed record as a dependency, because "is the first instance of" was recorded as "depends on". Approved first-client work formally waits on proposals you may reject.

**PRV-06 (P3).** AAOS-GOV-02 and AAOS-ARC-01 are Developer-tested and depend without condition on AAOS-GOV-01, which is Not started. The check looks at Deferred only.

**PRV-07 (P3).** "Reserved" is a row in a table, not a field; the check does not compare table and records.

**PRV-08 (P3).** Stray punctuation in 13 Dependencies fields. The references still parse.

**PRV-09 (P3).** The change inventory omits `START_HERE.md` and 18 archive files under `exports/`. Every source, test and script change is listed.

**PRV-10 (P3, optional).** The client-boundary check does not read Description fields or person names.

## Decisions that are yours

1. **PR-11, time-critical.** The register now says procedure capture as written documentation, outside the application and with no client records loaded, may proceed before G1; processing client samples in the application needs human G0 acceptance and G1 authorization. That position was written into D-012 by the developer during the correction pass. The finding asked the product owner and accounting lead to decide. Please confirm it in writing or change it, and name the held-out validation month. November is half over.
2. PR-05: the order of unassigned requirements after G0.
3. PR-06, PR-08, PR-09: ratify, change or reject the six Proposed shared records (ONB-01, ONB-02, INT-07, GL-06, BNK-07, RPT-03).
4. PR-10: confirm each exclusion and reservation, including whether payroll and tax work stay outside the product long term.
5. PR-14: the parameter values named in the eight criteria, each before its stated gate.
6. The nine open decisions already listed in the register. None was answered by this review.

## Classification

| Kind | Items |
| --- | --- |
| Code defects | PRV-02, PRV-03 (register check); PRV-04 (web page). RC-01 to RC-03 are in the RB report. |
| Documentation defects | PRV-01, PRV-05, PRV-06, PRV-07, PRV-08, PRV-09 |
| Future enhancement | PRV-10 |
| Intentionally deferred, not defects | All proposed shared records; AP, AR, reconciliation, close, reporting, integrations, hosting, briefing, communications; PR-16 schema limits |
| Product or client decisions | The six items above |

## Files returned

1. `FABLE_PR_REVERIFICATION_REPORT.md` (this file)
2. `FABLE_PR_REVERIFICATION_CORRECTIONS.json`: 17 finding verdicts, verification conclusions for the seven records, PRV-01 to PRV-10 with acceptance criteria, owner decisions
3. Evidence is shared with the RB review: `../FABLE_RB_ACCEPTANCE/evidence/register_checks_output.txt`, `register_fault_tests_output.txt`, `inventory_checks_output.txt` and the scripts that produced them
