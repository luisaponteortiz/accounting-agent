"""Owner instruction of 17 November 2026 (D-037): modify the standing rule for the Independently verified state."""
import sys
from pathlib import Path
root=Path(sys.argv[1])
def once(t,old,new):
    assert t.count(old)==1,(old[:70],t.count(old));return t.replace(old,new)
# checker: negated statements are not claims that a record is failed
p=root/'scripts/check_documentation.py';t=p.read_text()
t=once(t,"        if not failed:require(STILL_FAILED.search(section) is None,","        if not failed:require(STILL_FAILED.search(NEGATED_FAILED.sub('',section)) is None,")
t=once(t,"STILL_FAILED=re.compile(r'(?:remain|remains|stay|stays|are|is) Verification failed')\n","STILL_FAILED=re.compile(r'(?:remain|remains|stay|stays|are|is) Verification failed')\nNEGATED_FAILED=re.compile(r'\\b(?:no|none|neither)\\b[^.;]{0,40}Verification failed',re.I)\n")
p.write_text(t)
RULE=('Only a recorded review may establish Independently verified for the specified source/scope: review tests or probes that are separate from the work\'s own unit tests, are shown able to fail, run on an identified checkpoint, and have a results file and report pinned in the checker. '
      'By owner decision D-037 the reviewer may be Fable (Claude) reviewing work Fable itself created, and the record\'s evidence must then say that the same author built the work and its review tests. Developer tests alone cannot establish it.')
p=root/'AGENTS.md';t=p.read_text()
t=once(t,'Only an independent review may establish Independently verified for the specified source/scope.',RULE)
t=once(t,'Until the owner decides otherwise, work that Fable both creates and tests is recorded as Developer-tested, not Independently verified (D-036).','The owner then changed the standing rule accordingly (D-037): review tests Fable builds may establish Independently verified for work Fable created, on the conditions in the standing rules below. No record has been raised on that basis yet.')
p.write_text(t)
p=root/'docs/PRODUCT_REQUIREMENTS.md';t=p.read_text()
t=once(t,'| Independently verified | An independent report names the exact checkpoint and verified scope; no broader gate is implied. |',
 '| Independently verified | A review report names the exact checkpoint and verified scope, from review tests separate from the work\'s own unit tests; no broader gate is implied. The reviewer is independent of the author or, under D-037, is Fable reviewing work it created, which the record\'s evidence must then state. |')
t=once(t,'Only an independent reviewer can establish independent verification.','Only a recorded review can establish the Independently verified state; under D-037 the reviewer may be Fable reviewing work it created, with that stated in the record. Developer tests alone cannot.')
t=once(t,'Only independent review can establish verification; a failed independent probe downgrades affected records in the same change.','Only a recorded review can establish verification (under D-037 the reviewer may be the author, Fable, when the record says so; developer tests alone cannot); a failed review probe downgrades affected records in the same change.')
last='| Owner decision D-036. |\n'
t=once(t,last,last+'\n| 2026-11-17 | By owner instruction, changed the rule for the Independently verified state: a recorded review with review tests establishes it, and the reviewer may be Fable reviewing work Fable created when the record says so. Changed the state definition, the maintenance paragraph and the matching sentence in the AAOS-GOV-02 acceptance criteria; no state, product decision or other criterion changed, and no record was raised on the new basis. Added executable documentation review checks (scripts/check_documentation.py, tests/test_documentation_review.py) to the T-08 crosswalk row. | Owner decision D-037; docs/documentation_review/. |\n')
t=once(t,'| T-08 | AAOS-GOV-02, AAOS-GOV-03 | Truthful capability documentation; maintained with this register. |','| T-08 | AAOS-GOV-02, AAOS-GOV-03 | Truthful capability documentation; maintained with this register. Executable documentation review checks compare the current documents with the code, the register and the readiness checklist (scripts/check_documentation.py, tests/test_documentation_review.py; D-037). |')
p.write_text(t)
# the registration test's invariant: GOV-02's criterion now differs by exactly that sentence
p=root/'tests/test_product_requirements_rf_registration.py';t=p.read_text()
t=once(t,"""            self.assertEqual(before[key]['Acceptance criteria'],after[key]['Acceptance criteria'],key)
""","""            if key!='AAOS-GOV-02':self.assertEqual(before[key]['Acceptance criteria'],after[key]['Acceptance criteria'],key)
""")
t=once(t,"""        self.assertEqual({field for field in cpr.FIELDS if before['AAOS-GOV-02'][field]!=after['AAOS-GOV-02'][field]},{'Scope note'})
""","""        self.assertEqual({field for field in cpr.FIELDS if before['AAOS-GOV-02'][field]!=after['AAOS-GOV-02'][field]},{'Scope note','Acceptance criteria'})
        # Owner decision D-037 changed one sentence of this criterion and nothing else in it.
        old_rule='Only independent review can establish verification; a failed independent probe downgrades affected records in the same change.'
        new_rule='Only a recorded review can establish verification (under D-037 the reviewer may be the author, Fable, when the record says so; developer tests alone cannot); a failed review probe downgrades affected records in the same change.'
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].replace(old_rule,new_rule),after['AAOS-GOV-02']['Acceptance criteria'])
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].count(old_rule),1)
""")
p.write_text(t)
print('ok')
