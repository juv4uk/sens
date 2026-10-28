"""Register independent C11 T09 tests with existing research CI discovery."""
import importlib.util
from pathlib import Path
import sys

_test_file = Path(__file__).resolve().parent / "corpus" / "c" / "test_t09_popcount.py"
_spec = importlib.util.spec_from_file_location("test_t09_popcount", _test_file)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
CPopcountParity = _module.CPopcountParity
