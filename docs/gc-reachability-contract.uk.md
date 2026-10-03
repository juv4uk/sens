# Контракт досяжності GC

**Статус:** ПРОЄКЦІЯ КОНТРАКТУ · **Authority:** #2544 · **Docs follow-up:** #2547
**Обсяг:** лише межа мова/runtime. Реалізація collector лишається приватною для субстрату.

## 1. Канонічний закон

```text
досяжне від оголошених roots -> переживає collection
недосяжний managed object    -> може стати повторно використовуваним storage
вибір collector              -> не може змінювати semantic result
```

Garbage collection — **механізм**, а не семантика SENS.

Семантична операція не повинна відрізняти:

- чи відбулось збирання;
- коли воно відбулось;
- скільки разів воно відбулось;
- чи storage повернув mark-sweep, copying collector, arena, host ownership
  або інший допущений механізм.

Engineering telemetry може існувати лише поза semantic observation і
conformance.

## 2. Жорсткі заборони

Мовний контракт не допускає:

- weak references;
- finalizers;
- resurrection недосяжних значень;
- семантичні `gc-journal`, `gc-stats`, `gc-promote`, collection counter,
  pause clock, mark bit, heap slot, address, generation, forwarding address чи
  free-list link;
- semantic identity, виведену з collector/storage metadata.

Життєвий цикл ресурсів має бути явним через capabilities/lifecycle API, а не
через finalization.

## 3. Закон roots

Collector може reclaim managed object лише після точного root traversal, який
доводить його недосяжність.

Кожен runtime/substrate механічно визначає власні root categories. Це можуть
бути active environments, evaluation temporaries, explicit handles, globals,
stacks, registers або static runtime tables, але жодна категорія не
ратифікується лише за аналогією з історичною реалізацією.

Якщо substrate оголошує immortal/static basis, він лежить поза reclamation
цього collector. Immortality — representation contract, а не semantic property
самої binary identity.

## 4. Закон child trace

Кожне **реально приземлене managed object representation** мусить мати точний
visitor для child edges. #2548 володіє representation census.

Поточні design-candidates, уже описані в репозиторії: Pair, Closure/Lambda,
Environment і Vector.

Не можна наперед ратифіковувати edges для representation, яких ще немає:

- managed Rational/exact-Q і будь-який bignum/limb chain;
- Text7/string backing;
- Map та інші aggregates.

Коли таке representation з'явиться, його повний edge law має отримати
executable falsifier до того, як collector матиме право reclaim його.

## 5. Safe points

Collection дозволений лише там, де implementation може довести повноту root set.

Allocation failure/threshold — допустимий перший кандидат: LISP 1.5 запускав
collection при вичерпанні free storage. Але сучасні safe points SENS треба
довести з поточного evaluator/compiler/runtime, а не успадкувати з історії.

## 6. Історичні донори

### LISP 1.5 / лінія Маккарті

LISP 1.5 Programmer's Manual описує:

1. active list structure, досяжну від fixed base registers;
2. marking досяжних car/cdr chains;
3. linear sweep free storage;
4. відновлення free-storage list з unmarked cells.

Primary manual:
https://www.softwarepreservation.org/projects/LISP/book/LISP%201.5%20Programmers%20Manual-1961.07.14.pdf

SENS бере **reachability/reclamation law**, але не sign-bit marking, machine
register layout, word format чи історичний список roots.

### Cheney 1970

C. J. Cheney, *A Nonrecursive List Compacting Algorithm*, Communications of the
ACM 13(11), 677–678 (1970), DOI 10.1145/362790.362798.

Це лише donor copying/compacting mechanism. Вибір substrate належить #2544 і
його активним mechanism lanes (`wsm-os-lisp#60`, `fpga-lisp#49`); copying
має перемогти альтернативи виміряними memory/timing evidence.

## 7. Обов'язкові witnesses

#2551 володіє adversarial corpus. Мінімум:

- reachable pair graph переживає collection;
- unreachable graph стає reusable;
- deep graph не переповнює host marker stack;
- tracing collector обробляє cycles;
- closure/environment та aggregate edges переживають collection;
- allocation працює після reclamation;
- stale/malformed handles fail closed;
- normal і stress-GC дають однаковий semantic result;
- заміна collector mechanism не змінює semantics;
- майбутній managed Rational/bignum representation мусить отримати власний
  reachable long-chain witness перед admission.

## 8. Відношення до старих GC-документів

Серпневі GC-документи 2026 року лишаються корисними historical/design evidence,
але такі твердження superseded межею mechanism #2544, задокументованою #2547:

- «GC є частиною machine semantics» як semantic authority;
- `(gc-journal)` як language semantics;
- `(gc-promote ...)` resurrection;
- weak references/finalizers як майбутня мовна feature.

Telemetry, quarantine experiments чи owner-facing trust tooling можуть
існувати як **external engineering instrumentation**, якщо виконувана SENS
програма не може їх спостерігати або branch по них.

## Принцип

**GC зберігає досяжність; він ніколи не визначає значення.**
