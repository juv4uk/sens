# Контрольна точка Sūtradhāra · 25.10.2026 · D6 Lisp-виклики

## Аватар і межі

**Sūtradhāra (सूत्रधार)** — зберігаю тотожність між ратифікованою адресою, реально визначеною SENS-функцією та її виконанням. Цей крок не оголошує D1–D12+ повністю готовими.

## Першопричина

- D6:000000 `довжина` та D6:000001 `довжина-до` уже мають визначення мовою SENS у Core4 і записи в таблиці D6 binding.
- Нижній шар джерела раніше зводив українську голову до `core_operation()`. Це правильно повертало `None` для не-примітивних D6 резидентів, але через це конкретні Lisp-визначення не доходили до `DomainCall`, хоча evaluator уже мав окремий точнодоменний слот для closure.
- Виправлення: українська голова може зберегти D6-ідентичність, коли адреса збігається з чинним generated binding. Це **не** створює примітива: evaluator досі вимагає реально зв'язаний closure у тому самому D6-слоті та відмовляє fail-closed, якщо його немає.
- Нових доменних кодів, host-семантики чи переходів через старий SID8 не додано.

## Уже наявні фізичні свідки

Файл `scripts/prove-lisp-semantic-t5m.sh` уже включає:
- `tests/semantic/d6-length-onto-d3-boundary-law.lisp` — правильний список, D3:() як база, D24+ акумулятор і виклик LENGTH;
- `tests/semantic/d6-length-onto-d3-boundary-mutant.lisp` — мутант на неправильному акумуляторі;
- `tests/semantic/d6-length-onto-d1-root-negative.lisp` — D1:ні як корінь;
- `tests/semantic/d6-length-onto-late-d1-tail-negative.lisp` — D1:ні в хвості.
Ці свідки проходять прямий SENS, mint/open/verify Zig/T5M, paired SENS та standalone; для нового коміту потрібне підтвердження hosted CI.

## Статус

**Зміна коду внесена; фізичний PASS на новому SHA ще не підтверджений.** Не змінювати ledger на `LISP_OWNED`, поки свідки не пройдуть на одному SHA.

## Наступний таргет

1. Підтвердити Rust lowering-тест і всі чотири hosted SENS/T5M свідки на exact SHA.
2. Якщо RED — класифікувати перший фактичний шар (lowering, binding slot, direct SENS, mint, Zig verify, paired або standalone); не змінювати очікування для маскування регресії.
3. Після PASS перевірити D6:000010 `найменше-у-списку` та D6:000011 `найбільше-у-списку` як Lisp-owned definitions із позитивом, мутантом і Type-негативом.
4. Далі окремо продовжити D12 numeric ladder та D10 execution coverage. Не оголошувати GO всьому релізу за успіхом цього зрізу.


## Продовження Sūtrādhāra · 25.10.2026 · точний D6 source routing

### Першопричина в попередньому виправленні

Коміт [4394ef6](https://github.com/juv4uk/sens/commit/4394ef6f352114136d4fd989a5bca4f94224c827) додав unit-test, який вимагає точне джерельне зниження D6:000000 `довжина` та D6:000001 `довжина-до`. Він завершився RED на Rust-кроці в [run 40154552423](https://github.com/juv4uk/sens/actions/runs/40154552423).

Виявлена причина в порядку резолвера: `source_head_domain_identity` спершу вимагав, щоб ім’я було в загальному індексі примітивних/викличних голів, і лише всередині цього успішного пошуку пробував D6 binding fallback. Для Lisp-owned D6-замикань ця передумова хибна, тому fallback був недосяжним. Наявність `D6_DEFINITION_BINDINGS` не гарантує, що ім’я вже потрапило в індекс прямих примітивів.

### Виправлення в main

Коміт [d8e7ac5](https://github.com/juv4uk/sens/commit/d8e7ac59ced95ae2b6e2604cff03ccd5b7fc212d) додає до `crates/sens/src/semantic_registry.rs` `d6_uk_source_identity`, який шукає лише перше, канонічне українське ім’я в generated D6 definition bindings. `crates/sens/src/eval/lower.rs` тепер перевіряє цей точний шлях **до** загального індексу примітивних голів.

Це зберігає межі контракту:
- D6 identity походить лише з generated D6 binding table; ширина й біти не виводяться з числа чи SID8;
- англійський alias `length` не стає українською викличною головою через цей шлях;
- lowering зберігає D6 identity, але не створює host-примітива: evaluator усе ще потребує конкретне виконуване замикання, записане у відповідний D6-слот;
- позитивний, мутантний та два Type-негативні SENS/T5M свідки вже зареєстровані в `scripts/prove-lisp-semantic-t5m.sh`; їхній результат на SHA `d8e7ac5` поки не підтверджений.

### Статус CI на момент оновлення

[Run 40154746518](https://github.com/juv4uk/sens/actions/runs/40154746518) для `d8e7ac5` ще триває, на останньому читанні він був на кроці 11 («Звірити повторне використання функцій D1–D11»). Отже:
- `D6_SOURCE_LOWERING_UNIT=NOT_VERIFIED`;
- `D6_LENGTH_ONTO_NATIVE_SENS_T5M=NOT_VERIFIED`;
- `D6_LEDGER_PROMOTION=NOT_APPLIED`;
- `D1_D12_PLUS_RELEASE=NO_GO`.

Не змінювати `knowledge/d6-mechanism-ledger.json` на `LISP_OWNED` до завершених позитивного, мутантного та Type-негативних запусків на одному SHA. Після цього окремо провести механічний аудит згенерованого binding slot — unit-test source head сам по собі не підтверджує виконання closure.


## Корекція після Rust RED · 25.10.2026

[Run 40154746518](https://github.com/juv4uk/sens/actions/runs/40154746518) для [`d8e7ac5`](https://github.com/juv4uk/sens/commit/d8e7ac59ced95ae2b6e2604cff03ccd5b7fc212d) підтвердив RED на кроці 13 «Rust — механізм без мовного оракула». Причиною було саме перетворення `identity.into()`: у цьому місці загальне перетворення `DomainIdentity` на `CoreDomainIdentity` не було коректним.

Коміт [`dcfcf00`](https://github.com/juv4uk/sens/commit/dcfcf005c8643650f0f28c8ccb246b35f9a238b8) виправив це явним pattern match:
`DomainIdentity::D6(word) => Some(CoreDomainIdentity::D6(word))`, а всі інші варіанти відхиляються. Це кращий доказовий бар’єр: джерельний маршрут не може випадково прийняти інший домен через загальне `Into`.

**Поточна перевірка ще не завершена:** run [40154818762](https://github.com/juv4uk/sens/actions/runs/40154818762) для `dcfcf00` під час останнього запиту ще був на встановленні Zig (крок 12), до Rust-кроку. Додатковий run [40154825127](https://github.com/juv4uk/sens/actions/runs/40154825127) для коментарного уточнення також триває. Тож `D6_SOURCE_LOWERING_UNIT=NOT_VERIFIED`, `D6_LENGTH_ONTO_NATIVE_SENS_T5M=NOT_VERIFIED`; жоден D6 ledger promotion не зроблено.
