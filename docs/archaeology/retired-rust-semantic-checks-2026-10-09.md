# Вилучення застарілих Rust-семантичних перевірок — 2026-10-09

Статус: історичний журнал для власницької ратифікації L1–L7 у [#5140](https://github.com/juv4uk/sens/issues/5140). Початковий зріз цієї гілки: `57efd24eefec729f92b08c4ce6d89c9f9f63c8c2`. Зміни прибирають старі Rust-оракули, не змінюючи семантику runtime; відсутність тесту сама по собі не доводить коректність нового контракту.

| Активний файл до зміни | Оригінальний Git blob SHA | Рішення |
| --- | --- | --- |
| `crates/sens/tests/meta_eval_environment_semantics.rs` | `1beb5a4367e42dfed0a0d382f6b78cfd3da8efeb` | Знято `mutually_recursive_group_keeps_bindings_inside_lisp_data`: even/odd parity була закріплена через старі `t`/NIL та спадкову COND. Lexical capture/shadowing тести залишено. |
| `crates/sens/tests/meta_eval_evidence.rs` | `d0f21eb0e6b7ec6efc635c0f9f19747d430baa9d` | Знято рекурсивні witnesses, що виводили pass із старих `t`/NIL COND результатів; збережено незалежні error-order, macro-arity, shadowing та структурні SCC тести. |
| `crates/sens/tests/meta_eval_mutual.rs` | `f5becd1c7f7d0c9f1201f58057de4fff18e68b1f` | Обидва even/odd та three-member recursive tests залежали від старого T/NIL оракула. Код збережений як `docs/archive/historical/retired-rust-tests/meta_eval_mutual.rs.txt`, активний Rust-модуль видалено. |
| `crates/sens/tests/mccarthy.rs` | `36966cfc8712cac7266d698bce0ad1d72b8bb711` | Виправлено хибну назву тесту: він перевіряє quote/car/cdr/cons, а не «сім примітивів». Conformance runner не запускає історичні рядки compatibility та старий Contract 8.0 `UnsatisfiedConditional` oracle; fixtures залишені як provenance. |
| `crates/sens/tests/d4_d5_append_dedup.rs` | `63d87459c9d268293e906b136cab3ff25f9dc1a1` | Збережено негативну перевірку improper left spine для D4 та surface APPEND; знято вимогу до retired error-kind `UnsatisfiedConditional`. |
| `crates/sens/tests/sens_smoke.rs` | `fa08073bbf7666d1f0d4a48f1959488af801c191` | Знято smoke assertion, що фіксувала flat Sens8 identity; базовий eval smoke залишено, старий inventory-рядок прибрано. |
| `crates/sens/tests/sens_exactly_eight_bits.rs` | `b646d0c7658c4677bd3927efea2d425e7ecba024` | Знято глобальну вимогу «усі функції/call heads рівно 8 біт». Код збережено в некомпільованому .txt-архіві; D1–D9 не можна зводити до однієї Sens8 ширини. |
| `crates/sens/tests/semantic_coordinate_matrix_845.rs` | `21111ee321674f1abc9e8ebed2ad45d71be922cd` | Знято активний matrix observer, що формував scope через legacy Sens8 та історичну SID-матрицю. Архівний код не є чинним semantic authority. |
| `crates/sens/tests/post_d4_control_derivation.rs` | `daa2e2e715ae6aabb904c449c20438ba4e1fa350` | GO/RETURN research, що використовував старий T/COND fallback, перенесено в `docs/archive/historical/retired-rust-tests/post_d4_control_derivation.rs.txt`. Workflow, що запускав цей retired test, видалено; research footprint script працює з архівним provenance. |

## Межі зміни

- Production Rust, Lisp runtime/library sources, exact-domain coordinates та canonical fixtures не переписувалися.
- Чинні exact-D1/D3 позитивні й fail-closed негативні witnesses залишаються активними.
- Архівні `.rs.txt` файли — лише provenance, не виконуваний код. Blob SHA дозволяє ідентифікувати точне вихідне джерело.
- Перед merge потрібні GitHub-hosted `cargo test -p sens` та всі required workflows на точному HEAD. Червоний або відсутній статус = **HOLD**; не послаблювати gates заради green.

Single-writer/merge policy: [#5041](https://github.com/juv4uk/sens/issues/5041).
