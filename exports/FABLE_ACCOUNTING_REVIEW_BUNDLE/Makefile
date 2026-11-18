PYTHON ?= python3
.PHONY: setup demo test core-test api-test check verify-no-egress export-demo backup
setup:
	$(PYTHON) -m accounting_agent setup
demo:
	$(PYTHON) -m accounting_agent demo
core-test:
	$(PYTHON) -m unittest tests.test_platform tests.test_validation -v
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
