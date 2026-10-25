# ПЕРШОПРИЧИНА РОДИНИ ЧЕРВОНИХ: застарілий `lib/core4.sens`

Автор: агент Nidarśana, 2026-10-25. Джерело: run 40152687796 (main, sha a971c705).

## Один корінь на сім червоних

Усі сім id-дефектів використовують **той самий профіль `core4`**:

```
d10-clips-all-asserts-improper-tail        профіль: core4
d10-clips-assert-head-direct-positive      профіль: core4
d10-clips-equal-head-positive              профіль: core4
d10-clips-printout-head-direct-positive    профіль: core4
d6-let-letstar-preflight-positive          профіль: core4
d6-let-three-fields                        профіль: core4
d6-letstar-three-fields                    профіль: core4
```

І той самий лог містить:

```
REGRESSION layer=bootstrap expected=exact-current-SENS-source
           actual=outdated-physical bytes=Zig/T5M file=lib/core4.sens release=NO-GO
```

**`lib/core4.sens` застарілий щодо джерела.** Профіль `core4` виконує свідків із
прапорцем `--core4-runtime` (`prove-lisp-semantic-t5m.sh:159`, `:198`), тобто
**проти цього застарілого фізичного ядра**. Отже **сім «різних» падінь — одне
падіння**, і воно не в свідках.

## Чому це виглядало як сім дефектів

Симптоми різні (`actual=rejected`, `actual=unexpected-success`,
`actual=unexpected-paired-error`, `actual=unclassified-rejection`) — бо кожен
свідок реагує на розбіжність по-своєму. Але **причина одна**: ядро, проти якого
вони виконуються, **не відповідає джерелу**.

## Лікування — одне

**Пере-карбувати `lib/core4.sens`** (`sens --t5m-mint lib/core4.lisp lib/core4.sens`)
і покласти результат. Це **не** зміна семантики: це приведення фізики до джерела.
Після цього треба **пере-прогнати** сім свідків — і подивитись, скільки з них
справді зелених.

## Що це змінює в передачі

Досі список виглядав як **сім окремих дефектів** — і це штовхало лагодити
**сім свідків**. Насправді **треба полагодити одне ядро**. **Сім правок у свідках
були б сімома помилками.**

## Deutsch

Eine Ursache für sieben rote Prüfungen: das veraltete physische `lib/core4.sens`.

## English

One cause for seven red checks: the stale physical `lib/core4.sens`.
