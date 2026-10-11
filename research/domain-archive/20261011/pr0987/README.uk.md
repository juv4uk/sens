# Архів PR #987 — виділення CLI із swarm-node

**Статус: ARCHIVE-ONLY / REPLAY REQUIRED.**

Збережені exact branch-head файли походять із `refactor/577-cli-v2`, SHA `50a06f95d03811fceb5049715e08cb32137c111d`. Поточний main має `crates/swarm-node/src/main.rs` 141,765 символів, проти 130,870 у гілці, і не має `crates/swarm-node/src/cli.rs`. Це доводить, що diff не можна злити як чисте переміщення без повторного вилучення з актуального файла та перевірки parity.

Намір — ізолювати Args/argv parsing/startup validation/usage text у модуль. Його можна реалізувати в поточному main після порівняння функцій, але цей архів не стверджує, що refactor вже інтегрований. Старі тексти збережені, нової гілки не створено.
