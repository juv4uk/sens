# Мовний контракт сумісності з островами виконання (#749)

Англійська версія: [ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.md](ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.md).

## 1. Призначення

`my-lisp` володіє семантикою власної мови й координує автономні острови виконання:

- **Common Lisp** — нативне Lisp-виконання/runtime;
- **Prolog** — уніфікація, пошук і backtracking;
- **Datalog** — реляційне замикання/fixpoint;
- **CLIPS** — продукційні правила, working memory та agenda.

Сумісність не повинна змушувати жоден острів приймати внутрішню онтологію іншого острова.

## 2. Межа семантичної влади

```text
SID -> семантична ідентичність my-lisp
ідентичність -> нуль / один / багато execution witnesses
виклик ядра -> нативне/непрозоре спостереження острова
явний bridge/projection -> звичайні дані my-lisp, коли це обґрунтовано
```

SID registry і Lisp-owned закони визначають, що означає ідентичність my-lisp. Ядро може виконувати, спостерігати або бути witness цієї ідентичності, але не отримує права переозначувати її.

Видалення, заміна або недоступність ядра не перенумеровує і не переозначує SID registry.

## 3. Механічна межа виклику

Спільна межа навмисно менша за спільну модель результату:

```text
target kernel
+ opaque SID
+ kernel-local payload
+ provenance
        |
        v
native / opaque kernel observation
+ producer identity
+ preserved provenance
```

Спільний C ABI переносить байти та identity. Він **не визначає** універсальний `island-result`, універсальний truth type, proof type, substitution type, tuple type чи working-memory type.

Результати лишаються нативними:

```text
Common Lisp -> Lisp value / runtime observation
Prolog      -> 0..N substitutions / search observations
Datalog     -> relation tuples / closure observations
CLIPS       -> facts / agenda firings / working-memory observations
```

Явний bridge може спроєктувати нативний результат у звичайні дані my-lisp, але це окрема операція, яка повинна зберігати достатньо producer/provenance для перевірки походження.

## 4. Множинність — не істина

Коли протокол острова повідомляє cardinality, `0`, `1` і `N` — це спостереження про конкретний завершений виклик.

Це **не** універсальна алгебра істини.

Зокрема:

- нуль Prolog substitutions означає лише, що цей виклик породив нуль substitutions;
- порожнє Datalog relation означає лише, що спостережене relation має нуль tuples;
- нуль CLIPS firings означає лише, що цей run не запустив жодного правила;
- Common Lisp цілком легально може повернути Lisp-значення `()`.

Жоден із цих фактів сам по собі не дає my-lisp права робити висновок `FALSE`, refutation, unknown, conflict чи negation-as-failure.

Літеральне `()` лишається Canon 0 мови й не повинно мовчки використовуватися як protocol sentinel «нуль результатів».

## 5. Шляхи 0 / 1 / N

Зовнішня вимога сумісності лише в тому, щоб my-lisp міг зберегти ці випадки без колапсу:

```text
0 results -> явне observation: producer + cardinality/native payload
1 result  -> явне observation: producer + один native result
N results -> явне observation: producer + native multiplicity
```

Конкретне представлення може відрізнятися між островами. Prolog substitution stream, Datalog tuple set і CLIPS agenda delta не повинні загортатися в один вигаданий семантичний datatype лише тому, що в усіх можна порахувати кількість елементів.

## 6. Потік між островами

Обмін між островами є явним і частковим:

```text
Island A native result
        |
        v
my-lisp спостерігає producer + provenance + native result
        |
        +-- існує обґрунтований projection/bridge --> input Island B
        |
        `-- обґрунтованого bridge немає ----------> зберегти результат і зупинитися
```

Відсутній bridge — легальний стан. Краще зберегти неперекладений нативний результат, ніж вигадати семантичну еквівалентність.

Коли відповідність відома, перевага за pairwise bridges. Універсальна interchange semantics не припускається.

## 7. Що цей контракт забороняє

- kernel-owned значення SID;
- перенумерацію SID при зміні ядра;
- обов’язкову універсальну онтологію результатів;
- автоматичне native-result -> truth перетворення;
- трактування нуля відповідей як спростування;
- трактування literal `()` як protocol no-result;
- оголошення семантичної еквівалентності лише тому, що два острови можуть обмінятися байтами.

## 8. Поточний доказ

Lisp-owned authority — `contracts/island-compat-contract.lisp`, який виконується через `tests/fixtures/island-compat-witness.lisp`.

Наявний kernel C ABI, kernel host і per-kernel integration tests лишаються **механічними witnesses**. Вони доводять транспорт/виконання, але не визначають наведену вище семантику.

Наступна acceptance-робота для #749 повинна показати реальні шляхи 0/1/N та один явний cross-island bridge, зберігаючи нативний result domain кожного producer.
