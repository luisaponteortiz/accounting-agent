"""Maintained assertion-based P01-P16 probes; original diagnostics in original/."""
import sys
import unittest
sys.path.insert(0,sys.argv[1])
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_reviewer_probes.ReviewerProbes')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
