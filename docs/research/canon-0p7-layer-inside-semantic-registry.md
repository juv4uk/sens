# canon()+7 layer history inside semantic-registry — archaeological note

**Date:** 2026-09-18
**Status:** design note / provenance finding; does not change semantics
**Verified against:** `main` at current pinned wsm-lazarus authority
**Scope:** why the closed McCarthy-7 identities appear inside
`lib/surface/semantic-registry.lisp` and what that does and does not mean.

## Українське резюме

Ця нотатка — археологічна знахідка про походження канону в реєстрі функцій.
Вона підтверджує: канон був визначений раніше як **окрема, замкнена
онтологічна категорія** (ADR-004, сім семантичних тотожностей
`PRIM_QUOTE…PRIM_COND`, без жодної нумерації), а семантичний реєстр
`lib/surface/semantic-registry.lisp` з'явився пізніше (ADR-007) як **таблиця
функцій**. У реєстр канон потрапив не як окрема категорія, а просто як перші
сім записів числової таблиці (0001–0007) — спершу у формі `m0001`…, потім
міграція прибрала `m-`префікс. У самому файлі канон не позначений (слово
`canon` у реєстрі не з'являється жодного разу), тому він виглядає як звичайні
сім функцій таблиці.

Висновок для незалежних субстратів свідків (FPC, C, asm, FPGA): **потрібна
тільки таблиця функцій** — `semantic-registry.lisp` як єдине числове джерело
ідентичностей. Канон не вимагає окремого реєстру: його сімка збігається з
першими сімма ID таблиці функцій, і цей збіг є домовленістю (wsm-lazarus
верифікує його проти ADR-004). Числові ID 01–07 для свідка — вільне
представлення семантичних тотожностей (ADR-004 дозволяє
opcode/integer/enum/resolution-table), вибране так, щоб не плодити третю
нумерацію.

## Timeline / real history (git evidence)

1. **2026-09-06 `c4b2e96d`** — `feat(canon): define executable 0+7 semantic laws
   in my-lisp`. This creates `lib/canon.lisp`. The canon is defined *without*
   any numeric registry: it is a closed set of seven semantic identities named
   only as `PRIM_QUOTE…PRIM_COND` / human spellings.
2. **2026-09-08 `16620d83`** — `feat(surface): seed meaning-first
   language-neutral registry` establishes ADR-007 and the registry file. The
   original registry entries for the canon spellings use the form `m0001`
   (opaque machine identity, `m`-prefix).
3. Later migration (rename of non-canonical files to canonical `.lisp`
   extension, `3fbfefbc`) drops the `m`-prefix: `m0001 → 0001`. From this point
   the same seven canon identities stand in the *function table* as plain
   rows `0001…0007`, next to ordinary functions such as `додати`=0104.

Search evidence:

```text
git log --oneline --follow -- lib/surface/semantic-registry.lisp
  15304119 … #502 (latest)
  …
  8e510341 feat(surface): make 0104 a direct peer semantic identity
  16620d83 feat(surface): seed meaning-first language-neutral registry

grep -ci canon lib/surface/semantic-registry.lisp   → 0
```

`grep -ci canon` returning `0` is the actionable finding: the registry file
never marks the canon rows as canonical. Nothing in the file distinguishes
`0001…0007` from ordinary function rows except first position and numeric
range. Semantics still come from ADR-004 / ADR-006 (immutable Canon resolver),
not from the registry.

## What this does NOT mean

1. Recovery of the numbering does **not** turn the canon into ordinary
   functions. ADR-004 still forbids an eighth primitive; ADR-006 still reserves
   the canon spellings (`(def car 42)` stays `InvalidForm`).
2. The registry is the *function table* — the numeric source of identity for
   surface spellings. It is not a replacement for the canon as a category.
3. The accidental look of canon-as-function inside one file is history, not
   semantics. A witness substrate must not rely on the registry alone to learn
   "these seven are immutable"; that property lives in ADR-004/006 and in the
   Canon executable laws (`lib/canon.lisp`).

## Consequence for the FPC witness (wsm-lazarus)

- The reader/build pipeline needs **only the function table**
  (`semantic-registry.lisp`) for numeric identity resolution (`0001…1152`).
- The canon seven (`kCanon`, `CANON_ID_QUOTE…CANON_ID_COND` in
  `src/wsm.values.pas`) use the first seven IDs by agreement with the registry,
  not because the registry defines them as a separate category.
- No third numbering is invented; the numeric alignment with the function
  table is a deliberate, verified convention.