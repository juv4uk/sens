"""Мова живе в SENS, а не в JSON/Python — розумний блокер переходу.

Ідея. Python і JSON лишаються КЛЕЄМ (CI, збірка, перенесення байтів, запуск).
Але коли хост-файл (.py/.json) починає НЕСТИ САМУ МОВУ — тобто містить SENS-код
укр-проєкцією (голови: визначити, функція, за-умовою, як-є, сполучити, перше, решта) — це означає,
що семантику мови переписали хост-мовою. Саме це заборонено: семантика мусить жити
в SENS (lib/**, tests/semantic/**), а хост — лише транспортувати.

Чому «розумний», а не суцільна заборона: суцільна заборона Python/JSON зламала б CI
й транспорт і нічого не дала б. Тут блокується рівно НОВЕ місце, де мова в хості.

Наявний борг заморожено у LEGACY_HOST_DEBT (кількість SENS-голів у файлі). Він мусить
скорочуватися до нуля; жоден файл не сміє набрати БІЛЬШЕ, ніж заморожено.
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ознака того, що файл несе САМУ МОВУ (SENS-код укр-проєкцією), а не просто клей.
SENS_HEAD_NAMES = ("визначити", "функція", "за-умовою", "як-є", "сполучити", "перше", "решта")
SENS_HEAD = re.compile(r"\(\s*(?:" + "|".join(SENS_HEAD_NAMES) + r")\b")

# Заморожений легасі-борг: хост-файли, що вже несуть мову. Це БОРГ, не дозвіл.
LEGACY_HOST_DEBT: dict[str, int] = {
    "knowledge/d11/база-доступних-функцій/кандидати.json": 12,
    "knowledge/d11/база-доступних-функцій/пропозиції-порожньої-програми-груп-20261020.json": 4,
    "knowledge/migration-dynamic-binding-triage-2026-10-08.json": 16,
    "scripts/apply-d10-queue-sortcar-mapinto-batch.py": 1,
    "scripts/audit-d11-available-functions.py": 1,
    "scripts/check-bija3-current-authority.py": 1,
    "scripts/check-core4-d24-migration.py": 2,
    "scripts/check-d9-final-semantic-fill-v1.py": 4,
    "scripts/check-d9-library-harvest-v1.py": 6,
    "scripts/check-d9-registry-tail-v1.py": 7,
    "scripts/check-d9-semantic-layer-harvest-v1.py": 4,
    "scripts/check-d9-world-quantity-harvest-v1.py": 6,
    "scripts/check-tier1-cond-authority.py": 2,
    "scripts/check_d10_time_law_review_v2.py": 1,
    "scripts/check_principle_force.py": 3,
    "scripts/check_semantic_registry.py": 1,
    "scripts/check_ukr_callsite_migration.py": 2,
    "scripts/generate-encoder-coverage-input.py": 1,
    "scripts/guard-domain-function-reuse.py": 2,
    "scripts/guard_ukr_lisp_keyboard.py": 3,
    "scripts/migrate-three-pass.py": 3,
    "scripts/report_ukr_projection_progress.py": 1,
    "scripts/test-content-store-d1-bitness.py": 1,
    "scripts/test-fs-d1-bitness.py": 2,
    "scripts/test-guard-d1-bitness.py": 2,
    "scripts/test-knowledge-d1-bitness.py": 1,
    "scripts/test-mechanism-selector-d1-bitness.py": 2,
    "scripts/test-meta-eval-fc-d1-bitness.py": 3,
    "scripts/test-meta-eval-mutual-d1-bitness.py": 1,
    "scripts/test-persistent-map-d1-bitness.py": 2,
    "scripts/test-result-status-d1-bitness.py": 1,
    "scripts/test-si-derived-d1-bitness.py": 1,
    "scripts/test-tcp-d1-bitness.py": 2,
    "scripts/test-translation-d1-bitness.py": 1,
    "scripts/test-unify-observe-d1-bitness.py": 5,
    "scripts/test-world-d1-bitness.py": 6,
    "scripts/test_cond_modernize.py": 2,
    "scripts/tests/test_translate_program.py": 13,
    "scripts/translate-domain-program.py": 3,
    "tests/fixtures/core1-domain-canary/regenerate.py": 7,
    "tests/test_audit_all_lisp_triplets.py": 15,
    "tests/test_audit_lisp_migration_edits.py": 38,
    "tests/test_audit_t5_file_pairs.py": 8,
    "tests/test_audit_t5_triplets.py": 1,
    "tests/test_build_inventory_ukr_projection.py": 7,
    "tests/test_capability_axis_ukr_projection.py": 6,
    "tests/test_changed_lisp_t5m_route.py": 1,
    "tests/test_check_migration_zig_only_path.py": 2,
    "tests/test_classify_lisp_source_forms.py": 4,
    "tests/test_clips_exact_d3_slot_2046.py": 25,
    "tests/test_code_runs.py": 71,
    "tests/test_content_store_ukr_primary_projection.py": 5,
    "tests/test_contest_uk_literal_free.py": 1,
    "tests/test_core1_domain_canary.py": 3,
    "tests/test_core1_fourth_domain_canary.py": 5,
    "tests/test_core1_third_domain_canary.py": 4,
    "tests/test_core3_profile_d3_source.py": 5,
    "tests/test_core3_ukr_projection.py": 14,
    "tests/test_core4_internal_sid8_migration.py": 4,
    "tests/test_core_lisp_helper_head_cutover.py": 19,
    "tests/test_core_ukr_primary_projection.py": 64,
    "tests/test_d10_time_law_review_v2.py": 2,
    "tests/test_d3_legacy_logic_guard.py": 26,
    "tests/test_d7_core_identity_triplet.py": 3,
    "tests/test_domain_function_reuse_rule.py": 10,
    "tests/test_domain_ladder_source_batch.py": 45,
    "tests/test_encoder_coverage_ukr_projection.py": 13,
    "tests/test_forward_macro_d4_2046.py": 2,
    "tests/test_fs_ukr_projection.py": 15,
    "tests/test_guard_t5_triplet_delta.py": 3,
    "tests/test_guard_ukr_lisp_keyboard.py": 12,
    "tests/test_knowledge_d1_recovery.py": 16,
    "tests/test_linter_domain_head_cutover.py": 70,
    "tests/test_machine_encoding_ukr_aliases.py": 3,
    "tests/test_machine_projection_ukr_locals.py": 13,
    "tests/test_mechanism_selector_d1_scan.py": 13,
    "tests/test_meta_eval_fc_ukr_remaining.py": 19,
    "tests/test_migrate_approved_t5_current.py": 1,
    "tests/test_migrate_english_predicates_question_mark.py": 7,
    "tests/test_migrate_entrypoint.py": 1,
    "tests/test_migrate_exact_domain.py": 43,
    "tests/test_migrate_exact_domain_uk_apostrophe.py": 4,
    "tests/test_migrate_selected_lisp.py": 16,
    "tests/test_migration_d1_cond_cohort.py": 2,
    "tests/test_migration_d4_selector_cohort.py": 5,
    "tests/test_migration_pair_cons_uk_triplet.py": 3,
    "tests/test_narrate_ukr_projection.py": 4,
    "tests/test_no_encoded_source_literals.py": 18,
    "tests/test_persistent_map_ukr_primary_projection.py": 6,
    "tests/test_persistent_vector_ukr_primary_projection.py": 6,
    "tests/test_process_d1_direct.py": 16,
    "tests/test_process_d1_predicate_cutover.py": 10,
    "tests/test_publish_verified_uk_triplets.py": 1,
    "tests/test_readme_owner_contract.py": 4,
    "tests/test_report_migration_git_delta.py": 2,
    "tests/test_report_nonprogram_pin_drift.py": 2,
    "tests/test_report_t5_triplet_inventory.py": 4,
    "tests/test_result_status_d1_bitness_current.py": 8,
    "tests/test_sens_inventory_failclosed.py": 1,
    "tests/test_sens_t5_spaced_view.py": 1,
    "tests/test_sid8_broad_source_cutover.py": 1,
    "tests/test_sid8_knowledge_layout_source.py": 27,
    "tests/test_sid8_knowledge_list_event_d3.py": 6,
    "tests/test_sid8_multisource_lisp_cutover.py": 1,
    "tests/test_sid8_witness_second_cohort.py": 3,
    "tests/test_sid8_witness_source_cutover.py": 2,
    "tests/test_t5_triplet_crosscheck.py": 1,
    "tests/test_tcp_d1_fallback.py": 6,
    "tests/test_tests_use_ukr_projection.py": 3,
    "tests/test_three_pass_migration.py": 42,
    "tests/test_translation_d1_bitness_current.py": 10,
    "tests/test_translation_ukr_primary_projection.py": 8,
    "tests/test_triple_projection_script_safety.py": 3,
    "tests/test_ukr_callsite_migration.py": 110,
    "tests/test_ukr_canon_d4_projection.py": 12,
    "tests/test_ukr_core1_bootstrap_projection.py": 1,
    "tests/test_ukr_core3_profile_projection.py": 1,
    "tests/test_ukr_default_t5m_contract.py": 4,
    "tests/test_ukr_enforcement_projection.py": 7,
    "tests/test_ukr_guard_projection.py": 28,
    "tests/test_ukr_lib_peers.py": 33,
    "tests/test_ukr_machine_projection_parity.py": 17,
    "tests/test_ukr_macro_bridge_unify_effects.py": 33,
    "tests/test_ukr_mechanism_checkers_projection.py": 4,
    "tests/test_ukr_mechanism_selector_projection.py": 37,
    "tests/test_ukr_narrate_block_projection.py": 6,
    "tests/test_ukr_narrate_peers.py": 6,
    "tests/test_ukr_native_first_dispatch_projection.py": 5,
    "tests/test_ukr_optin_sources.py": 75,
    "tests/test_ukr_persistent_map_projection.py": 19,
    "tests/test_ukr_program_symbol_table_projection.py": 25,
    "tests/test_ukr_projection_progress_report.py": 70,
    "tests/test_ukr_quantity_projection.py": 21,
    "tests/test_ukr_registry_read_benchmark.py": 6,
    "tests/test_ukr_result_status_projection.py": 14,
    "tests/test_ukr_scale_functions_md_projection.py": 5,
    "tests/test_ukr_semantic_authority_guard_projection.py": 2,
    "tests/test_ukr_tcp_island_projection.py": 9,
    "tests/test_ukr_tcp_map_current.py": 7,
    "tests/test_ukr_translation_result_prolog.py": 14,
    "tests/test_ukr_verify_repo_domain_calls.py": 5,
    "tests/test_ukr_x86_encoder_first_five.py": 4,
    "tests/test_unify_observe_exact_2046.py": 5,
    "tests/test_unify_occurs_exact_domains_2046.py": 1,
    "tests/test_utf8_d1_predicate_migration.py": 6,
    "tests/test_verify_uk_t5_triplet.py": 41,
    "tests/test_world_ukr_primary_projection.py": 18,
    "tests/test_yantra_ukr_projection.py": 16
}


def _tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True, check=False).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _host_files() -> dict[str, int]:
    found: dict[str, int] = {}
    for pattern in ("scripts/*.py", "tests/*.py", "knowledge/*.json"):
        for rel in _tracked(pattern):
            path = ROOT / rel
            if not path.is_file():
                continue
            heads = SENS_HEAD.findall(path.read_text(encoding="utf-8", errors="ignore"))
            if heads:
                found[rel] = len(heads)
    return found


class LanguageStaysInSens(unittest.TestCase):
    def test_no_new_host_file_carries_sens_semantics(self) -> None:
        new = sorted(rel for rel in _host_files() if rel not in LEGACY_HOST_DEBT)
        self.assertEqual(
            new, [],
            "Новий .py/.json несе SENS-семантику (укр-проєкцію) — це переписування мови "
            "хост-мовою. Семантика мусить бути в SENS: lib/** або tests/semantic/**. "
            "Хост лишається транспортом.",
        )

    def test_frozen_host_debt_only_shrinks(self) -> None:
        current = _host_files()
        grown = {rel: (LEGACY_HOST_DEBT[rel], current[rel])
                 for rel in LEGACY_HOST_DEBT
                 if rel in current and current[rel] > LEGACY_HOST_DEBT[rel]}
        self.assertEqual(grown, {}, f"борг мови-в-хості не сміє зростати: {grown}")

    def test_probe_recognises_sens_code_in_host(self) -> None:
        # Приклад збираємо з частин, інакше сам охоронець рахує
        # власну тестову фікстуру як новий SENS-код у Python.
        probe = 'program = "(' + 'визначити список (' + 'функція (х) х))"'
        self.assertTrue(SENS_HEAD.search(probe))
        self.assertFalse(SENS_HEAD.search("def helper(): return 1  # звичайний клей"))


# ── Подвоєння механіки: Python не перевіряє те, за що відповідає Rust ──────────
# Механіку рантайму засвідчують Rust-тести (crates/*/tests/*.rs); ізоляцію — Zig.
# Python-тест, що лізе в Rust-джерело механіки, — це подвоєння. Борг заморожено.
RUST_MECHANISM_SOURCE = re.compile(r"crates/(sens|sens-cli|sens-host)/src")
MECHANISM_TERM = re.compile(
    r"\b(arena|cons|environment|eval|value|closure)\b|сполучити|перше|решта|середовище|комірк",
    re.IGNORECASE,
)
LEGACY_PYTHON_RUST_DOUBLING: dict[str, int] = {
    "tests/test_core1_fourth_domain_canary.py": 4,
    "tests/test_core1_third_domain_canary.py": 4,
    "tests/test_d3_legacy_logic_guard.py": 1,
    "tests/test_d4_define_source_cutover.py": 1,
    "tests/test_migrate_selected_lisp.py": 12,
    "tests/test_migrated_historical_two_projections.py": 4,
    "tests/test_migration_d1_cond_cohort.py": 5,
    "tests/test_migration_d4_selector_cohort.py": 5,
    "tests/test_migration_dynamic_binding_census.py": 5,
    "tests/test_migration_dynamic_binding_triage.py": 5,
    "tests/test_migration_eq_cohort.py": 5,
    "tests/test_migration_eq_cond_cohort.py": 5,
    "tests/test_migration_multiform_cohort.py": 5,
    "tests/test_migration_pair_cohort.py": 5,
    "tests/test_migration_pair_cons_uk_triplet.py": 5,
    "tests/test_migration_print_host_effect_triage.py": 5,
    "tests/test_migration_quote_cohort.py": 5,
    "tests/test_repl_physical_prerequisites.py": 3,
    "tests/test_sterile_zig_corridor.py": 30,
    "tests/test_three_pass_quoted_datum_law.py": 4,
    "tests/test_ukr_default_t5m_contract.py": 1,
    "tests/test_ukr_tcp_map_current.py": 1,
    "tests/test_verify_uk_t5_triplet.py": 1,
    "tests/test_wsm_f6_zig_source_boundary.py": 2,
    "tests/test_zig_build_environment_watch.py": 1,
    "tests/test_zig_ffi_v2_contract.py": 10
}


def _python_rust_doubling() -> dict[str, int]:
    found: dict[str, int] = {}
    for rel in _tracked("tests/*.py"):
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if RUST_MECHANISM_SOURCE.search(text) and MECHANISM_TERM.search(text):
            found[rel] = len(RUST_MECHANISM_SOURCE.findall(text))
    return found


class PythonDoesNotDoubleRustMechanism(unittest.TestCase):
    def test_no_new_python_test_doubles_rust_mechanism(self) -> None:
        new = sorted(rel for rel in _python_rust_doubling() if rel not in LEGACY_PYTHON_RUST_DOUBLING)
        self.assertEqual(
            new, [],
            "Новий Python-тест перевіряє механіку рантайму, за яку відповідає Rust. "
            "Механіку засвідчують Rust-тести (crates/*/tests), ізоляцію — Zig-тести.",
        )

    def test_python_rust_doubling_debt_only_shrinks(self) -> None:
        cur = _python_rust_doubling()
        grown = {r: (LEGACY_PYTHON_RUST_DOUBLING[r], cur[r])
                 for r in LEGACY_PYTHON_RUST_DOUBLING
                 if r in cur and cur[r] > LEGACY_PYTHON_RUST_DOUBLING[r]}
        self.assertEqual(grown, {}, f"подвоєння не сміє зростати: {grown}")


if __name__ == "__main__":
    unittest.main()
