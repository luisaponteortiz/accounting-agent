#!/bin/bash
R=/private/tmp/claude-501/rf; X=$R/tools/run_cmd.sh; C=$R/run1; O=$R/out
$X re-probes-21 $C python3 exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py .
$X rd-probes-12 $C python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py . Y01 Y02 Y03 Y04 Y06 E01 E02 E03 E03c E04 E05 E06
$X y05-adapted $C python3 review/fable_rd_feed_contract_probes.py . Y05
$X rc-probes $C python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .
$X rb-probes $C python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
$X ra-probes $C python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
$X owner-clarification-repro $C python3 docs/corrections_re/locked_second_claim_reproduction.py
$X rd-order-search-336 $C python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py . --json $O/rd-order-search-336.results.json
$X rc-order-search-120 $C python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py . --json $O/rc-order-search-120.results.json
