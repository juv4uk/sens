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

---

# Додаток (Anusaraṇa, 2026-10-25): ЧОМУ ядро застаріле — повний ланцюг

## Творець застарілості — знайдено

`.github/workflows/remint-drifted-pairs.yml:142-148` **навмисно пропускає** Core4:

```sh
# Дані/опис профілю та окремо діагностовані Core4/Янтра
# перевіряються на власну зміну, але не кожним чужим push.
case "$source" in
  lib/core2.lisp|lib/core-math.lisp|lib/core4.lisp|lib/yantra.lisp) continue ;;
esac
```

А `.github/workflows/ci.yml:533-535` пояснює задум:

```
# Core4 is executed from lib/core4.sens (Zig-restored at build),
# not from the textual file changed in Git. Detect stale bootstrap
# BEFORE calling old bytecode a successful implementation of a new law.
```

## Ланцюг (від джерела до семи падінь)

```
1. lib/core4.lisp змінено в якомусь коміті
2. remint-drifted-pairs.yml НАВМИСНО пропускає core4 → пара НЕ пере-карбується
3. закомічений lib/core4.sens лишається застарілим
4. bootstrap-перевірка це ПОМІЧАЄ:
      REGRESSION layer=bootstrap expected=exact-current-SENS-source
                 actual=outdated-physical file=lib/core4.sens release=NO-GO
5. профіль core4 виконує свідків із --core4-runtime проти ЗАСТАРІЛОГО ядра
6. сім свідків падають: d10-clips-* (4) і d6-let* (3)
```

## Що це означає

**Перевірка працює як задумано.** Вона **ловить справжню неузгодженість** — і саме
тому `release=NO-GO`. **Це не збій CI, а його правильна відповідь.**

**Причина неузгодженості одна:** джерело `lib/core4.lisp` змінили, а фізичну пару
`lib/core4.sens` — ні. Виключення в `remint-drifted-pairs.yml` **доречне** (щоб
чужий push не пере-карбовував ядро), але воно означає, що **пару мусить
пере-карбувати ТОЙ, ХТО ЗМІНЮЄ ДЖЕРЕЛО**.

## Лікування — і воно одне

```sh
sens --t5m-mint-pair lib/core4.lisp lib/core4.sens
git add lib/core4.sens
```

Після цього — пере-прогнати сім свідків. **Якщо всі сім зелені — корінь
підтверджено остаточно, і сім свідків були невинні.**

## Deutsch

Die Prüfung arbeitet wie beabsichtigt; die Ursache ist eine nicht neu geprägte
Core4-Paarung.

## English

The check works as intended; the cause is an un-reminted Core4 pair.

---

# Додаток (Kāraṇa, 2026-10-25): ВИНУВАТЕЦЬ — коміт `962ea550`

## Історія обох файлів (GitHub API)

```
lib/core4.lisp (останні 6)
  962ea550  2026-10-25T02:02:04  Д10/Д6: відкат двох регресій джерела, які ловить крок 8 core4-
  e0141a86  2026-10-25T01:33:07  Д10 CLIPS: строгий D3-кінець списків ASSERTS і PRINTOUTS
  7f98688c  2026-10-25T01:30:07  Д6 LENGTH-ONTO: …
  09c9051f  2026-10-25T01:26:54  Д10 CLIPS: …
  00597015  2026-10-25T01:24:19  SENS_PAIR_REGEN · Д6: правильний D3-хребет до NTH і REDUCE
  acb1f170  2026-10-25T01:22:42  Д6 LENGTH-ONTO: …

lib/core4.sens (останні 5)
  c5157142  2026-10-25T01:36:44  ремонт пар: канонічні SENS/Zig T5M на актуальному main
  4f46b296  2026-10-24T22:36:40  ремонт пар: канонічні SENS/Zig T5M на актуальному main
  c285e11c  2026-10-24T02:28:40  Відновити фізичний F6 шлях через T5M
  …
```

## Що це показує

- **`lib/core4.sens` востаннє оновлено `c5157142` о 01:36:44.**
- **`lib/core4.lisp` змінено `962ea550` о 02:02:04 — на 26 хвилин ПІЗНІШЕ.**

Отже **`main` застарілий ПРЯМО ЗАРАЗ**: джерело пішло вперед, пара — ні.
Коміт `962ea550` («відкат двох регресій джерела, які ловить крок 8 core4-…»)
змінив **джерело без пари** — і саме тому bootstrap-перевірка каже
`actual=outdated-physical`.

## Важливе спостереження

У гілці вже є коміти **`SENS_PAIR_REGEN`** (00597015) і **`ремонт пар`**
(c5157142, 4f46b296) — тобто **пере-карбування пар роблять вручну й нерегулярно**.
Це і є справжня хвороба: **пара оновлюється тоді, коли хтось згадає**, а не тоді,
коли змінюється джерело.

**Мій `check-core4-pair-together.py` робить це обов'язковим.** І він би **впіймав
`962ea550`** — бо той змінив `lib/core4.lisp` без `lib/core4.sens`.

## Deutsch

Der Schuldige ist Commit `962ea550`: er änderte die Quelle ohne das Paar.

## English

The culprit is commit `962ea550`: it changed the source without the pair.
