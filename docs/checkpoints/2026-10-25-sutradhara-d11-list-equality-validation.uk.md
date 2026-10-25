# Sūtrādhāra — checkpoint D11 list equality та D6 source routing
Дата: 2026-10-25 (Europe/Kyiv)
Репозиторій: https://github.com/juv4uk/sens
Відгалуження: main

## Поточний стан

Останній перевірений HEAD перед цим checkpoint: `4c4ecaa7be4de1154bfcf81fcdb9636c8aa764f2`. Коміти створюються безпосередньо в `main`; цей процес має багато паралельних CI запусків, тож перед наступною зміною слід перечитати головний ref і файли.

## Нове SENS-виправлення list=

Коміт [4c4ecaa](https://github.com/juv4uk/sens/commit/4c4ecaa7be4de1154bfcf81fcdb9636c8aa764f2) змінює `lib/d11-srfi1-list-equality.lisp`, blob `bd418db0775da99d02b31a8ceb9350e03bd82fc3`. Джерельна першопричина попередніх чотирьох негативних RED: перевірка неправильної форми могла повертати D1:ні замість помилки Type. У новій формі правильний скінченний список завершується лише точним D3:(); будь-який інший атомний хвіст передається до D3 ПЕРШЕ, яке повинно підняти Type. Валідація переліку вкладених списків використовує ту саму межу та не перетворює неправильну форму на логічну хибу.

Негативні свідки, які потрібно перевірити на свіжому HEAD:
- `d11-list-equality-improper-left-type`
- `d11-list-equality-improper-right-type`
- `d11-list-equality-invalid-singleton-type`
- `d11-list-equality-invalid-third-type`

Run [40155580648](https://github.com/juv4uk/sens/actions/runs/40155580648) для цього коміту був `in_progress`, Rust-крок завершився `failure`, Zig-крок продовжувався. Тому новий SENS код ще `NOT_VERIFIED`; результат не слід описувати як PASS. Цей commit message також запитує канонічний artifact mint; після появи артефакту перевірити обидва фізичні файли, Git blob SHA і джерельний SHA перед оновленням sidecar-ів.

## D6 українські source heads

Коміт [dcfcf00](https://github.com/juv4uk/sens/commit/dcfcf005c8643650f0f28c8ccb246b35f9a238b8) виправляє зафіксований старий Rust E0277: замість generic `identity.into()` явним чином оброблюється лише `DomainIdentity::D6(word)`. Коміт [30778c7](https://github.com/juv4uk/sens/commit/30778c70846569b7729789b29adcb4101ffd4427) дозволяє точні українські `ук`/`укр` імена з generated D6 binding table; тест включає `довжина`→D6:000000, `довжина-до`→D6:000001 та `нехай*`/`нехай-послідовно`→D6:001001. Англійські `length`/`let*` і санскритський `krama-sthānika-bandha` мають залишатись недопущеними.

Важливо: старий E0277 з run [40154655166](https://github.com/juv4uk/sens/actions/runs/40154655166) належить SHA до коміту `dcfcf00`, отже не доводить, що його виправлення зараз хибне. Новіше підтвердження потрібне від актуального CI. Запуски [40155227315](https://github.com/juv4uk/sens/actions/runs/40155227315), [40155192565](https://github.com/juv4uk/sens/actions/runs/40155192565), [40155112922](https://github.com/juv4uk/sens/actions/runs/40155112922) та [40154920750](https://github.com/juv4uk/sens/actions/runs/40154920750) ще були в роботі на останній перевірці. У деяких із них Rust-крок уже позначений `failure`, але повні журнали не можна витлумачити, доки job ще не завершився.

## Фізична пара D11 SPAN/BREAK

Чинне джерело `lib/d11-srfi1-span-break.lisp` має blob SHA `a48fd9e54b1de26f95121f8eb690e6cb407b4702`. Старий artifact run [40154844558](https://github.com/juv4uk/sens/actions/runs/40154844558) був створений для іншого source blob (`0ebc16d...`) і його байти **не можна** комітити проти нового джерела. Його старий артефакт звітував `physical=ZIG_VERIFIED semantic=NOT_CERTIFIED`.

Run [40155227315](https://github.com/juv4uk/sens/actions/runs/40155227315) запускає повторний mint саме після змін D6 source routing; на останній перевірці він дійшов до Zig-кроку після Rust failure, артефакт ще не з'явився. Чекати лише синхронним опитуванням стану; коли артефакт доступний, зберегти точні raw outputs, перевірити source blob збігається з поточним, потім оновити `lib/d11-srfi1-span-break.sens` і `lib/d11-srfi1-span-break`. Ніколи не реконструювати фізичні байти вручну.

## Інші підтверджені архітектурні межі

- D1 — точне бінарне значення істини/хиби; D2 — структура; D3/D4 — базові механізми.
- Резидентність D5–D10 не доводить викличності кожної адреси; D11 — SENS-композиції/селектори без нових opcode.
- D12+ — числова драбина, а не каталог функцій. D12 signed діапазон — −2048…2047; widening у D24 без wrapping. Загальний CLI/REPL лишається D24-first.
- Попередній D6 ledger мав 60/64 резиденти без механічного доказу.
- Release GO не надавати, доки не пройдено свіжі Rust, Zig/T5M, pair/view parity та SENS позитивні й негативні закони.

## Наступна послідовність

1. Перевірити run 40155580648: точні Type результати чотирьох list-equality свідків і статус pair/view artifact.
2. Отримати актуальну причину Rust failure з завершеного job на найновішому SHA; не плутати старий E0277 із новим failure.
3. Дістати output run 40155227315; оновити SPAN/BREAK sidecar-и тільки після blob SHA та source SHA перевірки.
4. Перевірити свіжі D6 uk/ukr та macro-Text7 закони, включно з негативами для English/Sanskrit peers.
5. Після кожного root-cause fix rerun exact law на одному SHA; далі продовжити ledger невизначених D1–D11, потім D12 source/REPL floor.

**Статус:** кілька точкових змін запушені; поточні фізичні та семантичні перевірки ще не дали повного PASS. Жодні незалежні субагенти тут не запускались.
