# D10 — уніфікація термів і лексична область видимості

**Стан:** research/unratified. Контракт 11.8 D1–D9 не змінюється; нові координати відсутні.

## Для чого це Lisp-машині

У lib/unify.lisp уже є спільний алгоритм розгалуженого проходження кон'юнкцій для прямого та зворотного логічного висновування. У lib/linter.lisp є два різні правила вільних змінних для послідовного let* і рекурсивного letrec. Це реальні джерела семантики, а не функції, вигадані заради заповнення таблиці.

Результат: додано 9; було 625, стало 634/1024, ще 390; 256 законних координат селекторів незмінні, 378 кандидатів не розміщено; ратифікацій 0.

## Нові значення

- **LOOKUP-SUBST** (lib/unify.lisp:93) — Return a bound logic variable value from a substitution alist keyed by possibly structured variable name, or the original variable if unbound
- **WALK-RESOLVED** (lib/unify.lisp:115) — Follow transitive bound-variable references until a nonvariable or an unbound variable is reached, preserving the original unbound variable
- **FAILED-SUBST?** (lib/unify.lisp:140) — Recognize explicit unification failure only for the designated failure atom, not for a nonempty substitution alist
- **UNIFY-WALKED** (lib/unify.lisp:147) — Unify two dereferenced logic terms recursively, propagating substitutions or explicit failure across compound pairs
- **UNIFY-VAR** (lib/unify.lisp:173) — Bind a logic variable to a term when identities differ and occurs-check permits it, otherwise preserve substitution or return failure
- **THREAD-CONJUNCTION** (lib/unify.lisp:249) — Evaluate each conjunction condition through an injected goal strategy, branching across every successful intermediate state and collecting final states
- **THREAD-CONJUNCTION-BRANCHES** (lib/unify.lisp:256) — Continue a conjunction against every intermediate state returned by one condition and concatenate resulting final states in order
- **COLLECT-FREE-VARS-LET*** (lib/linter.lisp:93) — Compute free identifiers of sequential let* bindings using each earlier binding only in later initializers and the body
- **COLLECT-FREE-VARS-LETREC** (lib/linter.lisp:119) — Compute free identifiers of mutually recursive letrec definitions with all names in scope for all initializers and body

## Не додаємо

- OCCURS-CHECK: Pure alias of OCCURS-CHECK? already a lower-domain resident
- EXTEND-SUBST: Thin CONS-based binding-cell wrapper, no separate proved universal law
- REASON-INDEX-CANDIDATES: Index optimization is not a language semantic meaning
- LINT-SHORT-HEAD: Legacy/surface spelling conversion for linter, not a new semantic law

## Верифікація

Джерела фіксуємо точними Git blob SHA й рядками визначень. Тест перевіряє інваріанти, але не доводить поведінкової еквівалентності. Перед ратифікацією потрібні runtime/oracle свідки: обмежена й необмежена змінна, occurs-check, гілкування кон'юнкції, let* проти letrec.

Запуск: python3 scripts/check-d10-unify-lexical-harvest-v1.py
