Evidence for the Fable RD/PRV review, 16 November 2026. Reviewed bundle SHA-256 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9.

commands/                       the fourteen required commands, unmodified, on a clean extraction: raw stdout, stderr, exit-codes.txt
baseline/                       the two RC scripts, unmodified, on a clean extraction of the RC baseline (9a85c78a...): both exit 1
baseline-rc-source-rd-probes.txt  my RD probes on the RC baseline source (they fail there, so they discriminate)
order-search-extended-rd-source.* my extended search (336 orders) on this bundle
order-search-gate-rd-source.*   the gate search (120 orders) with --json, used as input for fable-rd-gate-faults.txt
fable-rc-register-faults-on-rd.txt  the supplied fault script, unmodified, on a second disposable copy
fable-rd-register-faults.txt    my PRV-12/PRV-13 fault cases (H01 to H39) on a third disposable copy
fable-rd-gate-faults.txt        my fault cases for the make rd-gate validators
rd-gate-negative-control.txt    make rd-gate with the two application files reverted to the baseline
integrity.txt, diff-vs-rc-baseline.json  archive, manifest and baseline comparison
preservation.txt, test-inventory.txt, register-diff.txt, inventory-and-states.txt  preservation checks
experimental-correction-re.patch, experiment/  RE-01 and RE-02 tried in a temporary copy; not a delivered fix
extra-exit-codes.txt            exit codes of my additional runs, in the order they were made (earlier lines predate probe Y06)
scripts/                        the scripts that produced the files above
versions.txt                    environment

Paths beginning /private/tmp/... in the logs are the session scratch directory that held the disposable copies.
The probe scripts of this review are one level up: fable_rd_acceptance_probes.py and fable_rd_order_search.py.
