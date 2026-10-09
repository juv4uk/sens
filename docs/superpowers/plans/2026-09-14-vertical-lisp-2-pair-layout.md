# VERTICAL-LISP-2 — контракт розміщення пари

Статус: активна реалізаційна нотатка для issue #126.

## Мета

До появи lowering для CAR/CDR/CONS подання пари повинно мати одну явну machine-readable authority. Target lowerer не має права локально вигадувати зміщення полів.

## Перший TDD-зріз

1. RED: вимагати, щоб спільний memory layout contract явно задавав storage та offsets пари.
2. GREEN: додати найменший pair-layout record до `memory-layout-contract.lisp`.
3. Лише після цього додавати x86-64 memory addressing і semantic lowering для `car`/`cdr`.
4. Allocation для `cons` лишається окремим mechanism slice, щоб Rust не отримав Lisp-семантику.

## Цільове подання

Пара — це heap cell, на яку вказує 48-бітний payload наявного NaN-box tag `cons`. Комірка містить два послідовні 64-бітні Lisp-значення:

```text
base + 0   car : 64-bit Lisp value
base + 8   cdr : 64-bit Lisp value
cell size  16 bytes
```

Цей документ лише пояснює рішення. Machine-readable authority — `memory-layout-contract.lisp`.

---

## English summary

Before CAR/CDR/CONS lowering exists, the pair representation must have one explicit machine-readable authority. The target lowerer must not invent field offsets locally. The intended cell is two consecutive 64-bit Lisp values at offsets 0 and 8, while `memory-layout-contract.lisp` remains the normative source.
