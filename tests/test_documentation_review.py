"""Review tests for the documentation: each check passes on the project and refuses an injected fault.

Built under owner decision D-037. The faults are made in copies of the document
texts; no project file is written.
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

import scripts.check_documentation as cd

ROOT=Path(__file__).resolve().parents[1]


class DocumentationReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.docs=cd.load(ROOT)

    def changed(self,name,old,new,count=1):
        text=self.docs[name]
        self.assertEqual(text.count(old),count,(name,old))
        return dict(self.docs,**{name:text.replace(old,new)})

    def changed_current(self,name,transform):
        """Apply a change inside the current-state section of one document only."""
        text=self.docs[name];section=cd.current_section(name,text)
        self.assertEqual(text.count(section),1,name)
        altered=transform(section)
        self.assertNotEqual(altered,section,name)
        return dict(self.docs,**{name:text.replace(section,altered)})

    def refused(self,check,docs,message):
        with self.assertRaisesRegex(ValueError,message):check(docs,ROOT)

    def test_current_documents_pass_every_check(self):
        result=cd.validate_documentation(ROOT)
        self.assertEqual(result['test_methods'],cd.test_method_count(ROOT))
        self.assertEqual(result['current_documents'],len(cd.CURRENT_DOCUMENTS))
        self.assertGreater(result['links_checked'],100)
        self.assertEqual(result['capabilities_named'],12)
        self.assertEqual((result['records'],result['verification_failed']),(88,0))

    def test_stated_test_count_must_equal_the_suite(self):
        actual=cd.test_method_count(ROOT)
        # The counter agrees with what the test loader finds, so it is not a number chosen to match the documents.
        loaded=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
        def count(suite):return sum(count(item) if isinstance(item,unittest.TestSuite) else 1 for item in suite)
        self.assertEqual(actual,count(loaded))
        for name,pattern in cd.TEST_COUNT_STATEMENTS.items():
            statement=re.search(pattern,self.docs[name])[0]
            with self.subTest(name=name):
                for wrong in (actual-1,actual+1):
                    self.refused(cd.check_test_count,self.changed(name,statement,statement.replace(str(actual),str(wrong))),'stated test count')
                self.refused(cd.check_test_count,self.changed(name,statement,'The suite has many test methods'),'test count statement missing')

    def test_readme_gates_must_match_the_makefile(self):
        _,gates=cd.makefile_targets(ROOT)
        self.assertEqual(gates,['batch2-gate','reverification-gate','acceptance-gate','rb-gate','rc-gate','rd-gate','re-gate','rf-gate'])
        for gate in gates:
            with self.subTest(gate=gate):
                self.refused(cd.check_gates,self.changed('README.md','make '+gate+'\n',''),'Makefile gate targets not listed: '+gate)
        self.refused(cd.check_gates,self.changed('README.md','make rf-gate\n','make rf-gate\nmake rg-gate\n'),'lists make targets the Makefile does not have: rg-gate')

    def test_code_names_routes_and_identifiers_must_exist_in_the_code(self):
        architecture='docs/ARCHITECTURE.md'
        renamed=dict(self.docs,**{architecture:self.docs[architecture].replace('SOURCE_CLAIM_DECLARED','SOURCE_CLAIM_ANNOUNCED')})
        self.refused(cd.check_code_names,renamed,'code names not found in accounting_agent/: SOURCE_CLAIM_ANNOUNCED')
        self.refused(cd.check_code_names,self.changed(architecture,'POST /api/dispositions','POST /api/target-selections'),'HTTP routes not found in accounting_agent/: /api/target-selections')
        self.refused(cd.check_code_names,self.changed(architecture,'`select_supersession_target`','`select_replacement_target`'),'identifiers not found in accounting_agent/: select_replacement_target')
        self.refused(cd.check_code_names,self.changed('docs/CAPABILITY_CONTRACTS.md','`select_supersession_target`','`choose_supersession_target`'),'identifiers not found')
        self.refused(cd.check_code_names,self.changed('README.md','## Implemented and unconnected','## Implemented and unconnected\n\nBlocked items carry SOURCE_FEED_PAUSED.'),'README.md: code names not found')
        # File names written in capitals are not mistaken for code names.
        cd.check_code_names(self.changed('README.md','## Implemented and unconnected','## Implemented and unconnected\n\nSee FABLE_RF_REVIEW_PROMPT.md and docs/PRODUCT_REQUIREMENTS.md.'),ROOT)

    def test_every_feed_contract_code_in_the_source_must_be_described(self):
        architecture='docs/ARCHITECTURE.md'
        for code in cd.check_code_names(self.docs,ROOT):
            with self.subTest(code=code):
                self.assertTrue(cd.names(self.docs[architecture],code))
                # The longer names contain the shorter one, so remove the exact token only.
                removed=re.sub(r'(?<![A-Za-z_])'+re.escape(code)+r'(?![A-Za-z_])','an event',self.docs[architecture])
                self.refused(cd.check_code_names,dict(self.docs,**{architecture:removed}),'feed-contract codes not described: .*'+code)

    def test_capability_status_must_match_the_registry(self):
        contracts='docs/CAPABILITY_CONTRACTS.md'
        self.refused(cd.check_capabilities,self.changed(contracts,'`banking.match_transfer_reconcile` is deferred','`banking.match_transfer_reconcile` executes'),'banking.match_transfer_reconcile is deferred in the registry')
        self.refused(cd.check_capabilities,self.changed(contracts,'`banking.card_prepare` executes the limited fictional card workflow','`banking.card_prepare` is deferred'),'banking.card_prepare is fixture-demonstrated in the registry')
        self.refused(cd.check_capabilities,self.changed(contracts,'`evidence.inventory`','the inventory step'),'registered capability not named: evidence.inventory')
        self.refused(cd.check_capabilities,dict(self.docs,**{contracts:self.docs[contracts].replace('gl.post','gl.posting')}),'registered capability not named: gl.post')

    def test_human_g0_status_must_agree_with_the_readiness_checklist(self):
        for name in cd.CURRENT_DOCUMENTS:
            with self.subTest(name=name,fault='denied'):
                denied=self.changed_current(name,lambda section:cd.ACCEPTED_G0.sub('Human G0 has not been accepted',section))
                self.refused(cd.check_status,denied,re.escape(name)+': current section')
            with self.subTest(name=name,fault='contradicted'):
                both=self.changed_current(name,lambda section:section+'\nHuman G0 has not been accepted.\n')
                self.refused(cd.check_status,both,re.escape(name)+': current section says human G0 is not accepted')
        # With the checklist box cleared, every acceptance statement becomes an unsupported claim.
        unticked=self.changed('docs/CONNECTION_READINESS.md','- [x] Human G0 acceptance','- [ ] Human G0 acceptance')
        self.refused(cd.check_status,unticked,'claims human G0 acceptance that the readiness checklist does not record')
        self.refused(cd.check_status,self.changed('docs/CONNECTION_READINESS.md','- [x] Human G0 acceptance','- [x] Human acceptance'),'one Human G0 acceptance checkbox required')

    def test_current_sections_name_the_latest_review_and_carry_no_stale_status(self):
        self.assertEqual(cd.latest_review_label(ROOT),'RF')
        for name in cd.CURRENT_DOCUMENTS:
            with self.subTest(name=name,fault='older review'):
                older=self.changed_current(name,lambda section:section.replace('RF review','RE review'))
                self.refused(cd.check_status,older,re.escape(name)+': current section does not name the latest registered review')
            for fault,sentence,message in (('pending','\nIndependent verification remains pending.\n','stale pending-verification statement'),
                                           ('awaiting','\nThe corrections await independent review.\n','stale pending-verification statement'),
                                           ('failed','\nThree requirements remain Verification failed.\n','says a requirement is Verification failed')):
                with self.subTest(name=name,fault=fault):
                    self.refused(cd.check_status,self.changed_current(name,lambda section:section+sentence),re.escape(name)+': current section.*'+message)
        # A statement that none is failed is not a claim that one is.
        cd.check_status(self.changed_current('README.md',lambda section:section+'\nNo requirement is Verification failed.\n'),ROOT)

    def test_register_figures_in_the_readme_and_header_must_match_the_register(self):
        self.refused(cd.check_status,self.changed('README.md','register has 88 retained records','register has 87 retained records'),'stated register size differs')
        self.refused(cd.check_status,self.changed('README.md','seven Independently verified records and none Verification failed','six Independently verified records and none Verification failed'),'stated verified/failed counts differ')
        self.refused(cd.check_status,self.changed('README.md','seven Independently verified records and none Verification failed','seven Independently verified records and one Verification failed'),'stated verified/failed counts differ')
        self.refused(cd.check_status,self.changed('docs/PRODUCT_REQUIREMENTS.md','**88 retained requirements**','**89 retained requirements**'),'header count differs')
        # A record that really is failed must be reflected: the README then disagrees with the register.
        register=self.docs['docs/PRODUCT_REQUIREMENTS.md'];start=register.index('### AAOS-GOV-01 —')
        failed=register[:start]+register[start:].replace('- **Implementation state:** Not started','- **Implementation state:** Verification failed',1)
        self.refused(cd.check_status,dict(self.docs,**{'docs/PRODUCT_REQUIREMENTS.md':failed}),'stated verified/failed counts differ')

    def test_links_and_decision_references_must_resolve(self):
        self.refused(cd.check_links,self.changed('README.md','## Run locally','See [a missing page](docs/NOT_WRITTEN.md).\n\n## Run locally'),'README.md: link target does not exist: docs/NOT_WRITTEN.md')
        self.refused(cd.check_links,self.changed('HANDOFF_RF_REGISTRATION_2026-11-17.md','(docs/registration_rf/RF_REGISTRATION_REPORT.md)','(docs/registration_rf/RF_REGISTRATION.md)'),'link target does not exist')
        cd.check_links(self.changed('README.md','## Run locally','See [the site](https://example.invalid/page) and [this section](#run-locally).\n\n## Run locally'),ROOT)
        latest=max(int(identifier[2:]) for identifier in re.findall(r'(?m)^(?:## |- \*\*)(D-\d{3})\b',self.docs['DECISIONS.md']))
        unknown='D-%03d'%(latest+1)
        for name in ('AGENTS.md','README.md','docs/PRODUCT_REQUIREMENTS.md'):
            with self.subTest(name=name):
                self.refused(cd.check_decisions,dict(self.docs,**{name:self.docs[name]+'\nSee '+unknown+'.\n'}),re.escape(name)+': cites decisions that DECISIONS.md does not record: '+unknown)
        decisions=self.docs['DECISIONS.md']
        self.refused(cd.check_decisions,dict(self.docs,**{'DECISIONS.md':decisions+'\n## D-%03d — A skipped number\n'%(latest+2)}),'not continuous')
        self.refused(cd.check_decisions,dict(self.docs,**{'DECISIONS.md':decisions+'\n## D-%03d — A repeated number\n'%latest}),'duplicate decision identifier')

    def test_verification_rule_is_stated_consistently_and_cites_its_decision(self):
        self.assertEqual(cd.check_verification_rule(self.docs,ROOT),'D-037')
        agents=self.docs['AGENTS.md'];rules=agents[agents.index('## Standing project rules'):]
        self.refused(cd.check_verification_rule,dict(self.docs,**{'AGENTS.md':agents.replace(rules,rules.replace('D-037','an owner decision'))}),'AGENTS.md: the standing rule does not cite D-037')
        self.refused(cd.check_verification_rule,dict(self.docs,**{'AGENTS.md':agents.replace(rules,rules.replace('Only a recorded review may establish Independently verified','Only a recorded review may confer the verified state'))}),'one standing rule for the Independently verified state required')
        register=self.docs['docs/PRODUCT_REQUIREMENTS.md'];row=re.search(r'(?m)^\| Independently verified \|[^\n]*',register)[0]
        self.refused(cd.check_verification_rule,self.changed('docs/PRODUCT_REQUIREMENTS.md',row,row.replace('D-037','an owner decision')),'state definition does not cite D-037')
        criterion='Only a recorded review can establish verification (under D-037 the reviewer may be the author, Fable, when the record says so; developer tests alone cannot)'
        self.refused(cd.check_verification_rule,self.changed('docs/PRODUCT_REQUIREMENTS.md',criterion,'Only a recorded review can establish verification'),'AAOS-GOV-02 does not cite D-037')
        for name,wording in (('AGENTS.md','Only an independent review may establish Independently verified for the specified source/scope.'),
                             ('docs/PRODUCT_REQUIREMENTS.md','Only an independent reviewer can establish independent verification.'),
                             ('docs/PRODUCT_REQUIREMENTS.md','Only independent review can establish verification.')):
            with self.subTest(wording=wording):
                self.refused(cd.check_verification_rule,dict(self.docs,**{name:wording+'\n\n'+self.docs[name]}),'superseded verification rule wording remains')

    def test_checker_runs_as_a_script_and_reports_the_same_facts(self):
        result=subprocess.run([sys.executable,'scripts/check_documentation.py'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertRegex(result.stdout,r'^PASS: documentation review — %d current documents'%len(cd.CURRENT_DOCUMENTS))
        facts=subprocess.run([sys.executable,'scripts/check_documentation.py','--json'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(facts.returncode,0,facts.stderr)
        import json
        self.assertEqual(json.loads(facts.stdout),cd.validate_documentation(ROOT))
