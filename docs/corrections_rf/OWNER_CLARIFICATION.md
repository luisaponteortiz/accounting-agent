# Sole retained-method exception

Recorded verbatim in DECISIONS.md D-031. D-026, D-029 and CODEX_RF_CORRECTIONS_PROMPT.md remain unchanged.

Yes. You may adapt only test_PRV14_third_authority_is_pinned_and_latest_verdict_controls in tests/test_product_requirements.py, on these conditions:

Only that method. Its name stays. The other 226 methods remain unchanged. Show the complete before and after text and the diff in your report, as you did for the RD02 method last pass.
The first half stays as it is and runs against the real four-authority configuration: one added byte in the RD results file is rejected with “Protected reviewer input hash differs”.
The second half may use a three-authority fixture, provided the fixture is made by leaving the fourth authority out of the checker’s pinned inputs as data. Do not stub, bypass or special-case any validation, and keep the method’s assertions as they are.
Add separate new methods on the unmodified four-authority configuration, covering at least:
the fourth authority’s results file and report are pinned (a one-byte change is rejected);
the fourth authority controls per record: a failed verdict cannot be promoted, and a downgrade is accepted when results and register follow;
an older authority that is altered and re-pinned cannot override the fourth;
results that follow the older file are rejected;
the seven-row order is still enforced.
Latest-wins is not weakened. The shipped checker always reads all four authorities; the three-authority path exists only through the test’s fixture.
Completion criterion changes accordingly: all 227 methods present, 226 unchanged, this one rewritten as authorized. No other retained test, probe or fault case may be adapted.
Record this answer as an owner clarification appended to DECISIONS.md, quoted, without changing D-026 or D-029 or the RF prompt file.
