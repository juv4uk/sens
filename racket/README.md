# my-lisp для Racket / DrRacket

Платформенна підтримка мови **my-lisp** як повноцінного `#lang`-плагіна
для Racket (Racket CS, версія 8+). Racket тут — **субстрат, а не
специфікація**: evaluator зобов'язаний виконувати той самий закон SENS,
а не мати власну T/NIL/truthiness-семантику
(`interpreter.rkt`), а поточний бібліотечний профіль — `lib/core4.lisp`, той самий
Contract-8 source, який використовує Rust-реалізація. JIT Chez Scheme компілює сам evaluator;
my-lisp-форми виконує `my-eval`.

> Важлива деталь діалекту: `quote` записується **явно** — `(quote x)` —
> без апострофа-скорочення `'x`. У my-lisp апостроф тепер є частиною
> символу (наприклад, `об'єкт`).

## Структура

```
racket/
├── info.rkt          ← опис пакета для raco + реєстрація мови в DrRacket
├── main.rkt          ← адаптер #lang: #%module-begin / #%top-interaction, echo
├── interpreter.rkt   ← ядро: my-eval, середовища, runtime-макроси, примітиви
├── reader-lib.rkt    ← reader: S-вирази, ' як символ, exact decimal literals
├── reader.rkt        ← syntax/module-reader обгортка над reader-lib
├── boot/core.lisp      ← compatibility-named packaged copy of current Core4 source
├── lang/
│   └── reader.rkt    ← точка входу, яку шукає `#lang my-lisp`
└── README.md         ← ця інструкція
```

## Архітектура: source is sacred

`lib/core4.lisp` — авторитетне бібліотечне джерело поточного Core4 для обох реалізацій. Core1/Core2/Core3 мають окремі профільні ролі, але PredicateBit/ATOM/EQ/COND належать до спільного фундаменту SENS і не змінюються вибором профілю. `interpreter.rkt` реалізує **машину** (evaluator, середовища, примітиви), а не бібліотечне знання: жоден алгоритм з `lib/*.lisp` не переписується у `.rkt`.

Макроси — **runtime-замикання над сирими datum** (традиційна
unhygienic модель, як у Rust-реалізації): при виклику макроса
`my-eval` застосовує transformer до невиражених форм аргументів і
ре-евалює результат у тому самому середовищі. Racket `syntax-case` /
hygiene в expansion не беруть участі — `datum->syntax` живе лише на
межі `#lang`-інтеграції (`main.rkt`). Expansion не мемоізується:
макрос у циклі розгортається на кожній ітерації, як і в Rust-версії,
тож кількість side-effectів збігається за конструкцією.

> Чому два reader'и? Рядок `#lang X` за контрактом шукає модуль
> `X/lang/reader`. Тому `lang/reader.rkt` — тонка обгортка, що
> реекспортує логіку з основного `reader.rkt`.

## Крок 1. Встановлення пакета

З кореня репозиторію виконайте в терміналі:

```sh
raco pkg install --link --name my-lisp racket/
```

(або з каталогу `racket/` — просто `raco pkg install --link`).
Прапорець `--link` не копіює файли, а створює посилання на каталог:
будь-які зміни у вихідниках одразу підхоплюються.

Перевірка, що колекцію зареєстровано:

```sh
raco pkg show my-lisp
```

**Пастка (реальний випадок, 2026-08-18):** `raco pkg show` підтверджує лише
що пакет *зареєстровано*, не звідки він фактично резолвиться. Якщо колись
уже виконувався `raco pkg install my-lisp` **без** `--link` (наприклад,
скопійовано з чужої інструкції), Racket мовчки скопіював файли в
`AppData/Roaming/Racket/<версія>/pkgs/my-lisp/` (Linux/macOS:
`~/.local/share/racket/<версія>/pkgs/`) — і відтоді будь-яка правка
`interpreter.rkt`/`main.rkt` у репозиторії **не матиме жодного ефекту**,
без помилки й попередження: `#lang my-lisp` продовжує тихо виконувати
застарілу копію. Симптом — "виправлений" баг виглядає так, ніби фікс не
застосувався. Перевірка, звідки реально резолвиться модуль:

```sh
racket -e '(displayln (collection-file-path "main.rkt" "my-lisp"))'
```

Якщо шлях веде в `AppData`/`.local/share`, а не в цей репозиторій —
перевстановіть з посиланням:

```sh
raco pkg remove my-lisp
raco pkg install --link --name my-lisp racket/
```

**Друга пастка, окрема від першої (реальний випадок, 2026-08-18):**
`--name my-lisp` **обов'язковий**. Без нього `raco pkg install --link`
називає пакет за basename каталогу — тобто `racket`, а не `my-lisp` —
попри те, що колекція всередині (`info.rkt`'s `collection`) все одно
`my-lisp`. Пакет під назвою `racket` при цьому працює ідентично (усі
приклади з цього README виконуються нормально), тому проблема
непомітна, доки хтось не спробує встановити `my-lisp` іншим шляхом
(наприклад `raco pkg install --name my-lisp git://github.com/...
racket#main`) — тоді виникає:

```
raco pkg install: packages conflict
  package: git://github.com/.../racket#main
  package: racket
  module path: my-lisp/reader
```

Це не конфлікт git-джерела з чимось стороннім — це конфлікт з вашим
власним, раніше неправильно названим локальним пакетом, який уже
застовпив колекцію `my-lisp`. Перевірка:

```sh
raco pkg show -a | grep -i "racket \|my-lisp "
```

Якщо бачите пакет із назвою `racket`, що вказує на `racket/`-каталог
цього репозиторію (не на вбудований дистрибутив) — видаліть і
перевстановіть з правильним `--name`:

```sh
raco pkg remove racket
raco pkg install --link --name my-lisp racket/
```

## Крок 2. Запуск constitution.lisp у DrRacket

Приклад лежить у [`examples/constitution.lisp`](examples/constitution.lisp).

1. Додайте **першим рядком** цього файлу:

   ```lisp
   #lang my-lisp
   ```

2. Відкрийте файл у **DrRacket**. Ліворуч унизу має з'явитися напис
   «Determine language from source» / мова `my-lisp`
   (мову також можна обрати вручну: *Language → Choose Language… → my-lisp*).

3. Натисніть кнопку **Run** (Ctrl+R). DrRacket скомпілює модуль
   JIT-компілятором Chez Scheme й виконає його; у панелі взаємодій
   (REPL) одразу доступні всі визначення файлу.

Той самий файл можна запустити і з терміналу (з каталогу `racket/`):

```sh
racket examples/constitution.lisp
```

## Що дає мова

Сім примітивів Маккарті — `quote`, `atom` (`atom?`), `eq`, `car`, `cdr`,
`cons`, `cond`, — плюс:

```lisp
#lang my-lisp

;; Точна арифметика: ділення завжди повертає exact-дріб
(/ 5 336)          ; ⇒ 5/336 (не наближення!)
(/ 5.0 2)          ; ⇒ 5/2

;; PredicateBit: control приймає тільки точний результат предиката
(atom (quote x))                  ; ⇒ 1
(atom (quote (x)))                ; ⇒ 0
(if (atom (quote x))
    (quote yes)
    (quote no))                   ; ⇒ yes

;; t, (), числа та інші значення не перетворюються неявно на truth

;; Класичні макроси (runtime transformers; quasiquote відсутній,
;; тож форми будуємо явно через list/cons)
(defmacro (when test . body)
  (list (quote if) test (cons (quote begin) body)))

(when (atom (quote x))
  (print "x — атом"))
```

## Echo-політика REPL

Як і в вашому CLI, у DrRacket (вкладка взаємодій / REPL) введення
одиночного нев'язаного ідентифікатора друкує `echo <ідентифікатор>`
замість помилки:

```text
> hello
echo hello
> мама
echo мама
> (+ 1 2)
3
```

## Відомі обмеження

* Reader не підтримує quasiquote/unquote (як і сама мова наразі) —
  macro transformers будують форми явно через `cons`/`list`, так само
  як це робить поточний `lib/core4.lisp`.
* За замовчуванням цей Racket-профіль завантажує поточний `lib/core4.lisp`; інші
  бібліотеки (`lib/reason.lisp`, `lib/unify.lisp` тощо) доступні через
  `(load "шлях")`, але conformance-покриття цього порту ще не
  зафіксоване в `evidence/`.
* Виконання — tree-walking інтерпретація, без компіляції expanded
  форм у Racket syntax. Це свідомий вибір fidelity-first: Chez JIT
  прискорює evaluator, а не my-lisp-програми. Компіляція expanded
  core-форм — можлива майбутня оптимізація, допустима лише за умови
  проходження тих самих conformance-фікстур.

## Видалення пакета

```sh
raco pkg remove my-lisp
```
