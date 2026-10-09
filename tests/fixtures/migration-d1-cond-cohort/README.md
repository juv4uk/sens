# D1 predicate-only COND · executable T5 canary

Issue: [SENS #4455](https://github.com/juv4uk/sens/issues/4455), coordinated by [#4449](https://github.com/juv4uk/sens/issues/4449).

- `branch.lisp` is the **canonical Ukrainian `ук` human surface**, not executable raw bit words: `(за-умовою (ні (перше ())) (так так))`. D1 `ні/так` and D3 `за-умовою/перше` are resolved through ratified domain surfaces; `()` is the structural empty-list spelling. The source is not historical SID8.
- Physical `branch.sens` is genuine T5 (5 ternary transport digits per byte); *only* the transport uses separator `2`. File EOF; no `22` terminator.\n- `branch` **без розширення** — не виконуваний машинний файл, а звичайний ASCII-перегляд точних бітових слів з одним пробілом між ними й одним фінальним LF; він походить із декодованого `branch.sens`. Python/Rust перевіряють побайтовий збіг і повернення в той самий T5. Масовий генератор та загальний релізний guard відстежуються у #4694 і #4430.
- D3:110 has **two-part** clauses only. D1:0 skips the invalid `D3 CAR(EMPTY)` expression; D1:1 selects exact `D1:1`. Historical Lisp non-NIL truthiness has no authority on this path.
- `scripts/migrate-three-pass.py` is the *existing* source-to-transport code; focused Python tests prove its projection, byte identity, no-overwrite, typed digest and manifest. Rust tests independently load committed bytes and run the current exact SENS oracle.
- Provenance stays separate from original strict scan 37810152645 (491 BLOCKED/0 admitted). This is a **new, bounded executable canary**, not an assertion that an old unsupported source migrated.
- Do not merge without both dedicated Python and Rust evidence; no codec/ratified-domain/release-pin edits.
