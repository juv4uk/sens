"""D10 symbolic AI research: finite ground-term least general generalization.

Reference semantics: Plotkin's first-order anti-unification and SWI-Prolog
term_subsumer/3. NOT a SENS runtime function, ratification, or machine opcode.
"""
import itertools
import json
import unittest
from pathlib import Path


def validate(term):
    if isinstance(term, str) and term:
        return
    if (isinstance(term, list) and len(term) >= 2
            and isinstance(term[0], str) and term[0]):
        for child in term[1:]:
            validate(child)
        return
    raise ValueError("Expected nonempty ground atom or compound [functor,arg,...]")


def freeze(term):
    return ("atom", term) if isinstance(term, str) else (
        "compound", term[0], tuple(freeze(v) for v in term[1:])
    )


def anti_unify(left, right):
    """Memoized Plotkin-style syntactic LGG plus two instance substitutions."""
    validate(left)
    validate(right)
    memo = {}
    left_sub, right_sub = {}, {}

    def visit(a, b):
        if a == b:
            return a
        if (isinstance(a, list) and isinstance(b, list)
                and len(a) == len(b) and a[0] == b[0]):
            return [a[0]] + [visit(x, y) for x, y in zip(a[1:], b[1:])]
        pair = freeze(a), freeze(b)
        if pair not in memo:
            idx = len(memo)
            memo[pair] = idx
            left_sub[idx] = a
            right_sub[idx] = b
        return {"var": memo[pair]}

    return visit(left, right), left_sub, right_sub


def instantiate(term, substitutions):
    if isinstance(term, dict):
        return substitutions[term["var"]]
    if isinstance(term, str):
        return term
    return [term[0]] + [instantiate(c, substitutions) for c in term[1:]]


def subsumes(pattern, target):
    """Independent matching: only variables in generic pattern may be bound."""
    substitutions = {}

    def visit(generic, specific):
        if isinstance(generic, dict):
            key = generic["var"]
            if key in substitutions:
                return substitutions[key] == specific
            substitutions[key] = specific
            return True
        if isinstance(generic, str):
            return generic == specific
        if (not isinstance(specific, list) or len(generic) != len(specific)
                or generic[0] != specific[0]):
            return False
        return all(visit(a, b) for a, b in zip(generic[1:], specific[1:]))

    return visit(pattern, target)


class D10FirstOrderAntiunificationResearch(unittest.TestCase):
    def test_source_examples_and_shared_variables(self):
        v0, v1 = {"var": 0}, {"var": 1}
        cases = [
            (["f", "a", "a"], ["f", "b", "b"], ["f", v0, v0]),
            (["f", "a", "b"], ["f", "b", "a"], ["f", v0, v1]),
            (["f", "a", ["g", "a"]], ["f", "b", ["g", "b"]],
             ["f", v0, ["g", v0]]),
            (["f", "a"], ["g", "a"], v0),
            (["f", "a"], ["f", "a"], ["f", "a"]),
            ("a", "b", v0),
            ("a", "a", "a"),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                general, a_sub, b_sub = anti_unify(left, right)
                self.assertEqual(general, expected)
                self.assertEqual(instantiate(general, a_sub), left)
                self.assertEqual(instantiate(general, b_sub), right)

    def test_all_bounded_term_pairs_instance_and_canonical_naming(self):
        atoms = ["a", "b", "c"]
        words = atoms + [["f", x] for x in atoms]
        words += [["g", x, y] for x in atoms for y in atoms]
        checked = 0
        for left, right in itertools.product(words, repeat=2):
            general, a_sub, b_sub = anti_unify(left, right)
            self.assertEqual(instantiate(general, a_sub), left)
            self.assertEqual(instantiate(general, b_sub), right)
            self.assertTrue(subsumes(general, left))
            self.assertTrue(subsumes(general, right))
            swapped, _, _ = anti_unify(right, left)
            self.assertEqual(general, swapped)
            checked += 1
        self.assertEqual(checked, 225)

    def test_finite_independent_generality_order_oracle(self):
        """Enumerate rival generalizations; each must subsume the computed LGG."""
        v0, v1 = {"var": 0}, {"var": 1}
        choices = ["a", "b", v0, v1]
        rivals = choices[:]
        rivals += [["f", x] for x in choices]
        rivals += [["g", x, y] for x in choices for y in choices]
        cases = [
            (["g", "a", "a"], ["g", "b", "b"]),
            (["g", "a", "b"], ["g", "b", "a"]),
            (["g", "a", "a"], ["g", "a", "b"]),
            (["f", "a"], ["f", "b"]),
            (["g", "a", "b"], ["f", "a"]),
        ]
        evidence = 0
        for a, b in cases:
            lgg, _, _ = anti_unify(a, b)
            for candidate in rivals:
                if subsumes(candidate, a) and subsumes(candidate, b):
                    self.assertTrue(
                        subsumes(candidate, lgg),
                        f"not least: candidate={candidate}, lgg={lgg}, a={a}, b={b}"
                    )
                    evidence += 1
        self.assertGreaterEqual(evidence, 5)

    def test_negative_mutations(self):
        good = anti_unify(["g", "a", "a"], ["g", "b", "b"])[0]
        self.assertNotEqual(good, ["g", {"var": 0}, {"var": 1}])
        bad = ["g", {"var": 0}, {"var": 0}]
        self.assertFalse(subsumes(bad, ["g", "a", "b"]))
        self.assertFalse(subsumes(["f", {"var": 0}], ["g", "a"]))
        for malformed in (None, 1, [], ["f"], ["f", None], {"var": 0}):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    anti_unify(malformed, "a")

    def test_research_is_not_core_or_machine_authority(self):
        path = Path(__file__).resolve().parents[1] / "knowledge" / "d10-symbolic-ai-antiunification-20261009.json"
        j = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(j["status"], "RESEARCH-HOLD-CORE-VS-LIBRARY-NOT-SELECTED")
        self.assertFalse(j["candidate"]["selected"])
        self.assertFalse(j["candidate"]["ratified"])
        self.assertIsNone(j["candidate"]["coordinate"])
        self.assertFalse(j["candidate"]["physical_t5_authorized"])


if __name__ == "__main__":
    unittest.main()
