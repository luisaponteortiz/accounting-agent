PYTHON ?= python3
.PHONY: setup demo test core-test api-test check verify-no-egress export-demo backup reviewer-test batch1-gate batch2-gate reverification-gate acceptance-gate rb-gate rc-gate rd-gate re-gate rf-gate
setup:
	$(PYTHON) -m accounting_agent setup
demo:
	$(PYTHON) -m accounting_agent demo
core-test:
	$(PYTHON) -m unittest tests.test_platform tests.test_validation tests.test_periods tests.test_reviewer_probes tests.test_reviewer_cases -v
api-test:
	$(PYTHON) -m unittest tests.test_http -v
test:
	$(PYTHON) -m unittest discover -s tests -v
check:
	$(PYTHON) scripts/check.py
verify-no-egress:
	$(PYTHON) -m unittest tests.test_platform.PlatformCase.test_workflows_complete_with_application_outbound_calls_denied -v
export-demo:
	$(PYTHON) -m accounting_agent export
backup:
	$(PYTHON) -m accounting_agent backup --output exports/local-synthetic-backup.sqlite3

reviewer-test:
	$(PYTHON) review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json

batch1-gate: batch2-gate

batch2-gate:
	$(PYTHON) review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate --json-report docs/batch2/final-validation.json
	$(PYTHON) review/batch2_verification_probes.py .
	$(PYTHON) scripts/synthetic_month.py

reverification-gate:
	$(PYTHON) exports/FABLE_REVERIFICATION/fable_reverification_probes.py . RN01 RN02b RN04 RN05 RN05b RN06 RT09a RT09b RT09c RT09d RT11 RT12b RT12c RT12d RT10a RT10b RT13 RT13n RT14c RT14d RT14e RT14f RT15 RT16 RT17 RT19a RT19b
	$(PYTHON) review/fable_reverification_probes.py .
	$(PYTHON) scripts/verify_corrective_checkpoint.py

acceptance-gate:
	$(PYTHON) exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py . A04 A01 A02 A06 A07 A08 A09 A10 A11 A12 A13 A14 X01 X12k X12s X15 U1 U4 M1 M2
	$(PYTHON) review/fable_rv_acceptance_probes.py .

rb-gate:
	$(PYTHON) exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
	$(PYTHON) -m unittest tests.test_ra_review_gate -v

rc-gate:
	$(PYTHON) scripts/verify_rb_review.py

rd-gate:
	$(PYTHON) scripts/verify_rc_review.py

re-gate:
	$(PYTHON) scripts/verify_rd_feed_review.py

rf-gate:
	$(PYTHON) scripts/verify_re_acceptance_review.py
