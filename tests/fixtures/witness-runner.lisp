; tests/fixtures/witness-runner.lisp — Lisp-owned semantic witness verdict protocol.
; tests/fixtures/witness-runner.lisp — протокол вердиктів семантичних свідчень, яким володіє Lisp.
;
; Authority stays in Lisp-owned fixture data. The historical conformance corpus
; is intentionally not rewritten in place when a ratified language contract is
; superseded: this runner records the explicit #218 supersession so the old
; T/NIL evidence remains visible while the current verdict uses the new domain
; result algebra.
;
; Host code may transport an actual value/error into the canonical
; `(value "...")` / `(error "Kind")` envelope, but it must not invent the
; expected answer.

(00001001 witness-d1-no
  (00001000 ()
    (тотожне? (00000001 witness-no-left) (00000001 witness-no-right))))

; Invert only exact D1 predicate values. No generic truthiness.
(00001001 witness-d1-no?
  (00001000 (value)
    (тотожне? value (witness-d1-no))))

; Witness-local lookup uses current exact-domain predicates: ATOM returns a
; D1 bit for both empty-list and pair inputs; field presence is independent of
; the value stored under a key (the string "()" is still a present value).
(00001001 witness-find-entry
  (00001000 (key alist)
    (за-умовою
      ((атом? alist)
       (00000001 ()))
      ((witness-d1-no? (атом? alist))
       (за-умовою
         ((тотожне? key (перше (перше alist)))
          (перше alist))
         ((witness-d1-no? (тотожне? key (перше (перше alist))))
          (witness-find-entry key (решта alist))))))))

(00001001 witness-field
  (00001000 (key witness)
    (10011100 ((entry (witness-find-entry key witness)))
      (за-умовою
        ((атом? entry)
         (00000001 ()))
        ((witness-d1-no? (атом? entry))
         (решта entry))))))

(00001001 witness-field-present?
  (00001000 (key witness)
    (witness-d1-no? (атом? (witness-find-entry key witness)))))

(00001001 witness-malformed-result
  (00001000 (reason actual)
    (00100111 (00000001 witness-result)
          (00100111 (00000001 status) (00000001 malformed))
          (00100111 (00000001 reason) reason)
          (00100111 (00000001 actual) actual))))

(00001001 witness-result-record
  (00001000 (status expected actual)
    (00100111 (00000001 witness-result)
          (00100111 (00000001 status) status)
          (00100111 (00000001 expected) expected)
          (00100111 (00000001 actual) actual))))

; #218 supersession layer.
; The old corpus remains historical evidence that atom/eq once returned T/NIL.
; Current authority maps only those ratified historical contracts to the new
; structural result data. No unrelated predicate is rewritten here.
(00001001 witness-superseded-outcome
  (00001000 (witness expected-entry)
    (за-умовою
      ((witness-d1-no? (witness-field-present? (00000001 expected) witness))
       (00000001 ()))
      ((witness-field-present? (00000001 expected) witness)
       (10011100 ((expr (witness-field (00000001 expr) witness)))
         (00000111
           ((00100010 expr "(00000010 (quote radio))")
            (00100111 (00000001 value) "(1)"))
           ((00100010 expr "(00000010 (quote ()))")
            (00100111 (00000001 value) "()"))
           ((00100010 expr "(00000010 (quote (radio antenna)))")
            (00100111 (00000001 value) "(0)"))
           ((00111101 "(00000011 " expr)
            (00000111
              ((00100010 (00000110 expected-entry) "t")
               (00100111 (00000001 value) "(1)"))
              ((00100010 (00000110 expected-entry) "()")
               (00100111 (00000001 value) "(0)"))
              ((witness-d1-no? (witness-d1-no))
               (00000001 ()))))
           ((witness-d1-no? (witness-d1-no))
               (00000001 ()))))))))

; Convert one authoritative conformance row into the current expected-outcome
; envelope. A non-empty supersession record wins over the historical expected
; field; otherwise the row is interpreted exactly as committed.
(00001001 witness-expected-outcome
  (00001000 (witness)
    (10011100 ((expected-entry (witness-field (00000001 expected) witness))
          (error-entry (witness-field (00000001 error) witness))
          (expected-present (witness-field-present? (00000001 expected) witness))
          (error-present (witness-field-present? (00000001 error) witness)))
      (10011100 ((superseded (witness-superseded-outcome witness expected-entry)))
        (за-умовою
          ((witness-d1-no? (атом? superseded))
           superseded)
          ((witness-d1-no? expected-present)
           (за-умовою
             (error-present
              (00100111 (00000001 witness-result)
                    (00100111 (00000001 status) (00000001 error))
                    (00100111 (00000001 actual) error-entry)))
             ((witness-d1-no? error-present)
              (witness-malformed-result (00000001 missing-outcome) witness))))
          (expected-present
           (за-умовою
             (error-present
              (witness-malformed-result (00000001 expected-and-error) witness))
             ((witness-d1-no? error-present)
              (00100111 (00000001 witness-result)
                    (00100111 (00000001 status) (00000001 value))
                    (00100111 (00000001 actual) expected-entry))))))))))

(00001001 witness-verdict
  (00001000 (witness actual)
    (10011100 ((expected (witness-expected-outcome witness)))
      (00000111
        ((00000011 (00000101 expected) (00000001 malformed))
         (witness-malformed-result (00101111 expected) actual))
        ((00100010 expected actual)
         (witness-result-record (00000001 pass) expected actual))
        (t
         (witness-result-record (00000001 fail) expected actual))))))

; #218/#220 transition: host observers consume an explicit status datum instead
; of asking Lisp for a universal truth value.
(00001001 witness-status
  (00001000 (result)
    (00101111 (00101111 result))))

; Migration-only adapter for older host observers not yet converted to
; `witness-status`. It dispatches on the explicit status datum; it does NOT
; coerce an arbitrary Lisp value to truth. New/modified observers must use
; `witness-status` directly. Remove this with the last old observer under #220.
(00001001 witness-pass?
  (00001000 (result)
    (00000111
      ((witness-status result) pass t)
      ((witness-status result) fail (00000001 ()))
      ((witness-status result) malformed (00000001 ()))
      (t (00000001 ())))))

; Meta-eval errors are Lisp data, not host exceptions. Normalize only the named
; correspondence already established by the meta-evaluator evidence.
(00001001 witness-meta-error-kind
  (00001000 (kind)
    (00000111
      ((00000011 kind (00000001 unbound-symbol)) "UnknownSymbol")
      ((00000011 kind (00000001 not-callable)) "Type")
      ((00000011 kind (00000001 arity)) "Arity")
      ((00000011 kind (00000001 invalid-form)) "InvalidForm")
      (t "UnsupportedMetaError"))))

(00001001 witness-meta-error?
  (00001000 (value)
    (00000111
      ((00000010 value) () (00000001 ()))
      ((00000010 value) (1) (00000001 ()))
      ((00000010 (00000101 value)) () (00000011 (00000101 value) (00000001 error)))
      ((00000010 (00000101 value)) (1) (00000011 (00000101 value) (00000001 error)))
      (t (00000001 ())))))

(00001001 witness-meta-outcome
  (00001000 (value)
    (00000111
      ((witness-meta-error? value)
       (00100111 (00000001 error) (witness-meta-error-kind (00101111 value))))
      (t
       (00100111 (00000001 value) (01001100 value))))))

; Witness transport adapter after #1623/#1648: machine write-to-string is now
; the tagged #q2 canonical wire, while conformance expected values remain on
; the guarded human projection. Error classification stays Lisp-owned; the
; host supplies only the already-guarded presentation text for successful
; values, exactly as the native witness transport has always done.
(00001001 witness-meta-outcome-presented
  (00001000 (value presented-text)
    (00000111
      ((witness-meta-error? value)
       (00100111 (00000001 error) (witness-meta-error-kind (00101111 value))))
      (t
       (00100111 (00000001 value) presented-text)))))

; Registry-driven peer-surface witness. The semantic ID is a selection input;
; surface→ID truth comes only from my-semantic-surface-registry.
(00001001 witness-peer-surface-count
  (00001000 (semantic-id entries)
    (00000111
      ((00000010 entries) () 0)
      ((00000010 entries) (1) 0)
      ((00100010 (00101111 (00000101 entries)) semantic-id)
       (00001100 1 (witness-peer-surface-count semantic-id (00000110 entries))))
      (t
       (witness-peer-surface-count semantic-id (00000110 entries))))))

(00001001 witness-peer-surfaces-consistent?
  (00001000 (semantic-id entries)
    (00000111
      ((00000010 entries) () t)
      ((00000010 entries) (1) t)
      ((00100010 (00101111 (00000101 entries)) semantic-id)
       (00000111
         ((00100010 (my-semantic-id-for-surface (00000101 (00000101 entries))) semantic-id)
          (witness-peer-surfaces-consistent? semantic-id (00000110 entries)))
         (t (00000001 ()))))
      (t
       (witness-peer-surfaces-consistent? semantic-id (00000110 entries))))))

(00001001 witness-peer-surface-verdict
  (00001000 (semantic-id)
    (10011100 ((count (witness-peer-surface-count semantic-id my-semantic-surface-registry)))
      (00000111
        ((10011010 (00011011 count 1)
              (witness-peer-surfaces-consistent? semantic-id my-semantic-surface-registry))
         (00100111 (00000001 witness-result)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 semantic-id) semantic-id)
               (00100111 (00000001 surface-count) count)))
        (t
         (00100111 (00000001 witness-result)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 semantic-id) semantic-id)
               (00100111 (00000001 surface-count) count)))))))
