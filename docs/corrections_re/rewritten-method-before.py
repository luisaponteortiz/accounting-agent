    def test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced(self):
        f = self.f
        o = f.approved_locked_november()
        o.intake(f.PREP2, f.packet('first', [f.sup('Y', '2026-12-03', '40.00', 'X')]))
        o.intake(f.PREP2, f.packet('new-target', [f.sup('Y', '2026-12-03', '41.00', 'W')]))
        o.intake(f.PREP2, f.packet('old-target-arrives', [f.tx('X', '2026-12-02', '40.00')]))
        with o.store.connect() as db:
            head = db.execute('SELECT snapshot_id FROM source_heads WHERE source_key=?', (f.CARD+':Y',)).fetchone()[0]
            self.assertIsNone(o.supersession_link(db, f.SCOPE, head))
        o.intake(f.PREP2, f.packet('new-target-arrives', [f.sup('W', '2026-12-02', '40.00', 'A1')]))
        self.prepare(o)
        self.held(o, f.CARD+':Y')
        before = self.lifecycle(o)
        o.intake(f.PREP2, f.packet('unrelated', [f.tx('D1', '2026-12-05', '15.00')]))
        after = self.lifecycle(o)
        for table in ('links', 'moves', 'events'):
            self.assertEqual(before[table], after[table])
