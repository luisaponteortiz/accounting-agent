# Fable C-01–C-06 corrective checkpoint

The seven failures were reproduced before source modification. See docs/corrections/baseline-probes.txt. Baseline suite: 72 run, 67 pass, 5 expected failures.

Implementation order: C-05, C-06, C-02, C-04, C-03, C-01, as prescribed. Core normalization keeps Unicode L/N/M categories; Actor.kind is mandatory; every decision is blocked under lock; authorship includes historical input/profile versions; append-only contributor records are separate from content identity; a moved locked-origin source is quarantined until reopen. Schema migrations 6–7 preserve existing artifact/evidence/decision bytes.

The exact supplied script, unmodified, now reports **N01–N07 OK** and **Corrective gate PASS**. Earlier required P01–P06/P09–P11/P14/P16/N11/N12/N13 remain OK. P07/P08/P12/P13/P15/N17 remain deferred at this checkpoint; N08/N09 await T-12. All four supplied input files remain unchanged.

Full corrective suite: **81 run, 76 pass, 5 expected Batch 2 failures**, no unexpected failures. New tests cover all locked decision types, Unicode marks, missing identity kind, historical authorship, displaced rejection, new contributor rights and the cross-period uniqueness invariant through lock/move/reopen. The independent 60-case runner remains 28 PASS / 6 FIXED / 4 KNOWN-FAIL / 22 DEFERRED-OK. make check passes.

Raw results: docs/corrections/final-probes.txt, final-tests.txt, final-check.txt and original-reviewer.txt. The corrective bundle is a frozen checkpoint for independent re-verification before later Batch 2 API/fixture changes. No live connection, posting, payment, paid service or deployment occurred.
