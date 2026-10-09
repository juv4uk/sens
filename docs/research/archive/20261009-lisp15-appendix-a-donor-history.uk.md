# Архівний повтор Lisp 1.5 / Appendix A — збережені дослідницькі дані

**Статус: ARCHIVE / HISTORICAL EVIDENCE / NOT CURRENT AUTHORITY.**

Перенесено з незлитої старої гілки `research/d8-lisp15-appendix-ledger` / PR #3947 (Git blob 0d521ad80a78c93f3eaa599483af19f5567ab72d для Markdown та 912bc99c41f6552aaa4d9a67b8698344b3815264 для JSON). Це НЕ злиття її застарілого нормативного стану.

**Чинний стан станом на 2026-10-09:** D1–D9 ратифіковані за Contract 11.8, D8 ратифікований (256 резидентів), а D10 залишається RESEARCH-UNRATIFIED (625/1024 selected, 0 ratified). Всі старі твердження нижче про нібито «D8 не ратифікований», provisional D8-коди й координати є **виключно історією**, НЕ поточними кодами, НЕ механізмом і НЕ повноваженням змінити чинні таблиці.

Мета архіву — не загубити первинні Lisp 1.5 / Appendix A функціональні родини, позитивні свідки, контрприклади та класифікації. Відновлення будь-якої нової функції — лише через D1–D9 dedup, D10 semantic audit і #4463. Не виконуйте автоматичну генерацію `.sens` із цього архіву.

Повний знімок JSON розміщено поруч: `20261009-lisp15-appendix-a-evidence.json`.

---

## Точний текст старого дослідження (історичний контекст, не чинна норма)

# D8: відновлення Lisp 1.5 / Appendix A

**Статус:** research ledger. Не semantic authority. D8 не ратифікований.

Цей ledger існує для одного: **нічого більше не загубити** між старими issue, гілками, історичними джерелами та новою драбинною картою.

Основне джерело зрізу — *LISP 1.5 Programmer's Manual*, 17 серпня 1962. Для окремих речей використовуються ранніші MIT memo, коли дата/походження вже встановлені.

## Правило

```text
історично існувало
        ↓
записати завжди
        ↓
вже є нижче / просто виводиться? → NO-SLOT
host/tooling/machine/D7/Core-Math? → зберегти, але не Core D8
справді нова observable capability? → D8 recovery candidate
невідомо? → UNRESOLVED, не викидати
```

## Поточний provisional D8

```text
00000000 RPLACA
00000001 RPLACD
00000010 ERRORSET
00000011 ERROR
00000100 ENV-REFLECTION
00000101 READ
00000110 WRITE-TO-STRING
00000111 SYMBOL->STRING
00001000 STRING->SYMBOL
00001001 VECTOR
00001010 VECTOR-REF
00001011 VECTOR-SET!
00001100 SPECIAL-BINDING
```

Це **не ратифіковані residents**. Координати можна переставляти під час recovery; семантичні рядки не можна мовчки втрачати.

## Що вже стиснуто без слотів

- `CONC/NCONC/EFFACE/MAPCON` — destructive-list algorithms; спочатку виводимо з `RPLACA/RPLACD`, а не даємо по слоту кожній назві.
- `EQUAL`, `PAIR`, `AND`, `OR`, `ONEP`, `MINUSP`, `PROG2`, `SELECT` — прості композиції/рекурсії нижчого basis.
- `GENSYM` — current SENS уже визначає мовою поверх наявного fresh-counter + text/symbol bridge.
- `MAKE-VECTOR` та `VECTOR-LENGTH` — convenience/extent поверх мінімального indexed-storage basis.
- `FSUBR` — історичний implementation class у вже відомій special-call protocol family.
- Hart `TRANSFORMER/MACRO` — protocol evidence збережене, але D5 вже має MACRO family.

## Що винесено в інші домени/межі

- `FIXP/FLOATP/LOGAND/LOGOR/LOGXOR/LEFTSHIFT` → Core-Math/carrier review #3928.
- character reader/`PACK/UNPACK/MKNAM/...` → D7/text bridge review.
- `PRINT/PRIN1/PRINC/PUNCH/...` → host/transcript I/O, не плутати з чистим `READ(string)` / canonical writer.
- `TRACE/COUNT/SPEAK/...` → tooling/debugging.
- `DUMP/EXCISE/RECLAIM/LAP/COMPILE/...` → machine/system mechanism.

## Високопріоритетне unresolved

### SYMBOL METADATA / APVAL

`CSET/CSETQ`, `GET`, `PROP`, `ATTRIB`, `REMPROP`, `FLAG/REMFLAG`, `PRINTPROP`, `DEFLIST` — це одна історична система прихованої metadata, прив'язаної до символу. #3941 має звести її до мінімального law, а не роздати десяток слотів.

### INTERN / OBLIST / REMOB

Історичний global symbol table не тотожний current `STRING->SYMBOL`: у current SENS символи вже мають name-based value semantics. Потрібно окремо вирішити, чи registry membership/enumeration — semantic capability чи runtime mechanism.

### SPECIAL / COMMON

`SPECIAL` пройшов дешевий recovery: його dynamic bind/save/restore закон observably відрізняється від current lexical capture, тому provisional `SPECIAL-BINDING = 00001100`.

`COMMON` не отримує другий слот: історично це a-list bridge для communication compiled↔interpreted; окремого source-level root понад context communication поки не доведено.

## Збережені старі D8 дослідження

Позитивні product-family та негативні falsifier-и з попередніх D8 гілок уже перенесені в `main` через #3926/#3927. Їхня роль — law/generator evidence, а не автоматична occupancy.

## Accounting v1

```text
historical semantic families   30
D8 candidate families          12
unresolved families             2
no-slot / foreign families     16
ratified D8 residents           0
```

Машинна версія: `knowledge/d8-lisp15-appendix-a-recovery.json`.

## Наступний порядок

1. Закрити `SPECIAL/COMMON` дешево через lexical-vs-dynamic witness.
2. Звести APVAL/property-list family #3941.
3. Класифікувати INTERN/OBLIST/REMOB.
4. Довести destructive conveniences як похідні від `RPLACA/RPLACD`.
5. Лише після цього йти далі після 1963 у #3919.

**Принцип:** верхній домен не лише продовжує історію — він прибирає борги нижньої драбини.