# СПРАВЖНІ ДАНІ CI (вперше за сесію)

Автор: агент Phala, 2026-10-24. Джерело: GitHub Actions, гілка
`feat/semantic-backlog-measurement`, run `40143723939`, job `121020590065`.

## Що виявилось

**CI ЗАПУСКАЄТЬСЯ на моїй гілці.** 30 workflow-запусків; **20 — failure**.
Тобто **реальні результати існували весь час**, і я їх **не питав** десятки ходів.

Workflow «SENS — короткий CI: охоронець, Rust, Zig, SENS» — **FAILURE**.
`host-debt0 + language-stays` — **SUCCESS**.

## П'ять кроків, що падають (з логу)

```
✗ 3.  Один автоматичний CI — тільки поточний main
✗ 12. Rust — механізм без мовного оракула
✗ 16. Core4 — точна фізична пара SENS/Zig T5M
✗ 17. PUSH Lisp → кодек Zig/T5M → виконання SENS
✗ 18. Lisp → Zig/T5M → SENS — позитивні та негативні закони
```

## Два справжні СЕМАНТИЧНІ дефекти (крок 18)

```
REGRESSION id=d11-clojure-juxt-positive layer=sens-direct
           expected=SENS-execution actual=rejected
REGRESSION id=d11-clojure-juxt-constructor-improper-tail
           expected=Type-rejection actual=unexpected-success
REGRESSION checked=420 passed=418 failed=2
```

**418 із 420 проходять; 2 падають.** Точна помилка:

```
sens: T5M source execution failed: SENS binary evaluator: unknown Text7 binding:
  #t7:67736c6e6474686c626e622d79662c73682d6a6c796a76736379625b2d61657972777371
  [physical_form_index=35 physical_word_start=5797 physical_word_end=5917]
  --> line 1:8
1 | ; Д11: чистий одномісний СЕНС-профіль Кложур зшити.
```

**Hex декодується у `gslndthlbnb-yf,sh-jlyjvscyb[-aeyrwsq` — ГІБЕРІШ.**
Це класична ознака **набраного не тією клавіатурною розкладкою**: літери
латинські, але послідовність беззмістовна. SENS-оцінювач не має прив'язки для
такого Text7-літерала й **відкидає виконання**.

## Третій дефект: фізичний дрейф ядра

```
REGRESSION layer=bootstrap expected=exact-current-SENS-source
           actual=outdated-physical bytes=Zig/T5M file=lib/core4.sens release=NO-GO
```

`lib/core4.sens` (275155 Б) **застарілий** щодо `lib/core4.lisp` (500229 Б).
Це **той самий клас**, що я виправив для `lib/core` і `lib/guard` — **але інший
бік**: там застарів **вигляд** (безрозширений), тут — **фізичний `.sens`** щодо
джерела. Виправлення вимагає **пере-карбування компілятором SENS** (у пісочниці
немає), а **не** Python-кодеком: `.lisp` символьний, `.sens` — скомпільований.

## Чому крок 3 падає

`✗ 3. Один автоматичний CI — тільки поточний main` — **guard, який вимагає, щоб
повний CI ганявся лише на `main`**. Тобто частина падінь **очікувана на гілці**,
а **не** спричинена моїми змінами. **Це треба відрізняти** — і я цього не робив,
поки не прочитав лог.

## Висновок

**Найцінніше за сесію — цей файл.** 77 комітів статичного аналізу не дали того,
що дав **один запит до GitHub API**. Справжній стан: **418/420 законів
проходять**, 2 семантичні дефекти (розкладка Text7), 1 фізичний дрейф ядра.

## Deutsch

Echte CI-Daten: 418/420 Gesetze bestehen; 2 semantische Defekte.

## English

Real CI data: 418/420 laws pass; 2 semantic defects.

---

# Додаток (Akṣara, 2026-10-24): hex розшифровано — і він веде до відсутньої назви

## Розшифровка

Hex з логу `#t7:67736c6e6474686c626e622d79662c73682d6a6c796a76736379625b2d61657972777371`
— це UTF-8 **латинського гіберіша** `gslndthlbnb-yf,sh-jlyjvscyb[-aeyrwsq`.
Через українську розкладку ЙЦУКЕН він дає:

```
gslndthlbnb-yf,sh-jlyjvscyb[-aeyrwsq
  → підтвердити-набір-одномісних-функцій
```

Тобто **текст набрано не тією клавіатурною розкладкою**, і SENS-оцінювач не має
прив'язки для такого Text7-літерала.

## Але назва НЕ ІСНУЄ в дереві

```
grep -rln "підтвердити-набір" .   → ПОРОЖНЬО
grep -rln "застосувати-набір" .   → lib/d11-clojure-juxt.lisp,
                                    tests/semantic/d11-clojure-juxt-laws.lisp,
                                    knowledge/d11/база-доступних-функцій/…
```

`lib/d11-clojure-juxt.lisp` визначає **`застосувати-набір-одномісних-функцій`** —
**інший префікс** (`застосувати`, не `підтвердити`).

## Що це означає

Помилка вказує на **рядок 1:8 — КОМЕНТАР** свідка. Тобто **runner сам утворює
Text7-літерал** із чогось (імовірно, з тексту ствердження або з імені), і цей
літерал **не має прив'язки**. Назва `підтвердити-набір-одномісних-функцій`
**не існує ні в одному файлі дерева** — отже вона **виникає під час виконання**,
а не читається з джерела.

**Тобто дефект не в свідку й не в `lib/`, а в ШЛЯХУ, який будує прив'язки.**
Саме тому фікстура `d11-clojure-juxt-laws.lisp` **сама по собі коректна**, а її
виконання — ні.

## Deutsch

Der Hex ist eine ukrainische Phrase in falscher Tastaturbelegung; der Name
existiert nirgends im Baum — der Defekt liegt im Bindungspfad, nicht im Zeugen.

## English

The hex is a Ukrainian phrase in the wrong keyboard layout; the name exists
nowhere in the tree — the defect is in the binding path, not the witness.
