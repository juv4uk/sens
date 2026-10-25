# Jīvanmukta (जीवन्मुक्त) — контрольна точка релізу D1–D12+ · 2026-10-25

## Межі та авторитет

Репозиторій: https://github.com/juv4uk/sens. Працюємо без створення гілок. Семантичний авторитет — SENS та Contract 12.0; фізичні пари `.lisp ↔ .sens ↔ bit-view` мають бути згенеровані штатним Zig/T5M та перевірені на одному SHA. Не редагувати фізичні байти вручну й не вважати наявність DEFINE доказом виконання.

## Дії, внесені цим ходом

- Створено контрольну точку комітом [c4ca399](https://github.com/juv4uk/sens/commit/c4ca399a277280e2dd5ddce580e25d82a8fa4c2b). Її повідомлення містило маркер `SENS_PAIR_REGEN`, щоб не пропускати наявний target-remint workflow.
- Стартував CI [run 40208478645](https://github.com/juv4uk/sens/actions/runs/40208478645): обидва job-и спочатку були активні, і target remint вже не був `skipped`.
- Не створював субагентів: у доступному інструментарії немає операції spawn; не видаю текстове доручення за реальну паралельну роботу.

## Що відомо про run 40208478645

Перевірений SHA: `c4ca399a277280e2dd5ddce580e25d82a8fa4c2b`.

- Механічні кроки CI до Rust були успішні.
- Крок **«Rust — механізм без мовного оракула» завершився failure**. Поки інший крок загального job продовжував виконання, GitHub не віддавав лог цього job для точного traceback; причину Rust RED не можна вигадувати.
- Target remint зміг зібрати `sens` і `sens-trit`, підготувати D24-корені та завершити крок канонічного mint. Однак наступна перевірка на чинному дереві завершилася `failure`; це не фізичний PASS.
- У парних джерелах помилка повторювалася як `domain identity is not callable under its ratified law: D6 000000`. За `contracts/d6-ratification.lisp`, D6:000000 — `LENGTH` / `довжина`. Це означає, що реальне парне виконання не мало доступного допущеного механізму/замикання для цієї адреси на перевіреному шляху. Діагностика сама по собі ще не визначає, чи проблема в source lowering, установленні D6 binding slot, чи в застарілому фізичному Core4: наступний крок мусить відрізнити ці шари.
- Runner повідомив `REMINT_CURRENT_MAIN_CONTEST_RED`, `REMINT_RECOVERY_NATIVE_RED` та розбіжність SHA для фізичної пари `benchmarks/contest-uk/акерман-малий.lisp`. Уже перевірені пари не були безумовно просунуті; commit-step remint закінчився failure.
- Census того SHA: `total_lisp_files=2264`, `potential_program_files=2154`, `complete_triplets=1384`, `potential_program_missing_sens=770`, `potential_program_missing_complete_triplet=770`; `semantic_runtime_proven=False`, `release_ready=False`. Це стан з конкретного run, не лічильник нового HEAD.

Run: https://github.com/juv4uk/sens/actions/runs/40208478645

## D1–D12+: поточна межа доказу

- **D1–D3:** `ні`/`так` залишаються точними D1-результатами; D3: `()`, QUOTE, ATOM, CDR, CAR, EQ, COND, CONS. Type не замінювати на false чи `()`.
- **D4–D5:** кожен оператор потребує точного закону, правильної арності та позитивного/негативного свідків.
- **D6:** ратифікована координата не гарантує виконуваності. Перший конкретний блокер — LENGTH D6:000000 та його фізичне парне виконання. Після нього — LENGTH-ONTO D6:000001, MIN/MAX D6:000010/000011, кожен з окремими laws/mutants/Type negatives.
- **D7–D10:** координатна резидентність — не викличність. Перевіряти за exact bits, реалізацією, binding і фізичним свідком; D7 текстові координати — дані, а не голови.
- **D11:** похідні композиції не створюють новий примітив чи opcode; спершу повторно використовувати наявні SENS-визначення.
- **D12+:** точні числові домени D12 → D24 → D48 → D96 → D192 …; без wrap, truncation і неявного bridge між ширинами. T5M переносить вже встановлені точні слова, а не надає ідентичність.

## Вузький еталон D12/T5M для наступного свідка

Вихідний вираз SENS:

```lisp
(додати -2048 2047)
```

Очікуваний точний результат — `-1`, ширина вхідних числових слів D12, ширина результату D12. Позитивний свідок має пройти source admission → Zig/T5M encode/decode → SENS evaluator; сусідні свідки мають перевірити `(додати 2047 1)` → D24 `2048`, `(додати -2048 -1)` → D24 `-2049`, а також фізичне відхилення ділення на нуль. Це цільові закони, не заява про PASS.

## Естафета наступному агенту

1. Взяти **поточний** `main` SHA; не переносити failure/успіх із `c4ca399` на новіші коміти без запуску на тому SHA.
2. Отримати конкретний Rust failure зі завершеного job-log і відтворити найменший failing test. Не ослаблювати law assertion заради зеленого CI.
3. Для D6:000000 локально в межах CI ізолювати три етапи: source head → exact D6 identity, binding конкретного SENS closure у його слот, виконання щойно mint-нутого Core4 через парний evaluator. Додати позитив, мутант і Type-негатив; заборонені host-side семантичні обхідні шляхи.
4. Переробити target remint так, аби він доводив паритет кандидатних пар і реальне виконання без оцінки застарілої пари, якщо саме це є встановленою причиною RED. Не просувати пару без нативного свідка та exact SHA/hash receipt.
5. Закрити 770 відсутніх `.sens`/triplets по одному перевіреному програмному джерелу; відділяти справжні програми від документів/тестових даних. Після цього переаудитувати D6 ledger за Contract 12.0 і продовжити D10/D12+.

**Вердикт на SHA `c4ca399`: `RELEASE=NO-GO`.** Target remint не завершився успішно, один Rust-крок червоний, фізична виконуваність усієї драбини D1–D12+ не підтверджена.

## Додаток Jīvanmukta — 2026-10-25, після manifest/F6-патчів

Поточний source HEAD на момент цього запису:
`ab805e8d97f357ca35fc60b4ba81851ce7f9b2dd`.

### Наступні виправлення в main

- [`b43eb09`](https://github.com/juv4uk/sens/commit/b43eb091592452ca247f083a113cc0ea5fd95be6): зберігати caller manifest після non-fast-forward; глобальні scans вмикаються лише для запуску без `inputs.files`.
- [`814cbfd`](https://github.com/juv4uk/sens/commit/814cbfd5e372a5f016eaa59fa3c83b6129a28a06): дозволити Core4 profile для F6 producer лише з чотирма точними залежностями SENS; інші комбінації залишено забороненими.
- [`e1e15df`](https://github.com/juv4uk/sens/commit/e1e15df4e2bbd3c117751db03c90a1ac4dc69165): призначити producer той самий dependency stack, який використовує вже наявний F6 WRITE→READ law runner: `lib/persistent-map.lisp`, `lib/world.lisp`, `lib/content-store.lisp`, `lib/lisp-fs.lisp`.
- [`ab805e8`](https://github.com/juv4uk/sens/commit/ab805e8d97f357ca35fc60b4ba81851ce7f9b2dd): виправити координатну помилку в новому Python workflow-invariant test. У тесті координати підрядка тепер порівнюються в одній системі індексів.

### CI-квитанція на момент запису

- [Run 40209958355](https://github.com/juv4uk/sens/actions/runs/40209958355) має exact SHA `ab805e8`, але статус `queued`; фінального результату немає.
- Попередні run-и для SHA до `ab805e8` містили власну невірну assertion-умову тесту або використовували ще стару remint-конфігурацію. Їх не можна рахувати перевіркою виправленого тесту/нового dependency stack.
- Ручна перевірка текстових інваріантів підтвердила наявність manifest guard, producer-case dependency list і точного Core4 allowlist. Це не замінює запуску Python unit test чи нативного SENS/Zig/T5M.

### Оновлений вердикт і передача

`RELEASE=NO-GO`. Нативні CI та remint на `ab805e8` очікують виконання. Після завершення перевірити в першу чергу:
1. Python `test_remint_explicit_manifest_scope` — має пройти без помилки індексації;
2. ремінт має залишитися в межах трьох початкових джерел після recovery;
3. producer повинен отримати повний dependency stack і відтворити WRITE→READ; невідомий Text7 key не можна дозволяти автоматично чи зводити до іншого ключа;
4. Core4/lisp-fs physical hash/source receipts повинні бути взяті лише з успішного завершеного job;
5. Rust RED зі старих SHA не переносити на `ab805e8`; так само жоден старий PASS не є підтвердженням нового HEAD.

## Додаток Jīvanmukta — D6 Core4 профіль повного фізичного пакета

**Знімок коду:** `92bf131c736389a85e54cd7edd534e5990b28484` (попередня база контрольної точки — `ab805e8`).

### Встановлена першопричина в run 40209958355

У [run 40209958355](https://github.com/juv4uk/sens/actions/runs/40209958355) на попередньому helper:
- pair-виконання producer уже мало `--core4-runtime` і чотири точні `--binding-source`;
- source-only фізичні пари `lib/core4.lisp` і `lib/lisp-fs.lisp` успішно пройшли свій профіль;
- але dependency-complete перевірка запускала `sens dependency-complete.sens`. CLI цього маршруту навмисно створює стерильний `Session::bare`; він не встановлює closure слот D6 LENGTH, тому повернув `domain identity is not callable under its ratified law: D6 000000`. Помилка стояла у verifier, не доводила дефекту SENS-алгоритму довжини.
- До цієї діагностики фізичний mint/обернення Zig/T5M були успішні, але producer мав `physical=NOT_CERTIFIED`; увесь remint правильно лишився RED.

### Точковий патч

- [`7272c28`](https://github.com/juv4uk/sens/commit/7272c288cc78fa65831b53d039357bcd5960e951) додає regression assertion: dependency-complete carrier мусить використовувати обраний runtime-профіль.
- [`92bf131`](https://github.com/juv4uk/sens/commit/92bf131c736389a85e54cd7edd534e5990b28484) змінює тільки виконавчу команду helper-а: `"${standalone_runtime[@]}" "$complete"`. За `--core4-runtime` це вже зареєстрований фізичний маршрут `sens-trit eval-core4`; у звичайному профілі зберігається звичайний runner. D6 не обходиться і не дозволяється автоматично.

### Поточний hosted verdict і естафета

- Новий run [40210368443](https://github.com/juv4uk/sens/actions/runs/40210368443) для `92bf131` був у черзі на останньому опитуванні. Тестовий run [40210355888](https://github.com/juv4uk/sens/actions/runs/40210355888) також очікував виконання.
- Старий run [40209958355](https://github.com/juv4uk/sens/actions/runs/40209958355) — `failure` до цього виправлення і не є вердиктом нового коду.
- Після нового запуску перевірити: (1) Python test `test_remint_explicit_manifest_scope`; (2) producer `T5M_REPAIR_OK` із фактичним dependency-complete Core4 round-trip; (3) негативний physical mutant rejected; (4) точні source/physical receipts; (5) загальний Rust/Zig/SENS job за exact SHA.

**Вердикт на час контрольної точки: `RELEASE=NO-GO`; новий root-cause patch внесений, hosted підтвердження очікується.** Не переносити ні RED, ні PASS з іншого SHA.

