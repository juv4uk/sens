# GC M0 DESIGN — Stop-the-world mark-and-sweep для my-lisp

> **SUPERSEDED BOUNDARY — 2026-10-03 / #2544 (docs follow-up #2547)**
>
> This document remains a historical/proposed mechanism design. Its older wording
> that GC is part of machine semantics is no longer authority. Canonical boundary:
> `docs/gc-reachability-contract.md`: GC is an unobservable reachability mechanism;
> weak references, finalizers and resurrection are not language semantics. The M0
> mark-sweep material remains a mechanism donor and test source.



**Статус:** PROPOSED DESIGN · **Дата:** 2026-08-23
**Джерело:** зовнішній рецензент (ChatGPT), через власника
**Редагування/оформлення:** Сакші (ox-alpha)
**Звʼязок:** memory-layout-contract.lisp · language-core-axioms.md (G-аксіоми)

---

## 0. Головна теза автора

> «GC не "щось, що звільняє памʼять" — це частина семантики машини.
> Перший GC має бути малим, доказовим stop-the-world tracing collector,
> якому можна довіряти. Не найшвидший — перевірюваний.»

## 1. Базова модель: mark-and-sweep

```text
roots → mark reachable → unmarked = unreachable → sweep
```

Чому саме цей алгоритм першим:
- простіший для верифікації інваріантів;
- природно працює з циклами;
- не вимагає reference-counting семантики;
- correctness формулюється чітко:

> GC ніколи не звільняє обʼєкт, досяжний від будь-якого root.

## 2. Структура heap

```rust
Heap { objects: Vec<Slot> }

Slot { mark: bool, value: HeapObject }

Value ::= Nil | Bool | Integer | Rational | Symbol | Ref(ObjectId)

HeapObject ::= Cons(Value, Value)
             | Lambda { params, body, env }
             | Environment { bindings, parent }
             | Vector ...
```

**Стабільні handles замість сирих вказівників:**

```rust
struct ObjectId { slot: u32, generation: u32 }
```

`generation` захищає від ABA: після звільнення і повторного
використання slot старий handle невалідний:

```text
slot 17 generation 4   ← old cons → freed
slot 17 generation 5   ← new lambda; старий (17,4) invalid
```

## 3. Явний root protocol

Root set (приблизно):

```text
Session
 ├─ global environment
 ├─ current lexical environments
 ├─ evaluation stack
 ├─ temporaries під час builtin calls
 ├─ macro-expansion temporaries
 └─ externally-held values / API results
```

**Заборонено магічне сканування Rust stack.** Замість цього:

```rust
heap.with_roots(&roots, |heap| { ... });
// або явні guards:
let x = heap.root(value);
```

Суворе правило дисципліни:

> будь-який heap reference, який повинен пережити allocation,
> мусить бути rooted до наступної allocation point.

Класична помилка, яку це викорінює:

```text
allocate A (тільки в локальній Rust змінній)
allocate B → allocation triggers GC → A не був rooted → A collected ✗
```

## 4. Інваріанти correctness

```text
I1 Reachability safety:
   кожен обʼєкт, досяжний від roots, живе після GC.

I2 Reclamation:
   кожен unreachable object зрештою може бути reclaim'ed.

I3 Graph preservation:
   для кожного reachable object усі його reachable edges після GC
   мають ту саму семантику.
```

Для non-moving mark/sweep I3 простий: handles не треба переписувати.
Саме тому перша версія — **не compacting**.

## 5. Що у heap, що immediates

```text
Rust-owned (поза GC): bool, small int, immutable rational, symbol id
GC heap:              cons cells, closures, environments, mutable aggregates
```

Collector лишається маленьким. Особливий випадок — closures:

```lisp
(def make-adder (lambda (x) (lambda (y) (+ x y))))
```

Граф: closure → environment → binding x; environment має parent.
GC керує **графом семантичних обʼєктів**, а не лише cons cells.

## 6. Тести ДО collector

1. Базове збереження: `(def x (cons 1 2)) (gc) (car x) ;; => 1`
2. Цикл без root → обидва reclaimed; з root на A → обидва живі
3. Closure capture: `(def f ((lambda (x) (lambda () x)) 42)) (gc) (f) ;; => 42`
4. Shadowed env після виходу → collectible
5. **Randomized graph property test**: згенерувати випадковий граф +
   roots; порахувати reachable set незалежним алгоритмом; запустити GC;
   `assert live_after == reachable_before`.

Останній тест — collector перевіряється **іншим простим алгоритмом**,
а не самим собою.

## 7. Stress mode

```bash
MY_LISP_GC_STRESS=1   # GC перед/після майже кожної allocation
```

Missing-root баги ховаються роками; stress-GC знаходить їх за секунди.
Якщо conformance suite зелений у stress-mode — сильний сигнал.

## 8. Metamorphic criterion (головний)

> GC не змінює observable Lisp semantics, окрім звільнення недоступної
> памʼяті та diagnostic statistics.

```text
run normal        → value/output/errors
run GC-stress     → value/output/errors
assert identical
```

## 9. Debug API (видима модель машини)

```lisp
(gc-stats)
;; ((allocated 18271) (live 913) (collections 24) (reclaimed 17358))
(gc)   ;; diagnostic primitive — можливо не назавжди, але корисно зараз
```

## 10. Еволюція (порядок важливий)

| Фаза | Вміст |
|---|---|
| **M0** | explicit heap, ObjectId+generation, non-moving mark/sweep, explicit roots, stress mode |
| M1 | property tests, heap verifier, statistics, threshold collection |
| M2 | weak refs / finalization — лише якщо реально потрібні |
| M3 | generational / copying / compacting — лише якщо measurements покажуть потребу |

Не навпаки.

## 11. Постановка задачі агенту (формулювання власника через рецензента)

> GC M0: спочатку опиши heap graph, root set і invariants. Потім напиши
> незалежний reachability oracle та failing tests. Лише після цього
> реалізуй non-moving mark-and-sweep. Жодної оптимізації, generational GC
> або compaction, доки stress-GC + conformance + randomized graph tests
> не зелені.
