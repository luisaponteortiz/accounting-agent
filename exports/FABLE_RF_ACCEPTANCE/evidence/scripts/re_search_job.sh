#!/bin/bash
R=/private/tmp/claude-501/rf; F="$1"
$R/tools/run_cmd.sh "re-step-search-$F" $R/run1 python3 exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py . --family "$F" --json "$R/out/re-step-search-$F.results.json"
