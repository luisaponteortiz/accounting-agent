"""Historical four-authority fixture for retained register tests.

The fixture is data only: it leaves the fifth (RF) pinned inputs out of the
checker's pin table and uses the register and derived-results bytes of the
delivered RF checkpoint, read from the immutable review bundle and checked
against their recorded hashes. No validation is stubbed, bypassed or
special-cased; the shipped checker always reads all five authorities.
"""
from contextlib import contextmanager
import hashlib
from pathlib import Path
from unittest.mock import patch
import zipfile

import scripts.check_product_requirements as cpr

ROOT=Path(__file__).resolve().parents[1]
BUNDLE='exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip'
FIFTH=('exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_RESULTS.json',
       'exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md')
CHECKPOINT={
    'docs/PRODUCT_REQUIREMENTS.md':'8a91c6ff07c512479b5c25d7b371164ed991998ec5e501401f5e1222349b680f',
    'docs/INDEPENDENT_VERIFICATION_RESULTS.json':'4371242db8cb93155e5fbfb8003efc66b8437e036a5a5f3665852d7eaff8d515',
}


def checkpoint_bytes(name):
    with zipfile.ZipFile(ROOT/BUNDLE) as bundle:raw=bundle.read(name)
    if hashlib.sha256(raw).hexdigest()!=CHECKPOINT[name]:raise ValueError('RF checkpoint fixture hash differs: '+name)
    return raw


@contextmanager
def rf_checkpoint(case,directory):
    """Yield (project copy, register text) as they stood when RE was the latest authority."""
    root=case.reviewer_fault_copy(directory)
    text=checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode()
    (root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json').write_bytes(checkpoint_bytes('docs/INDEPENDENT_VERIFICATION_RESULTS.json'))
    four={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in FIFTH}
    with patch.dict(cpr.REVIEW_INPUT_HASHES,four,clear=True):yield root,text
