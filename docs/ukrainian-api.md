# Українська програмна поверхня SENS

**Статус:** актуальний довідник human surfaces для Contract 11.7.

Українські назви — це **проєкції над exact-domain semantic identity**, а не окремі semantic IDs. Канонічні human-readable таблиці лежать у `lib/domains/d1.lisp … lib/domains/d8.lisp`, по одному домену на файл.

Старий `lib/surface/semantic-registry.lisp` і generated Function8/Sens8 таблиці можуть лишатися для compatibility/provenance. Вони **не визначають current placement або meaning**.

## Дві українські колонки

У current domain tables:

- `ук` — компактна програмна форма;
- `укр` — повна українська розшифровка.

Обидві ведуть до **того самого exact `(domain,bits)` resident-а**. `укр` не є другою функцією.

Приклади:

| `ук` | `укр` | Пояснення |
|---|---|---|
| `п-р` | `перше-від-решти` | selector-path: `п=перше`, `р=решта` |
| `видалити!` | `видалити-на-місці!` | destructive/in-place operation |
| `нсд` | `найбільший-спільний-дільник` | усталене математичне скорочення |
| `а-короткий` | `звук-голосний-а-ротовий-короткий` | D7: domain context прибрано з compact surface |

Повні списки не дублюються в документації — дивіться відповідний `lib/domains/dN.lisp`.

## Предикати: `?`

Предикатна surface закінчується на `?` у програмних колонках:

```text
ук   атом?
укр  атом?
en   atom?
san  aṇu
```

`san` не використовує програмний знак `?`.

Предикат повертає **PredicateBit D1**:

```text
1 = YES
0 = NO
```

Structural `()` — це D3 `000`, а не predicate false.

## Мутація: `!`

Destructive/in-place operations мають `!` синхронно в `ук`, `укр` та `en`:

```text
ук    видалити!
укр   видалити-на-місці!
en    delete!
LISP  DELETE
```

`LISP` лишається історичним/reference spelling; `san` не використовує програмний `!`.

## Selector-path: `п/р`

Для складених selector-ів compact `ук` використовує стабільну path-граматику:

```text
п = перше
р = решта

CAAR   → п-п
CADR   → п-р
CDAR   → р-п
CDDR   → р-р
CADDR  → п-р-р
```

Повна форма зберігається в `укр`.

## Скорочення

Ми скорочуємо **структуру**, а не корені слів. Не вводяться випадкові форми на кшталт `відобр`, `посл`, `заст`.

Допустимі:

- сталі граматичні маркери `?`, `!`;
- selector-path `п/р`;
- усталені скорочення `нсд`, `нск`;
- вилучення надлишкового domain-контексту в D7, коли `укр` зберігає повне пояснення.

Докладніше: [`uk-surface-naming.md`](uk-surface-naming.md).

## Де лежать таблиці

```text
lib/domains/d1.lisp
lib/domains/d2.lisp
lib/domains/d3.lisp
lib/domains/d4.lisp
lib/domains/d5.lisp
lib/domains/d6.lisp
lib/domains/d7.lisp
lib/domains/d8.lisp
```

Порядок колонок:

```text
ук → укр → san → en → LISP → sym
```

D7 — 126/128: owner-reserved `0100001`, `0101010` не отримують фальшивих rows. D8 — owner-ratified 256/256 під #3960.

## Перевірки

`scripts/check-domain-tables.py` та workflow `.github/workflows/domain-tables.yml` перевіряють:

- повноту й exact-width координати;
- відповідність ratified residents;
- відсутність пропусків `ук/укр/san`;
- відсутність surface-колізій;
- `?` у `ук/укр/en` для предикатів;
- `!` у `ук/укр/en` для destructive operations;
- compact-`ук` grammar.

Surface ніколи не замінює semantic authority: current identity — exact bits + exact domain + admitted/ratified law.
