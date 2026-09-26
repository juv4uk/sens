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

(def witness-field
  (lambda (key witness)
    (let ((entry (assoc key witness)))
      (cond
        ((atom? entry) () (quote ()))
        ((atom? entry) (1) (quote ()))
        (t (cdr entry))))))

(def witness-malformed-result
  (lambda (reason actual)
    (list (quote witness-result)
          (list (quote status) (quote malformed))
          (list (quote reason) reason)
          (list (quote actual) actual))))

(def witness-result-record
  (lambda (status expected actual)
    (list (quote witness-result)
          (list (quote status) status)
          (list (quote expected) expected)
          (list (quote actual) actual))))

; #218 supersession layer.
; The old corpus remains historical evidence that atom/eq once returned T/NIL.
; Current authority maps only those ratified historical contracts to the new
; structural result data. No unrelated predicate is rewritten here.
(def witness-superseded-outcome
  (lambda (witness expected-entry)
    (cond
      ((atom? expected-entry) () (quote ()))
      ((atom? expected-entry) (0)
       (let ((expr (witness-field (quote expr) witness)))
         (cond
           ((equal? expr "(00000010 (quote radio))")
            (list (quote value) "(1)"))
           ((equal? expr "(00000010 (quote ()))")
            (list (quote value) "()"))
           ((equal? expr "(00000010 (quote (radio antenna)))")
            (list (quote value) "(0)"))
           ((string-prefix? "(00000011 " expr)
            (cond
              ((equal? (cdr expected-entry) "t")
               (list (quote value) "(1)"))
              ((equal? (cdr expected-entry) "()")
               (list (quote value) "(0)"))
              (t (quote ()))))
           (t (quote ()))))))))

; Convert one authoritative conformance row into the current expected-outcome
; envelope. A non-empty supersession record wins over the historical expected
; field; otherwise the row is interpreted exactly as committed.
(def witness-expected-outcome
  (lambda (witness)
    (let ((expected-entry (assoc (quote expected) witness))
          (error-entry (assoc (quote error) witness)))
      (let ((superseded (witness-superseded-outcome witness expected-entry)))
        (cond
          ((atom? superseded) (0) superseded)
          ((and expected-entry error-entry)
           (list (quote malformed) (quote expected-and-error)))
          ((and (00100001 (10110001 (00000010 expected-entry))) (00100001 (10110001 (00000010 error-entry))))
           (list (quote malformed) (quote missing-outcome)))
          (expected-entry
           (list (quote value) (cdr expected-entry)))
          (t
           (list (quote error) (cdr error-entry))))))))

; The normative comparator. Backends provide ACTUAL only. Expected authority is
; read/derived above in Lisp.
(def witness-verdict
  (lambda (witness actual)
    (let ((expected (witness-expected-outcome witness)))
      (cond
        ((eq? (car expected) (quote malformed))
         (witness-malformed-result (second expected) actual))
        ((equal? expected actual)
         (witness-result-record (quote pass) expected actual))
        (t
         (witness-result-record (quote fail) expected actual))))))

; #218/#220 transition: host observers consume an explicit status datum instead
; of asking Lisp for a universal truth value.
(def witness-status
  (lambda (result)
    (second (second result))))

; Migration-only adapter for older host observers not yet converted to
; `witness-status`. It dispatches on the explicit status datum; it does NOT
; coerce an arbitrary Lisp value to truth. New/modified observers must use
; `witness-status` directly. Remove this with the last old observer under #220.
(def witness-pass?
  (lambda (result)
    (cond
      ((witness-status result) pass t)
      ((witness-status result) fail (quote ()))
      ((witness-status result) malformed (quote ()))
      (t (quote ())))))

; Meta-eval errors are Lisp data, not host exceptions. Normalize only the named
; correspondence already established by the meta-evaluator evidence.
(def witness-meta-error-kind
  (lambda (kind)
    (cond
      ((eq? kind (quote unbound-symbol)) "UnknownSymbol")
      ((eq? kind (quote not-callable)) "Type")
      ((eq? kind (quote arity)) "Arity")
      ((eq? kind (quote invalid-form)) "InvalidForm")
      (t "UnsupportedMetaError"))))

(def witness-meta-error?
  (lambda (value)
    (cond
      ((atom? value) () (quote ()))
      ((atom? value) (1) (quote ()))
      ((atom? (car value)) () (eq? (car value) (quote error)))
      ((atom? (car value)) (1) (eq? (car value) (quote error)))
      (t (quote ())))))

(def witness-meta-outcome
  (lambda (value)
    (cond
      ((witness-meta-error? value)
       (list (quote error) (witness-meta-error-kind (second value))))
      (t
       (list (quote value) (write-to-string value))))))

; Registry-driven peer-surface witness. The semantic ID is a selection input;
; surface→ID truth comes only from my-semantic-surface-registry.
(def witness-peer-surface-count
  (lambda (semantic-id entries)
    (cond
      ((atom? entries) () 0)
      ((atom? entries) (1) 0)
      ((equal? (second (car entries)) semantic-id)
       (+ 1 (witness-peer-surface-count semantic-id (cdr entries))))
      (t
       (witness-peer-surface-count semantic-id (cdr entries))))))

(def witness-peer-surfaces-consistent?
  (lambda (semantic-id entries)
    (cond
      ((atom? entries) () t)
      ((atom? entries) (1) t)
      ((equal? (second (car entries)) semantic-id)
       (cond
         ((equal? (my-semantic-id-for-surface (car (car entries))) semantic-id)
          (witness-peer-surfaces-consistent? semantic-id (cdr entries)))
         (t (quote ()))))
      (t
       (witness-peer-surfaces-consistent? semantic-id (cdr entries))))))

(def witness-peer-surface-verdict
  (lambda (semantic-id)
    (let ((count (witness-peer-surface-count semantic-id my-semantic-surface-registry)))
      (cond
        ((and (> count 1)
              (witness-peer-surfaces-consistent? semantic-id my-semantic-surface-registry))
         (list (quote witness-result)
               (list (quote status) (quote pass))
               (list (quote semantic-id) semantic-id)
               (list (quote surface-count) count)))
        (t
         (list (quote witness-result)
               (list (quote status) (quote fail))
               (list (quote semantic-id) semantic-id)
               (list (quote surface-count) count)))))))
