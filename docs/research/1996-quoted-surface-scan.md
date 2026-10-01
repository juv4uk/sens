# Post-#1996 quoted-surface scan

**Agent:** grok-xai  
**After:** #2041 closed TCP `read` heads

## Closed

```text
receive-knowledge-package / tcp-read-to-eof  → 01001010
accept-knowledge-exchange / tcp-read-frame   → 01001010
import-knowledge-file / read-file            → 01001010 (#1960)
```

## Still human-quoted in expanded forms (`lib/knowledge.lisp`)

Not all of these are **eval heads**. Many are data tags (`accepted`, `rejected`, `module`) or special forms lowered at load time.

| site (approx) | quoted symbol | risk |
|---------------|---------------|------|
| L157 `load-knowledge` | `load` | **possible** executable head if expanded then eval'd |
| L233+ `tell-knowledge` | `cond`, `def`, `append`, … | macro body — usually lowered when defmacro loads |
| L409+ | `equal?`, `second`, `list`, `def` | same |
| data tags | `accepted`, `rejected`, `reason`, … | **data**, not Function8 |

## Rule for next fixes

1. Claim **one** site if it is a later-evaluated call head.
2. Confirm registry has exact Function8 (or refuse).
3. Do **not** bulk-rename data tags to SIDs.
4. Prefer inventory PR before mass edit.

`load` had no obvious registry row in a quick scan — do not invent a SID.
