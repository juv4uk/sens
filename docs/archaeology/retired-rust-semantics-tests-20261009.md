# Археологія Rust-тестів скасованої семантики — 2026-10-09

Власникове рішення: [L1–L7 #5140](https://github.com/juv4uk/sens/issues/5140), зокрема L1 exact-PredicateBit, L2 `t` не спец, L5 retired `structural-kind` / `identity-relation`.

**Цей документ — лише provenance.** Жоден запис не дозволяє відновлення історичних expected outputs у активних Rust-тестах. Оригінальні blob SHA збережено в Git; source/runtime, canonical fixture та domain-table файли ця зміна не переписує.

| Початковий Rust-тест | Git blob на `sens/main@466848dfaa8582310c616b4b92cb7a97074e3ada` | Що вилучено з active tests |
|---|---|---|
| `crates/sens/tests/meta_eval.rs` | `c5a3ad3e8a7aeb2750f536d9ef8c1a53df9a49a3` | Очікування truthiness з `COND (() ...)`, виклик `t` як default, макрос `my-if` зі старим `t`, рекурсивні функції з `t`-else, `not` з Lisp truthiness. Інші незалежні метаевалювальні smoke-тести лишаються. |
| `crates/sens/tests/mccarthy.rs` | `12282c8b2b0825ccc064c1ef2a855b3a9929353b` | Генератор `Lcg` і property cohort, який вважав будь-який `Value::is_truthy()` успіхом. `string<?` натомість звіряє `as_predicate_bit() == Some(true/false)`. |
| `crates/sens/tests/world.rs` | `9b40a6dbf3f366461224c30ec2596f5846f69a4e` | Шість кінцевих тестів `#1312` з активними очікуваннями `identity-relation`, `structural-relation` та `universal-t` як старих онтологічних категорій. Тести історії та переходів world лишаються. |
| `crates/sens/tests/semantic_coordinate_law_axis.rs` | `3c79982fde7b3bf37a8de3f3a8547bbdfe4a0aa4` | Повністю вилучено перевірку, що старі 8-бітні SID є *чинними* семантичними координатами `cond`, `car`, `eq?`, `cons`, та згадки про `identity-relation`. |
| `crates/sens/tests/semantic_coordinate_matrix_845.rs` | `21111ee321674f1abc9e8ebed2ad45d71be922cd` | Повністю вилучено історичний SID8/machine/math/kernel matrix observer із твердженнями про `identity-relation` та застарілу SID-первинність. |

## Що НЕ видаляємо

- `crates/sens/tests/d3_empty_control.rs`: негативні перевірки, що `D1:0` ≠ структурне `()` і `COND` приймає лише exact D1 0/1. Самі історичні рядки тут лише марковані як **нечинна provenance**, а не позитивні оракули.
- `crates/sens/tests/migration_d1_cond_cohort.rs`, `migration_eq_cond_cohort.rs`: поточні D1/D3 та фізичний T5, НЕ host truthiness.
- Чинні тести типової помилки на не-D1 тесті, двочленної `COND` та її вичерпання в `()` залишаються.
- Історичні Lisp-джерела та fixtures не переписуються навмання; L6 — тільки canonical regeneration + oracle.

## Повернення матеріалу до канону

Якщо частина історичного випробування потрібна в новій машині, створюється **окремий** тест із доказом відповідності L1–L7, точними D1/D3 координатами, актуальним Rust-оракулом і зеленим GitHub-hosted CI. Просте повернення старої назви або очікування `t`, `Nil` чи truthiness — заборонено.
