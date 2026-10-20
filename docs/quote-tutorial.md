# Remove the quote · Приберіть quote · Entfernen Sie das quote

## English

**SENS** is homoiconic: code and data share one notation. Wrapping an expression in `(quote ...)` tells the evaluator "treat this as inert data, don't run it." Delete that wrapper and the exact same text becomes a running program. This tutorial is a five-stage `.lisp` file: run each block with the `(quote ...)`, read the printed result, then delete the `quote` wrapper and run it again.

Try each pair with the CLI:

```powershell
cargo run --manifest-path crates/sens-cli/Cargo.toml -- your-file.lisp
```

### Stage 1 — data vs. arithmetic

```lisp
(quote (+ 1 2 3))
```
Prints the inert list `(+ 1 2 3)` — three symbols, nothing computed.

```lisp
(+ 1 2 3)
```
Prints `6` — the exact same text, now executed.

### Stage 2 — data vs. a definition

```lisp
(quote (def answer 42))
```
Prints `(def answer 42)` — a description of a definition, not yet made.

```lisp
(def answer 42)
```
Prints `42` and `answer` now exists in the environment.

### Stage 3 — data vs. a function

```lisp
(quote (def square (lambda (x) (* x x))))
```
Prints the lambda expression itself, unevaluated.

```lisp
(def square (lambda (x) (* x x)))
(square 5)
```
Defines `square`, then prints `25`.

### Stage 4 — data vs. control flow

```lisp
(quote (cond ((eq 2 2) 100) (t 0)))
```
Prints the `cond` form as a plain list.

```lisp
(cond ((eq 2 2) 100) (t 0))
```
Prints `100` — the condition actually runs.

### Stage 5 — growing the language itself

A `defmacro` receives its arguments as data (unevaluated, like `quote` does) and returns new code for the evaluator to run — this is how `lib/core.lisp` bootstraps derived forms without adding anything to the Rust core (see the bootstrap-boundary principle in `docs/language-core.md`):

```lisp
(defmacro unless (condition body)
    (list (quote cond)
        (list condition (quote ()))
        (list (quote t) body)))

(unless (eq 1 2) (quote different))
```
Prints `different`. `unless` did not exist in the language a moment ago; you just grew it, out of the same quote/no-quote trick as stages 1–4.

### Stage 6 — the trick taken all the way

`quote` treats code as data; `defmacro` builds new code from data. The next step is a program that *runs* code passed to it as data — an evaluator. [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) is one, written with SENS, using `read` to turn text into data (see stage 1) and its own `car`/`cdr`/`cons`/`atom`/`eq`/`cond`/`lambda` to interpret it — the same primitives this tutorial has used throughout, now dispatching to themselves:

```lisp
(my-eval (read "((lambda (x) (* x x)) 6)") (quote ()))
```
Prints `36`. Load it alongside `lib/core.lisp` and read the file's own header comment for what it deliberately leaves out and why.

## Українська

**SENS** гомоіконічна: код і дані записуються однаково. Обгортання виразу в `(quote ...)` каже evaluator'у "став до цього як до інертних даних, не виконуй". Приберіть цю обгортку — і той самий текст стає програмою, що виконується. Цей туторіал — `.lisp`-файл із п'яти етапів: запустіть кожен блок з `(quote ...)`, подивіться на надрукований результат, потім приберіть `quote`-обгортку і запустіть знову.

Перевіряйте кожну пару через CLI:

```powershell
cargo run --manifest-path crates/sens-cli/Cargo.toml -- your-file.lisp
```

### Етап 1 — дані проти арифметики

```lisp
(quote (+ 1 2 3))
```
Друкує інертний список `(+ 1 2 3)` — три символи, нічого не обчислено.

```lisp
(+ 1 2 3)
```
Друкує `6` — той самий текст, тепер виконаний.

### Етап 2 — дані проти визначення

```lisp
(quote (def answer 42))
```
Друкує `(def answer 42)` — опис визначення, ще не зроблений.

```lisp
(def answer 42)
```
Друкує `42`, і `answer` тепер існує в середовищі.

### Етап 3 — дані проти функції

```lisp
(quote (def square (lambda (x) (* x x))))
```
Друкує сам lambda-вираз, необчислений.

```lisp
(def square (lambda (x) (* x x)))
(square 5)
```
Визначає `square`, потім друкує `25`.

### Етап 4 — дані проти керуючої логіки

```lisp
(quote (cond ((eq 2 2) 100) (t 0)))
```
Друкує форму `cond` як звичайний список.

```lisp
(cond ((eq 2 2) 100) (t 0))
```
Друкує `100` — умова справді виконується.

### Етап 5 — вирощування самої мови

`defmacro` отримує свої аргументи як дані (необчислені, як і при `quote`) і повертає новий код для виконання evaluator'ом — саме так `lib/core.lisp` розгортає похідні форми, не додаючи нічого до Rust-ядра (див. принцип межі bootstrap у `docs/language-core.md`):

```lisp
(defmacro unless (condition body)
    (list (quote cond)
        (list condition (quote ()))
        (list (quote t) body)))

(unless (eq 1 2) (quote different))
```
Друкує `different`. Секунду тому `unless` не існувало в мові — ви щойно виростили його з того самого прийому quote/без-quote, що й у етапах 1–4.

### Етап 6 — прийом, доведений до кінця

`quote` ставиться до коду як до даних; `defmacro` будує новий код із даних. Наступний крок — програма, що *виконує* код, переданий їй як дані — evaluator. [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) — саме такий, написаний засобами SENS, через `read`, що перетворює текст на дані (див. етап 1), і власні `car`/`cdr`/`cons`/`atom`/`eq`/`cond`/`lambda` для інтерпретації — ті самі примітиви, що й у цьому туторіалі, тепер диспетчеризовані самі на себе:

```lisp
(my-eval (read "((lambda (x) (* x x)) 6)") (quote ()))
```
Друкує `36`. Завантажте його поряд з `lib/core.lisp` і прочитайте власний header-коментар файлу — що він навмисно лишає поза межами і чому.

## Deutsch

**SENS** ist homoikonisch: Code und Daten teilen sich eine Notation. Ein Ausdruck, der in `(quote ...)` gewickelt ist, sagt dem Evaluator "behandle dies als reglose Daten, führe es nicht aus". Entfernen Sie diesen Wrapper, und derselbe Text wird zu einem laufenden Programm. Dieses Tutorial ist eine fünfstufige `.lisp`-Datei: Führen Sie jeden Block mit `(quote ...)` aus, lesen Sie das ausgegebene Ergebnis, entfernen Sie dann den `quote`-Wrapper und führen Sie ihn erneut aus.

Jedes Paar mit der CLI ausprobieren:

```powershell
cargo run --manifest-path crates/sens-cli/Cargo.toml -- your-file.lisp
```

### Stufe 1 — Daten gegen Arithmetik

```lisp
(quote (+ 1 2 3))
```
Gibt die reglose Liste `(+ 1 2 3)` aus — drei Symbole, nichts berechnet.

```lisp
(+ 1 2 3)
```
Gibt `6` aus — derselbe Text, jetzt ausgeführt.

### Stufe 2 — Daten gegen eine Definition

```lisp
(quote (def answer 42))
```
Gibt `(def answer 42)` aus — eine Beschreibung einer Definition, noch nicht erstellt.

```lisp
(def answer 42)
```
Gibt `42` aus, und `answer` existiert nun in der Umgebung.

### Stufe 3 — Daten gegen eine Funktion

```lisp
(quote (def square (lambda (x) (* x x))))
```
Gibt den Lambda-Ausdruck selbst aus, unausgewertet.

```lisp
(def square (lambda (x) (* x x)))
(square 5)
```
Definiert `square`, gibt dann `25` aus.

### Stufe 4 — Daten gegen Kontrollfluss

```lisp
(quote (cond ((eq 2 2) 100) (t 0)))
```
Gibt die `cond`-Form als einfache Liste aus.

```lisp
(cond ((eq 2 2) 100) (t 0))
```
Gibt `100` aus — die Bedingung wird tatsächlich ausgeführt.

### Stufe 5 — die Sprache selbst wachsen lassen

Ein `defmacro` erhält seine Argumente als Daten (unausgewertet, wie bei `quote`) und gibt neuen Code zurück, den der Evaluator ausführt — so bootstrappt `lib/core.lisp` abgeleitete Formen, ohne die Rust-Kern-Oberfläche zu vergrößern (siehe das Bootstrap-Grenze-Prinzip in `docs/language-core.md`):

```lisp
(defmacro unless (condition body)
    (list (quote cond)
        (list condition (quote ()))
        (list (quote t) body)))

(unless (eq 1 2) (quote different))
```
Gibt `different` aus. Einen Moment zuvor existierte `unless` noch nicht in der Sprache — Sie haben es gerade aus demselben Quote/Ohne-Quote-Trick wie in den Stufen 1–4 wachsen lassen.

### Stufe 6 — der Trick zu Ende gedacht

`quote` behandelt Code als Daten; `defmacro` baut neuen Code aus Daten. Der nächste Schritt ist ein Programm, das als Daten übergebenen Code *ausführt* — ein Evaluator. [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) ist genau das, mit SENS geschrieben, mit `read`, das Text in Daten verwandelt (siehe Stufe 1), und den eigenen Primitiven `car`/`cdr`/`cons`/`atom`/`eq`/`cond`/`lambda` zur Interpretation — dieselben Primitive, die dieses Tutorial durchgehend benutzt hat, jetzt auf sich selbst angewendet:

```lisp
(my-eval (read "((lambda (x) (* x x)) 6)") (quote ()))
```
Gibt `36` aus. Zusammen mit `lib/core.lisp` laden und den eigenen Header-Kommentar der Datei lesen — was sie bewusst auslässt und warum.
