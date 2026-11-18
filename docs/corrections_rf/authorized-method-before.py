    def test_PRV14_third_authority_is_pinned_and_latest_verdict_controls(self):
        import hashlib,json
        from unittest.mock import patch
        import scripts.check_product_requirements as cpr
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;original=path.read_bytes()
            path.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):validate_register(self.text,root)
            data=json.loads(original)
            for row in data['register_verdicts']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            changed=json.dumps(data).encode();path.write_bytes(changed)
            result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
            for row in results['results']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            result_path.write_text(json.dumps(results))
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
                validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
