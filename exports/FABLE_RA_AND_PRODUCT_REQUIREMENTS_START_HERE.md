# Start the combined Accounting Agent OS review

This outer ZIP is a transfer container for two reviews, not an executable project root. Start with FABLE_PRODUCT_AND_RA_REVIEW_PROMPT.md, which preserves the exact prompt supplied to Luis. Do not run the test commands from this outer directory.

## 1. Verify the delivery

The outer REVIEW_MANIFEST.json lists SHA-256 hashes for every payload file except the manifest itself. The adjacent .zip.sha256 supplied by Codex identifies the whole outer ZIP; its hash cannot be embedded inside itself. Reject duplicate/unsafe archive paths or any mismatch.

The nested FABLE_RA_CORRECTIONS_REVIEW_BUNDLE.zip must have SHA-256:

```text
dec028b06a745ba52ceca448c766893c33e863f98d5728aafd8b6edadb274e4f
```

This is the existing RA source/evidence checkpoint, included byte-for-byte. Its own REVIEW_MANIFEST.json remains unchanged. The older frozen RV submission inside that checkpoint must still have SHA-256 247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75.

## 2. Separate executable source from the documentation addendum

Extract the nested RA ZIP into a new disposable directory, such as ra_checkpoint/. That directory, containing Makefile and accounting_agent/, is the project root for all commands in the prompt. Its FABLE_RA_REVIEW_PROMPT.md contains the detailed corrective verification assignment. Do not run a nested historical checkpoint as the current RA source.

In the exact combined prompt, “the ZIP” and “inside the bundle” refer to this nested RA checkpoint. “Separately attached” updated documents are provided together under documentation_addendum/ in this transfer container. This packaging convention avoids changing the already supplied prompt.

The addendum contains seven current project documents with their repository paths preserved:

- AGENTS.md
- DECISIONS.md
- PROGRESS.md
- README.md
- FABLE_ACCOUNTING_HANDOFF.md
- docs/PRODUCT_REQUIREMENTS.md
- docs/CONNECTION_READINESS.md

Use these as the current documentation for the product-register review; the new register did not exist in the RA checkpoint. Do not copy them over the extracted checkpoint or claim they were covered by its old manifest. Runtime source, tests and earlier execution logs stay those of the unchanged RA checkpoint. Subsequent documentation and packaging checks do not constitute new runtime test results or independent acceptance.

The register's relative source links refer to repository paths: original review/source/evidence files are in ra_checkpoint/, updated documents are in documentation_addendum/, and original implementation-package references are in reference_material/ss_agent_system_handoff/. The reference-material directory contains all 16 original handoff files byte-for-byte, including the Bird Bowl pilot and accounting-relevant build/backlog/acceptance specifications that were absent from the earlier RA ZIP. Treat their broader executive/business-development scope and engineering proposals as historical reference, subject to current accounting-only instructions and decisions.

## 3. Preserve the existing review gates

Use temporary fictional databases. Run the commands from ra_checkpoint/ and keep new evidence/probes separate from supplied originals. All 76 requirements need a completeness/status review; future/deferred features are not required to exist today. Product approval is not implementation or operating authority.

The supplied logs report 154 tests and maintained gates passing; rerun them independently. The unmodified full acceptance script's statement-setup incompatibilities remain disclosed. Independently judge the additional acceptance setups and retain separate verdicts for RA controls, product-register quality and G0 technical criteria.

No source change, live connection, paid call/service, sending, accounting posting, payment, deployment, human G0 release or Batch 3 work is authorized by this transfer. Return the deliverables named in the exact prompt.
