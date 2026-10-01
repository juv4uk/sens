# #1962 — перший графовий зріз LISP I → LISP 1.5

**Статус:** research-only, не semantic authority, без production migration.  
**Branch:** `research/1962-lisp1-15-domain-graph`.

## Питання

Чи можна вивести `D3`, `mūla4`, `janya5+` не ручним призначенням, а зі
стійкої структури залежностей між мовними сутностями?

Перший corpus навмисно малий: історичне ядро, кілька простих похідних
функцій і універсальний evaluator. Мета першої фази — перевірити метод
раніше, ніж завантажувати весь каталог LISP 1.5.

## Первинні джерела

- *LISP I Programmer's Manual*, MIT, 1 березня 1960:
  https://softwarepreservation.computerhistory.org/LISP/book/LISP%20I%20Programmers%20Manual.pdf
- *LISP 1.5 Programmer's Manual*, MIT Press, 1962:
  https://softwarepreservation.computerhistory.org/LISP/book/LISP%201.5%20Programmers%20Manual.pdf
- J. McCarthy, *Recursive Functions of Symbolic Expressions and Their
  Computation by Machine, Part I*, CACM, 1960:
  https://www-formal.stanford.edu/jmc/recursive.pdf

Внутрішні донори доказів:
`ecosystem/docs/correspondence/mccarthy-1960-eval-apply-*`,
`ecosystem/docs/correspondence/manus-ai-mylisp-vs-lisp15-*`,
`ecosystem/memory/mccarthy-eval-x86-64-prototype.md`.

## Знахідка 1: історичний матеріал сам розділяє 5 + 4

LISP I прямо каже: спочатку визначаються **п'ять elementary functions
and predicates**, а ширший клас будується композицією, conditional
expressions і recursion. Ці п'ять:

```text
ATOM EQ CAR CDR CONS
```

LISP 1.5 зберігає ту саму п'ятірку і ще сильніше відділяє її від
evaluator forms. У pedagogical `evalquote/apply/eval`:

```text
APPLY: CAR CDR CONS ATOM EQ
       + LAMBDA LABEL

EVAL:  QUOTE COND
       + general application
```

Після цього manual окремо зауважує, що в pure theory усі функції,
крім п'яти basic functions, мають бути визначені.

### Гіпотеза H3-A

Звідси виникає перший **позитивний**, але ще не ратифікований кандидат
для D3:

```text
D3 candidate = {QUOTE, COND, LAMBDA, LABEL}
mūla4         = {ATOM, EQ, CAR, CDR, CONS}
```

Причина не в кількості слотів. Це два різні класи поведінки:

- `mūla4` — ordinary elementary operations/predicates над S-expressions;
- D3-кандидати змінюють evaluation/control/binding relation і не
  поводяться як звичайні strict function calls.

Це треба ще falsify: перевірити, чи клас лишається стійким при
переході від математичного M-language до реального interpreter system,
і чи не є це лише історичною нотаційною випадковістю.

## Знахідка 2: SCC evaluator-а змінюється між LISP I та LISP 1.5

Теоретичний LISP I:

```text
apply_lisp1 -> eval_lisp1

eval_lisp1 <-> evcon_lisp1
eval_lisp1 <-> evlis_lisp1
```

Отже multi-node SCC:

```text
{eval_lisp1, evcon_lisp1, evlis_lisp1}
```

`apply_lisp1` стоїть над цим компонентом, бо формує quoted call і
передає його `eval`.

У LISP 1.5 архітектура pedagogical evaluator змінена:

```text
eval_lisp15  -> apply_lisp15
apply_lisp15 -> eval_lisp15
```

разом із `evcon`/`evlis`, тому multi-node SCC:

```text
{apply_lisp15, eval_lisp15, evcon_lisp15, evlis_lisp15}
```

Висновок: **належність до recursive SCC не є сама по собі ознакою
первинності або домену**. Це може змінитися через організацію
evaluator-а при збереженні тієї самої основної мовної ідеї.

## Знахідка 3: два очевидні rank-алгоритми обидва недостатні

### Model A — named dependency depth

Стискаємо SCC, потім беремо глибину DAG залежностей від нижнього базису.

Вона дає корисне розшарування, наприклад для LISP I:

```text
cadr/null/equal  -> depth 1 -> naive janya5
append/assoc     -> depth 2 -> naive janya6
eval SCC         -> depth 3 -> naive janya7
apply            -> depth 4 -> naive janya8
```

Але ця модель **неінваріантна до refactoring**.

Приклад:

```text
pairlis -> null -> atom/eq
```

Якщо `null` inline-нути в `pairlis`, семантика не зміниться, а named
depth зменшиться. Отже сама по собі ця модель не може визначати
бітність.

### Model B — transitive basis support

Повністю розгортаємо залежності і питаємо лише, з яких базових
елементів D3∪D4 функція зрештою виражається.

Це стійкіше до helper names, але губить відстань: `append`, `eval` і
багато інших вузлів просто стають «виразні через той самий нижній
базис». Отже transitive derivability **сплющує ієрархію**.

## Що потрібно замість цього

Наступний кандидат — **normalized derivation cost**, де definitional
aliases/helper names не додають штучного шару, але реальна структурна
складність не зникає.

Початковий вектор для експерименту:

```text
C(v) = (
  primitive/application count,
  branch count,
  binder count,
  recursive-SCC count,
  distinct lower-domain dependencies,
  normalized description bits
)
```

Ваги поки **не визначені**. Спочатку треба отримати 2–3 конкурентні
нормалізації й перевірити їх на refactoring invariance.

Можлива правильна математична форма — не простий directed graph, а
directed hypergraph / implicational closure:

```text
{A, B, C} -> F
```

бо факт «F виводиться з множини A,B,C» не дорівнює трьом незалежним
ребрам.

## Важливий наслідок для D3

До цього `saṃbhava3` не мав позитивної evidence. Тепер маємо H3-A:
чотири evaluation/binding forms. Але **не перейменовувати D3 і не
призначати коди**, доки не буде:

1. перевірки LISP I system APPLY та Appendix B LISP 1.5 interpreter;
2. порівняння operational role цих чотирьох;
3. перевірки, чи існує контрприклад — інша сутність тієї ж ролі, яка
   руйнує клас або переповнює 3-bit capacity;
4. перевірки, що `quote/cond/lambda/label` справді утворюють один
   relation class, а не два випадково сусідні класи.

## Артефакти

- `1962-lisp1-15-nodes.tsv` — вузли та candidate-domain labels;
- `1962-lisp1-15-edges.tsv` — typed dependency evidence;
- `scripts/research-domain-graph-1962.py` — Tarjan SCC + дві
  діагностичні rank-моделі;
- `1962-lisp1-15-first-run.txt` — відтворюваний перший результат.

Жоден із цих файлів не є contract/runtime authority.

## Наступний експеримент

Побудувати **Model C**:

1. quotient graph за definitional equivalence / transparent helper
   expansion;
2. SCC condensation;
3. normalized proof/description cost;
4. capacity check для кожного `Dn`;
5. stability test: LISP I → LISP 1.5.

Критерій успіху: вставка або видалення допоміжної назви (`NULL`,
`CADR`, тощо) не повинна пересувати незмінну семантику між доменами.
