# Археологія: вилучені Rust-перевірки скасованої логіки (2026-10-09)

Директива власника: прибрати **активні host-authored перевірки старої семантики**, а не переписувати поточні правила SENS під старі очікування. Підстава: [L5 з ратифікованих L1–L7](https://github.com/juv4uk/sens/issues/5140) і [Rust semantic test retirement #1708](https://github.com/juv4uk/sens/issues/1708).

Цей файл — **ненормативний історичний реєстр**, не тестова фікстура і не авторитет семантики. Оригінальні версії можна відновити лише для дослідної археології за Git blob SHA нижче. Нічого не переносити автоматично у чинні тести або runtime.

| Старий файл | Вихідний blob SHA | Виведено з active Rust tests |
|---|---|---|
| `crates/sens/tests/forward.rs` | `10ca0a6650ffaf4f29878f1930f6722d16d9cd0e` | `run_multi_supports_test_conditions`, `match_test_condition_succeeds_when_the_expression_is_truthy`, `match_test_condition_fails_when_the_expression_is_falsy`: старі очікування неявної істинності умови в rule engine |
| `crates/sens/tests/ukrainian_api_docs.rs` | `8f0c0df09f9fcc413cdf1c59aaa7a99e64e07a93` | `istina_i_khyba_ie_imenamy_tyh_samykh_kanonichnykh_znachen`, `novi_predykatni_nazvy_i_stari_aliasy_vykonuiutsia_odnakovo`: старі `t/()` sentinel-очікування замість exact D1 і незалежного Lisp-оракула; допоміжний `uk_session` не потрібен |
| `crates/sens/tests/mccarthy.rs` | `12282c8b2b0825ccc064c1ef2a855b3a9929353b` | `property_tests_from_my`: приймав довільне `Value::is_truthy()` замість доведеного D1; видалено тільки невикористані генератори `Lcg` / `alist_list` |
| `crates/sens/tests/d3_empty_control.rs` | `e95a6011d0a7c331e0276cf2b22077cf60817527` | `historical_truthiness_rows_cannot_reenter_current_tier1_authority`: старе Rust-очікування наявності historical truthiness records в активній фікстурі; актуальні негативні D1/D3-тести лишаються |
| `crates/sens/tests/migration_cond_d1.rs` | `d599a4e047db5f843cee4de77e7f8d6d7f1589e0` | окремий compatibility-only тест історичного SID8 `COND`, не нова нормативна основа |
| `crates/xtask/tests/license_policy.rs` | `81f51ec69c9610efb742de8c2f60e2eae689304a` | `superseded_truthiness_assertions_are_explicitly_classified_before_test_transition`: сам вимагав зберігання retired Rust assertions у чинному inventory |
| `tests/authority-inventory.tsv` | `b95cc2b45a0451d27c9a88d29f328d6b9eef74f4` | видалено п'ять outdated рядків із старими `t/()`, truthiness, історичним `t` sentinel; поточну перевірку exact large literal рекатегоризовано як спостерігача |

**Залишено як чинні регресійні гарантії:** `D3:110` двочленний `COND`, керування через точний `D1:1 / D1:0`, структурне `()` як окремий результат, відхилення не-D1 тестів/трипольної `COND`, поточні числові/механічні та структурні тести й незалежні Lisp-owned оракули. Негативний тест, який *забороняє* застарілу поведінку, не є вимогою старої поведінки й не підлягає загальному видаленню.

**Межа:** зняття застарілих Rust-oracles не означає, що нинішній GitHub-hosted CI є зеленим; тестові відмови повинні вирішуватися за чинним каноном. Жодного «зеленого» результату через зміну expected-відповіді.

## Додатковий прохід: Rust meta-evaluator, CLI та WASM (2026-10-09)

| Старий файл | Git blob SHA | Вилучена скасована перевірка |
|---|---|---|
| `crates/sens/tests/meta_eval.rs` | `c5a3ad3e8a7aeb2750f536d9ef8c1a53df9a49a3` | Чотири old-logic тести: `cond_picks_the_first_truthy_clause`, `defmacro_expands_before_evaluating_using_unevaluated_argument_forms`, `self_recursive_top_level_def_sees_its_own_binding`, `recursive_factorial_matches_native_language_meaning`. Прибрано також `t` self-evaluation та old `not` з очікуваним `t`. Залишено числові, парні й лексичні механізми. |
| `crates/sens-cli/src/repl.rs` | `377cbf3980013fa806559c3ba7eb134a52440d57` | Із surface-тесту прибрано fallback `хибне?` як `t/()` і повернення `істина→t, хиба→()`; перемикання поверхонь і ізоляція binding залишені. |
| `crates/sens-wasm/src/lib.rs` | `c13f713eb058847003fa28145da971b19015827d` | Прибрано старе презентаційне `t/()` у WASM. Залишено перевірки перемикання поверхонь, збереження сесії й замикань. |

Це вилучення **старих очікувань**, а не доведення нових семантичних законів; чинний exact D1/D3 перевіряє окремий Lisp-owned корпус. Без жодних змін у production evaluator.
