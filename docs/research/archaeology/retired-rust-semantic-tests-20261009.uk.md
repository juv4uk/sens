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

## 2026-10-09 — наступне очищення, commit 0b629892

- `crates/sens/tests/meta_eval.rs` (`c5a3ad3e8a7aeb2750f536d9ef8c1a53df9a49a3`): знято п’ять Rust-тестів історичних `COND`/`t` і старий self-evaluating `t`; сучасні арифметичні, lambda, pair тести збережені.
- `crates/sens/tests/sens_foundation.rs` (`478074548c8e1602057a7c0029ce0f5e3324e0ab`): знято тести, які називали Sens8 канонічною семантичною ідентичністю.
- `crates/sens/tests/semantic_coordinate_law_axis.rs` (`3c79982fde7b3bf37a8de3f3a8547bbdfe4a0aa4`): знято застарілий observer 8-бітного Function8 як доменного авторитету.
- `.github/workflows/834-semantic-coordinate-targeted.yml` (`a9699d8da7cb2c7cd4ad1ade67a152756715f090`): застарілий CI target `semantic_coordinate_law_axis`; workflow підлягає вилученню, бо інакше гарантовано викличе неіснуючий тест.


### 2026-10-09: Content Store — знято Rust-обгортку старої COND-семантики

- `crates/sens/tests/content_store_authority.rs`, вихідний Git blob `0955eb39dbdc54743155f310ae99aa8da5724512`: видалено **лише** `content_store_semantic_relations_are_owned_by_lisp_witness`.
- Причина: `tests/fixtures/content-store-authority-witness.lisp` містить тричленні клаузи `COND (query expected result)` старого семантичного контракту; власник ратифікував L1: **точний D1 PredicateBit, двочленний COND, вичерпання — структурне `()`**. Rust-вимога, щоб цей retired witness повертав `(content-store-authority-witness (status pass) ...)`, не є чинною гарантією.
- Збережено `content_store_mechanism_keeps_deterministic_images_and_distinct_history_entries` (серіалізація та кількість записів). Архівну Lisp-фікстуру не переписано й не видалено; її семантичне оновлення можливе лише через reader → L1–L7 → exact-domain emitter → незалежний оракул.


## Подальше вилучення історичних Rust-оракулів — 2026-10-09

| Шлях | Початковий Git blob SHA | Вилучений тест | Причина |
|---|---|---|---|
| `crates/sens/tests/canon_adversarial.rs` | `6b8ab8f372a5e8c38d32c49d0c1d9f56cb998025` | `cond_surface_stops_at_the_first_true_clause` | Rust-authored outcome через спадкові `totzhne?/abheda` surface-вирази й «першу істинну клаузу»; замість окремого авторитету Rust за актуальний exact D1/D3 відповідає незалежний Lisp-owned oracle; решта binding/quote/fail-closed механізмів у файлі збережена. |
| `crates/sens/tests/world.rs` | `e60b04f091950f278a580ed7df69796b06af5d73` | `defmodule_after_world_load_keeps_legacy_reason_in_behavior` | Rust-oracle, який закріплював historical `reason-in` proof-shape. Інші тести реального world snapshot, transaction atomicity, history, query та interface механіки залишені. |

Жоден production evaluator чи source library не змінюється. Не прибирати захисні тести `D1:1/0`, `D3:000`, wrong-domain/non-two-part `COND`.
