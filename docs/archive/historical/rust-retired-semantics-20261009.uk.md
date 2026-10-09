# Археологія вилучених Rust-перевірок спадкової семантики (2026-10-09)

Статус: **ненормативна історія**. Підстава — ратифікована власником таблиця міграції L1–L7, особливо L1, L5, L6. Цей документ фіксує, які старі очікування **вилучено з активних Rust-тестів**, без зміни виконуваного ядра чи джерел Lisp.

| Файл | Вилучена перевірка | Чому не є поточним оракулом | Чинна перевірка, яка залишається |
| --- | --- | --- | --- |
| `crates/sens/tests/meta_eval_errors.rs` | `canonical_cond_exhaustion_is_a_named_failure_in_native_and_meta_eval` | Очікувала `UnsatisfiedConditional` і тричленну клаузу COND; L1 ратифікує D3:110, exact D1 1/0 та структурне `()` при вичерпанні | `crates/sens/tests/d3_empty_control.rs`: `explicit_d1_no_continues_and_exhaustion_is_structural_empty`, `three_part_clause_is_rejected_on_exact_d3_cond` |
| `crates/sens/tests/content_store_authority.rs` | `content_store_semantic_relations_are_owned_by_lisp_witness` | Історичний Lisp witness спирався на старий спосіб спостереження семантичних відношень і на поточному runtime повертав `()` замість старого pass envelope; це не доказ помилки нового D1/D3 | `content_store_mechanism_keeps_deterministic_images_and_distinct_history_entries` збережено; семантичний witness потребує **окремого переписування за каноном**, не фальшивого PASS |
| `crates/sens/tests/d3_empty_control.rs` | `historical_truthiness_rows_cannot_reenter_current_tier1_authority` | Тест активного Rust-сьюту перевіряв історичні fixtures `truthiness` і їхню класифікацію, а не поведінку поточного exact-domain керування | `structural_empty_is_not_an_exact_d3_cond_predicate`, `non_d1_values_fail_closed_as_cond_tests` та інші поточні D1/D3 інваріанти збережено |

| `crates/sens/tests/decimal_comma_authority.rs` | `decimal_comma_semantics_are_owned_by_lisp_witness` | Ненормалізована Lisp-фікстура застосовує застарілий тричленний COND та падає з `UnsatisfiedConditional` | Нові поточні parser-only перевірки `decimal_comma_reader_preserves_exact_rational_identity` і `comma_inside_non_numeric_tokens_remains_symbol_data` зберігають граматику без старого control oracle |

| `crates/sens/tests/epistemic.rs` | 11 позитивних/аксесорних тестів `observation/claim/evidence/intent`, включно з `intent_capabilities_satisfied_is_true_when_all_requirements_present` | Спиралися на старі `t`/`()` та тричленні/неявні `COND` у реалізації Lisp; 11 із 35 падали у Hosted CI | **24** решта перевірок залишено, включно з `supporting_evidence_record_is_not_implicit_cond_truth`. Позитивна канонічна semantics/accessor parity — **BLOCK до L1–L7 та незалежного оракула** |

## Межа змін

- **Не** вилучено runtime-код, `language-contract.lisp`, чинні D1/D2/D3/D4–D10 закони, правила fail-closed, тести правильної логіки.
- **Не** перейменовано старий oracle на канонічний і не підмінено `UnsatisfiedConditional` на `()` у його очікуваннях вручну.
- Літерали, історичні fixtures, дослідження та коміти залишаються доступними для археології. Перенесення чинного Lisp-корпусу до L1–L7 — окреме завдання нормалізатора, не наслідок цього видалення.
- Перевірку правильності нових Rust-тестів слід виконувати на GitHub-hosted runner і не трактувати загальний зелений статус як доказ всієї семантичної міграції.

Пов'язано: [#5029](https://github.com/juv4uk/sens/issues/5029) і [#5143](https://github.com/juv4uk/sens/pull/5143).
