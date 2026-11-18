"""Re-run the supplied unmodified verifier on the frozen pre-Batch-2 checkpoint."""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(root/'exports/FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip') as z:
        for name in z.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Invalid archive member')
        z.extractall(tmp)
    script=Path(tmp)/'exports/FABLE_BATCH_1_VERIFICATION/batch1_verification_probes.py'
    print('FROZEN CORRECTIVE CHECKPOINT: original supplied script; not the later Batch 2 API.',flush=True)
    sys.exit(subprocess.call([sys.executable,str(script),tmp]))
