"""Compatibility entry point; original reviewer script preserved in review/original/."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[2]/"review"/'run_fable_validation_cases.py'),run_name="__main__")
