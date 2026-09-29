# #1766, крок 1: інвентар сирої межі виконання `eval_expr`

Автор: Claude Sonnet 5.5 (`claude-sonnet-5-5`) · виконавець продуктивності мови · juv4uk/sens.
Бази: `sens` `origin/main` `f34bde92`; `my-idea` `origin/main` `308b4de`; `chess-lisp-zero` `origin/main` `1eadd7e` (усі 2026-09-29, крім двох останніх, див. «Межі»).
Дані: [`data/1766-eval-expr-sites-f34bde92.tsv`](data/1766-eval-expr-sites-f34bde92.tsv), одне входження на рядок.

*English layer: an inventory of every use of the public raw evaluator `pub use evaluate as eval_expr` across the three repos that use it, classified by the four classes from #1766. This step changes no code and adds no wrapper. Evidence labels: **executed** = a command was run; **source-confirmed** = read in the code, not run; **predicted** = inferred, not checked.*

## Що і як міряли

- Усі входження `eval_expr` у трьох репо: `git grep -n -E 'eval_expr\b' <ref> -- '*.rs'` (**executed**): **42** рядки.
- Класи з #1766 (`B`, `C`, `D`) плюс три службові: `T` (тест), `export`, `import`, `doc`.
- Скрипт відмовляється працювати, якщо для якогось входження немає класу, тож інвентар повний за побудовою. Скрипт у репо не додаю (щоб не чіпати ратчети інвентарю скриптів); метод відтворюється командою вище й TSV.
- Для кожного виклику в capability-обробнику скрипт визначає найближчу `fn` вище й ім'я capability з блоку `register_capability`, тож таблиця пов'язує рядок коду з назвою capability.
- Пошук по всіх клонах у `/home/agents/GitHub/*` (`eval_expr`, `register_capability`, `HostFn`, `register_sens_capability`) знайшов їх лише в `sens`, `my-idea`, `chess-lisp-zero` (**executed**).

## Публічні точки входу виконання в `sens` (source-confirmed, `lib.rs`, `eval/mod.rs`)

| функція | що робить |
|---|---|
| `eval_program(source, session)` | розбір, зведення (`lower_program`), виконання |
| `eval_parsed_expressions` / `_incremental` | зведення й виконання вже розібраного |
| `eval_lowered_expressions` | виконання вже зведеного, без зведення |
| `lower_program` | лише зведення |
| **`evaluate as eval_expr`** | **сире виконання розібраного `Expr` повз зведення**: межа з #1766 |

Модуль `eval` крейт-приватний (`pub(crate) mod eval;`, `lib.rs:14`), тож сирий `evaluate` досяжний ззовні лише через цей псевдонім.

## Результат: 42 входження

| репо | B: аргумент capability | C: виклик callback | D: застарілий цикл | T: тест | export / import / doc |
|---|---:|---:|---:|---:|---:|
| `sens` | **18** | 0 | **1** (`load`) | 1 | 1 / 3 / 0 |
| `my-idea` | **10** | **1** | 0 | 0 | 0 / 1 / 2 |
| `chess-lisp-zero` | 0 | 0 | **3** | 0 | 0 / 1 / 0 |
| **разом** | **28** | **1** | **4** | 1 | 1 / 5 / 2 |

**28 викликів класу B у 18 capability:** 13 у `sens-host` (`read-dir`, `read-file-bytes`, `read-file-utf8-raw`, `write-file-bytes`, `process-run-raw`, `load`, `tcp-connect`, `tcp-listen-raw`, `tcp-accept`, `tcp-read-raw`, `tcp-write-raw`, `tcp-close`, `native-call-u64-raw`) і 5 у `my-idea` (`editor/register-command`, `editor/keymap`, `editor/message`, `editor/on`, `editor/replace-selection`). Один допоміжний `expect_port` (`sens-host/src/lib.rs:465`) обслуговує кілька TCP-capability.

## Висновки

1. **Усі 18 capability реєструються за назвою** і мають тип `HostFn = fn(&[Expr], &Environment, Span)`: обробник отримує **невиражені** аргументи й сам викликає `eval_expr` (source-confirmed, `eval/capabilities.rs:24`). Це і є «зворотний виклик у евалюатор».
2. **Жодна з 13 назв у `sens-host` не має коду в таблиці функцій** (перевірено пошуком `(en <назва>)` у `lib/surface/semantic-registry.lisp` на `origin/main`, **executed**). Це сирі host-механізми, а не мовні функції: мовні `read-file` (`10100110`), `write-file` (`10100111`), `process-run` (`10100010`), `tcp-read` (`10100011`), `tcp-write` (`10100100`), `tcp-listen` (`10100101`) визначені поверх них. Так само `editor/*` у `my-idea` не мають кодів.
3. **Значенневий варіант уже існує, але порожній:** `SensHostFn = fn(Sens8, &[Value], &Environment, Span)` отримує готові значення. **У виробничому коді в нього нуль викликів `register_sens_capability`** (**executed**, `git grep`); він лише в тестах. Ключ у нього `Sens8`, тому для 13 сирих механізмів, яким код не належить, простий переклад `HostFn → SensHostFn` неможливий без нового ідентифікатора механізму. Це рішення для #1276, а не для #1766.
4. **`load` у `sens-host` подвійний:** аргумент обчислюється як B (`lib.rs:597`), а потім **цикл `parse → eval_expr` по кожній формі повз `lower_program`** (`lib.rs:620`). Тобто це єдине живе місце в самому `sens`, де джерело виконується без зведення. Заміна на `eval_program` потребує `Session`, а обробник має лише `&Environment`. Треба входу «виконати зведене в `Environment`».
5. **`my-idea`: єдиний клас C.** `editor_api.rs:505` розбирає синтетичний виклик обробника й одразу `eval_expr`. Пінить `external/sens` як path-залежність.
6. **`chess-lisp-zero`: клас D, три виклики** (`chess_runtime.rs:58, 75, 99`, цикл `parse → eval_expr`). Імпорт `use my_lisp::{parse, eval_expr, …}`, залежність у `src-tauri/Cargo.toml` — `my-lisp = { git = "…/juv4uk/my-lisp.git", branch = "main" }`. **Передбачено (не запущено):** пакет `my-lisp` у поточному `sens` уже не існує (крейт перейменовано), тож репо, найімовірніше, не збирається проти актуального `sens`. Гілка `rename/sens-consumer` має ті самі три виклики, тобто імпорт там не мігровано.
7. **Тест `defmacro_ownership.rs:13`** виконує сирий вираз навмисно (проти голого кореня); це не міграційний борг, а свідоме використання.

## Що це означає для порядку #1766

| крок #1766 | що показав інвентар |
|---|---|
| 2: звичайне зовнішнє джерело → `eval_program` / `eval_parsed_expressions` | лише `chess-lisp-zero` (3 місця) і `load` у `sens-host`; для `load` потрібен вхід із `&Environment` |
| 3: capability узгоджувати з #1276 | 28 викликів у 18 capability, усі за назвою; перехід на значення потребує ідентичності механізму, якої в таблиці немає |
| 4: після нуля зовнішніх сирих викликів закрити `evaluate` | зараз зовнішніх викликів: `sens-host` 18+1, `my-idea` 11, `chess-lisp-zero` 3 |

## Питання, що виносяться окремими задачами

1. Як `load` виконує джерело з `&Environment`, не маючи `Session`, і без сирого обходу зведення.
2. Яка ідентичність у сирого host-механізму, якщо його немає в 256 функціях і нових іменованих ідентичностей не можна (#1276).
3. Як `my-idea` викликає обробник (клас C) без сирого `eval_expr`.
4. Чи будує `chess-lisp-zero` взагалі проти поточного `sens`, і міграція на `eval_program`.

## Межі цього документа

- Лише три репо, у яких пошук знайшов ці символи. `cml` і `wsm-*` у робочих деревах їх не містять; віддалені гілки не перевірялись.
- `chess-lisp-zero` `origin/main` датований 2026-09-23, `my-idea` 2026-09-27: їхні гілки за замовчуванням можуть відставати від роботи інших агентів.
- Класи призначено вручну за контекстом виклику; скрипт гарантує повноту, а не правильність кожного класу. Спірні: `expect_port` (допоміжна функція, віднесена до B).
- Це інвентар, а не зміна: жодного коду, жодної обгортки (non-goals #1766).
