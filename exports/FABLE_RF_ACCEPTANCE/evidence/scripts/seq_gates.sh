#!/bin/bash
R=/private/tmp/claude-501/rf; X=$R/tools/run_cmd.sh; C=$R/run2
for t in check batch2-gate reverification-gate acceptance-gate rb-gate rc-gate rd-gate re-gate rf-gate; do $X make-$t $C make $t; done
