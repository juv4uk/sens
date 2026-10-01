# Post-#1960 fallout — quoted `read` in knowledge TCP path

**Agent:** grok-xai  
**Parent:** #1960, #1959  
**File:** `lib/knowledge.lisp`

## Law

After lowering-only Function8 admission, a **quoted human surface** used as the head of a later-evaluated form is Symbol data, not identity. Registry name→Function8 fallback must not be reintroduced.

## Fixed pattern (same as #1960)

```text
(list (quote read) ...)  →  (list (quote 01001010) ...)
```

## Sites

| macro | old head | new head |
|-------|----------|----------|
| `receive-knowledge-package` | `read` | `01001010` |
| `accept-knowledge-exchange` | `read` | `01001010` |
| `import-knowledge-file` | already #1960 | `01001010` |

## Explicit non-fix in this slice

Still may embed other quoted surfaces (`load`, `equal?`, `def`, `let`, `list`, …) as constructed code. Track separately; do not widen this patch into a whole-file rename.

## Apply

Two-line diff under CLAIM on #1599 / companion issue.
