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

(def changed-host-tests
  (read-all (read-file "tests/changed-host-tests.lisp")))

; Consume the transported facts so malformed/unreadable transport still stays
; visible to the Lisp process, but do not classify host semantics.
(cond
  ((atom changed-host-tests)
   (structural-kind empty-list)
   (quote (authority-ok)))
  ((atom changed-host-tests)
   (structural-kind pair)
   (quote (authority-ok))))
