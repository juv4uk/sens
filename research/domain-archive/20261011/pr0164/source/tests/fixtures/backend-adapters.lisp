; #116 mechanism-only backend manifest.
; Semantic expected/error truth lives only in tests/fixtures/conformance.lisp.
; These rows say which execution mechanism consumes that corpus; they do not
; define what any Lisp expression means.

(backend native
  (corpus "tests/fixtures/conformance.lisp")
  (adapter native-eval))

(backend meta
  (corpus "tests/fixtures/conformance.lisp")
  (adapter meta-eval))

(backend cml
  (corpus "tests/fixtures/conformance.lisp")
  (adapter cml-eval))
