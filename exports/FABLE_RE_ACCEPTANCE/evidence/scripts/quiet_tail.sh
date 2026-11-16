#!/bin/bash
# After every search and gate has finished: time the HTTP class setup on a quiet machine, then run make test alone.
cd /tmp/fre/out
until [ "$(grep -c '^experiment-step-search' _progress.txt)" -ge 4 ] && [ "$(grep -c '^step-search' _progress.txt)" -ge 5 ] && grep -q '^make-re-gate' _progress.txt; do sleep 15; done
sleep 20
( uptime; python3 /tmp/fre/tools/http_setup_timing.py /tmp/fre/rdbase 5; python3 /tmp/fre/tools/http_setup_timing.py /tmp/fre/extract 5; uptime ) > /tmp/fre/out/http-setup-timing.txt 2>&1
/tmp/fre/tools/run_cmd.sh make-test-rerun-alone /tmp/fre/run6 make test
( uptime; python3 /tmp/fre/tools/http_setup_timing.py /tmp/fre/rdbase 5; python3 /tmp/fre/tools/http_setup_timing.py /tmp/fre/extract 5 ) >> /tmp/fre/out/http-setup-timing.txt 2>&1
tail -3 _progress.txt; cat http-setup-timing.txt
