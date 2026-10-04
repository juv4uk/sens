; #3161 / #1708 — Lisp-owned exact D1 / structural EMPTY control cases.
;
; This is test data, not source syntax. Rust may decode these descriptors into
; exact-domain AST values because the ordinary human parser still has no
; free-standing D1 literal. The semantic case matrix and expected outcomes live
; here, in Lisp-owned data.
(
  ((case . "d1-yes-selects")
   (program . (за-умовою
                (clause (d1 "1") (d1 "0"))))
   (expect-value . (d1 "0")))

  ((case . "d1-no-skips")
   (program . (за-умовою
                (clause (d1 "0") (d1 "1"))
                (clause (d1 "1") (d1 "0"))))
   (expect-value . (d1 "0")))

  ((case . "empty-skips")
   (program . (за-умовою
                (clause empty (d1 "1"))
                (clause (d1 "1") (d1 "0"))))
   (expect-value . (d1 "0")))

  ((case . "two-empty-tests-exhaust-to-empty")
   (program . (за-умовою
                (clause empty (d1 "1"))
                (clause empty (d1 "0"))))
   (expect-value . empty))

  ((case . "d1-no-exhausts-to-empty")
   (program . (за-умовою
                (clause (d1 "0") (d1 "1"))))
   (expect-value . empty))

  ((case . "other-domain-value-is-not-truth")
   (program . (за-умовою
                (clause (d3-value "001") (d1 "1"))))
   (expect-error . "Type"))

  ((case . "number-one-is-not-d1")
   (program . (за-умовою
                (clause (number "1") (d1 "1"))))
   (expect-error . "Type"))

  ((case . "symbol-t-is-not-d1")
   (program . (за-умовою
                (clause (symbol "t") (d1 "1"))))
   (expect-error . "Type"))

  ((case . "three-part-clause-is-not-canonical")
   (program . (за-умовою
                (clause (d1 "1") (d1 "0") (d1 "1"))))
   (expect-error . "InvalidForm"))

  ((case . "partial-eq-empty-feeds-cond")
   (program . (за-умовою
                (clause
                  (call-d3 "111"
                    (call-d3 "100" (d1 "1") (d1 "0"))
                    (d1 "1"))
                  (d1 "1"))
                (clause (d1 "1") (d1 "0"))))
   (expect-value . (d1 "0")))

  ((case . "computed-empty-feeds-cond")
   (program . (за-умовою
                (clause
                  (за-умовою
                    (clause (d1 "0") (d1 "1")))
                  (d1 "1"))
                (clause (d1 "1") (d1 "0"))))
   (expect-value . (d1 "0")))

  ((case . "direct-d1-no-remains-d1")
   (program . (d1 "0"))
   (expect-value . (d1 "0")))

  ((case . "direct-empty-remains-structural")
   (program . empty)
   (expect-value . empty))
)
