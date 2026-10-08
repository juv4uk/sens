# D10: повернення пропущених Interlisp та PSL-значень

**Статус:** дослідницький добір, не ратифікація і не кодова реалізація.

## Джерела

- [Portable Standard Lisp 3.2 User Manual (1984)](https://manuals.plus/m/000ffa02fa9f17a7abece89bb6a08bd2e3330bef1b4947c7bfdb2bee1670c42b): 8.2.1, 8.2.2, 8.2.6, 8.3.1, 8.3.2. Опис семантики функціональних комірок, операцій із визначеннями та оголошень змінних.
- [Medley Interlisp історична хроніка](https://interlisp.org/history/timeline/): розділ 1970 — History, UNDO, повторне виконання із підстановками.

## Облік

```text
Було             589/1024
Історичних        13
Стало            602/1024
Залишилося       422
Доведені коди     256 (селектори, незмінно)
Без кодів         346
Ратифікація         0
```

## Кандидати

- **PUTD** — Install a typed function body under a named function identity, with language-level redefinition semantics (PSL 8.2.2 pp.8.3-8.4; web L3210-3224)
- **GETD** — Return the stored function type and definition body or absence when undefined (PSL 8.2.2 p.8.4; web L3256-3257)
- **COPYD** — Copy the definition type and body from a defined function to another name; fail if missing (PSL 8.2.2 pp.8.4-8.5; web L3258-3266)
- **REMD** — Remove a named function definition and return its previous type-and-body pair or empty when absent (PSL 8.2.2 p.8.5; web L3274-3277)
- **FLUIDP** — Test explicit fluid declaration independently from ordinary variable boundness (PSL 8.3.2 p.8.12; web L3518-3520)
- **GLOBALP** — Test whether an identifier is globally declared or names a defined function in PSL (PSL 8.3.2 p.8.12; web L3521-3523)
- **UNFLUID** — Remove FLUID declarations for listed identifiers while preserving other declarations (PSL 8.3.1 p.8.12; web L3515-3516)
- **EXPRP** — Test PSL expr-function kind of a code pointer, lambda or named expr function (PSL 8.2.1 p.8.10; web L3477-3480)
- **FEXPRP** — Test the defined fexpr kind, which receives unevaluated argument list (PSL 8.2.1 p.8.10; web L3481-3482)
- **NEXPRP** — Test the defined nexpr kind, which receives evaluated arguments as one list (PSL 8.2.1 p.8.10; web L3483-3484)
- **FUNBOUNDP** — Test absence of a function definition, distinct from variable-value absence (PSL 8.2.6 p.8.9; web L3438-3450)
- **UNDO** — Undo a selected recorded interactive operation without forcibly undoing intervening history events (Interlisp 1970 BBN-LISP History; timeline L93-97)
- **INTERLISP-HISTORY-REPLAY** — Replay an earlier recorded interactive operation with optional substitutions; label is a new semantic proposal, not a historically attested function spelling (Interlisp 1970 BBN-LISP History; timeline L93-94)

## Епістемічна межа

PSL описує окремі *function cells* та *value cells*: `PUTD/GETD` — не механічні синоніми `DEFINE`; `REMD` повертає попереднє визначення. Але SENS **не зобов'язаний** переймати PSL cell layout, spread/nospread ABI або виконання власної мікроінструкції. Це семантичні кандидати для порівняння з нашою моделлю визначень.

В Interlisp задокументовано вибіркове `UNDO` і можливість history replay з підстановками. `INTERLISP-HISTORY-REPLAY` — **наша нова назва кандидата**, не підтверджена точна історична функція. До реалізації в `wsm-os-lisp` необхідний закон конфліктів/залежностей при нелінійному UNDO. Ніякого автоматичного переписування двійкових програм.

`MACROP` вже присутній у D10; `DWIM`, `UNBINDN` і цілий редактор не додано (див. ledger exclusions).

**Прогалини до ратифікації:** поведінкові oracle fixtures, зіставлення із чинним SENS без дублювання, незалежне review функцій, перевірка безпечного undo на незмінному журналі.

Перевірка: `python3 scripts/check-d10-interlisp-psl-history-v1.py`.
