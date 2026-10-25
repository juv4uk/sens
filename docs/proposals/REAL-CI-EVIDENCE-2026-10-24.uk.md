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

---

# Додаток 2 (Udbhava, 2026-10-24): МЕХАНІЗМ падіння знайдено

## Творець id — знайдено

`scripts/prove-lisp-semantic-t5m.sh:839-847`:

```sh
# Д11 juxt: першокласні одномісні функції та контрприклад перевіряє SENS.
d11_juxt_law_bundle="$evidence/d11-clojure-juxt-positive-complete.lisp"
d11_juxt_mutant_bundle="$evidence/d11-clojure-juxt-mutant-complete.lisp"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-laws.lisp > "$d11_juxt_law_bundle"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-mutant.lisp > "$d11_juxt_mutant_bundle"
run_case run_law d11-clojure-juxt-positive "$d11_juxt_law_bundle" 1
run_case run_law d11-clojure-juxt-mutant "$d11_juxt_mutant_bundle" 0
```

Тобто **id народжується тут** — у скрипті, а не в манифесті.

## Що це дає

**LAW-комплект і MUTANT-комплект відрізняються ЛИШЕ останнім файлом:**

| | склад | результат CI |
|---|---|---|
| law | `lib/d11-clojure-juxt.lisp` + `…-laws.lisp` | **RED** (unknown Text7 binding) |
| mutant | `lib/d11-clojure-juxt.lisp` + `…-mutant.lisp` | **PASS** |

**Той самий `lib/`, той самий код запуску — а результат протилежний.** Отже
дефект **у `…-laws.lisp`**, а не в `lib/` і не в шляху запуску.

## Перевірене й ВІДКИНУТЕ

- **Гіпотеза «`cat` зліплює рядки»** — **ВІДКИНУТО**: усі три файли закінчуються
  `\n` (перевірено `tail -c 1 | od -c`), зліплення чисте.
- **Латиниця в джерелі** — у `…-laws.lisp` є лише `Clojure` (назва мови), у
  `lib/…` — `runtime`, `opcode`. Шуканого гіберіша **немає в жодному файлі**
  (`grep -c "pstdverdyty\|gslndthlbnb"` → 0 в обох).

## Що лишається з'ясувати

Помилка вказує на **рядок 1:8 — це КОМЕНТАР** `; Мовні закони D11: одномісне
зіставлення Clojure juxt у SENS Lisp.`

Тобто **mint перетворює текст із коментаря на Text7-літерал**, і цей літерал не
має прив'язки. **Перевір гіпотезу:** прибери/зміни коментар першого рядка — і
подивись, чи зникне `unknown Text7 binding`. Це **єдина логічна нитка**, що
лишилась: різниця між law і mutant — у файлі, а помилка вказує на **коментар**.

## Deutsch

Der Mechanismus: law- und mutant-Bundle unterscheiden sich nur in der letzten
Datei; die Fehlermeldung zeigt auf Zeile 1:8 — einen KOMMENTAR.

## English

The mechanism: the law and mutant bundles differ only in the last file; the
error points at line 1:8 — a COMMENT.

---

# Додаток 3 (Saṅkhyā, 2026-10-24): мою гіпотезу ВИМІР ВІДКИДАЄ

## Гіпотеза була

«Латиниця в коментарі стає Text7-літералом без прив'язки» — і тому
`d11-clojure-juxt-laws.lisp` падає.

## Вимір її відкидає

```
усього .lisp у tests/semantic : 559
з латиницею >=4 у КОМЕНТАРЯХ : 274
без латиниці в коментарях    : 285
```

**274 файли мають латиницю в коментарях — і майже всі ПРОХОДЯТЬ** (418/420).
Отже латиниця в коментарі **не ламає виконання**. Гіпотеза **ХИБНА**.

Приклади серед тих, що проходять: `clips-deftemplate-d1-law.lisp`,
`clips-form-dispatch-d1-law.lisp`, `core-d3-car-cdr-cons-law.lisp`.

## Що це залишає

Дефект **специфічний для `d11-clojure-juxt-laws.lisp`**, а не класовий.
Єдина **структурна** відмінність цього файла:

| | ім'я | зміст |
|---|---|---|
| падаючий | `…-laws.lisp` (**множина**) | **24 свідки** в одному файлі |
| успішний | `…-mutant.lisp` (однина) | один контрприклад |

І помилка — на `physical_form_index=35`: `lib/` дає ~33 форми, отже це **перша
форма `…-laws.lisp`**. Саме вона й не знаходить прив'язки.

## Наступна перевірка (не «коментар», а ЗЧЕПЛЕННЯ)

Назва `підтвердити-набір-одномісних-функцій` **не існує в дереві**, а виклик у
коді — `застосувати-набір-одномісних-функцій` (**інший префікс**). Отже
перевіряти треба **не коментар, а те, як перша форма резолвиться після
зчеплення** `lib/` + `…-laws.lisp`: чи не **зсувається** межа форм, і чи не
**розрізає** `cat` одну форму навпіл.

## Deutsch

Meine Hypothese ist durch Messung widerlegt: 274 Dateien mit Latein in
Kommentaren bestehen. Der Defekt ist spezifisch für die laws-Datei.

## English

My hypothesis is disproved by measurement: 274 files with Latin in comments
pass. The defect is specific to the laws file.

---

# Додаток 4 (Sandhi, 2026-10-24): індекс 35 при 34 формах — аномалія

## Вимір (reader'ом, тим самим, що в міграції)

```
lib/d11-clojure-juxt.lisp          9 форм
tests/semantic/…-laws.lisp        25 форм
        разом                    34 форми
bundle після cat                  34 форми   ← ЗЧЕПЛЕННЯ ЧИСТЕ, межі не зсунуто

tests/semantic/…-mutant.lisp       1 форма
        lib + mutant              10 форм    ← і цей комплект ПРОХОДИТЬ
```

**Зчеплення не винне:** `cat` дає рівно 34 форми — стільки ж, скільки сума.
Гіпотезу «`cat` розрізає форму» **відкинуто виміром**.

## Але ось АНОМАЛІЯ

CI каже:

```
unknown Text7 binding: #t7:… [physical_form_index=35 physical_word_start=5797
                              physical_word_end=5917]
```

**`physical_form_index=35` — а у bundle ЛИШЕ 34 форми.** Індекс **на одиницю поза
межами**. Тобто:

- або індексація **1-базована**, і 35 = «наступна після останньої» → виконавець
  **шукає форму, якої немає**;
- або **mint додає одну форму** (обгортку), якої немає в джерелі;
- або `lib/` дає **не 9**, а 10 форм **для компілятора** (наприклад, неявний
  `(початок …)` навколо модуля).

**Це і є найсильніший слід:** помилка вказує **за межі** наявних форм. Досі всі
шукали дефект **усередині** свідка; а він, можливо, **у тому, як виконавець
індексує форми** — і тоді він вразить **кожен свідок**, а не лише цей.

## Deutsch

Der Fehler zeigt auf Index 35, aber das Bundle hat nur 34 Formen — der Index
liegt außerhalb. Das ist die stärkste Spur.

## English

The error points at index 35, but the bundle has only 34 forms — the index is
out of range. That is the strongest lead.

---

# Додаток 5 (Sūcaka, 2026-10-24): три гіпотези відкинуто — і що з цього випливає

## Відкинуто виміром

| гіпотеза | вимір | вирок |
|---|---|---|
| `cat` розрізає форму | bundle = рівно сума (34 = 9+25) | **відкинуто** |
| латиниця в коментарі | 274 файли мають її й ПРОХОДЯТЬ | **відкинуто** |
| em-dash `—` у коментарі | 142 файли мають її й ПРОХОДЯТЬ | **відкинуто** |

## Підтверджено на ТОЧНОМУ SHA CI (`664d7013`)

```
lib/d11-clojure-juxt.lisp        9 форм
tests/semantic/…-laws.lisp      25 форм
        разом                  34 форми
CI: physical_form_index=35      ← на 1 БІЛЬШЕ
```

І `binary_execution.rs:678` **стверджує `physical_form_index=1`** — отже індекс
**1-базований**. Тоді **35 при 34 формах = поза межами джерела**, а це означає, що
**mint додає рівно одну форму** (обгортку), і index 35 = **остання форма
`…-laws.lisp`** — маркер `(атом? (як-є ()))`.

## Що з цього випливає — і це головне

**Джерело КОРЕКТНЕ.** `grep` не знаходить гіберіша **ні в `lib/`, ні в `laws`**
(перевірено на SHA). Латиниця там лише `Clojure`, `runtime`, `opcode`.

**А помилка Є.** Отже спотворення — **не в джерелі, а в ШЛЯХУ**:

```
.lisp (коректна українська)
   → sens --t5m-mint  ← ТУТ народжується «підтвердити-набір-одномісних-функцій»
   → T5M байти
   → Zig open/verify-view
   → SENS --t5m-pair  ← «unknown Text7 binding»
```

**Тобто кодек `--t5m-mint` спотворює український текст** — і робить це так, що
назва **не існує в джерелі**. Саме тому **жоден grep не допомагає**: шукати треба
**не в `.lisp`, а в кодеку**.

## Найгостріше питання

Назва — **осмислена українська фраза** («підтвердити набір одномісних функцій»),
набрана **латинською розкладкою**. Тобто кодек **не просто губить байти — він
відтворює чиюсь помилку набору**. **Звідки кодек бере текст, якого немає в
джерелі?** Це або **кеш**, або **шаблон**, або **пере-використання попереднього
буфера**. Перевіряти треба **стан між свідками**, а не вміст одного свідка.

## Deutsch

Drei Hypothesen widerlegt; die Quelle ist korrekt — die Verfälschung entsteht
im Codec `--t5m-mint`, nicht im `.lisp`.

## English

Three hypotheses disproved; the source is correct — the corruption arises in
the `--t5m-mint` codec, not in the `.lisp`.

---

# Додаток 6 (Pravāha, 2026-10-24): індекс 0-базований — і це міняє арифметику

## Код, що формує індекс

`crates/sens/src/binary_execution.rs:137-156`:

```rust
pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
    let mut cursor = 0;
    let mut form_index = 0usize;                 // ← СТАРТ З НУЛЯ
    loop {
        let physical_word_start = cursor;
        let Some(form) = next_lowered_exact_form(&self.words, &mut cursor)? else { break; };
        value = eval_lowered_expressions(std::slice::from_ref(&form), session)
            .map_err(|mut error| {
                error.message = format!(
                    "{} [physical_form_index={} physical_word_start={} physical_word_end={}]",
                    error.message, form_index, physical_word_start, cursor);
                error
            })?;
        form_index += 1;                         // ← ІНКРЕМЕНТ ПІСЛЯ
    }
```

**`form_index` починається з `0`** і збільшується **після** обробки. Отже:

| | значення |
|---|---|
| перша форма | `physical_form_index=0` |
| N форм | індекси `0 … N-1` |
| **CI повідомив** | **`physical_form_index=35`** |
| **потрібно форм** | **≥ 36** |
| **джерело має** | **34** (9 + 25) |

**Розбіжність — ДВІ форми, а не одна.** Тобто **mint виробляє щонайменше 36
фізичних форм із 34 форм джерела.**

## Чому це важливо

Раніше я припускав 1-базований індекс і «+1 обгортку». **Код це відкидає:**
`form_index` **0-базований**, отже йдеться про **дві зайві форми**.

І `binary_execution.rs:678` (тест, що стверджує `physical_form_index=1`) — це
**не** перша форма: при 0-базовому індексі `1` = **друга**. Тест **не суперечить**
коду; він підтверджує, що перша — `0`.

## Що це лишає

**Джерело має 34 форми, а фізика — щонайменше 36.** Значить, `--t5m-mint` **додає
або розщеплює** форми. І серед цих зайвих — та, що містить
`підтвердити-набір-одномісних-функцій`.

**Перевіряти треба:** скільки форм дає **сам кодек** на цьому вході — і **які
саме** дві форми зайві. Це вже не питання свідка: це питання **відповідності
джерело↔фізика**.

## Deutsch

`form_index` beginnt bei 0; der Fehler bei 35 verlangt ≥36 Formen, die Quelle hat
34 — der Codec erzeugt zwei zusätzliche Formen.

## English

`form_index` starts at 0; an error at 35 requires ≥36 forms while the source has
34 — the codec produces two extra forms.

---

# Додаток 7 (Tulanā, 2026-10-24): межа статичної перевірки — і чесний підсумок

## Що я спробував і чого НЕ зміг

Спробував порахувати форми **фізичного `.sens`** статично, щоб довести «36 проти
34» без запуску. **Не вдалося:**

```
decode_t5m_bytes("lib/d11-clojure-juxt.sens") →
  ['10', '0011', '00', '10', '1100100', '00', '1100010', '00', …]
```

Це **бітові поля**, не текст. Порахувати **D2-кадри** (межі форм) Python-кодеком
**не можна**: кадрування робить `lower_exact_domain_program` у Rust. Отже «36
проти 34» лишається **виведеним із коду індексу** (`form_index` з нуля) плюс
повідомлення CI — але **не** виміряним напряму.

**Чесно: це межа, а не результат.**

## Підсумок дослідження CI

| крок | стан |
|---|---|
| CI запускається на гілці | **встановлено** (30 runs, 20 failure) |
| справжній прогін SENS у CI | **встановлено** (крок 17-18) |
| проходять 418/420 законів | **встановлено** |
| 2 семантичні дефекти | **встановлено** (d11-clojure-juxt-*) |
| фізичний дрейф `lib/core4.sens` | **встановлено** |
| гіпотеза `cat` розрізає | **відкинуто** виміром |
| гіпотеза латиниця в коментарі | **відкинуто** виміром (274 файли) |
| гіпотеза em-dash | **відкинуто** виміром (142 файли) |
| гіпотеза 1-базований індекс | **відкинуто** кодом (`form_index = 0`) |
| джерело коректне, спотворення в кодеку | **виведено** |
| 36 форм проти 34 | **виведено, не виміряно** ← межа |

## Що лишається зробити (і чого я не можу)

1. **Порахувати D2-кадри** зчепленого `.sens` — потрібен Rust-шлях.
2. **Перевірити, чи `--t5m-mint` додає 2 форми** — потрібен запуск.
3. **Перевірити гіпотезу стану між формами** — потрібен запуск.

**Усе три потребують бінарника, якого в пісочниці немає.** Тому дослідження
закінчується **межою**, а не коренем — і це треба сказати прямо.

## Deutsch

Grenze der statischen Prüfung erreicht: die D2-Rahmen brauchen den Rust-Pfad.

## English

Limit of static checking reached: D2 framing requires the Rust path.

---

# Додаток 8 (Yajña, 2026-10-24): помилка на стадії `direct` — розбіжність ЧИТАЧІВ

## Що каже лог

```
SENS_LAW_STAGE id=d11-clojure-juxt-positive stage=direct exit=1 elapsed_us=528311
```

**Помилка — на стадії `direct`**, тобто на виклику `sens <bundle.lisp>` (читання
`.lisp` **напряму**, ще до карбування). Дивись `run_law`:

```sh
if ! profile_stage "$id" direct timeout 45s "$sens" "$source" >"$dir/direct.out" ...
```

## Що це означає

`physical_form_index=35` походить **не від T5M-карбування**, а від **читання
`.lisp`**. Отже:

| читач | форм із `cat lib + laws` |
|---|---|
| **Python** (`migrate-three-pass.py`, я ним міряв) | **34** |
| **Rust** (`sens`, судячи з index=35 при 0-базовому) | **≥ 36** |

**Два читачі тієї самої мови дають різну кількість форм.** І оскільки `form_index`
0-базований, Rust-читач бачить **щонайменше 36** форм там, де Python бачить 34.

## Чому це найсильніший слід із усіх

1. **Це не питання свідка.** Обидва читачі читають **той самий файл**.
2. **Це не питання карбування.** Помилка — на стадії `direct`.
3. **Це не питання зчеплення.** `cat` дає рівно суму (перевірено).

**Це розбіжність ДВОХ РЕАЛІЗАЦІЙ ОДНОГО READER'А.** Якщо Rust-читач бачить
форми, яких немає (або розщеплює наявні), то **`physical_form_index` у кожному
повідомленні про помилку вказує не туди** — і **всі, хто «лагодив свідка» за цим
індексом, лагодили не те**.

## Де шукати

- **`crates/sens/src/`** — Rust-reader `.lisp` (той, що живить стадію `direct`).
- **`scripts/migrate-three-pass.py`** — Python-reader (я ним міряв).
- **Розбіжність** між ними на **одному** вході — ось де корінь. Візьми
  `lib/d11-clojure-juxt.lisp` + `…-laws.lisp`, прочитай **обома** і **порівняй
  форми по одній**.

## Deutsch

Der Fehler liegt auf der Stufe `direct` — zwei Reader derselben Sprache liefern
verschiedene Formzahlen (Python 34, Rust ≥36).

## English

The error is on the `direct` stage — two readers of the same language yield
different form counts (Python 34, Rust ≥36).

---

# Додаток 9: ПРИЧИНА ЧЕРВОНИХ — гілка відстала від main на 449 комітів

## Вимір (GitHub API)

```
main head:  acb1f17011
гілка head: a9df774558
compare main...feat/semantic-backlog-measurement:
  behind_by = 449      ← гілка ВІДСТАЄ на 449 комітів
  ahead_by  = 82       ← і випереджає на 82
```

## Що це пояснює

Обидва RED-id'и — `d11-clojure-juxt-positive` і
`d11-clojure-juxt-constructor-improper-tail` — **не існують у поточному дереві**:

```
grep «constructor-improper» → лише мій власний документ
tests/semantic/d11-clojure-juxt-constructor-improper-tail-negative.lisp → 404 (і на SHA 664d7013)
scripts/prove-lisp-semantic-t5m.sh на SHA: 99408 Б   ← а зараз 78808 Б
```

**Скрипт доказу на ревізії CI був на 20 КБ БІЛЬШИЙ за поточний.** Тобто **CI ганяв
іншу ревізію**, ніж та, яку я читав, — і саме тому звітує про id'и, яких немає.

## Отже «червоні» — двох різних прирід

1. **Червоні від застарілої бази** — id'и й фікстури, яких у `main` уже немає.
   **Лікування: освіжити гілку на поточний `main`** — не лагодити свідка, якого
   немає.
2. **Червоні, що лишаться й після освіження** — `lib/core4.sens` (фізичний дрейф)
   і, ймовірно, `d11-clojure-juxt-*`. Їх треба перевіряти **після** освіження, на
   свіжому дереві.

## Чесний висновок

**Я не можу «виправити червоні» наосліп.** Половина з них — **тіні застарілої
бази**; лагодити їх означало б лагодити код, якого в проєкті вже немає. **Перший
правильний крок — освіжити гілку**, і тільки потім дивитися, що лишилось червоним.

## Deutsch

Die Zweige sind 449 Commits hinter `main`; die roten Prüfungen gehören teils zu
einer veralteten Basis.

## English

The branch is 449 commits behind `main`; part of the red checks belongs to a
stale base.
