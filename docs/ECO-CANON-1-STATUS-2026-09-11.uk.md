# Стан ECO-CANON-1 — 2026-09-11 (оновлено 2026-09-20)

Завдання: [my-lisp#75](https://github.com/juv4uk/my-lisp/issues/75)  
Виведення generated-проєкції з ролі вхідного API: [my-lisp#1004](https://github.com/juv4uk/my-lisp/issues/1004)

## Принцип

```text
Canon / ідентичність таблиці функцій живе в lib/surface/semantic-registry.lisp
відображуване написання ≠ ідентичність
generated function-table = відтворювана проєкція, а не вхідна семантична влада
```

## Поточна влада і проєкції

| Частина | Роль |
|---|---|
| `lib/surface/semantic-registry.lisp` | Єдина влада числових ідентичностей і peer-surface |
| `scripts/generate-function-table.lisp` | Lisp-owned генератор проєкції; читає registry безпосередньо |
| `lib/generated/function-table.lisp` | Машиночитана оглядова/вихідна проєкція (`ft/2`) |
| `docs/generated/function-table.md` | Людська оглядова проєкція, яка може приєднувати metadata машинної реалізації |
| `lib/machine/intel-core-i5-6400.lisp` | Лише фізична execution/mechanism-проєкція; не може створювати значення |

Живий registry зараз містить **170 ідентичностей загалом**:

- `00000000` — структурне `()`;
- **169 callable/form ідентичностей**, які проєктуються в generated function table.

Схема generated table:

```text
ft/2:
(sid-bitstring formal (uk ...) (ukr ...) (en ...) (sa ...) (sym ...) authority)
```

`ukr` — повна українська peer-surface того самого SID. Окремого namespace
`full-uk` не існує.

## Напрям семантичної влади

```text
lib/surface/semantic-registry.lisp
        ↓
один Canon/function-table SID
        ↓
generated/review проєкції
        ├─ lib/generated/function-table.lisp
        └─ docs/generated/function-table.md
        ↓
огляд / tooling, який явно трактує їх як проєкції
```

Зворотний напрям для семантичної влади заборонений:

```text
generated проєкція
        ✗
реконструювати / перевизначати значення SID
```

У межах #1004 активні українські генератори й coverage-перевірки переводяться
з `lib/generated/function-table.lisp` як вхідного API безпосередньо на
`lib/surface/semantic-registry.lisp`.

## Українські surface-колонки

| Колонка | Джерело |
|---|---|
| `uk` | registry `uk` surface |
| `ukr` | registry `ukr` peer surface |
| `en` | registry `en` surface |
| `sa` | registry `sa` surface |
| `sym` | registry `sym` surface |
| `authority` | `my-lisp` у generated оглядовій проєкції |

Генератор не вигадує відсутнє peer-написання і не виводить один surface
namespace з іншого.

## Reader-sensitive випадок апострофа

Символьна surface identity `quote` зберігається в registry як рядок:

```lisp
(sym "'")
```

Так registry лишається звичайними повторно читабельними Lisp-даними без
конфлікту з reader shorthand для quote. Generated-проєкції механічно
зберігають це представлення; окрема семантична реконструкція не потрібна.

## Що дозволено споживачам generated table

Дозволено:

- оглядати generated artifact як вихід, що тестується;
- перевіряти формат і схему цієї проєкції;
- перевіряти, що machine-specific metadata реалізації не забруднила її;
- публікувати або pin-ити її явно як похідний artifact.

Не дозволено:

- виводити з неї semantic identity coverage, коли доступний registry;
- трактувати generated row як незалежну SID→meaning владу;
- реконструювати з неї значення, якого немає в Canon/function-table authority;
- створювати hand-maintained таблицю-заміну.

## Команди

```bash
cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
python3 scripts/check_semantic_registry.py
```

## Залишкова робота

- #1046 відповідає за зведення meaning/domain/law + admitted mechanisms до
  наявного Canon/function-table identity row.
- #1049 відповідає за загальний структурний guard проти host/island
  SID→meaning влади поза Canon.
- #1004 виводить generated function-table саме з ролі активного input API,
  зберігаючи її як відтворювану output/review проєкцію.

## Правило готовності для інших репозиторіїв

Коли потрібні semantic identity або peer-surface дані, слід віддавати перевагу
авторитетному registry. Споживач може використовувати опубліковану generated
function-table лише як явно pin-нуту **похідну проєкцію**; вона ніколи не має
ставати незалежним джерелом значення Lisp.
