"""D10 CHANGE-CLASS historical-law and adversarial admission tests."""
import copy
import json
import unittest
from pathlib import Path
from scripts.check_d10_change_class_selected_v1 import (
    ROOT, MANIFEST, INVENTORY, STATE, FOUNDATION, DONOR, LEDGER, HISTORY,
    ContractError, audit,
)

class ChangeClassSelectionReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory_bytes = (ROOT / INVENTORY).read_bytes()
        cls.source = (
            json.loads((ROOT / MANIFEST).read_text(encoding="utf-8")),
            json.loads(cls.inventory_bytes.decode("utf-8")),
            json.loads((ROOT / STATE).read_text(encoding="utf-8")),
            json.loads((ROOT / FOUNDATION).read_text(encoding="utf-8")),
            json.loads((ROOT / DONOR).read_text(encoding="utf-8")),
            (ROOT / LEDGER).read_text(encoding="utf-8"),
            json.loads((ROOT / HISTORY).read_text(encoding="utf-8")),
            cls.inventory_bytes,
        )

    def test_pinned_selection_accounting_and_provenance(self):
        result = audit(*self.source)
        self.assertEqual(result["selected"], 648)
        self.assertEqual(result["ratified"], 0)

    def test_coordinate_and_ratification_mutations_fail_closed(self):
        for field, value in (("coordinate", "0000000000"), ("ratified_resident", True)):
            data = list(self.source)
            data[1] = copy.deepcopy(data[1])
            row = next(r for r in data[1]["rows"] if r["semantic_name"] == "CHANGE-CLASS")
            row[field] = value
            with self.subTest(field=field), self.assertRaises(ContractError):
                audit(*data)

    def test_exact_lower_duplicate_is_rejected(self):
        data = list(self.source)
        data[1] = copy.deepcopy(data[1])
        row = next(r for r in data[1]["rows"] if r["semantic_name"] == "CHANGE-CLASS")
        row["semantic_name"] = "CONS"
        with self.assertRaises(ContractError):
            audit(*data)

    def test_dossier_cannot_self_admit(self):
        data = list(self.source)
        data[4] = copy.deepcopy(data[4])
        row = next(r for r in data[4]["rows"] if r["proposal_id"] == "CLOS-03")
        row["selected_in_d10"] = True
        with self.assertRaises(ContractError):
            audit(*data)

    def test_transition_must_remain_unplaced_and_unratified(self):
        data = list(self.source)
        data[6] = copy.deepcopy(data[6])
        data[6]["transitions"][-1]["coordinates_added"] = 1
        with self.assertRaises(ContractError):
            audit(*data)

if __name__ == "__main__":
    unittest.main()
