#!/bin/bash
R=/tmp/fre/tools/run_cmd.sh; C=/tmp/fre/run1
$R rd-probes-12 $C python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py . Y01 Y02 Y03 Y04 Y06 E01 E02 E03 E03c E04 E05 E06
$R y05-adapted $C python3 review/fable_rd_feed_contract_probes.py . Y05
$R rd-order-search-336 $C python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py . --json /tmp/fre/out/rd-order-search-336.results.json
$R rd-order-search-336-noflag $C python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py .
$R rc-probes $C python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .
$R rc-order-search-120 $C python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py . --json /tmp/fre/out/rc-order-search-120.results.json
$R rb-probes $C python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
$R ra-probes $C python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
$R owner-clarification-repro $C python3 docs/corrections_re/locked_second_claim_reproduction.py
