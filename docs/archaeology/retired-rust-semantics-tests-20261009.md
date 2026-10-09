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

## CI та реєстри

- Видалено лише застарілий workflow `.github/workflows/834-semantic-coordinate-targeted.yml`, який виконував виключно вилучений `semantic_coordinate_law_axis`. Оригінальний blob зберігається в Git: `a9699d8da7cb2c7cd4ad1ade67a152756715f090`.
- Із чинного `scripts/test-current-semantic-slice.sh` вилучено виклик відсутнього `semantic_coordinate_matrix_845`. Решта актуальних цілей, зокрема `d3_empty_control`, залишаються.
- З активного `tests/authority-inventory.lisp` та `.tsv` вилучено лише посилання на retired `semantic_coordinate_law_axis`; записи про давні `my-lisp` paths — історична provenance.
- `current-rust-tests-after-retirement.yml` окремо запускає збережені Rust-тести та перевіряє, що прибрані тестові цілі не з'явилися в поточному semantic-slice script.

Червоний CI **не** можна «виправляти» додатковим викреслюванням чинних exact-D1/D3 тестів; позитивні нинішні свідки мають бути перевірені окремо.

## Додатковий тріаж після hosted-прогону

[Run #37966767683](https://github.com/juv4uk/sens/actions/runs/37966767683) довів, що Rust-тести **компілюються**, але у старому `mccarthy.rs` виявив вісім семантичних невідповідностей. Вилучено лише ті старі твердження, чий зміст доведено неприйнятним для L1–L7:

- `implements_mccarthys_seven_primitives`: прибрано тільки стару `COND` з `()`-truthiness; перевірки `QUOTE/CAR/CDR/CONS` лишилися.
- `bootstrap_library_provides_list_utilities`: прибрано лише `FILTER`-assert, що припускав host-truthy `EQ`; незалежні `LENGTH/MAP/REDUCE` лишилися.
- `list_is_a_sens_function_in_core_my_not_a_rust_builtin`: прибрано застарілий `unwrap_err()` для `LIST` без `core.lisp`; позитивний результат `LIST` збережено.
- `linter_tests_from_my` та `meta_eval_lambda_witness_env_capture_and_application`: вилучені як Rust-оракули історичного Lisp-свідка, що не має прийнятого exact-domain перестворення; історичні `tests/fixtures/linter.lisp` та бібліотека лишаються в Git.

**Не вилучаємо для «зеленого» CI без окремого доказу:** `bootstrap_library_provides_let_and_let_star`, `symbolic_reasoning_layer_stays_loaded_and_tested`, exact-D1 `string<?` (на початковому hosted-прогоні повертав не-PredicateBit), а також сучасні D1/D3 негативні охоронці. Якщо чинний код повертає `()` або нетипований результат там, де повинен бути D1 `1/0`, це окрема проблема реалізації чи неперенесеного Lisp-корпусу, а не дозвіл вигадати стару семантику.

## Пряме вилучення з main за директивою «Rust знає лише драбину доменів»

- `crates/sens/tests/sens_exactly_eight_bits.rs` — плоский 8-бітний універсальний тест; первісний blob `b646d0c7658c4677bd3927efea2d425e7ecba024`, main-коміт `67c7eada3d57e12ffe51d9bddfbf483b4d742014`.
- `scripts/test-current-semantic-slice.sh` — Rust-вибірка зведена до п'яти чинних доменних тестів, Lisp-owned witnesses збережено; коміт `5231c29cfaea9a8313abb3e5e933f3da4adc8cb6`.
- `crates/sens/tests/sens_smoke.rs` — колишні arithmetic `(+ 40 2)` та W8 identity; blob `fa08073bbf7666d1f0d4a48f1959488af801c191`, main-коміт `1ff20d90b2a8098802aacecd016e4f3c8ad09cd1`; активні authority-inventory rows також прибрані.
- `crates/sens/tests/meta_eval_mutual.rs` — старі `t`-COND / лексичні expected; blob `f5becd1c7f7d0c9f1201f58057de4fff18e68b1f`, main-коміт `b5193f630a2a14d145bb6064c9f38a23ce35fc78`.
- `crates/sens/tests/meta_eval_environment_semantics.rs` — host-authoritative evaluation semantics; blob `1beb5a4367e42dfed0a0d382f6b78cfd3da8efeb`, main-коміт `c2aa2fc304a73e86597690f8d725e42a999f5c70`.
- `crates/sens/tests/meta_eval_evidence.rs` — host-authored Lisp semantic oracle; blob `a9e61d79471e890bf9a0b91828f9876590d8aafb`, main-коміт `867cf81af7a31314ad7df09f819cc1f409574ab6`.
- `AGENTS.md` отримав загальне правило «Rust: exact-domain carriers/transport; Lisp: meaning/laws», main-коміт `e6fb97ebaaf160da7d8f16ba5d68cebef26bf79f`.

Ці зміни не є твердженням, що всі Rust-оракули в усіх crates уже вилучено. Невибрані тести потребують індивідуального тріажу; runtime, compiler, host/GPU/FPGA транспорту й ратифіковані D1–D9 дані не видаляються сліпо.
