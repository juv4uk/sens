# SENS: усі наявні гілки → одна `main` — облік станом на 11.10.2026

> Директива власника: не створювати жодних нових гілок. Це **доказовий аудит**, а не масове git merge історичних дерев і не твердження, що весь код 4 133 гілок уже злитий. Записано **прямо в `main`**.

## Повна інвентаризація доступних refs

GitHub REST `GET /repos/juv4uk/sens/branches?per_page=100&page=N`, сторінки 1–42, остання має 33 ref; сторінка 43 порожня. Послідовні каталоги фіксують назву й точний commit SHA **кожної з 4 133 наявних на момент обходу гілок**, включно з `main`:

- [частина 1: 1–1400](20261011-sens-existing-branches-part1.tsv)
- [частина 2: 1401–2800](20261011-sens-existing-branches-part2.tsv)
- [частина 3: 2801–4133](20261011-sens-existing-branches-part3.tsv)

Повторним читанням трьох файлів на `main` встановлено: **4 133 унікальні назви гілок**, **4 034 різні SHA голів** (99 додаткових refs вказують на SHA, які вже зустрічаються; це не 99 доведених дублів семантики). Префікси: `fix/` 941; `research/` 642; `replay/` 433; `feat/` 300; `agent/` 216; `impl/` 171; `bench/` 168; `test/` 113. Інші назви й префікси — у трьох TSV. Ці дані є **знімком**: зміну ref під час пагінації не виключено. Видалені у минулому гілки, неліцензовані/недоступні PR і донори з інших repo не входять до переліку наявних refs і потребують окремого all-time recovery.

## Семантична перевірка проти актуального main (початкові 12 refs)

Результат GitHub REST compare `base=main, head=ref` під час огляду 11.10.2026 (поточний `main` змінюється, отже behind можна збільшити при подальших commits):

| Branch | ahead / behind | Рішення для Git ancestry |
|---|---:|---|
| `604-lisp-coverage-binary-clean` | 0 / 5384 | **ALREADY-IN-MAIN** — ref не має власних незлитих ancestry commits |
| `1413` | 0 / 6908 | **ALREADY-IN-MAIN** |
| `feature/core1-domain-physical-canary-20261008` | 0 / 5338 | **ALREADY-IN-MAIN** |
| `feat/1098-sid-binary-identity` | 0 / 7321 | **ALREADY-IN-MAIN** |
| `test/291-exact-quantity-roundtrip-authority` | 0 / 7961 | **ALREADY-IN-MAIN** |
| `archive/d10-canonical-topological-order-proof-20261011` | 3 / 80 | **DIVERGED: dedup**; звірити наявний архів доказу |
| `research/d10-canonical-ledger-evidence-batch23-20261011` | 62 / 81 | **DIVERGED: HOLD**; старе 653→698 не перезаписує живий реєстр |
| `fix/d10-yantra-dual-provenance-20261010` | 3 / 748 | **DIVERGED: dedup/negative witnesses** |
| `replay/4506-eq-cond-current-main` | 1 / 5232 | **DIVERGED: dedup** |
| `impl/3394-d6-selectors-on-3530` | 12 / 5976 | **DIVERGED: змінився контракт, review до перенесення** |
| `research/2036-rewrite-normal-form` | 3 / 6424 | **DIVERGED: historical proof review** |
| `bench/adaptive-carrier-decode-current-main-20261010` | 1 / 217 | **DIVERGED: measurement provenance/CI review** |

**5 із 12** зразків уже включені в ancestry `main`; **7 із 12** розійшлись і не мають права на автоматичне злиття. `DIVERGED` не доводить ні незалежності нового закону, ні відсутності однакових байтів у `main`. Це лише перший доказовий зріз, не підсумок 4 133.

## Заборона нових гілок

В [AGENTS.md](../../AGENTS.md) на початку додано `SENS-ALL-BRANCHES-MAIN-ONLY-20261011`: всім агентам **заборонено** branch-create, тимчасові refs, інші merge staging, «нову PR-гілку». Допустимі записи — перевірені атомарні commits на `main` через single-writer #5041. GitHub API `GET /repos/juv4uk/sens/rulesets?includes_parents=true` відповів **[]**: серверна політика створення гілок не активна. Цей GitHub connector **не має write-операції для rulesets**, а віддалений Desktop Commander наразі offline — не можна правдиво оголосити GitHub-side заборону технічно встановленою. Адміністратору потрібен активний branch ruleset `Restrict creations` з target **all branches**, без bypass для агентів; це не забороняє оновлення вже наявного `main`. Не включати `Restrict updates` як замінник цієї вимоги.

## Доказове приймання, не масове злиття

Для кожного запису зі списку:

1. Повторити `main...ref` compare за точним SHA та перевірити, чи вже є equivalent source Git blob/semantic stable ID у `main`. `ahead=0` → ancestry already in main.
2. Для `ahead>0`: positive + falsifier + provenance + contemporary Contract 11.8; відмінний прийнятний зміст додати в `main` після чинних required CI. Якщо gate блокує без можливості пройти на єдиній гілці — **BLOCKED** і ескалація #5041, не створювати нової.
3. Застаріле або суперечливе — не запускати. Зберігати **інертне** походження SHA/path у `main`; вердикт `DUPLICATE`, `REJECT` чи `OWNER-REVIEW` із доказом.
4. Урахувати видалені гілки й закриті PR з усієї історії за #5549 і координаційним #2786; для D10 зберігати research-unratified, не підміняти selected/ratified.

**Ні один лише каталог refs, ні злиття історії без перегляду не є виконанням вимоги «весь код у main».** Показник завершення: кількість *перевірених* refs з конкретним main SHA / accepted code / задокументованим дублікатом чи відхиленням, а не кількість створених гілок і PR.
