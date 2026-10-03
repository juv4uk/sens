# Garbage collector: цілісна карта теми

> **POLICY OVERLAY — 2026-10-03 / #2544 (docs follow-up #2547)**
>
> This remains a technical survey, not semantic authority. SENS fixes GC as an
> unobservable reachability mechanism. Weak refs/finalizers/resurrection are excluded
> from the language contract. Collector choice is owned by #2544 and its actual
> substrate lanes (`wsm-os-lisp#60`, `fpga-lisp#49`), not preselected here.
> See `gc-reachability-contract.md`.



**Статус:** технічний довідник для проєктування мовного runtime
**Джерело:** Manus AI, через власника · **Дата:** 2026-08-23
**Оформлення:** Сакші (ox-alpha) · **Доповнює:** [[gc-m0-design]] (M0-дизайн)
**Межа:** це не одна «найкраща» реалізація. Garbage collection — сімейство
компромісів між безпекою, памʼяттю, latency, throughput, складністю runtime
та конкретним workload.

---

## 1. Найкоротше визначення

**Garbage collector (GC)** — це частина runtime, яка автоматично повертає
памʼять, зайняту обʼєктами, що програма більше не може досягти. У tracing
GC «живим» вважається обʼєкт, до якого є шлях від коренів виконання:
globals, stack frames, registers, current result, closures, compiler state
та інших explicit roots [2] [5].

```
roots → reachable object graph → live objects
everything else in managed heap → reclaimable garbage
```

GC не знає, чи обʼєкт «важливий людині», чи він був «створений давно», чи
він входить у semantic World. Він вирішує вузьке фізичне питання:

> **Чи може виконувана програма ще прочитати цей object через дозволені
> references?**

Це відрізняє GC від persistence, database cleanup, knowledge pruning,
cache eviction, журналу подій і semantic retraction. Вони можуть виглядати
схоже, але мають інші критерії істини.

## 2. Чому Lisp майже природно приводить до GC

У класичному Lisp базова структура — S-expression, утворений атомами й
ordered pairs; lists є chains of pairs [1]. Обчислення постійно створює
temporary lists, evaluated arguments, closures, syntax trees та derived
values. Частина з них стає недосяжною одразу після завершення `let`,
function call або rewrite.

```lisp
(let ((x (cons 1 (cons 2 (cons 3 '())))))
  (car x))
```

Після повернення `1` весь list може стати недосяжним. Якщо runtime ніколи
не повертає цю памʼять, довга сесія поступово закінчиться `OutOfMemory`,
хоча user-visible result давно зник.

Перший Lisp Маккарті створювався для маніпуляції symbolic expressions у
звʼязку з Advice Taker, а не як «мова з функціями для програмістів» [1].
Тому memory management тут не другорядна оптимізація: воно дає symbolic
computation право породжувати тимчасові структури без ручного `free` в
кожному rule або proof step.

## 3. Базові поняття

| Термін | Значення |
| --- | --- |
| **Object** | Dynamically allocated block або logical heap record. |
| **Heap** | Простір обʼєктів із dynamic lifetime. |
| **Mutator** | Звичайне виконання програми; назва протиставляється collector-у. |
| **Root** | Reference, доступна runtime без проходження через інший GC object. |
| **Reachable / live** | Object, до якого є шлях від root. |
| **Garbage** | Heap object, до якого такого шляху немає. |
| **Trace / mark** | Обійти graph від roots і позначити live objects. |
| **Sweep** | Повернути unmarked objects у free storage. |
| **Moving collector** | Копіює/переміщує live objects та коригує references. |
| **Non-moving collector** | Reclaim in place, адреси не змінює. |
| **Safe point** | Момент, де runtime точно знає roots. |
| **Write barrier** | Малий код на pointer write (generational/concurrent GC). |

Корені та reachable graph — це **контракт безпеки**, не detail
implementation. Пропущений live root → use-after-free на рівні runtime.
Помилково збережений garbage → втрата памʼяті, але не semantic correctness.
Тому в GC safety важливіша за completeness.

## 4. Звідки беруться roots

| Клас root-ів | Приклади |
| --- | --- |
| Global/session state | REPL environment, global bindings, modules, intern tables. |
| Active evaluation | Current expression, arguments, temporaries, exception payload. |
| Call state | Stack frames, executing closures, open upvalues, lexical environments. |
| Compiler/reader state | AST under construction, constant pool, macroexpansion. |
| Host/FFI state | Handles passed to native code, pinned objects, callbacks. |
| Runtime metadata | Caches/object tables зі strong references. |

> **Правило:** якщо GC може запуститися під час allocation, кожен live
> value, який code ще тримає поза managed heap, уже має бути root-ом.

«Collector algorithm» простіший за «rooting protocol»: у VM tutorial Lox
roots include stack, globals, call-frame closures, open upvalues і
compiler-held objects [4]. Rust GC designs показують, що rooting, а не
власне sweep, є найважчим safety question [7].

## 5. Три підходи до lifetime

### 5.1 Manual deallocation
Швидко і передбачувано, але ownership leaks into every API. Для symbolic
graph зі shared lists і closures — непридатно.

### 5.2 Reference counting
Count inbound strong references; нуль → reclaim (можливо cascade).

| Плюси | Мінуси |
| --- | --- |
| Simple; prompt reclamation. | Не збирає cycles без cycle collector. |
| Без global pause. | Bookkeeping на кожен pointer update. |
| Добре для acyclic immutable trees. | Cascade latency spikes; atomic RC costs. |

Rust `Rc`/`Arc` — reference counting, не tracing GC. `Rc` cycles leak —
це наслідок моделі, не bug [7].

### 5.3 Tracing GC
Heap як graph: старт від roots, reachable objects live, решта garbage.
Naturally handles cycles [2]. Основна тема документа.

## 6. Mark-and-sweep: найменший справжній tracing collector

```
MARK:
  put all roots in worklist
  while worklist not empty:
    object = pop worklist
    if object not marked:
      mark object
      add every child reference to worklist

SWEEP:
  for every slot in heap:
    if marked: clear mark for next cycle
    else: reclaim slot
```

Object header мінімально: `type tag | mark bit | size/layout | payload`.
Tricolor abstraction:

| Колір | Сенс |
| --- | --- |
| White | Ще невідомо, чи reachable. |
| Gray | Discovered live, children not scanned. |
| Black | Object + outgoing references scanned. |

Explicit gray worklist кращий за рекурсію host stack: Lisp створює дуже
deep lists, collector не має падати від stack overflow [4].

Precise, handles cycles, does not move objects — ideal first own collector.
Недоліки: stop-the-world, full-heap sweep, fragmentation.

## 7. Allocation і fragmentation

| Підхід | Ідея |
| --- | --- |
| Bump allocation | `cursor += size`; fast; для nursery/semispace. |
| Free list | Natural companion for mark-sweep. |
| Size classes | Free lists per size. |
| Arena/region | Allocate/free by phase. |
| Object table/handles | Stable handle → address; moving objects, FFI. |

Fragmentation: total free bytes достатньо, але розбиті на small holes.
Non-moving mark-sweep suffers external fragmentation; compaction/copying
trade pointer complexity for denser memory [3].

## 8. Mark-compact
Trace, then pack live objects together, update every pointer.
Плюс: compact heap, no long-term fragmentation. Ціна: precise pointer
information required; raw pointers dangerous; більше фаз і metadata.

## 9. Copying / semispace
Two spaces; allocate linearly in from-space; copy live graph to to-space;
forwarding addresses; swap.

| Перевага | Недолік |
| --- | --- |
| Allocation = pointer increment. | Резерв spare space. |
| Work ∝ live data, not dead heap. | Moving; references correctable. |
| Compacts automatically. | Large/pinned objects complicate design. |

Cheney breadth-first copying використовує newly copied region як work
queue — elegant, але moving semantics робить його second/third collector
для young runtime [3].

## 10. Generational GC: гіпотеза, а не аксіома
Багато objects die young → nursery + frequent cheap minor collections +
promotion. Потрібні remembered set / card table + write barrier для
old→young references.

| Коли сильні | Коли не поспішати |
| --- | --- |
| High allocation rate, temporaries die young. | Small runtime без measured pressure. |
| Budget for barriers/tests. | Mutable object model не стабільний. |
| Shorter typical pauses. | Root/layout contract еволюціонує. |

G1 — generational + incremental + parallel + mostly concurrent + STW +
evacuating + regions + pause prediction [6]. Це lesson in scale, не starter
template.

## 11. Incremental, concurrent, real-time
STW — simplest/safest first form. Incremental — bounded work between
mutator steps. Concurrent — collector+mutator разом: barriers,
synchronization, race reasoning. Real-time — bounded worst-case [3].

Central concurrent problem: black object → white reference inserted без
barrier → collector пропускає white object. Barriers: incremental-update /
SATB / read barriers [5].

## 12. Exact vs conservative
Exact: runtime знає всі references → can move, collects all garbage.
Conservative: any bit pattern that might be a pointer = pointer; retains
garbage accidentally; cannot move [2]. Для власної мови — **exact tracing**;
conservative — pragmatic bridge для unmanaged host code.

## 13. Identity, handles, pinning, ABA

| Technique | Idea | Cost |
| --- | --- | --- |
| Rooted handle | Handle замість naked pointer. | Indirection/discipline. |
| Pinning | Object cannot move temporarily. | Fragmentation. |
| Stable ObjId | Value stores ID; heap maps ID→location. | Lookup/table. |
| Generational index | `(slot, generation)` rejects stale handles. | Counter metadata. |

Generational arenas: після removal той самий index може бути reused —
generation prevents stale reference silently naming the replacement [9].

## 14. Weak refs, ephemerons, finalization

Weak ref не тримає object alive; nondeterministic vanishing. Ephemeron:
value alive only if key independently alive (plain weak pairs insufficient).
Finalizer небезпечний як primary resource management: timing
недетермінований, порядок не гарантований, resurrection races [3].

> **Використовуй explicit `close`/capability lifecycle для sockets, files,
> processes, transactions. Finalization — тільки backup diagnostics.**

## 15. FFI — де GC найнебезпечніший

| FFI case | Safe pattern |
| --- | --- |
| Short-lived data into native call | No-GC region / borrow for call duration. |
| Native retains language object | Rooted handle; release explicitly. |
| Native points into managed heap | Trace hook / opaque handle. |
| Pinned buffer to C API | Pin bounded duration; copy if long-lived. |
| Callback C→language | Re-enter through safe point/rooting API. |

JNI strategy: root objects crossing into unmanaged side [7].

## 16. Persistence is not GC

GC = in-memory reachability now. Persistence = durability, schema,
ownership, retention policy.

| Question | GC | Persistence/Worlds/journal |
| --- | --- | --- |
| Reachable by running program? | Core question. | Maybe irrelevant. |
| Survive restart? | No. | By storage contract. |
| Deletion = semantic retraction? | No, storage reclamation. | Needs provenance/policy. |

Для my-lisp: World може бути semantically retained у journal/history,
тоді як in-memory граф reclaimed і reload later. **Ніколи не прирівнювати
`World unreachable in heap` до `World no longer valid knowledge`.**

## 17. Lisp-specific subtleties

- **Pairs/lists**: trace car+cdr; arbitrarily deep → iterative worklist.
- **Closures**: live closure → body + captured lexical environment live.
  Classic root bug: returned closure retains a large graph.
- **Symbols/interning**: strong intern table = symbols live forever (може
  бути ок для language symbols); dynamic user symbols → unbounded. Weak
  interning — не first GC feature.
- **Immutable/persistent structures**: sharing — сила; tracing reclaim
  shared node only after all paths disappear.
- **Cycles**: closures/environments/mutable cells/host handles create
  cycles; RC alone cannot reclaim them; tracing can.

## 18. Rust-specific subtleties

Hard problem: values held in Rust locals rooted whenever collection may
occur [7].

| Rust mechanism | Relation to GC |
| --- | --- |
| `Box<T>` | Unique ownership; no tracing if tree ownership fits. |
| `Rc<T>`/`Arc<T>` | RC; cycles leak without `Weak`. |
| `RefCell<T>` | Interior mutability ≠ reachability. |
| Arena + ObjId | Stable handles, simple boundary. |
| Generational arena | Rejects stale reused IDs [9]. |
| `gc-arena` | Exact tracing + **mutation xor collection** boundary [8]. |

`gc-arena`: mutation runs OR collection runs, never both — makes roots and
stack safety tractable in safe Rust. Excellent mental model для першого
my-lisp collector: collect only at controlled allocation/safe points.

## 19. FPGA and constrained machines

| Constraint | Consequence |
| --- | --- |
| Fixed cons heap | `OutOfMemory` — named result, not exceptional crash. |
| Limited BRAM bandwidth | Mark/sweep FSM cycles; measurable pause. |
| 32-bit tagged words | Exact pointer recognition easier. |
| No large semispace | Copying collector unattractive. |
| Single-thread evaluator | STW mark-sweep remarkably natural. |

Cross-target contract: **same language-level object tags, child-layout
rules, root categories, named resource outcome** — не «same Rust collector».

## 20. Performance vocabulary

Allocation rate · Live heap · Heap residency · GC throughput cost · Pause
time · Latency · Fragmentation · Promotion rate · Root size · Pointer
density. Higher collection frequency → lower peak memory, more CPU; lower —
навпаки. Scanning live heap + references drives tracing cost [5].

## 21. Correctness, safety, testing

Core laws: Safety · Graph closure · Root completeness · Representation
correctness · Observational invisibility.

| Test | Ловить |
| --- | --- |
| GC after every allocation | Missing temporary/root. |
| Returned closure retains binding | Missing closure→env edge. |
| Deep list/tree | Recursive marker stack overflow. |
| Cyclic graph | Duplicate marking / RC limitation. |
| Reused slot, stale handle | ABA bug. |
| FFI rooted vs unrooted | Invalid external pointer lifecycle. |
| Differential: GC off vs stress | Collector changes semantics. |
| Heap limit after collect | Named OutOfMemory, not false success. |

Не починати performance tuning до чистого stress mode [4].

## 22. Decision framework

| Ситуація | Перша відповідь |
| --- | --- |
| Short-lived CLI, no cycles | Keep Rc/Rust ownership; maybe no custom GC. |
| Phase-bounded compiler pass | Arena/region. |
| Small single-thread Lisp VM, cycles, stable addresses | **Precise STW non-moving mark-sweep.** |
| High temp allocation, mature exact roots | Copying nursery, потім generational. |
| Large long-running service, pause target | Mature concurrent runtime, не first custom. |
| Hard real-time | Specialized RT GC / avoid heap allocation in deadline path. |
| Need C FFI/raw addresses | Non-moving heap, handles, scoped pinning. |
| Persistent semantic history | Separate persistent store/journal від heap GC. |
| Small FPGA heap | Fixed-capacity tagged heap + named OOM. |

## 23. Що радиться саме my-lisp

1. **Зараз:** не replace `Rc`. Міряти workload; `cons_limit` = resource test seam.
2. **Перший real step:** private `ManagedHeap` зі stable `ObjId` slots для
   `Pair` only; no language-visible API change.
3. **Before mark:** implement `visit_roots()` + child-trace protocol; stress tests спершу.
4. **First collector:** precise, STW, non-moving mark-and-sweep, iterative worklist.
5. **Then:** closures/environments після того як pair graph переживе stress GC.
6. **Later:** align ObjId/tag ABI з CML і FPGA; NaN-box representation ≠ ownership model.
7. **Much later:** generational/copying лише після profiling.

> Build the next organ only when the current organism has a concrete reason
> to need it.

## 24. Міні-глосарій

Allocation · Collector · Compaction · Evacuation · Forwarding pointer ·
Handle · Liveness · Mark bit · Nursery · Pin · Remembered set · Rooting ·
Safe point · Sweep · Tracing · Write barrier.

## 25. Головна думка

GC — не «машина, яка чистить непотрібне». Це **формальна угода між object
layout, allocator-ом, evaluator-ом, compiler-ом, FFI і root protocol-ом про
те, що означає “ще доступне програмі”**.

У хорошому Lisp GC не втручається в думку мови. Він тихо дозволяє цій думці
породжувати багато тимчасових символічних форм, не перетворюючи memory
bookkeeping на обовʼязок кожного правила та кожної функції.

## References

[1] McCarthy 1960: https://dl.acm.org/doi/pdf/10.1145/367177.367199
[2] Cornell GC lecture: https://www.cs.cornell.edu/courses/cs312/2007sp/lectures/lec20.html
[3] The Garbage Collection Handbook: https://gchandbook.org/contents.html
[4] Crafting Interpreters: https://craftinginterpreters.com/garbage-collection.html
[5] Go GC guide: https://go.dev/doc/gc-guide
[6] G1 tuning: https://docs.oracle.com/en/java/javase/17/gctuning/garbage-first-g1-garbage-collector1.html
[7] Safe tracing GC in Rust: https://manishearth.github.io/blog/2021/04/05/a-tour-of-safe-tracing-gc-designs-in-rust/
[8] gc-arena: https://github.com/kyren/gc-arena
[9] generational-arena: https://docs.rs/generational_arena/latest/generational_arena/
[10] my-lisp value.rs: https://github.com/juv4uk/my-lisp/blob/main/crates/my-lisp/src/value.rs
[11] my-lisp environment.rs: https://github.com/juv4uk/my-lisp/blob/main/crates/my-lisp/src/environment.rs
[12] memory-layout-contract.lisp: https://github.com/juv4uk/my-lisp/blob/main/memory-layout-contract.lisp
