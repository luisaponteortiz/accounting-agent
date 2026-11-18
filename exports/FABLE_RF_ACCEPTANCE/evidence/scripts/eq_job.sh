#!/bin/bash
R=/private/tmp/claude-501/rf; L="$1"; shift
$R/tools/run_cmd.sh "$L" $R/dev python3 $R/scripts/fable_rf_equivalence.py . "$@"
