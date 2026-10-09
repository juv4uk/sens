# Rust-тести знятої семантики — 2026-10-09

Зміна стосується лише застарілих тестових тверджень. Чинні D1/D3-тести збережено.
Канон: предикат точно `1`/`0`; `()` — структурне значення, а не predicative truthiness; `COND` споживає D1 PredicateBit; `t` не є спеціальною клаузою.

Вилучено:
- `structural_observation_contract.rs` (#218 structural-kind): вилучений окремим паралельним комітом у main;
- `migration_cond_d1.rs` (історичний восьмибітний COND): вилучений окремим паралельним комітом у main;
- `canon_let_ephemeral_diagnostic.rs`: тимчасові старі ATOM/EQ/COND/LET-проби;
- із `canon_surface.rs`: історичні English/uk/sa порівняння, включно зі старим COND; залишено лексичний контракт;
- із `mccarthy.rs`: стару перевірку COND на структурному `()` (вже вилучено паралельно у main);
- із `world.rs`: `backward_reasoning_reads_the_selected_world_snapshot`, `backward_reasoning_keeps_independent_branches_isolated`, `advise_world_accepts_into_a_new_queryable_world`, `advise_all_world_accepts_one_atomic_dependent_batch`, `world_package_import_atomically_creates_a_queryable_child` — тричленні клаузи `ATOM` та неявні `(t ...)`.

Код старих перевірок збережено у Git-історії до вилучення. Це не ратифікація альтернативної семантики й не зміна production evaluator.
