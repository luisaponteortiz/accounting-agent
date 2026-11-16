#!/bin/bash
R=/tmp/fre/tools/run_cmd.sh
$R rb-register-faults-F /tmp/fre/run3 python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
$R rc-register-faults-G /tmp/fre/run4 python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py /tmp/fre/run4
$R rd-register-faults-H /tmp/fre/run5 python3 exports/FABLE_RD_ACCEPTANCE/evidence/scripts/fable_rd_register_faults.py /tmp/fre/run5
