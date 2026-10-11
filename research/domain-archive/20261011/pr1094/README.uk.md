# Архів PR #1094 — модуль introspection для swarm-node

**Статус: ARCHIVE-ONLY / CURRENT-MAIN REPLAY REQUIRED.**

Три змінені шляхи з branch head refactor/577-introspect (SHA abba5b1e9a05225a7806d85c60fca43f889e4264) збережено безпосередньо в архіві. Гілка виносила обробники presence/status, delivery/status/metrics, join/leave/evict/compact/list-members у новий файл introspect.rs та змінювала видимість типів/полів. Однак чинний crates/swarm-node/src/main.rs виріс до 141,765 байтів, тож точний старий move не можна застосувати wholesale.

Унікальний module split і контрольований build-gate намір лишаються в архіві. Компіляція swarm-node уже додана до чинного .github/workflows/ci.yml комітом 7649512dbfe3d13b0477a26d842e3dbd25605922; це єдина активна частина, перенесена окремо. Сам код extraction потребує повторного виділення із чинного main.rs та parity-тестів. Нова гілка не створювалась.
