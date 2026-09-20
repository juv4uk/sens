# Аудит допуску примітивів — перший доказовий зріз (#747 / #734)

Статус: **експериментальний аудит, без перенумерації й без видалення**.

Цей документ застосовує Contract 7.0 / ADR-005 до першого репрезентативного
зрізу чинного неперервного byte-SID реєстру. Класифікація тут є доказом для
майбутніх міграційних рішень; вона **не змінює** жодного чинного SID.

## Правило допуску

Першокласну identity варто залишати тоді, коли відмінність зовнішньо
спостережувана, композиційно необхідна або мусить бути стабільною між кількома
execution witnesses. Якщо поведінку чесно виражають наявні identities разом зі
звичайними даними або derived operation — віддаємо перевагу їм. Приватна
онтологія ядра й host/runtime mechanism не стають примітивами мови лише тому,
що вони потрібні конкретній реалізації.

## Перший зріз

| SID | Identity | Клас аудиту | Доказ / рішення |
|---|---|---|---|
| 00000000 | Canon 0 / `()` | **primitive-essential** | Основа порожнього списку/відсутності й термінатор списку; Contract 7.0 лишає його незмінним. |
| 00000001 | `quote` | **primitive-essential** | Історичний корінь Маккарті; керує обчисленням, а не є convenience-функцією. |
| 00000010 | `atom` | **primitive-essential** | Структурна відмінність на межі мови; є executable Canon witnesses. |
| 00000011 | `eq` | **primitive-essential** | Стабільне identity relation історичного кореня; не замінюється host equality. |
| 00000100 | `cons` | **primitive-essential** | Конструктор базової pair-структури; існують незалежні execution witnesses. |
| 00000101 | `car` | **primitive-shared** | Canon primitive і вже має реальний Common Lisp C-ABI execution witness. |
| 00000110 | `cdr` | **primitive-shared** | Canon primitive; структурно незвідний без еквівалентної pair-проєкції. |
| 00000111 | `cond` | **primitive-essential** | Control form мови; не є звичайними payload-даними. |
| 00001000 | `lambda` | **primitive-essential** | Побудова first-class lexical function; має спостережувану binding/evaluation поведінку. |
| 00001001 | `define` | **primitive-essential** | Операція binding з видимим для програми ефектом на environment. |
| 00001100 | `+` | **primitive-shared** | Публічна exact-arithmetic operation з незалежними semantic witnesses; залишити до повного арифметичного аудиту. |
| 00100111 | `list` | **derived-operation** | Чесно будується з `cons` + Canon 0; SID не видаляється до compatibility witness. |
| 00101000 | `length` | **derived-operation** | Рекурсивний обхід списку через `cdr`/Canon 0; кандидат на демоцію. |
| 00101001 | `append` | **derived-operation** | Звичайна рекурсивна list construction через `cons`/`car`/`cdr`. |
| 00101010 | `reverse` | **derived-operation** | Виражається list primitives; convenience/performance сам по собі не створює ontology. |
| 00101011 | `nth` | **derived-operation** | Повторний `cdr` + `car`; кандидат на демоцію після compatibility evidence. |
| 00101111 | `second` | **derived-operation** | Точно `car(cdr(x))`; сильний reclaim candidate. |
| 00110000 | `third` | **derived-operation** | Повторний `cdr` + `car`; сильний reclaim candidate. |
| 00110001 | `fourth` | **derived-operation** | Повторний `cdr` + `car`; сильний reclaim candidate. |
| 00110010 | `fifth` | **derived-operation** | Повторний `cdr` + `car`; сильний reclaim candidate. |
| 00110011 | `caar` | **derived-operation** | `car(car(x))`; окрема ontology не потрібна. |
| 00110100 | `cadr` | **derived-operation** | `car(cdr(x))`; поведінково перекривається з `second`. |
| 00110101 | `cddr` | **derived-operation** | `cdr(cdr(x))`; сильний reclaim candidate. |
| 00110110 | `cadddr` | **derived-operation** | Чиста композиція наявних list primitives. |
| 01001000 | `print` | **primitive-candidate / observable effect** | Вивід зовнішньо спостережуваний; лишити до family-аудиту print/princ/write-to-string. |
| 01001101 | `eval` | **execution-specific / review** | Історично Lisp execution. Common Lisp тепер автономне Lisp execution kernel; цей SID не можна мовчки розширити до universal island invoke. |
| 01011010 | `mono-ns` | **runtime-mechanism boundary** | Сире monotonic-clock observation є host/substrate-facing; primitive necessity потребує окремого доказу. |
| 01011100 | `ntp-query-raw` | **runtime-mechanism** | Сире зовнішнє observation; host capability не повинна автоматично рости в ontology. |
| 01011101 | `timezone-declarations-raw` | **runtime-mechanism** | Mechanism-only raw observation; timezone interpretation уже Lisp-owned. |
| 01111011 | `forward-in` | **kernel-owned / optional** | Full production-rule execution природно належить CLIPS island; compatibility лишається до replacement witness. |
| 01111100 | `reason-in` | **kernel-owned / optional** | Broad reasoning/search не повинен нав'язувати одну truth ontology поверх Prolog/Datalog/CLIPS. |
| 10000111 | `unify` | **kernel-owned / optional witness** | First-order unification — нативна територія Prolog; Lisp implementation може лишитися optional/reference evidence. |
| 10000100 | `provenance` | **primitive/data distinction under review** | Provenance універсально корисна, але значна частина може бути ordinary data. Не демотувати без graph/result evidence. |
| 10100010 | `process-run` | **public capability identity** | Зовнішньо спостережувана language-visible operation над raw host mechanism. |
| 10100110 | `read-file` | **public capability identity** | Language-visible operation; raw file bytes лишаються substrate mechanism. |
| 10100111 | `write-file` | **public capability identity** | Зовнішньо спостережуваний ефект і чинний public contract. |

## Конкретні рішення цього зрізу

### Лишити примітивом

`car` (SID `00000101`) лишається first-class. Він входить до незмінного
McCarthy-root і тепер має більше одного execution witness: історичний my-lisp
шлях та реальний Common Lisp C-ABI witness.

### Кандидат на демоцію

`second` (SID `00101111`) — найчистіший derived-operation candidate:

```lisp
(car (cdr x))
```

Цей аудит не видаляє і не перенумеровує SID. Пізніша міграція спершу має
довести compatibility й зберегти корисне surface name як derived operation.

### Island-composition candidate: `invoke`

Чотири вже злиті kernel boundaries дають executable evidence, що **generic
island invocation є реальною cross-kernel operation**, тоді як чинний `eval`
специфічний для Lisp execution і не може чесно означати Prolog query, CLIPS
agenda execution чи Datalog fixpoint evaluation.

Тому `invoke` — перший evidence-backed **new primitive candidate** за #747.

У цьому PR він навмисно **не admitted**. Чинна registry migration має generated
projections і guards, зафіксовані на Canon 0 + 167 identities. Правильний
admission мусить бути атомарним:

1. додати один наступний contiguous free byte SID;
2. оновити authoritative `sr/2`;
3. regenerated function table і meta-registry projections;
4. свідомо оновити exact-count migration guards;
5. додати executable four-kernel invocation witness;
6. довести, що identity не несе kernel-private semantics.

До виконання всіх шести пунктів називати `invoke` admitted означало б створити
split semantic authority.

## Відхилена пропозиція примітива

Окремі primitives **Common-Lisp-result**, **Prolog-result**, **CLIPS-result**,
**Datalog-result** відхиляються за поточним evidence. `FourKernelObservation`
вже зберігає producer-native results поруч, а `NativeResultRef` адресує їх як
ordinary data. Чотири нові result-type SIDs лише скопіювали б приватну ontology
ядер у shared registry без operational necessity.

## Що цей аудит доводить, а що ні

Зріз перевіряє понад 20 identities, як вимагає #747, і містить як keep, так і
demotion decisions, а також evidence-backed island-composition candidate і
явно відхилену candidate identity.

Він **не** завершує #734, бо той вимагає обліку всіх identities, і **не** закриває
#747, бо `invoke` ще не пройшов atomic registry admission.


## Наступний крок admission — `invoke` тепер має executable evidence

Replay на поточному main допускає `invoke` як SID `10101000` і зберігає
атомарність admission:

1. `10101000` — наступний вільний contiguous byte SID;
2. authority лишається `sr/2`, generated projections походять із неї;
3. exact-count/contiguity guards переходять на Canon 0 + 168 identities;
4. один реальний integration witness проводить той самий SID через Common Lisp,
   Prolog, CLIPS і Datalog через shared C ABI;
5. кожне ядро зберігає власну інтерпретацію payload і native result domain;
6. witness перевіряє opaque SID provenance і не переозначує `invoke` як CAR,
   Prolog goal, CLIPS command чи Datalog relation.

Ширший primitive-budget audit #734 уже завершено окремо; цей replay закриває
лише atomic admission gap `invoke`, який відстежують #747/#779.

## Raw REPL `invoke` — це escape hatch, а не semantic routing

Інтерактивна поверхня може давати `invoke / викликати` як низькорівневу
native-boundary для діагностики, експериментів і прямого доступу до islands.
Цей шлях **не** замінює звичайне семантичне виконання Lisp.

Два шляхи навмисно різні:

```text
звичайний Lisp
  surface -> Canon/function-table SID + meaning
  -> admitted mechanism
  -> mechanism selector
  -> mechanical lowering
  -> executor

raw invoke
  invoke SID
  -> registered host capability
  -> opaque producer-native payload
  -> island
  -> explicit island-native observation
```

Common Lisp form, Prolog goal, CLIPS command або Datalog relation, передані в
raw `invoke`, лишаються native data. Їхнє написання не може створити Lisp SID,
admit execution mechanism, встановити Canon law чи переозначити чинну Lisp
identity. Raw result так само лишається producer-native observation і сам факт
успішного виконання не робить його доказом semantic law.
