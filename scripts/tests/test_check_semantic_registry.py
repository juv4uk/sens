import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "check_semantic_registry.py"
SPEC = importlib.util.spec_from_file_location("check_semantic_registry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HeaderlessRegistryTests(unittest.TestCase):
    def test_canonical_rows_are_valid_without_legacy_binary_header(self):
        source = (Path(__file__).resolve().parents[2] / "lib" / "surface" / "semantic-registry.lisp").read_text(encoding="utf-8")
        registry = MODULE.parse_all(MODULE.tokens(source))[0]
        self.assertEqual(MODULE.check(registry[1:])[0], 170)


if __name__ == "__main__":
    unittest.main()
