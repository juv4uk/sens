# Археологія Rust-тестів: відмова від старої семантики (2026-10-09)

Цей запис — **історична provenance**, а не нова норма. Власник ратифікував L1–L7 у [#5140](https://github.com/juv4uk/sens/issues/5140). Вихідна база PR: `466848dfaa8582310c616b4b92cb7a97074e3ada`. Кожний blob SHA нижче відтворює старий файл через Git; архівні перевірки **не виконуються** як чинні семантичні Rust-тести.

| Старий шлях у `crates/sens/tests/` | Git blob SHA перед очищенням | Рішення |
| --- | --- | --- |
| `migration_cond_d1.rs` | `d599a4e047db5f843cee4de77e7f8d6d7f1589e0` | Видалити тест 8-бітної COND/migration truthiness |
| `sens_foundation.rs` | `478074548c8e1602057a7c0029ce0f5e3324e0ab` | Видалити твердження про плоску 8-бітну семантичну основу |
| `meta_eval_mutual.rs` | `f5becd1c7f7d0c9f1201f58057de4fff18e68b1f` | Видалити стару рекурсивну T/NIL-логіку |
| `post_d4_control_derivation.rs` | `daa2e2e715ae6aabb904c449c20438ba4e1fa350` | Видалити тести трипольової COND і T; research source як неактивний `.rs.txt` |
| `d3_empty_control.rs` | `e95a6011d0a7c331e0276cf2b22077cf60817527` | Видалити тільки historical-truthiness fixture assertion; чинні D1/D3 негативні тести зберегти |
| `meta_eval.rs` | `c5a3ad3e8a7aeb2750f536d9ef8c1a53df9a49a3` | Видалити п’ять функцій зі старими `(t ...)`/truthiness законами; інші функції лишити |
| `meta_eval_environment_semantics.rs` | `1beb5a4367e42dfed0a0d382f6b78cfd3da8efeb` | Видалити T/NIL recursive parity, зберегти lexical capture і shadowing |
| `meta_eval_errors.rs` | `4336441ac42b0e2f16ac497e0329c5e51a312e89` | Видалити очікування `UnsatisfiedConditional` для старої тричленної COND і спеціальний `t`-call |
| `meta_eval_evidence.rs` | `d0f21eb0e6b7ec6efc635c0f9f19747d430baa9d` | Видалити три T/NIL recursive-group witnesses |
| `ukrainian_api_docs.rs` | `8f0c0df09f9fcc413cdf1c59aaa7a99e64e07a93` | Видалити старі `істина/хиба → t/()` assertions; зберегти doc/surface checks |

Чинна семантична межа залишається у `contracts/answer-contract.lisp`, `language-contract.lisp` і ратифікованих D1–D9. `D1:0` — не `D3:000`; двочленна `D3:110 COND` сприймає лише доведені D1-відповіді. Відсутність CI-гвардії чи видалення тесту **не доводить** коректність production evaluator. Merge тільки після GitHub-hosted CI на точному HEAD.
