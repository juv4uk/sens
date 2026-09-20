; #996 — machine-readable binary SID authority handoff.
;
; This artifact contains authority metadata only. It deliberately does NOT copy
; semantic rows, decimal IDs, surface spellings, evaluator dispatch, or machine
; lowering policy. Consumers pin the canonical source content revision below
; and derive every row from that source.
;
; Git blob identity is content-addressed: unrelated repository commits do not
; invalidate the pin, while any registry byte change requires an explicit
; handoff update.

(sid-registry-handoff/1
  (authority-source . "lib/surface/semantic-registry.lisp")
  (source-git-blob . "c37df0d9a629ffdd77e5edba6374dabe7d88e7d9")
  (identity-width-bits . 8)
  (canonical-id-encoding . binary-token)
  (canonical-row-count . 170)
  (projection-policy . derived-only)
  (consumer-policy . observe-or-lower)
  (meaning-owner . my-lisp)
  (forbidden
    decimal-shadow-registry
    string-sid-shadow-registry
    hand-maintained-projection
    consumer-redefinition))
