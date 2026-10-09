"""D10 RESEARCH ONLY: finite length-decreasing binary string-rewrite confluence.

Two independent exact oracles:
A. critical overlapping left-side occurrences (including containment);
B. direct full census of all local one-step peaks for bounded source words.

Newman 1942 + Knuth/Bendix 1970 apply ONLY because every step
strictly decreases the exact finite word length. No SENS runtime or opcode.
"""
import itertools
import json
import unittest
from functools import lru_cache
from pathlib import Path


def validate_rules(rules):
    if not isinstance(rules, (list, tuple)):
        raise ValueError("rules must be finite ordered sequence")
    out = []
    for pair in rules:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or not all(isinstance(s, str) for s in pair)):
            raise ValueError("each rule is (lhs,rhs) of bit strings")
        lhs, rhs = pair
        if not lhs or len(rhs) >= len(lhs) or any(c not in "01" for c in lhs + rhs):
            raise ValueError("rules must be strict length-reducing binary words")
        out.append((lhs, rhs))
    return tuple(out)


def one_steps(word, rules):
    result = set()
    for lhs, rhs in rules:
        for pos in range(len(word) - len(lhs) + 1):
            if word.startswith(lhs, pos):
                result.add(word[:pos] + rhs + word[pos + len(lhs):])
    return tuple(sorted(result))


@lru_cache(maxsize=None)
def normal_forms(word, rules):
    """All exact reachable normal forms under nondeterministic rewriting."""
    next_words = one_steps(word, rules)
    if not next_words:
        return frozenset((word,))
    found = set()
    for nxt in next_words:
        assert len(nxt) < len(word)
        found.update(normal_forms(nxt, rules))
    return frozenset(found)


def critical_peaks(rules):
    """Minimal overlap superpositions; includes inclusion & same-position peaks."""
    peaks = set()
    for i, (left_a, right_a) in enumerate(rules):
        for j, (left_b, right_b) in enumerate(rules):
            # Relative start of b versus a; only strictly overlapping spans.
            for shift in range(1 - len(left_b), len(left_a)):
                start_a = max(0, -shift)
                start_b = max(0, shift)
                n = max(start_a + len(left_a), start_b + len(left_b))
                origin = [None] * n
                valid = True
                for start, lhs in ((start_a, left_a), (start_b, left_b)):
                    for k, bit in enumerate(lhs):
                        pos = start + k
                        if origin[pos] is not None and origin[pos] != bit:
                            valid = False
                            break
                        origin[pos] = bit
                    if not valid:
                        break
                if not valid:
                    continue
                source = "".join(origin)
                a = source[:start_a] + right_a + source[start_a + len(left_a):]
                b = source[:start_b] + right_b + source[start_b + len(left_b):]
                peaks.add((source, a, b, i, j, start_a, start_b))
    return tuple(sorted(peaks))


def confluence_via_critical_pairs(rules_input):
    rules = validate_rules(rules_input)
    for source, a, b, i, j, pa, pb in critical_peaks(rules):
        na, nb = normal_forms(a, rules), normal_forms(b, rules)
        if na.isdisjoint(nb):
            return {
                "verdict": "NONCONFLUENT",
                "source": source,
                "branch_a": a, "branch_b": b,
                "normal_a": sorted(na), "normal_b": sorted(nb),
                "rule_indices": (i, j), "positions": (pa, pb),
            }
    return {"verdict": "CONFLUENT"}


def independent_full_peak_census(rules_input, source_max_length):
    """Different algorithm: enumerate source words and all direct successors."""
    rules = validate_rules(rules_input)
    for n in range(source_max_length + 1):
        for word in ("".join(x) for x in itertools.product("01", repeat=n)):
            successors = one_steps(word, rules)
            for a, b in itertools.combinations(successors, 2):
                if normal_forms(a, rules).isdisjoint(normal_forms(b, rules)):
                    return {"verdict": "NONCONFLUENT", "source": word,
                            "branch_a": a, "branch_b": b}
    return {"verdict": "CONFLUENT"}


class D10CriticalPairResearch(unittest.TestCase):
    def test_named_semantic_witnesses(self):
        examples = [
            ([], "CONFLUENT"),
            ([("00", "0")], "CONFLUENT"),
            ([("01", "0"), ("10", "0")], "CONFLUENT"),
            ([("01", "0"), ("10", "0"), ("00", "0")], "CONFLUENT"),
            ([("01", "0"), ("10", "1")], "NONCONFLUENT"),
            ([("00", "0"), ("00", "1")], "NONCONFLUENT"),
            ([("010", "0"), ("10", "0")], "NONCONFLUENT"),
        ]
        for rules, expected in examples:
            with self.subTest(rules=rules):
                result = confluence_via_critical_pairs(rules)
                self.assertEqual(result["verdict"], expected)
                direct = independent_full_peak_census(rules, 6)
                self.assertEqual(direct["verdict"], expected)
                if expected == "NONCONFLUENT":
                    self.assertTrue(set(result["normal_a"]).isdisjoint(result["normal_b"]))
                    self.assertIn(result["branch_a"], one_steps(result["source"], rules))
                    self.assertIn(result["branch_b"], one_steps(result["source"], rules))

    def test_complete_all_two_short_rule_systems(self):
        alphabet = "01"
        candidates = []
        for lhs_len in (1, 2):
            for lhs_tuple in itertools.product(alphabet, repeat=lhs_len):
                lhs = "".join(lhs_tuple)
                for rhs_len in range(lhs_len):
                    for rhs_tuple in itertools.product(alphabet, repeat=rhs_len):
                        candidates.append((lhs, "".join(rhs_tuple)))
        self.assertEqual(len(candidates), 14)
        # All unordered TWO-rule multisets, including repeat of the same rule.
        checked = 0
        for rules in itertools.combinations_with_replacement(candidates, 2):
            with self.subTest(rules=rules):
                self.assertEqual(
                    confluence_via_critical_pairs(rules)["verdict"],
                    independent_full_peak_census(rules, 5)["verdict"],
                )
                checked += 1
        self.assertEqual(checked, 105)

    def test_three_rule_interactions(self):
        # Mixed three-rule systems ensure multi-step joinability isn't mistaken
        # for equality of direct branches.
        base = [("0", ""), ("1", ""), ("00", ""), ("00", "0"),
                ("01", ""), ("01", "0"), ("10", ""), ("10", "1"),
                ("11", ""), ("11", "1")]
        checked = 0
        for rules in itertools.combinations(base, 3):
            actual = confluence_via_critical_pairs(rules)
            direct = independent_full_peak_census(rules, 5)
            self.assertEqual(actual["verdict"], direct["verdict"], rules)
            checked += 1
        self.assertEqual(checked, 120)

    def test_reject_nonterminating_and_malformed_profiles(self):
        invalid = [
            [("0", "0")], [("0", "10")], [("", "")],
            [("2", "")], [("01", "2")], [("10", "01")],
            [["01"]], "rules", [(1, "")], [("01", None)],
        ]
        for rules in invalid:
            with self.subTest(rules=rules):
                with self.assertRaises(ValueError):
                    confluence_via_critical_pairs(rules)

    def test_research_no_semantic_authorization(self):
        path = (Path(__file__).resolve().parents[1] / "knowledge" /
                "d10-critical-pairs-confluence-20261009.json")
        obj = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(obj["status"], "RESEARCH-HOLD-CORE-VS-LIBRARY-NOT-SELECTED")
        self.assertFalse(obj["candidate"]["selected"])
        self.assertFalse(obj["candidate"]["ratified"])
        self.assertIsNone(obj["candidate"]["coordinate"])
        self.assertFalse(obj["candidate"]["physical_t5_authorized"])


if __name__ == "__main__":
    unittest.main()
