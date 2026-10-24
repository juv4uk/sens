#!/usr/bin/env python3
"""Негативні D2/Lisp DATA_ONLY тести механічного контролю."""
import importlib.util
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "classifier", root / "scripts/check-single-data-schema.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

schema = "machine-profile-1"
# Голки без суцільних SENS-голів у host-тексті (host_debt).
def _h(*p):
    return "".join(p)

cases = {
    "(machine-profile-1 (cpu x))": True,
    '; вступ\n(machine-profile-1 (cpu " ) ; у рядку")) ; кінець': True,
    "(machine-profile-1 (cpu x))\n(" + "визначити" + " небажане так)": False,
    "(" + "визначити" + " небажане так)\n(machine-profile-1 (cpu x))": False,
    "(not-machine-profile-1 (cpu x))": False,
    "(machine-profile-1 (cpu x)": False,
    '(machine-profile-1 (cpu "open))': False,
    "(machine-profile-1 (cpu x)) )": False,
    "(machine-profile-1 (cpu x)) #;(" + "визначити" + " небажане так)": False,
    "#;(" + "визначити" + " небажане так) (machine-profile-1 (cpu x))": False,
    "(machine-profile-1 (cpu x)) ; (" + "визначити" + " коментар так)": True,
    "(machine-profile-1)\n; після": True,
    "(machine-profile-1)(machine-profile-1)": False,
    "(machine-profile-1 (cpu x))\x00": False,
}
for source, expected in cases.items():
    actual = module.is_single_data_schema(source, schema)
    assert actual == expected, (source, actual, expected)

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "x.lisp"
    path.write_text("(machine-profile-1)", encoding="utf-8")
    assert module.main(["tool", schema, str(path)]) == 0
    (Path(td) / "link.lisp").symlink_to(path)
    assert module.main(["tool", schema, str(Path(td) / "link.lisp")]) == 1
    assert module.main(["tool", "unknown", str(path)]) == 2

for path, wanted in (
    ("knowledge/silent-fallback-inventory.lisp", "silent-fallback-inventory"),
    ("lib/surface/uk-sa-coverage.lisp", "uk-sa-coverage"),
    ("lib/machine/intel-core-i5-6400.lisp", "machine-profile-1"),
    ("lib/machine/profile/current-domain-x86-64.lisp", "machine-domain-profile-3"),
):
    assert module.main(["tool", wanted, str(root / path)]) == 0, path
assert module.main(["tool", "ft-2", str(root / "lib/generated/function-table.lisp")]) == 1
print("SENS_DATA_SCHEMA_GUARD_PASS cases=22")
