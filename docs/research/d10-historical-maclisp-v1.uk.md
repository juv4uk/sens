# D10 historical MacLisp v1 — 21 recovered Core meanings

**Статус:** research / unratified  
**Issue:** #4039  
**Foundation:** #4008 / Contract 11.8 / D1–D9

Primary donor:

MacLisp Reference Manual, 17 December 1975  
https://www.softwarepreservation.org/projects/LISP/MIT/MACLISP_Reference_Manual-Dec_17_1975.pdf

Історичні сторінки й назви використовуються як provenance. Старі адреси, SUBR/FSUBR класи та implementation representation не є D10 identity.

## Результат

```text
D10 before            367
historical SELECT      21
-------------------------
D10 after             388/1024
law-forced placed     256
unplaced selected     132
remaining             636
ratified                0
```

## Відібрані historical semantics

```text
CATCH
FUNCALL
COPYSYMBOL
MAKUNBOUND
MEMQ
DELQ
REMPROP
SETPLIST
INTERN
REMOB
SXHASH
PROGN
SYMEVAL
INDEX
GETL
SASSOC
SASSQ
ARRAYDIMS
FILLARRAY
LISTARRAY
STORE
```

## Чому вони не lower duplicates

- **FUNCALL** приймає окремі arguments; D4 APPLY приймає argument list.
- **CATCH** задає scope/target для вже наявного THROW.
- **MEMQ / DELQ** використовують EQ identity, а MEMBER / DELETE мають іншу comparison law.
- **INTERN / REMOB / COPYSYMBOL** працюють із symbol identity та intern-table state, а не лише з текстовим представленням.
- **SXHASH** — equality-compatible hash S-expression, не SHA-256.
- **PROGN** — явна sequential form composition.
- **SYMEVAL / MAKUNBOUND** — прямі symbol-value operations.
- **INDEX** повертає позицію substring, а не boolean contains.
- **GETL / REMPROP / SETPLIST / SASSOC / SASSQ** доповнюють admitted property/alist families.
- **ARRAYDIMS / FILLARRAY / LISTARRAY / STORE** доповнюють уже admitted ARRAY / AREF / row-major lineage.

## Sens8

Sens8 **не очищено й не демонтовано**.

`knowledge/sens8-current-coverage-v1.json` лишається окремим historical donor/provenance artifact:

```text
legacy cells      256
named rows        182
accounted         182
coverage          100%
```

Цей tranche не використовує жодну Sens8 coordinate як D10 placement.

## Координати

Усі 21 meanings:

```text
coordinate = null
coordinate_basis = UNPLACED
ownership = CORE-OWNED-CANDIDATE
```

Тобто історія дає meanings, але не адреси.
