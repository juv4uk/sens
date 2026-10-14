# Хронологія семантики `narrate` / `reason` і контроль міжфайлової міграції

**Дата зрізу:** 2026-10-14. **Завдання:** підготовка інтеграції PR [#5765](https://github.com/juv4uk/sens/pull/5765) без неявного присвоєння D9/D8 викличності, відкотів змін інших виконавців або злиття застарілого CI.

## Джерело істини та історичні повороти

| Коли (UTC) | Коміт | Перевірений семантичний поворот |
| --- | --- | --- |
| 2026-09-18 00:20 | [`b5a128f8`](https://github.com/juv4uk/sens/commit/b5a128f8b1c7c85ded7670be8f94f1e153e7f8e3) | `narrate-outcome` почав відхиляти структурні теги, зокрема пару й порожній список; це давніша передумова, ніж теперішня міграція `SYMBOL?`. |
| 2026-09-25 22:21 | [`1be761d2`](https://github.com/juv4uk/sens/commit/1be761d203db) | `reason` переводили на тодішні коди SENS; цей шар **не є дозволом** автоматично тлумачити історичний SID8 як сучасний D8. |
| 2026-10-10 02:45 | [`a2c68486`](https://github.com/juv4uk/sens/commit/a2c684863427) | У `reason` тричленний історичний `COND` замінено двопольовим; свідки мають використовувати чинну форму. |
| 2026-10-11 18:16–18:17 | [`0b7a4bae`](https://github.com/juv4uk/sens/commit/0b7a4bae1b775beb1c1c3fc741f462f156c4c99a), [`0376e4f0`](https://github.com/juv4uk/sens/commit/0376e4f0159e2960fb590d0cead536df967952c7) | Перенесено історичні функціональні голови в `reason` (384) і `narrate` (177). Ідентичність дорівнює **(домен, ширина, біти)**, а не лише бітовому тексту. |
| 2026-10-13 19:22 | [`a6be2ae8`](https://github.com/juv4uk/sens/commit/a6be2ae8df9165ba86b96b36a3b35d34648da386) | Структурні перевірки двох/трьох комірок `narrate` замінили стару аритметику довжин; важливий реальний D3/D4-донор. |
| 2026-10-13 22:55 | [`37c9756b`](https://github.com/juv4uk/sens/commit/37c9756b0219154a72fecb0c97025e490616e3a0) | Дванадцять fallback `ATOM(QUOTE NIL)` → точний D1:YES в `narrate`, без зміни COND-тіл. |
| 2026-10-13 23:10 | [`9b8f90a9`](https://github.com/juv4uk/sens/commit/9b8f90a9028849e024e05651370e46e352720a49) | У `reason` глибину перейменування зроблено структурною (D3 CONS), не неявним D24-числом. |
| 2026-10-14 00:52 | [`fe9493bb`](https://github.com/juv4uk/sens/commit/fe9493bbcb2fe310a594ae542bbd090ea0d99b12) | У PR #5765 одноразове D6 LET для `narrate-answer` замінено негайно викликаною D4 LAMBDA; свідок з 1-бітним мутантом. |
| 2026-10-14 05:57–09:23 | [`1db34028`](https://github.com/juv4uk/sens/commit/1db340282815853af8ea287c896151ad4c4343e3), [`341b7923`](https://github.com/juv4uk/sens/commit/341b79237248ebd6df9bb6a7b0b83a5719bf7518), [`65ebf11b`](https://github.com/juv4uk/sens/commit/65ebf11bfa10150b3afa0d288b90b764d8fe4fbd) | Послідовно прибрано зайві D9 FIFTH, PROVENANCE і SYMBOL? виклики. **Не** замінювали SYMBOL? на ATOM: `narrate-outcome` зберіг D3-перевірку структурної голови, точні EQ з шістьма тегами й fail-closed fallback. |
| 2026-10-14 09:59–10:07 | [`fb423dc1`](https://github.com/juv4uk/sens/commit/fb423dc11ab882ac74742b0e4a0b200573f02d7), [`115a4789`](https://github.com/juv4uk/sens/commit/115a47897ca8) | У PR уведено **суворий preview із blob-pinned D4 DEFINE** і забороною невідомої викличної голови. Це лише доказ текстового зв'язування, не автоматичний дозвіл публікації фізичної програми. |
| 2026-10-14 10:26–11:14 | [`0a4c4637`](https://github.com/juv4uk/sens/commit/0a4c46379e3f), [`5ddc1624`](https://github.com/juv4uk/sens/commit/5ddc16249d3a), [`d1a25ae1`](https://github.com/juv4uk/sens/commit/d1a25ae18a7cf6f94bd36a3a6590b482b45ab617) | Додані native physical T5-проби й **обмежений структурний підзакон**. Не плутати успіх D3/D4-структурних випадків із повним `narrate` на довільних D7-символах. Одноразові probes з центрального CI потім знято. |

## Чинний міжфайловий контракт

У `lib/reason.lisp` реально визначено `(0011 provenance-list (0010 (nodes) ...))` — це SENS `DEFINE`, а не просто назва таблиці. У `lib/narrate.lisp` вживання `(provenance-list (100111 proof))` потребує **того самого** зв'язування під час виконання.

Існуючий preview в PR #5765 вже підтримує явне
`--linked-definition lib/reason.lisp@<точний-Git-blob-SHA1>:provenance-list`.
Перевіряльник `scripts/migrate-t5-batch.py::verified_linked_definitions` вимагає точний Git blob, один справжній D4 DEFINE, забороняє duplicate names та вже ратифіковані domain surfaces. Звіт маркирує такий імпорт `D4_DEFINE_LEXICAL_ONLY`, `runtime_admitted=false`. **`--write` з імпортами залишається забороненим**.

Це суттєва межа: D7 може переносити текстову ідентичність зв'язування, однак сам по собі не перетворюється на callable D9, D10, або physical T5 semantic authority. Без чинного runtime binding і позитивного/негативного самосвідка міграцію не сертифікувати.

## Підтверджені та ще не підтверджені результати

- На точному PR HEAD [`d1a25ae1`](https://github.com/juv4uk/sens/commit/d1a25ae18a7cf6f94bd36a3a6590b482b45ab617) [центральний CI #38555206632](https://github.com/juv4uk/sens/actions/runs/38555206632) завершився **SUCCESS**. Серед перевірених кроків: blob-pinned linked T5 transport, NARRATE SENS D4/law + 1-bit mutant, загальний фізичний T5 transport oracle. **FULL_CARGO_WORKSPACE було skipped**, не оголошувати його зеленим.
- Є окрема пара SENS-фікстур `tests/fixtures/narrate-structural-physical-{law,mutant}.lisp` для D2/D3/D4. Вона навмисно не заявляє паритету Lisp/quoted D7 Symbol для всього narrator. Фізична придатність носія ≠ семантичне виконання всього файлу.
- Раніше виконаний `scripts/migrate.py preview` на `narrate` послідовно знімав D9 FIFTH, PROVENANCE, SYMBOL?, після чого виявив неімпортоване `provenance-list`. **Наразі суворий blob-linked preview уже реалізовано в самій PR**: не потрібно створювати другий linker.
- Стара база PR #5765 (`4c216b3cbbafada430cff417655f6e9964cd1077`) відстає від `main`. PR містить кілька production і test файлів, у тому числі модифікації мігратора та CI. Без механічного 3-way і свіжих SHA **не переносити весь snapshot CI або domain foundation з PR у main**.

## Практичний handoff для інтегратора #5041

1. Перевірити найновіші Git blob-и `lib/reason.lisp` та `lib/narrate.lisp`, починаючи із власних source definitions, а не з історичного SID8-словника.
2. Використати **вже існуючий** strict linked preview із blob-pinned `provenance-list`; перевірити негативи stale blob, невідоме callable ім'я, дубль DEFINE та фізичне `--write` без runtime admission.
3. Зберігати результат `BLOCKED`, коли D7 quoted-symbol vs runtime Symbol parity ще не доведено; не замінювати `SYMBOL?` на `ATOM`, не надавати D9 право виклику за резидентністю.
4. Переносити лише схвалені вузькі зміни PR #5765 на **свіжий main** із перевіркою точних Git SHA. Усе нове в `.github/workflows/ci.yml` треба інтегрувати в наявний **єдиний** автоматичний workflow, не відновлюючи старий snapshot.
5. Заявляти фізичний повний narrator PASS лише за окремим SENS-owned фізичним T5 law / negative witness, де справжнє `reason` зв'язування й D7 quoted symbol виконуються без хостової підміни.

**Координація:** [#5029](https://github.com/juv4uk/sens/issues/5029) — CLAIM і взаємне розведення ділянок; [#5041](https://github.com/juv4uk/sens/issues/5041) — контрольована інтеграція. Це історичний/доказовий документ, а **не** новий нормативний семантичний авторитет.
