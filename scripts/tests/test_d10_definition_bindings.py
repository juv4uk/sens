import importlib.util
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_migration_module():
    path = SCRIPTS / "migrate-three-pass.py"
    spec = importlib.util.spec_from_file_location("migrate_three_pass_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class D10DefinitionBindingTests(unittest.TestCase):
    def test_generated_bindings_are_only_concrete_d10_library_definitions(self):
        migration = load_migration_module()
        expected = set(migration.core4_d10_defined_rows())
        source = (ROOT / "crates/sens/src/d10_definition_bindings_generated.rs").read_text()
        actual = set(re.findall(r"D10DefinitionBinding \{ bits: 0b([01]{10}),", source))

        self.assertEqual(actual, expected)
        self.assertIn("0100001100", actual)  # LISTP
        self.assertIn("0011010111", actual)  # MKLIST
        self.assertIn("0010011001", actual)  # SOURCE-REF? has a Lisp definition
        self.assertNotIn("0000000000", actual)  # codebook row, no concrete definition


if __name__ == "__main__":
    unittest.main()
