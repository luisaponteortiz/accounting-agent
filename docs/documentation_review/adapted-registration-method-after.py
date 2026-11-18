    def test_three_recorded_scopes_cite_the_fifth_checkpoint_and_nothing_else_moved(self):
        before=cpr.parse_register(fixture.checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode());after=cpr.parse_register(self.text)
        self.assertEqual(list(before),list(after))
        changed={key for key in before if before[key]!=after[key]}
        self.assertEqual(changed,set(RECORDED)|{'AAOS-GOV-02'})
        for key in before:
            self.assertEqual(before[key]['Product decision'],after[key]['Product decision'],key)
            if key!='AAOS-GOV-02':self.assertEqual(before[key]['Acceptance criteria'],after[key]['Acceptance criteria'],key)
            if key not in RECORDED:self.assertEqual(before[key]['Implementation state'],after[key]['Implementation state'],key)
        self.assertEqual({field for field in cpr.FIELDS if before['AAOS-GOV-02'][field]!=after['AAOS-GOV-02'][field]},{'Scope note','Acceptance criteria'})
        # Owner decision D-037 changed one sentence of this criterion and nothing else in it.
        old_rule='Only independent review can establish verification; a failed independent probe downgrades affected records in the same change.'
        new_rule='Only a recorded review can establish verification (under D-037 the reviewer may be the author, Fable, when the record says so; developer tests alone cannot); a failed review probe downgrades affected records in the same change.'
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].replace(old_rule,new_rule),after['AAOS-GOV-02']['Acceptance criteria'])
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].count(old_rule),1)
        for key in RECORDED:
            with self.subTest(key=key):
                self.assertEqual(before[key]['Implementation state'],'Verification failed')
                self.assertEqual(after[key]['Implementation state'],'Independently verified')
                self.assertEqual({field for field in cpr.FIELDS if before[key][field]!=after[key][field]},{'Implementation state','Scope note','Evidence'})
                self.assertIn(RF_BUNDLE,after[key]['Evidence']);self.assertIn(REPORT,after[key]['Evidence'])
                self.assertIn(RF_BUNDLE,after[key]['Scope note'])
                # The earlier review failed this record: citing it alone cannot carry the verified state.
                stale=self.changed_field(key,'Evidence','independent review '+RE_BUNDLE+' '+RE_REPORT+' tests/test_product_requirements_rf.py')
                with self.assertRaisesRegex(ValueError,'independent review entry/checkpoint differs from evidence'):cpr.validate_register(stale,ROOT)

