#!/bin/bash
R=/private/tmp/claude-501/rf; X=$R/tools/run_cmd.sh
$X rb-register-faults-F $R/run3 python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
$X rc-register-faults-G $R/run4 python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py $R/run4
$X rd-register-faults-H $R/run5 python3 exports/FABLE_RD_ACCEPTANCE/evidence/scripts/fable_rd_register_faults.py $R/run5
$X re-register-faults-J $R/run7 python3 exports/FABLE_RE_ACCEPTANCE/evidence/scripts/fable_re_register_faults.py $R/run7
