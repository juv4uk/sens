# Експеримент self-carry СЕНС #1397 — exact-функція через дві стадії

Дата: 2026-09-26  
Гілка: `research/1397-exact-sens-self-carry`  
Батьківське дослідження: #1397 / #1383

## Питання

Чи може функція СЕНС пройти через одну мовну стадію і стати виконуваною
головою наступної **без** round-trip через людське ім'я, рядок, quoted-symbol,
десяткове/шістнадцяткове представлення або backend semantic enum?

У bounded-експерименті використано `00000101`, бо ця функція вже має admitted
callable mechanism у root runtime. Переносник — exact `00001000`, а не
іменований helper.

## Виконуваний шлях

```text
00000101
   ↓
((00001000 (f) f) 00000101)        стадія A
   ↓
exact runtime value 00000101
   ↓
(((00001000 (f) f) 00000101)
  (00000001 (alpha beta)))          стадія B
   ↓
alpha
```

Rust-witness спостерігає стадію A через чинне runtime-представлення
`Value::Sid(Sens8)` і вимагає, щоб payload дорівнював `sens!(00000101)`.
Назва цього Rust-variant є лише vocabulary реалізації; експеримент не вводить
другої мовної identity поверх восьми бітів.

Жоден Core loader не викликається. До і після двостадійного виконання
`selected_core_profile() == None`.

## Adversarial surface-bindings контроль

Окремий тест через exact-функції `00000001`, `00000101` і `00001000`
отримує їхні admitted peer-surfaces лише для **налаштування ворожого середовища**
і переприв'язує кожне таке ім'я в root environment до sentinel
`surface-poison`.

Після цього той самий двостадійний exact-source без жодного surface spelling:

```text
((00001000 (f) f) 00000101)
(((00001000 (f) f) 00000101) (00000001 (alpha beta)))
```

усе одно переносить `00000101` як exact function і повертає `alpha`.

Це сильніше за просту перевірку «в source немає слів»: навіть runtime bindings
людських peer-surfaces, що відповідають трьом задіяним exact-функціям, навмисно
робляться неправильними, а exact-path їх не читає.

Registry projection у цьому тесті використовується лише test harness-ом, щоб
знайти bindings для отруєння. Він не бере участі в перенесенні або виконанні
самого exact source.

## Fail-closed контроль

Той самий carrier переносить `11111111` без зміни:

```text
11111111 → стадія A → exact 11111111 → виклик стадії B
```

Стадія B завершується вже наявною іменованою помилкою:

```text
SENS function has no admitted callable mechanism: 11111111
```

Отже, помилка виникає тому, що exact-функція не має admitted callable
mechanism, а не тому, що її identity загубилась або була неправильно
реконструйована.

Негативний контроль — семибітний lookalike `1111111`. Канонічний parser
читає його як exact-десяткове число `1111111`; те саме замикання переносить
це число, а стадія B завершується `expression is not callable`. У SENS
mechanism admission це значення не потрапляє. Так ми відділяємо належність
до восьмибітного простору функцій від самого факту успішного перенесення.

## Що саме доведено

- exact-функція СЕНС може бути first-class value;
- стадія A повертає те саме exact-представлення функції, яке отримала;
- стадія B безпосередньо використовує повернуте значення як виконувану голову;
- source witness не виконує перетворення function-name → SENS;
- для identity не використовується string, quoted-symbol, decimal, hex або
  semantic enum;
- unsupported exact-функція лишається exact і fail-closed на admission
  механізму;
- схожий токен поза восьмибітним function space проходить інший,
  ordinary-value failure path;
- експеримент не потребує вибору Core profile і не змінює production semantics.

## Чесна межа доказу

`Session::default()` встановлює звичайне root builtin environment, реалізація
якого скомпільована разом із generated registry projection. Поточний public
test API не дає production-neutral способу фізично прибрати всі root surface
bindings або compiled registry table.

Тому цей перший slice доводить, що двостадійний exact-path **не потребує
завантаження surface source/library, не робить function-name round-trip і
залишається працездатним, коли peer surface bindings задіяних функцій навмисно
отруєні**.
Він не стверджує, що compiled projection фізично був відсутній у процесі.
Сильніший witness із фізично вилученими surface tables потребував би окремого
bounded test hook або substrate witness; такий hook не можна непомітно
протягувати в цей research PR як production runtime change.

## Не є метою

- повертати deprecated `Sid8` як мовну онтологію;
- створювати named primitive table;
- повертати `CanonicalIdentity` / `NecessaryFormIdentity`;
- переписувати історичну семантику Core1;
- автоматично переносити результат цього research у production.

Це лише evidence для #1383.
