# Dhṛti (धृति) · Д11 APPEND-REVERSE · 25.10.2026

## Аватар та спадкоємність
**Dhṛti** — вірність точному закону й доказу, а не кількості комітів.
Дякую Pramiti (LIST-TABULATE), Nirṇaya (LIST= Type) і колегам
Ṛju та Satya (D9/F6) за попередні незалежні свідки.
Під час початкового аудиту LIST-TABULATE уже був інтегрований у main;
не створюємо його вдруге. D9 F6 ключовий guard паралельно відновив інший
агент; чужий SENS-код не переписано.

## Аудит доменів
D1 — істина/хиба; D2 — reader; D3 — пара/перший/решта/порожнеча;
D4 — lambda/COND; D5 і D24+ — арифметика точних чисел;
D6 — уже визначені LET/LET*, NTH, MAPLIST, REDUCE із різним ступенем
механічної атестації; D7 — текстові дані; D8 — структурна рівність;
D9 — filesystem/reason; D10 — ратифіковані комбінації; D11 — бібліотека
SRFI-1 і реєстр кандидатів; D12+ — ще не доведена повна викличність.
Це класифікація, НЕ свідоцтво PASS для всіх координат.

## Нова чиста SENS реалізація
`lib/d11-srfi1-append-reverse.lisp`: три визначення SENS:
`перевірити-д3-голову-оберненого-додавання`,
`приєднати-обернену-голову-ядро`,
`приєднати-обернену-голову`.

Нормативний SRFI-1 закон: `append(reverse(rev-head), tail)`.
Перший аргумент є **скінченним правильним D3 списком**; його
повністю перевіряємо за D3:() до складання результату.
Другий аргумент — **довільне значення** за оригінальним SRFI-1,
необов'язково правильний список. Наприклад, D1:ні як tail
утворює dotted pair, не є «порожнім» кінцем і не має зникати.
Один хвостово-рекурсивний обхід накопичує результат на початку
вже наявного хвоста (час O(n); додаткові D3-пари O(n)).
Жодного нового D11 слова, D7 дублювання чи Rust-реалізації.

## Свідки та механічний маршрут
- `tests/semantic/d11-srfi1-append-reverse-law.lisp`:
  порядок елементів, елемент D3:(), порожня голова та хвіст.
- `tests/semantic/d11-srfi1-append-reverse-dotted-tail-law.lisp`:
  явний dotted tail D1:ні й точна нееквівалентність D3:().
- `tests/semantic/d11-srfi1-append-reverse-mutant.lisp`:
  хибне припущення, що елементи не обернулися (D1:ні).
- Три незалежні Type негативи: D1 корінь, пізній і глибокий
  неправильний D1 хвіст у першому аргументі.
- `scripts/prove-lisp-semantic-t5m.sh` запускає шість SENS законів
  через direct / Zig T5M mint+open+verify / paired / standalone core4;
  порівнює D1:1, D1:0 або точний CAR Type та створює SHA256 квитанції.
- `scripts/execute_changed_lisp_t5m.sh` забезпечує ті самі
  SENS DEFINE при запуску окремо змінених файлів; невідомі імена
  не допускаються замість очікуваного Type.

Статична перевірка балансу форм не дорівнює нативному PASS.
У середовищі цього агента немає Zig/SENS runner, а віддалений
Desktop Commander раніше не мав активного підключення;
нативний вердикт залишено GitHub CI на точному SHA коміту.

## Відомі реальні блокери на момент аудиту
Завершений CI #40167865589 для 06b762488cf:
мовний proof-runner **528/529**, RED:
`d9-f6-package-key-canonicalization-positive`, actual D1:0;
фізичний F6 consumer відхилив корінь з `invalid-format`.
Це два окремі свідки, не причина змін APPEND-REVERSE.
Новіші зміни колег могли змінити висновок; перевіряти новий HEAD.
Реліз `l0.42.0`: **NO-GO**, доки власник не ратифікує GO.

## Завдання наступному Swarm
1. Прогнати всі шість D11 APPEND-REVERSE свідків на точному SHA,
   не оголошувати PASS до реального direct/paired/standalone.
2. Якщо будь-який RED: надати id, шар, source SHA256, індекс фізичної
   форми, очікуваний і фактичний D1/Type. Не повторювати червоні workflow.
3. Перевірити Rust CLI F6 `invalid-format` як точне значення
   `фс-формат-кореня?` після D8 WRITE/READ; D9 пакетний key guard
   не підмінювати дозволом на довільні D7-гліфи.
4. Синхронізувати `lib/lisp-fs.lisp/.sens` і Core4 через справжній
   Zig/T5M mint; ніякого ручного перепакування або фальшивого PASS.
5. Для D6 MACROEXPAND-1/MACROEXPAND довести SENS lexical macro
   scope або чесно залишити MISSING. Після цього D10/D11/D12+
   аудит координата → нормативний закон → механізм → нативний свідок.

Deutsch: APPEND-REVERSE in reinem SENS; D1:nein ist als dotted
Tail keine D3-Leerliste. Native CI-Bestätigung ausstehend.

English: Pure SENS SRFI-1 append-reverse with full first-list
preflight, arbitrary tail, three laws and three exact Type negatives.
Native verification not claimed.
