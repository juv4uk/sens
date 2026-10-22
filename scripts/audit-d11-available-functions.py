#!/usr/bin/env python3
"""Non-authoritative, fail-closed inventory audit for D11 research candidates.

This checks *names, widths, provenance, and admission metadata* only.
No external runtime may infer SENS semantic equivalence from this audit.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "base": "knowledge/d11/база-доступних-функцій/кандидати.json",
    "foundation": "knowledge/d1-d9-foundation.json",
    "aggregate": "knowledge/d1-d11-foundation.json",
    "d10": "knowledge/d10-v18-semantic-inventory.json",
    "d10_owner": "knowledge/d10-owner-whole-domain-ratification-20261012.json",
    "d11_test": "knowledge/d11-testing-vocabulary-ratified.json",
}
EXPECTED_COUNTS = {
    "D1": 2, "D2": 4, "D3": 8, "D4": 16, "D5": 32, "D6": 64,
    "D7": 128, "D8": 256, "D9": 512, "D10": 1024, "D11": 43,
}


class AuditError(ValueError):
    """One narrowly identifiable mechanical inventory inconsistency."""


def require(ok: bool, test_id: str, detail: str) -> None:
    if not ok:
        raise AuditError(f"test_id={test_id} layer=registry {detail}")


def key_upper(value: str) -> str:
    return value.casefold()


def read_sources(root: Path) -> tuple[dict, dict]:
    sources: dict = {}
    hashes: dict = {}
    for name, rel in PATHS.items():
        raw = (root / rel).read_bytes()
        sources[name] = json.loads(raw.decode("utf-8"))
        prefix = f"blob {len(raw)}\0".encode("ascii")
        hashes[name] = {
            "path": rel,
            "git_blob_sha1": hashlib.sha1(prefix + raw).hexdigest(),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return sources, hashes


def check_words(domain: str, words: dict, expected: int) -> None:
    require(isinstance(words, dict), "WORD_MAP", f"{domain}: expected object")
    require(len(words) == expected, "OCCUPANCY", f"{domain}: expected {expected} rows; actual {len(words)}")
    width = int(domain[1:])  # Mechanical width metadata, never a SENS semantic identifier.
    for bits, name in words.items():
        require(isinstance(bits, str) and len(bits) == width and set(bits) <= {"0", "1"},
                "BIT_WIDTH", f"{domain}: invalid key {bits!r}; exact width={width}")
        require(isinstance(name, str) and bool(name), "EMPTY_NAME", f"{domain}:{bits} has no resident name")


def validate(s: dict, hashes: dict, root: Path, *, source_files: bool = True) -> dict:
    base, foundation, aggregate = s["base"], s["foundation"], s["aggregate"]
    d10, owner, d11 = s["d10"], s["d10_owner"], s["d11_test"]
    require(base.get("schema") == "sens.available-functions/v1", "CATALOG_SCHEMA", "unexpected catalogue schema")
    require(base.get("target_domain") == "D11" and base.get("bit_width") == 11 and
            base.get("domain_capacity") == 2048, "CATALOG_WIDTH", "D11 is 11 bits / capacity 2048")
    require(owner.get("decision") == "RATIFY_D10_AS_ONE_COMPLETE_DOMAIN" and owner.get("ratified") is True,
            "OWNER_D10", "whole-domain D10 ratification document absent or invalid")
    require(owner.get("inventory", {}).get("git_blob") == hashes["d10"]["git_blob_sha1"],
            "OWNER_PIN", "D10 codebook bytes differ from owner-ratified inventory SHA")
    require(d11.get("status") == "UNRATIFIED_REVIEW" and
            d11.get("ratified") is False and d11.get("ratified_by") is None,
            "D11_OWNER_AUTHORITY", "43 historical test words are not owner-ratified")
    require(aggregate.get("domains", {}).get("D11", {}).get("ratified") is False and
            aggregate.get("domains", {}).get("D11", {}).get("fixture_only") is True,
            "D11_AGGREGATE_SCOPE", "D11 historical test data cannot become ratified residents")
    require(d11.get("semantic_scope") == "Testing vocabulary for binary SENS semantic tests; not callable Core",
            "TESTING_SCOPE", "D11 testing-only scope unexpectedly changed")
    require(d11.get("width") == 11 and d11.get("occupancy") == 43, "TESTING_WIDTH", "D11 test width/occupancy changed")
    ordered = [f"D{i}" for i in range(1, 12)]
    require(aggregate.get("current_domains") == ordered, "DOMAIN_ORDER",
            f"current_domains expected D1..D11 once; actual {aggregate.get('current_domains')}")
    require(set(aggregate.get("domains", {})) == set(ordered), "DOMAIN_SET", "aggregate has wrong domain keys")
    require(foundation.get("current_domains") == ordered[:9], "FOUNDATION_ORDER", "D1–D9 owner foundation differs")
    require(set(foundation.get("domains", {})) == set(ordered[:9]), "FOUNDATION_SET", "D1–D9 keys differ")

    for domain in ordered:
        record = aggregate["domains"][domain]
        require(record.get("width") == int(domain[1:]), "DECLARED_WIDTH", f"{domain} declared width mismatch")
        check_words(domain, record["residents"], EXPECTED_COUNTS[domain])
        if domain in foundation["domains"]:
            authoritative = foundation["domains"][domain]
            require(record["residents"] == authoritative["residents"], "AUTHORITY_DRIFT",
                    f"{domain}: aggregate differs from current ratified D1–D9 source (D7 v2 matters)")

    selected = d10.get("rows")
    require(isinstance(selected, list) and len(selected) == 1024, "D10_ROWS", "D10 must have 1024 inventory rows")
    by_code = {}
    d10_names = set()
    for row in selected:
        bits, name = row.get("coordinate"), row.get("semantic_name")
        require(isinstance(bits, str) and len(bits) == 10 and set(bits) <= {"0", "1"},
                "D10_WIDTH", f"invalid D10 coordinate {bits!r}")
        require(isinstance(name, str) and bool(name), "D10_NAME", f"missing semantic name for {bits}")
        require(bits not in by_code and key_upper(name) not in d10_names,
                "D10_BIJECTION", f"repeated D10 coordinate/name {bits} / {name}")
        by_code[bits] = name
        d10_names.add(key_upper(name))
    require({bits: key_upper(name) for bits, name in by_code.items()} ==
            {bits: key_upper(name) for bits, name in aggregate["domains"]["D10"]["residents"].items()},
            "D10_AGGREGATE", "D10 aggregate does not match pinned owner inventory")

    # 512 селекторів уже визначені композицією 256 чинних селекторів D10.
    # Не дозволяти бібліотечним переможцям займати їхні математичні адреси.
    selector_parents = {
        bits for bits, name in by_code.items()
        if len(name) == 10 and name.startswith("C") and name.endswith("R")
        and len(name[1:-1]) == 8 and set(name[1:-1]) <= {"A", "D"}
    }
    require(len(selector_parents) == 256, "D11_DERIVED_PARENTS",
            f"expected 256 exact selector parents, got {len(selector_parents)}")
    mathematically_defined_selector_codes = {
        bits + suffix for bits in selector_parents for suffix in ("0", "1")
    }
    require(len(mathematically_defined_selector_codes) == 512, "D11_DERIVED_COUNT",
            "512 selector laws must be unique")

    test_names, test_coordinates = set(), set()
    tests = d11.get("table")
    require(isinstance(tests, list) and len(tests) == 43, "D11_TEST_ROWS", "expected 43 D11 testing entries")
    for entry in tests:
        bits, name = entry.get("bits"), entry.get("lisp")
        require(isinstance(bits, str) and len(bits) == 11 and set(bits) <= {"0", "1"},
                "D11_TEST_WIDTH", f"invalid testing coordinate {bits!r}")
        require(isinstance(name, str) and bool(name), "D11_TEST_NAME", "empty D11 testing name")
        require(bits not in test_coordinates, "D11_TEST_DUP_BITS", f"duplicate {bits}")
        require(key_upper(name) not in test_names, "D11_TEST_DUP_NAME", f"duplicate {name}")
        test_coordinates.add(bits)
        test_names.add(key_upper(name))
        require(key_upper(aggregate["domains"]["D11"]["residents"].get(bits, "")) == key_upper(name),
                "D11_AGGREGATE", f"D11 testing table differs from aggregate at {bits}")

    lower_names = {key_upper(name) for domain in ordered[:10]
                   for name in aggregate["domains"][domain]["residents"].values()}
    rows = base.get("rows")
    require(isinstance(rows, list), "CANDIDATE_ROWS", "catalogue has no rows list")
    seen = set()
    winner_positions = set()
    selected_winners = 0
    families = set()
    kinds = {"HISTORICAL_LISP": 0, "SENS_LIBRARY_SNAPSHOT": 0}
    for index, item in enumerate(rows):
        name = item.get("surface_name")
        require(isinstance(name, str) and bool(name), "CANDIDATE_NAME", f"row {index} empty name")
        label = key_upper(name)
        require(label not in seen, "CANDIDATE_DUPLICATE", f"row {index}: duplicate candidate {name}")
        require(label not in lower_names, "LOWER_DOMAIN_COLLISION", f"row {index}: {name} already in D1–D10")
        require(label not in test_names, "D11_TEST_COLLISION", f"row {index}: {name} already in D11 testing table")
        seen.add(label)
        # Матеріальний переможець визначеного SENS-закону вже має адресу.
        # Це не допуск до прямого D11 opcode і не ратифікація нового примітива.
        winner = item.get("winner_20261022")
        require(item.get("callable") is False and item.get("ratified") is False and
                item.get("exact_bit_width_if_admitted") == 11,
                "NOT_ADMITTED", f"row {index}: new direct opcode was not authorized")
        if winner is None:
            require(item.get("coordinate") is None,
                    "NOT_ADMITTED", f"row {index}: missing executable winner law for {name}")
        else:
            coordinate = item.get("coordinate")
            require(isinstance(coordinate, str) and len(coordinate) == 11 and
                    set(coordinate) <= {"0", "1"} and coordinate not in test_coordinates
                    and coordinate not in mathematically_defined_selector_codes,
                    "WINNER_WIDTH", f"row {index}: invalid/occupied D11 coordinate")
            require(coordinate not in winner_positions,
                    "WINNER_COORD_COLLISION", f"row {index}: repeated winner coordinate")
            winner_positions.add(coordinate)
            selected_winners += 1
            require(item.get("domain_candidate") == "D11_DEFINED_COMPOSITE_WINNER" and
                    item.get("review_status") == "LAW_DEFINED_EXECUTABLE_LIBRARY_WINNER" and
                    winner.get("coordinate") == coordinate and
                    winner.get("status") == "ПЕРЕМОЖЕЦЬ_ВИЗНАЧЕНОЇ_КОМПОЗИЦІЇ" and
                    winner.get("semantic_defined") is True and
                    winner.get("new_primitive") is False and
                    winner.get("direct_d11_opcode_verified") is False and
                    winner.get("source_file") in {"lib/persistent-vector.lisp", "lib/unify.lisp", "lib/reason.lisp", "lib/forward.lisp", "lib/unify-observe.lisp", "lib/codec-d2.lisp", "lib/world.lisp", "lib/si.lisp", "lib/repl-core.lisp" , "lib/epistemic.lisp", "lib/meta-eval.lisp"} and
                    winner.get("native_law_test") in {
                        "crates/sens/tests/persistent_vector.rs::d11_пятнадцять_визначених_переможців_виконує_sens",
                        "crates/sens/tests/d11_unify_once.rs::d11_розвязати_один_раз_не_підмінює_рекурсивне_проходження",
                        "crates/sens/tests/reason_index.rs::reason_index_d1_verdicts_from_real_predicates",
                        "crates/sens/tests/core_postcore_ukr.rs::meta_eval_graph_exact_d1_law_and_negative_mutant_execute_in_sens",
                        "crates/sens/tests/core_postcore_ukr.rs::meta_eval_predicates_are_actual_d1_bits",
                        "crates/sens/tests/reasoning_forward_knowledge_d3_migration.rs::d11_jtms_знайти_запис_за_фактом_зберігає_докази_й_перший_збіг",
                        "crates/sens/tests/d11_unify_once.rs::d11_застосувати_підстановку_обійдений_працює_рекурсивно",
                        "crates/sens/tests/d11_unify_once.rs::d11_спостерігати_уніфікацію_розрізняє_порожній_успіх_і_невдачу",
                        "crates/sens/tests/d11_unify_once.rs::d11_розширити_підстановку_зберігає_пари_та_пріоритет",
                        "crates/sens/tests/codec_in_sens.rs::codec_emits_exact_t5_d2_order",
                        "crates/sens/tests/codec_in_sens.rs::codec_round_trips_every_shape",
                        "crates/sens/tests/codec_in_sens.rs::d11_кодек_д2_три_допоміжні_закони_у_sens",
                        "crates/sens/tests/world_ancestor_sens.rs::d11_world_remove_first_native_law_and_mutant",
                        "crates/sens/tests/world_ancestor_sens.rs::d11_world_event_and_module_presence_are_native_sens_compositions",
                        "crates/sens/tests/world_ancestor_sens.rs::d11_world_internal_three_defined_compositions",
                        "crates/sens/tests/scientific_constants.rs::d11_si_три_закони_запису_значення_та_одиниці",
                        "crates/sens/tests/repl_core_malformed_tails.rs::d11_four_repl_library_laws_run_inside_sens",
                        "crates/sens/tests/epistemic_exact_ref_equality.rs::посилання_на_джерело_повертає_точні_значення_d1",
                        "crates/sens/tests/epistemic_exact_ref_equality.rs::неправильний_хвіст_вимог_не_створює_хибної_істини",
                    },
                    "WINNER_LAW", f"row {index}: missing real SENS-defined winner law")
        kind, family = item.get("source_kind"), item.get("source_family")
        require(kind in kinds and isinstance(family, str) and bool(family),
                "SOURCE_CLASS", f"row {index}: invalid source kind/family")
        kinds[kind] += 1
        families.add(family)
        provenance = item.get("provenance")
        path = provenance.get("repo_file") if isinstance(provenance, dict) else None
        require(isinstance(path, str) and path and not Path(path).is_absolute() and
                ".." not in Path(path).parts, "SOURCE_PROVENANCE", f"row {index}: unsafe/missing source path")
        if source_files:
            require((root / path).is_file(), "MISSING_SOURCE", f"row {index}: evidence missing {path}")
    actual = {
        "total": len(rows), "historical": kinds["HISTORICAL_LISP"],
        "library": kinds["SENS_LIBRARY_SNAPSHOT"], "distinct_families": len(families),
    }
    require(base.get("counts") == actual, "CATALOG_COUNTS", f"counts declared={base.get('counts')} actual={actual}")
    require(base.get("current_d11", {}).get("occupied") == 0 and
            base.get("current_d11", {}).get("legacy_fixture_count") == 43 and
            base.get("current_d11", {}).get("admitted_resident_occupancy") == 0 and
            base.get("current_d11", {}).get("unratified") is True and
            base.get("current_d11", {}).get("ratified") is False,
            "D11_CATALOG_SCOPE", "43 unratified fixtures are not 43 occupied semantic resident slots")
    expect_winners = base.get("winners_20261022", {})
    # Переможці зростають з доведеними законами: жодного штучного стопу на 27.
    # Перевіряємо поточний підрахунок, а не заморожене історичне число.
    require(selected_winners == len(winner_positions) and
            selected_winners == expect_winners.get("native_sens_composition_winners") and
            expect_winners.get("mathematically_derived_selectors") == 512 and
            expect_winners.get("semantic_winners_total") == 512 + selected_winners,
            "WINNER_COUNT", f"D11 expected 512 + {selected_winners} defined laws")
    if source_files:
        for item in rows:
            winner = item.get("winner_20261022")
            if winner is None:
                continue
            source_head = winner["ukr"]
            source_rel = Path(winner["source_file"])
            require(not source_rel.is_absolute() and ".." not in source_rel.parts,
                    "WINNER_SOURCE", f"invalid source path {source_rel}")
            source_text = (root / source_rel).read_text(encoding="utf-8")
            require(f"(визначити {source_head}" in source_text,
                    "WINNER_SOURCE", f"missing actual SENS function {source_head}")
            test_rel, sep, function = winner["native_law_test"].partition("::")
            require(sep == "::" and test_rel.startswith("crates/sens/tests/") and
                    ".." not in Path(test_rel).parts,
                    "WINNER_NATIVE_TEST", f"invalid native SENS test {test_rel}")
            proof_text = (root / test_rel).read_text(encoding="utf-8")
            require(f"fn {function}()" in proof_text,
                    "WINNER_NATIVE_TEST", f"missing real SENS witness {function}")
        map_path = root / "knowledge/d11/база-доступних-функцій/розміщення-інших-функцій-д11.tsv"
        selected = [line.split("\t") for line in map_path.read_text(encoding="utf-8").splitlines()
                    if "\tWINNER_DEFINED_SENS_COMPOSITION\t" in line]
        require(len(selected) == selected_winners and
                {row[0] for row in selected} == winner_positions,
                "WINNER_PLACEMENT", "winner addresses must agree with existing D11 geometric map")
    # A source snapshot is historical evidence, NOT a veto if modern authority evolves.
    original = base.get("exclusion_snapshot", {})
    require(original.get("d10_blob_sha") == owner["inventory"]["git_blob"],
            "D10_CATALOG_PIN", "candidate exclusion was not made against owner-pinned D10")
    return {
        "test_id": "D11_AVAILABLE_FUNCTIONS_CANDIDATE_INVENTORY", "layer": "registry",
        "status": "MECHANICAL_PASS", "semantic_status": f"{selected_winners}_LIBRARY_WINNERS_SENS_LAW_512_DERIVED_SELECTORS",
        "target": "D11", "bit_width": 11, "capacity": 2048,
        "candidates": actual, "winner_compositions": selected_winners, "derived_selectors": 512,
        "defined_functions_total": 512 + selected_winners, "d10_owner_pinned": 1024,
        "d11_legacy_fixture_count": 43, "d11_owner_ratified_residents": 0,
        "historical_aggregate_sha": original.get("foundation_blob_sha"),
        "current_aggregate_sha": hashes["aggregate"]["git_blob_sha1"],
        "aggregate_changed_since_ingest": original.get("foundation_blob_sha") != hashes["aggregate"]["git_blob_sha1"],
        "input_sha256": {k: v["sha256"] for k, v in hashes.items()},
    }


def self_test(s: dict, hashes: dict, root: Path) -> int:
    validate(s, hashes, root)
    cases = []

    def bad_duplicate(x):
        x["base"]["rows"][1]["surface_name"] = x["base"]["rows"][0]["surface_name"]
    cases.append(("CANDIDATE_DUPLICATE", bad_duplicate))

    def bad_lower_domain(x):
        x["base"]["rows"][0]["surface_name"] = next(iter(x["aggregate"]["domains"]["D3"]["residents"].values()))
    cases.append(("LOWER_DOMAIN_COLLISION", bad_lower_domain))

    def bad_admission(x):
        x["base"]["rows"][0]["coordinate"] = "00000000000"
    cases.append(("NOT_ADMITTED", bad_admission))

    def bad_selector_overlap(x):
        winning = next(row for row in x["base"]["rows"] if row.get("winner_20261022"))
        winning["coordinate"] = "01100000000"
    cases.append(("WINNER_WIDTH", bad_selector_overlap))

    def bad_test_width(x):
        x["d11_test"]["table"][0]["bits"] = "0000000000"
    cases.append(("D11_TEST_WIDTH", bad_test_width))

    def bad_owner_claim(x):
        x["d11_test"]["status"] = "owner-ratified"
    cases.append(("D11_OWNER_AUTHORITY", bad_owner_claim))

    def bad_d11_reauthorization(x):
        x["aggregate"]["domains"]["D11"]["ratified"] = True
    cases.append(("D11_AGGREGATE_SCOPE", bad_d11_reauthorization))

    def bad_fixture_occupancy(x):
        x["base"]["current_d11"]["occupied"] = 43
    cases.append(("D11_CATALOG_SCOPE", bad_fixture_occupancy))

    def bad_d7_v1(x):
        first = next(iter(x["aggregate"]["domains"]["D7"]["residents"]))
        del x["aggregate"]["domains"]["D7"]["residents"][first]
    cases.append(("OCCUPANCY", bad_d7_v1))

    def bad_duplicate_d11(x):
        x["aggregate"]["current_domains"][9] = "D11"
    cases.append(("DOMAIN_ORDER", bad_duplicate_d11))

    def bad_source(x):
        x["base"]["rows"][0]["provenance"]["repo_file"] = "../escape"
    cases.append(("SOURCE_PROVENANCE", bad_source))

    for test_id, mutation in cases:
        cloned = copy.deepcopy(s)
        mutation(cloned)
        try:
            validate(cloned, hashes, root)
        except AuditError as exc:
            require(f"test_id={test_id}" in str(exc), "NEGATIVE_TEST",
                    f"{test_id}: rejected by wrong rule: {exc}")
        else:
            raise AuditError(f"test_id=NEGATIVE_TEST layer=registry accepted invalid {test_id}")
        print(f"D11_AUDIT_NEGATIVE_PASS test_id={test_id}")
    return len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="root of existing SENS repository")
    parser.add_argument("--self-test", action="store_true", help="positive and synthetic negative mutations")
    args = parser.parse_args()
    try:
        s, hashes = read_sources(args.root)
        result = validate(s, hashes, args.root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        if args.self_test:
            print(f"D11_AUDIT_SELF_TEST_PASS rejected={self_test(s, hashes, args.root)}")
        return 0
    except (AuditError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"D11_AUDIT_FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
