# Археологія Rust-тестів скасованої логіки — 2026-10-09

**Підстава:** ратифіковані власником правила L1–L7. Цей файл — лише історична довідка, а не виконувана семантика.

## Вилучені активні перевірки

| Файл / тест | Історичний Git blob | Дія і причина |
|---|---|---|
| `crates/sens/tests/migration_cond_d1.rs` | `d599a4e047db5f843cee4de77e7f8d6d7f1589e0` | Вилучено legacy SID8 `COND` / migration-only truthiness. |
| `crates/sens/tests/mccarthy.rs` — `property_tests_from_my`, генератор Lcg | `12282c8b2b0825ccc064c1ef2a855b3a9929353b` | Вилучено старий критерій успіху `Value::is_truthy()`. |
| `crates/sens/tests/forward.rs` — `match_test_condition_*_truthy/falsy` | `10ca0a6650ffaf4f29878f1930f6722d16d9cd0e` | Вилучено обидві перевірки generic truthiness у логіці правил. |
| `crates/sens/tests/ukrainian_api_docs.rs` — `istina_i_khyba_...` і `novi_predykatni_nazvy_...` | `8f0c0df09f9fcc413cdf1c59aaa7a99e64e07a93` | Вилучено Rust-еталон `t/()` і перевірку старого результату alias. Поверхневу документацію не видалено. |
| `crates/sens/tests/d3_empty_control.rs` — `historical_truthiness_rows_cannot_reenter_current_tier1_authority` | `e95a6011d0a7c331e0276cf2b22077cf60817527` | Вилучено Rust-сторож для історичних truthiness-рядків; ті самі старі фікстури зберігаються окремо як джерела. |
| `crates/sens/tests/canon_laws_v2_contract.rs` | `e80b2b6ecdc6965226f1461db5170b8b12d11265` | Вилучено активне оцінювання давніх layered-answer Canon V2 expectations. |
| `crates/sens/tests/structural_observation_contract.rs` | `2c13dc19e280cf455ffdb1bb4784f48f53b92eeb` | Вилучено Rust-прогін давнього структурного алгебраїчного свідчення, яке містить старі тричленні COND та identity-kind припущення. |
| `crates/sens/tests/semantic_coordinate_law_axis.rs` | `3c79982fde7b3bf37a8de3f3a8547bbdfe4a0aa4` | Вилучено Rust-еталон старої спільної Function8 адресації. |
| `crates/xtask/tests/license_policy.rs` — `superseded_truthiness_assertions_are_explicitly_classified_before_test_transition` | `81f51ec69c9610efb742de8c2f60e2eae689304a` | Вилучено примусову вимогу зберігати старі тести у чинному наборі. |

**Замість старої логіки в активних CI-завданнях:** `d3_empty_control`, `canon_d1_migration_cohort`, `domain_width_authority_test`; вони перевіряють точні D1-біти, структурний `()`, відхилення недопустимих умов і чинні координати. Наявні runtime і канонічні файли не переписуються цим набором комітів.

## Збереження історії

Початкові байти доступні через Git blob SHA та історію `main` станом на `466848dfaa8582310c616b4b92cb7a97074e3ada`. Ліспові фікстури і контракти не стиралися, але **не повинні виконуватися як поточні Rust-оракули**. Прямі Rust-тести історичного truthiness/structural-kind/identity-relation не є джерелом канонічної семантики.

Це вилучення не означає, що всі поточні Lisp-користувачі вже мігровані. Міграція залишається за L1–L7: точний PredicateBit `1/0`, двочленна COND, `t` тільки через явну L2 нормалізацію, відсутні координати → BLOCK + D10, помилковий parse → L7 HOLD, fixtures → L6 генератор. Без зеленого Hosted CI і незалежних оракулів `main` не змінювати.
