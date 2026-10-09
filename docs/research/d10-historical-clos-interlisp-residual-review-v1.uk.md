# D10 — історичний залишок CLOS / Interlisp / Scheme

Дата: 2026-10-09. **Research only: 625/1024 відібраних, 0 ратифікованих, +0 нових.**

Перевірено проти `knowledge/d1-d9-foundation.json` (blob `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`) і `knowledge/d10-v1-semantic-inventory.json` (blob `73dd518469f972c55411e004b70b054ba8b3ec86`): у 9 ідей немає точного збігу назв з чинними D1–D9/D10. **Точна відсутність імені не означає незалежної семантики.**

Історичний стан: MacLisp-1975-1 та -2, PSL/Interlisp #4795 і gap #4837 вже злиті. Відкриті #4838 R7RS і #4839 R6RS не дублюємо. #4800/#4829 already cover method applicability and standard combination. Не переписувати канонічний 625 ledger через старі незлиті гілки (вони diverged після merge!).

## Пропозиції до перевірки

### CLOS-01: FIND-METHOD
Статус: **REVIEW-SEMANTIC-CANDIDATE**. Поверхні: `знайти-метод` / `одержати-точний-метод`.
- Закон: Pure lookup by exact ordered qualifiers and specializers within one generic function; it does not select all methods applicable to runtime arguments.
- Позитивний свідок: A generic function has :before method specialized on class C and primary method on C: lookup :before yields only :before; with errorp false absent signature yields NIL.
- Спростування: Do not treat APPLICABLE-METHODS result as identical; searching by runtime applicability may return a method with a different qualifier/signature.
- Сусіди/власник: DEFGENERIC, DEFMETHOD and #4800 APPLICABLE-METHODS already exist as different definition/applicability operations.
- Першоджерело: https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/stagenfun_find-method.html

### CLOS-02: REMOVE-METHOD
Статус: **REVIEW-SEMANTIC-CANDIDATE**. Поверхні: `вилучити-метод` / `прибрати-точний-метод`.
- Закон: Remove one particular method object from its generic function without removing the generic function or unrelated methods. Removing a method that is not present must not signal an error.
- Позитивний свідок: Given two methods on one generic function, removing method A leaves B; removing A again does not signal an error.
- Спростування: Deletion of an entire generic function or arbitrary method based on print-name instead of method identity is not equivalent.
- Сусіди/власник: D10 DEFMETHOD; D9 REMD removes named definition, not one method of a generic function.
- Першоджерело: https://www.lispworks.com/documentation/HyperSpec/Body/f_rm_met.htm

### CLOS-03: CHANGE-CLASS
Статус: **REVIEW-SEMANTIC-CANDIDATE**. Поверхні: `змінити-клас-об’єкта` / `перевести-екземпляр-у-клас`.
- Закон: Transform an instance to a new class destructively while retaining the original object's identity, retaining values of same-name slots and leaving previously unbound common slots unbound.
- Позитивний свідок: Instance x has common slot p=7 and class A; change to B that also has p; result is EQ-identical x with p=7 and valid new class.
- Спростування: Returning a fresh instance, losing a common slot, or binding an originally unbound common slot as a side effect violates the law.
- Сусіди/власник: D10 DEFCLASS, MAKE-INSTANCE, SLOT-VALUE; this is not constructor equivalence.
- Першоджерело: https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_change-class.html

### CLOS-04: ADD-METHOD
Статус: **HOLD-DERIVABILITY**. Поверхні: `додати-метод` / `приєднати-метод-до-узагальненої-функції`.
- Закон: Attach an existing method object to a generic function, updating dispatch membership under agreement rules; assess whether action is derivable from already selected DEFMETHOD or a new effect law.
- Позитивний свідок: After adding a :before method its descriptor can be found; unaffected primary methods still exist.
- Спростування: Registering a method under a different generic function or duplicating agreeing signatures without replacement policy is invalid.
- Сусіди/власник: D10 DEFMETHOD, DEFGENERIC and pending FIND-METHOD; mutable generic function identity requires owner review.
- Першоджерело: https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/stagenfun_add-method.html

### CLOS-05: UPDATE-INSTANCE-FOR-DIFFERENT-CLASS
Статус: **HOLD-LIFECYCLE-HOOK**. Поверхні: `оновити-стан-після-зміни-класу` / `узгодити-поля-оновленого-екземпляра`.
- Закон: Customization hook triggered during CHANGE-CLASS, receiving an ephemeral copy of the prior instance and the altered current instance; not a standalone call for user code.
- Позитивний свідок: Transition A->B invokes hook after preserving shared slots; hook can read old-only slot from ephemeral previous object.
- Спростування: Calling hook as an independent public operation, treating previous as persistent, or assuming its return value is a general semantic result is not allowed.
- Сусіди/власник: Possibly subsumed by CHANGE-CLASS lifecycle; scope and effect ownership must be determined.
- Першоджерело: https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_upd_ferent-class.html

### CLOS-06: ALLOCATE-INSTANCE
Статус: **HOLD-CONSTRUCTOR-DERIVED**. Поверхні: `виділити-екземпляр` / `створити-екземпляр-без-ініціалізації`.
- Закон: Create a fresh instance of a class without standard MAKE-INSTANCE initialization; standard-class slots are initially unbound.
- Позитивний свідок: Allocate then inspect slot-boundness: slots are unbound, whereas make-instance may apply initform/initargs.
- Спростування: Confusing allocated instance with fully initialized MAKE-INSTANCE result is a semantic failure.
- Сусіди/власник: D10 MAKE-INSTANCE, D8 MAKE-CLOSURE and existing type laws; independent constructor slot requires distinctness proof.
- Першоджерело: https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_all_ate-instance.html

### INTERLISP-01: INTERLISP-RECORD-FIELD-RESOLVE
Статус: **HOLD-D2-REWRITE-AND-DEDUP**. Поверхні: `визначити-поле-запису` / `розв’язати-позицію-поля`.
- Закон: Resolve a symbolic record field label to a location in the current declared record layout; after layout redefinition the same field name resolves to the new offset.
- Позитивний свідок: Fields of PERSON change from FIRSTNAME LASTNAME TITLE to FIRSTNAME INITIAL LASTNAME TITLE: TITLE changes from third to fourth field without modifying field-name references.
- Спростування: Keeping a stale fixed CADDR reference after schema redefinition violates source-level record meaning.
- Сусіди/власник: Compare D10 SLOT-VALUE, D8 DEFSTRUCT and D2-controlled compilation; likely derivable from schema and lookup, not new language control.
- Першоджерело: https://interlisp.org/history/timeline/

### INTERLISP-02: MASTERSCOPE-CALL-RELATION
Статус: **HOLD-TOOLING-NOT-CORE**. Поверхні: `зв’язок-викликів-програми` / `хто-викликає-функцію`.
- Закон: A static program relation query over indexed sources (e.g., who calls a given function and uses a bound/free variable); treat as analysis tooling unless independent universal law is demonstrated.
- Позитивний свідок: Same source graph yields stable caller set regardless of traversal/reindexing; free-variable query distinguishes bound from free occurrences.
- Спростування: Text-only name occurrence or a tooling UI query with no binding analysis is not equivalent to a source semantic relation.
- Сусіди/власник: D10 MY-BUILD-DEPENDENCY-GRAPH, COLLECT-FREE-VARS already selected; likely composition/tool feature.
- Першоджерело: https://interlisp.org/history/timeline/

### SCHEME-01: DYNAMIC-WIND
Статус: **HOLD-D2-CONTROL**. Поверхні: `охоронити-динамічну-область` / `виконати-вхід-і-вихід-області`.
- Закон: Run before/after hooks whenever a captured continuation reenters/exits dynamic extent, not only at normal function call/return.
- Позитивний свідок: Captured continuation reentered after nonlocal exit repeats before and then after; ordered event trace must match Scheme specification.
- Спростування: Running before/after only once despite continuation reentry violates the required trace.
- Сусіди/власник: D10 CALL/CC already selected but user mandates D2 as only structural/control authority. Research #4837 covers this, do not mint D10 control.
- Першоджерело: https://standards.scheme.org/r7rs-html5/index.html

## Рамка приймання
1. Behavioral-vs-D1–D9 **і** selected-D10 dedup, а не лише порівняння імен.
2. Мати мінімальний виконуваний свідок в оракулі для source/modern parity, з фальсифікатором.
3. D2 залишається єдиним структурним/керувальним доменом. У CLOS data/effect semantics не перетворювати зручність на нову структуру мови.
4. `coordinate=null`, `ratified=false`, `physical_t5_authorized=false`, не змінювати `knowledge/d10-v1-semantic-inventory.json` без review власника.
5. Історичний MacLisp: повний функціональний індекс Moonual не аудитований; дослідження — не сертифікат повного покриття.
