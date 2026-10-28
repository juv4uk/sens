"""Expose isolated SENS native measurement mechanics tests to the existing research CI.

The research-tools job already discovers test_*.py in this directory.
This import does not test or define SENS semantics.
"""
from pathlib import Path
import sys

_sens_tests = Path(__file__).resolve().parent / "corpus" / "sens"
if str(_sens_tests) not in sys.path:
    sys.path.insert(0, str(_sens_tests))

from test_measure_verified import NativeRunnerTest, TimeParserTest  # noqa: E402,F401
