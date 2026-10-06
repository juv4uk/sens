# D9 human surfaces

Canonical D9 human table: `lib/domains/d9.lisp`.

Authority: `knowledge/d9-ratified.json` (#4008), Contract 11.8.

D9 is owner-ratified **512/512**. The canonical human table contains exactly 512 9-bit rows in coordinate order.

Columns:

`ук → укр → san → en → LISP → sym`

Surface rules:

- 128 selector-generator residents use the same structural path law as earlier selector families;
- `ук` uses compact selector paths (`п/р`) for those residents;
- `укр` keeps the expanded selector explanation;
- predicates use `?` in `ук/укр/en`, not in `san`;
- destructive operations use `!` in `ук/укр/en`; Sanskrit distinguishes destructive semantics lexically rather than by punctuation;
- technical acronyms such as UTF8/TCP/JSON/CLIPS/JTMS remain recognizable inside the human projection.

Important boundaries:

- the human table does **not** alter any #4008 coordinate or resident;
- human spelling does not imply Core ownership; post-ratification ownership audit #4033 remains separate;
- human spelling does not imply runtime callability;
- Rust W9 carrier support is a separate mechanism cut tracked by #4038 and may fail closed meanwhile;
- historical Sens8/Sid8/Function8 and old source-registry bytes have zero D9 placement authority.

This document intentionally does not duplicate the 512-row table.
