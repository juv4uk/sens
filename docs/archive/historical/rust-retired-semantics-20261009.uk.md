# Археологія вилучених Rust-перевірок спадкової семантики (2026-10-09)

Статус: **ненормативна історія**. У поточних Rust-тестах не повинні закріплюватися старі truthiness/T-NIL правила, тричленна COND чи плоска Sens8/Sid8-онтологія всупереч Contract 11.8 та чинним D1–D9. Цей файл зберігає причини вузьких вилучень, не змінюючи runtime чи Lisp-контракт.

| Шлях | Вилучена перевірка | Причина | Що залишено |
| --- | --- | --- | --- |
| `crates/sens/tests/meta_eval_errors.rs` | `canonical_cond_exhaustion_is_a_named_failure_in_native_and_meta_eval` | Очікувала `UnsatisfiedConditional` для вичерпаної/тричленної COND, а не поточний структурний `()` | Існуючі тести іменованих помилок, арності, неправильних lambda-параметрів |
| `crates/sens/tests/meta_eval.rs` | `cond_picks_the_first_truthy_clause` та сценарії `t`/truthiness і старої рекурсії/макросів | Закріплювали загальну truthiness та стару форму COND | Залишено приклади quote, арифметики, списків, застосування lambda і параметричного зв'язування |
| `crates/sens/tests/meta_eval_environment_semantics.rs` / `meta_eval_evidence.rs` / `meta_eval_mutual.rs` | Рекурсивні й взаємно-рекурсивні свідчення з `t`/NIL та старою COND | Результати спиралися на retired truth sentinel, тому не були незалежним доказом поточної семантики | Збережено актуальні перевірки closure, lexical capture/shadowing, binding і відмов |
| `crates/sens/tests/d3_empty_control.rs` | `historical_truthiness_rows_cannot_reenter_current_tier1_authority` | Перевіряла метадані історичних fixture-рядків, а не виконуваний закон | Збережено D1:0 проти структурного EMPTY, fail-closed для не-D1 і двочленну D3:110 COND |
| `crates/sens/tests/migration_cond_d1.rs` | `migration_cond_distinguishes_exact_d1_no_from_yes` | Старий eight-bit migration oracle не є поточним джерелом семантичної влади | Чинні exact-width D1/D3 тести залишаються |
| `crates/sens/tests/sens_foundation.rs` | Тести про універсальну Sens8 основу та aliases | Плоска Sens8/Sid8-модель — історичні/compatibility дані; поточна ідентичність зберігає точні біти й домен D1–D9 | Інші механічні перевірки round-trip та domain identity залишаються |
| `crates/sens/tests/forward.rs` | `match_test_condition_succeeds_when_the_expression_is_truthy`, `match_test_condition_fails_when_the_expression_is_falsy` | Вимірювали довільну truthiness rule-test виразу замість чинного explicit control/результатного контракту | Інші механічні тести forward / reasoning лишаються |
| `crates/sens/tests/mccarthy.rs` | `property_tests_from_my`, T/NIL assertion для `not?`, COND-перевірка в `implements_mccarthys_seven_primitives` | Generic `Value::is_truthy()` приймав різні форми результатів як один семантичний pass; `not?` і COND очікували стару пару `t`/`()` | Збережено exact arithmetic, reader/printer, closure, спискові примітиви й спільний поточний conformance corpus |
| `crates/sens/tests/content_store_authority.rs` | `content_store_semantic_relations_are_owned_by_lisp_witness` | Старий Lisp witness вимагав legacy pass-envelope, але поточне виконання повертало `()`; його не можна маскувати переписуванням очікування на PASS | Збережено тест детермінованих content-store images та окремих history entries |
| `crates/xtask/tests/license_policy.rs` + `tests/authority-inventory.tsv` | Облік знятого forward truthiness-тесту як активного `legacy-semantic` доказу | Видалена перевірка більше не повинна бути обов'язковим рядком активного реєстру | Інші класифікації та інвентарні рядки не чіпались |

## Історичні fixture-рядки

Рядки, явно позначені `role = "historical-compatibility"`, лишаються у спільному corpus як provenance. Rust-інтеграційний runner більше не трактує їх як поточні виконавчі очікування. Це **не** видаляє fixture і не оголошує, що їх уже мігровано; це лише знімає суперечність між архівним прикладом і поточним оракулом.

## Межі зміни

- Зміни стосуються тестів/їхнього інвентарю й археологічної нотатки; production-семантика, координати доменів, `language-contract.lisp` і самі historical fixtures не переписувались.
- Чинні exact-domain позитивні перевірки та fail-closed негативні перевірки залишаються.
- Вилучення червоного застарілого тесту не є доказом коректності runtime і не замінює окремого Lisp-виправлення/міграції.
- Перед злиттям потрібні GitHub-hosted `cargo test -p sens` і повний CI на точному HEAD. Якщо hosted CI не зелений — **HOLD**, не обходити gate.

Пов'язано: [#5029](https://github.com/juv4uk/sens/issues/5029), [#5140](https://github.com/juv4uk/sens/issues/5140), [#5148](https://github.com/juv4uk/sens/pull/5148), [#5150](https://github.com/juv4uk/sens/pull/5150).
