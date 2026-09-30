; #115 historical host-test authority guard.
; #1347 supersedes the old deny policy.
;
; Host/runtime/compiler/backend code and tests may contain local semantics.
; This compatibility producer remains in place so older CI wiring keeps a
; stable Lisp-owned verdict shape, but it deliberately imposes no semantic
; restriction on host files.
;
; The active semantic boundary is now scripts/semantic-authority-guard.lisp:
; only host/backend -> Lisp language-authority leakage is forbidden.

(00001001 changed-host-tests
  (01001011 (10100110 "tests/changed-host-tests.lisp")))

; Consume the transported facts so malformed/unreadable transport still stays
; visible to the Lisp process, but do not classify host semantics.
(00000111
  ((00000010 changed-host-tests)
   ()
   (00000001 (authority-ok)))
  ((00000010 changed-host-tests)
   (#b0)
   (00000001 (authority-ok))))
