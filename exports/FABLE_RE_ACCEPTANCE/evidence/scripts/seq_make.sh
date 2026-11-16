#!/bin/bash
R=/tmp/fre/tools/run_cmd.sh; C=/tmp/fre/run2
for t in test check batch2-gate reverification-gate acceptance-gate rb-gate rc-gate rd-gate re-gate; do $R make-$t $C make $t; done
