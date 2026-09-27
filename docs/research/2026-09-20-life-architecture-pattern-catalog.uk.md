# Каталог архітектурних патернів LIFE — спочатку докази, потім механізм

Задача: #793  
Статус: обмежений дослідницький каталог  
Авторитет: **лише дослідницькі свідчення** — цей файл не визначає семантику my-lisp.

## Правило неперетинання осей

Дві осі лишаються незалежними:

```text
парадигми виконання: Common Lisp | Prolog | Datalog | CLIPS
субстрати my-lisp:   Rust | GraalVM | WASM/C | майбутній FPGA
```

Зовнішній прецедент може підказати механізм на будь-якій осі, але не може
перетворити одну парадигму виконання на мову реалізації всіх інших або один
субстрат — на semantic authority. Значення SID лишається власністю my-lisp.

## Словник рішень

- **borrow / запозичити** — механізм можна використати в тій самій архітектурній ролі.
- **adapt / адаптувати** — механізм корисний лише після посилення меж ownership/provenance.
- **reject / відхилити** — прецедент зливає native-домени або semantic authority.

## Каталог

### 1. Виявлення ядра та життєвий цикл — ADAPT

**Зовнішній прецедент.** MetaCall відділяє per-language loaders від core та
надає явний initialize/load/clear lifecycle. Plugin-архітектура дозволяє
runtime-specific компоненти завантажувати й вивантажувати незалежно.

Джерела:
- https://core.metacall.io/
- https://github.com/metacall/core-landing-page/blob/master/docs/docs.md

**Поточні докази my-lisp.**
- `experiments/metacall-pattern-audit-789.lisp`
- `contracts/life-1-contract.lisp`
- `crates/my-lisp/src/eval/capabilities.rs`

**Правило.** Ядро виявляється та запускається через явний механічний
descriptor/handle. Availability — це observation, а не нове значення SID.

**Відхилено.** Не вводити універсальну foreign-value ontology заради єдиного lifecycle.

---

### 2. Межа виклику — ADAPT

**Зовнішній прецедент.** GraalVM Truffle має явний interoperability protocol
зі стандартизованими повідомленнями для foreign values; реалізації мов можуть
взаємодіяти через протокол без прямого знання одна про одну.

Джерела:
- https://www.graalvm.org/jdk21/reference-manual/espresso/interoperability/
- https://www.graalvm.org/jdk21/graalvm-as-a-platform/language-implementation-framework/

**Поточні докази my-lisp.**
- `contracts/island-compat-contract.lisp`
- `tests/fixtures/island-compat-witness.lisp`
- `crates/wsm-kernel-c-abi/`

**Правило.** Запозичуємо один явний механічний invocation protocol, але payload
лишається producer-native, а semantic ID — opaque.

**Відхилено.** Interop protocol не стає спільною семантикою мов або універсальним result type.

---

### 3. Посилання на native-result — ADAPT

**Зовнішній прецедент.** OpenCog AtomSpace розрізняє стабільну/незмінну
ідентичність Atom і приєднані Values для мінливих metadata/observations.

Джерела:
- https://github.com/opencog/atomspace/blob/master/opencog/README.md
- https://wiki.opencog.org/w/AtomSpace

**Поточні докази my-lisp.**
- `crates/wsm-native-result-types/src/lib.rs`
- `experiments/atomspace-pattern-audit-791.lisp`

**Правило.** Stable observation/native-result reference може адресувати
producer-owned результат без копіювання або нормалізації payload. Lifecycle,
timestamps, costs і capability metadata зберігаються окремо.

**Відхилено.** Не приймати центральну AtomSpace-подібну knowledge ontology
або universal truth/attention attachment.

---

### 4. Явний bridge admission — BORROW

**Зовнішній прецедент.** KIF задуманий як interchange language між
гетерогенними knowledge systems, а не як обов'язкове internal representation
для кожного учасника.

Джерело:
- https://logic.stanford.edu/people/genesereth/papers.html
  (Michael Genesereth, *Knowledge Interchange Format*, 1991)

**Поточні докази my-lisp.**
- `contracts/island-compat-contract.lisp`
- `contracts/life-1-contract.lisp`
- `docs/architecture/ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.md`

**Правило.** Bridge — явне, часткове й інспектоване перетворення. Відсутній
bridge є легальним станом. Native source-result не зникає після projection.

**Відхилено.** Interchange form не стає internal representation Common Lisp,
Prolog, Datalog або CLIPS.

---

### 5. Provenance trace — ADAPT

**Зовнішній прецедент.** Розділення stable identity і attached Values в
AtomSpace корисне для provenance; KIF показує, що interchange records можуть
бути явними даними, а не прихованою runtime-equivalence.

**Поточні докази my-lisp.**
- `contracts/life-1-contract.lisp`
- `crates/wsm-native-result-types/src/lib.rs` (`ObservationRef`, `ProvenanceEdge`)

**Правило.** Ланцюг `producer → observation → explicit bridge → target
observation` записується як ordinary provenance data. Bridge reference
лишається opaque для механізму зберігання.

**Відхилено.** Provenance не є truth value і не може заднім числом оголосити
semantic equivalence.

---

### 6. Scheduling та activation — ADAPT

**Зовнішній прецедент.** Blackboard/Hearsay-II відділяє knowledge sources,
blackboard data structure та control; Hearsay-II застосовував opportunistic
scheduling на основі змін blackboard.

Джерела:
- https://www.cs.cmu.edu/afs/cs/project/tinker-arch/www/html/1998/questions/20.Blackboard.html
- https://www.cs.cmu.edu/~raj-symposium/lesser.html

**Поточні докази my-lisp.**
- `experiments/atomspace-pattern-audit-791.lisp`
- `contracts/life-1-contract.lisp`
- механізми queue/scheduling у `crates/wsm-kernel-host/`

**Правило.** Scheduler може використовувати явні availability, cost, freshness
або queue metadata для вибору *коли/де* виконувати.

**Відхилено.** Shared blackboard не стає semantic truth authority, а scheduler
priority не змінює значення SID.

---

### 7. Ізоляція відмов — BORROW

**Зовнішній прецедент.** MetaCall loader/plugin boundaries мають окремі
initialization/loading/clear/error boundaries для runtime.

**Поточні докази my-lisp.**
- `experiments/metacall-pattern-audit-789.lisp`
- per-kernel tests у `crates/wsm-*-kernel/tests/`
- `contracts/island-compat-contract.lisp`

**Правило.** Kernel startup/transport/native failures лишаються named failures
на механічній межі. Відмова одного острова не переписує результат іншого або
Lisp semantic registry.

**Відхилено.** Не перетворювати execution failure на Lisp falsehood, Canon
`()` або вигадану semantic answer.

---

### 8. Поведінка при відсутньому kernel — BORROW MECHANISM, REJECT FALLBACK SEMANTICS

**Зовнішній прецедент.** Poplog має явні language subsystems та loaded-state
queries; MetaCall має явні runtime loaders. Обидва корисні як precedent для
спостережуваної runtime availability.

Поточні research records:
- `experiments/poplog-pattern-audit-787.lisp`
- `experiments/metacall-pattern-audit-789.lisp`

**Поточний authority/evidence my-lisp.**
- `contracts/island-compat-contract.lisp`: missing kernel — легальна execution availability.
- `contracts/life-1-contract.lisp`: missing source kernel не змінює SID meaning.
- Common Lisp kernel tests відрізняють missing runtime від semantic result.

**Правило.** `missing-kernel` — це execution unavailability, і нічого більше.

**Відхилено.** Заборонено fallback через зміну semantic identity, renumbering
registry, повернення Canon 0 або вдавання, що unavailable producer повернув
zero results.

## Інваріанти між патернами

1. **SID — identity; execution mechanisms — evidence/projections.**
2. **Producer-native result domains переживають observation.**
3. **Bridge admission завжди explicit і partial.**
4. **Missing capability не дорівнює semantic absence.**
5. **Scheduling metadata не є meaning.**
6. **Substrate можна замінити без зміни language semantics.**
7. **Жоден precedent не приймається лише через історичний успіх: borrowed
   mechanism мусить зберігати двоосьову архітектуру.**

## Використання в реалізації

Майбутні LIFE-1/LIFE-2 задачі мають посилатися на відповідний патерн перед
додаванням нового loader, bridge, scheduler rule, result reference або failure
policy. Якщо механізм не вкладається в цей каталог, спочатку слід записати нові
докази й додати bounded catalog entry, а не мовчки розширювати архітектуру.
