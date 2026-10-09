# Вилучення застарілих Rust-семантичних перевірок — 2026-10-09

Статус: історичний журнал для L1–L7 з #5140. Джерело: `main` на початковому зрізі `52d6dad377596de6f9cf164f009ab146853ce068`. Цей журнал не змінює контракт мови і не оголошує runtime правильним лише через видалення старих тестів.

| Активний файл до зміни | Оригінальний Git blob SHA | Рішення |
| --- | --- | --- |
| `crates/sens/tests/meta_eval_environment_semantics.rs` | `1beb5a4367e42dfed0a0d382f6b78cfd3da8efeb` | Знято `mutually_recursive_group_keeps_bindings_inside_lisp_data`: парність even/odd перевірялась через старі `t`/NIL і спадкову COND. Збережено lexical capture та shadowing. |
| `crates/sens/tests/meta_eval_evidence.rs` | `d0f21eb0e6b7ec6efc635c0f9f19747d430baa9d` | Знято три рекурсивні witnesses, що виводили семантичний pass із старих `t`/NIL COND результатів; залишено незалежні error-order, macro-arity, ordinary shadowing і recursive-group structure cases. |
| `crates/sens/tests/meta_eval_mutual.rs` | `f5becd1c7f7d0c9f1201f58057de4fff18e68b1f` | Обидва активні even/odd та три-member цикли залежали від старого T/NIL oracle. Джерело збережено у `docs/archive/historical/retired-rust-tests/meta_eval_mutual.rs.txt`, активний Rust-модуль видалено. |
| `crates/sens/tests/mccarthy.rs` | `30669582aa5d9e17203d33df14ec8ffecc500c0d` | Назву тесту McCarthy виправлено: він перевіряє лише quote/car/cdr/cons, не «сім примітивів». Runner не виконує historical-compatibility рядки та старе Contract 8.0 очікування `UnsatisfiedConditional` з fixture. Самі fixtures лишено. |
| `crates/sens/tests/d4_d5_append_dedup.rs` | `63d87459c9d268293e906b136cab3ff25f9dc1a1` | Збережено відхилення improper left spine для D4 і surface APPEND; прибрано вимогу до retired error-kind `UnsatisfiedConditional`. |
| `crates/sens/tests/sens_smoke.rs` | `fa08073bbf7666d1f0d4a48f1959488af801c191` | Знято smoke assertion, яка фіксувала flat Sens8 identity; базовий eval smoke залишено. Старий inventory-рядок прибрано. |
| `crates/sens/tests/sens_exactly_eight_bits.rs` | `b646d0c7658c4677bd3927efea2d425e7ecba024` | Знято глобальну вимогу, що кожний function identity/call head у всьому проєкті має бути рівно 8 біт. Архівний код не компілюється; поточні exact-width домени D1–D9 не зводяться до Sens8. |
| `crates/sens/tests/semantic_coordinate_matrix_845.rs` | `21111ee321674f1abc9e8ebed2ad45d71be922cd` | Знято активний test-axis observer, який формував scope через legacy Sens8 та стару SID-матрицю. Архівний код не є поточним semantic authority. |
| `crates/sens/tests/post_d4_control_derivation.rs` | `daa2e2e715ae6aabb904c449c20438ba4e1fa350` | GO/RETURN research із старим T/CONД переміщено до `docs/archive/historical/retired-rust-tests/post_d4_control_derivation.rs.txt`; видалено workflow, що запускав retired тест; research footprint script читає тільки archived provenance. |

## Межі

- Production Rust, бібліотеки Lisp, exact-domain координати та canonical fixtures не переписувались.
- D1/D3 positive/negative checks, structural EMPTY і fail-closed guards лишаються активними.
- Архівні `.rs.txt` файли — довідкова історія, не виконуваний код. Git blob SHAs наведено, щоб можна було відновити точне джерело.
- Після інтеграції потрібні GitHub-hosted `cargo test -p sens` і всі required workflow на **точному HEAD**. Червоний або відсутній статус = **HOLD**; видалення assertion не можна видавати за доказ проходження нової семантики.

Ратифікація: [#5140](https://github.com/juv4uk/sens/issues/5140). Поточна coordination/merge policy: [#5041](https://github.com/juv4uk/sens/issues/5041).
