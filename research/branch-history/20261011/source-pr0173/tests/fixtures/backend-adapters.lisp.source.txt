; #116 — execution-path declarations only.
; Semantic truth remains exclusively in tests/fixtures/conformance.lisp.
; Backends are students of that corpus; this file must never contain expected answers.

(def witness-corpus "tests/fixtures/conformance.lisp")

(def witness-backends
  (quote
    ((backend native) (adapter native-eval)
     (backend meta)   (adapter meta-eval)
     (backend cml)    (adapter cml-execution))))
