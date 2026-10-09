# Археологія: Rust не визначає закони мови (2026-10-09)

Директива власника: Rust має переносити точні бітові слова й доменну ідентичність D1–D9. Закон, назви функцій, логіка, результати предикатів і ратифікація належать SENS-контракту та Lisp-owned свідкам, не історичній SID8-матриці Rust.

Вилучені тести (історію збережено у Git, базовий коміт e0b7afd99b72eae78e0437f6dcf309e3099803eb):

- `crates/sens/tests/semantic_coordinate_join.rs`
- `crates/sens/tests/semantic_coordinate_join_2.rs`
- `crates/sens/tests/semantic_coordinate_matrix_845.rs`
- `crates/sens/tests/semantic_registry_lisp.rs`
- `crates/sens/tests/semantic_authority_guard_1049.rs`
- `crates/sens/tests/authority_guard_contract.rs`
- `crates/sens/tests/canon_authority_inventory.rs`
- `crates/sens/tests/core_profile_runtime_1272.rs`
- `crates/sens/tests/core3_profile_runtime_1414.rs`

Це усунення старих Rust-очікувань, **не** вимкнення реального виконання, транспорту, перевірки exact-width і domain-identity. Поточні доменні тести D1–D9 не видалені. Історичні дані зберігаються в контрактах, дослідних матеріалах та Git; вони не утворюють другого канону.

Решта Rust-реалізації й тестів потребує окремого аудиту на самостійні семантичні таблиці. Цей коміт не стверджує, що повний аудит завершений чи CI зелений.
