# SENS s0.42.3 — доказова підготовка патч-релізу

> **Кандидат, не опублікований реліз.** Попередній [s0.42.2](https://github.com/juv4uk/sens/releases/tag/s0.42.2) опубліковано 28.10.2026. Незмінний тег s0.42.3 ще не створено; реліз потребує явного GO власника.

## Обсяг виправлень

- D3 COND: хвостовий перехід передається чинному trampoline ([812851ed](https://github.com/juv4uk/sens/commit/812851edc86a3bc483d326756593c66eed345ba8)).
- Арена CONS: одна пара без повторної рекурсивної матеріалізації попереднього списку ([c0c41183](https://github.com/juv4uk/sens/commit/c0c41183737a84eefdd27cde0c5ee873f55973ef), імпорт PairNode [69350846](https://github.com/juv4uk/sens/commit/69350846d7d6fe66f37fcf07bcaa8640b55d0d40)).
- Contract 12.0 і мовні закони незмінні. Rust — механізм, Zig — T5M/F3C транспорт, SENS — семантика.

## Попередні докази, не для нового SHA

- [SENS CI #40683999847](https://github.com/juv4uk/sens/actions/runs/40683999847): SUCCESS на `69350846d7d6fe66f37fcf07bcaa8640b55d0d40`, включно з native SENS законами і focused preflight.
- [my-idea CI #40685416634](https://github.com/juv4uk/my-idea/actions/runs/40685416634): SUCCESS на `c36c67fa0a975244a9fb00c85fe9f963b818266d` з SENS gitlink `69350846`, 45/45 Node/Playwright, включно з 100k WASM/Web. [TUI #40684115863](https://github.com/juv4uk/my-idea/actions/runs/40684115863) SUCCESS.

**Це не доказ нового SHA з версією 0.42.3.** Вимагати окремого exact-head GitHub CI, native SENS REPL laws, повного release-preflight та всіх обов'язкових релізних збірок.

## Публікація

- [ ] Релізний SHA із зеленими required hosted CI / preflight.
- [ ] Явний власницький дозвіл для `s0.42.3`, видимості й точного SHA.
- [ ] Новий незмінний тег і завершений повний `.github/workflows/release.yml`.
- [ ] Після SENS-релізу: перепінити my-idea на опублікований SHA, оновити lockfile, пройти exact-head hosted IDE CI й тегувати `v0.13.9`.

Не пересувати `s0.42.2` та не обходити ворота.
