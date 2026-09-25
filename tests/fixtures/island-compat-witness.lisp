; #749 — executable Lisp-owned witness for island compatibility.
;
; The host may transport contracts/island-compat-contract.lisp as bytes and
; bind it to island-compat-document. Every semantic expectation remains here.

(def island-compat-schema
  (lambda () (car island-compat-document)))

(def island-compat-entries
  (lambda () (cdr island-compat-document)))

(def island-compat-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom? found) (quote ()))
        (t (cdr found))))))

(def island-compat-find
  (lambda (identity entries)
    (cond
      ((atom? entries) (quote ()))
      ((equal? (island-compat-field (car entries) (quote identity)) identity)
       (car entries))
      (t (island-compat-find identity (cdr entries))))))

(def island-compat-entry
  (lambda (identity)
    (island-compat-find identity (island-compat-entries))))

(def island-compat-check
  (lambda (identity field expected)
    (let ((entry (island-compat-entry identity)))
      (cond
        ((atom? entry) (list (quote missing-entry) identity))
        ((equal? (island-compat-field entry field) expected) (quote ()))
        (t (list (quote mismatch) identity field expected
                 (island-compat-field entry field)))))))

(def island-compat-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) (quote ()))
      ((atom? (car checks)) (island-compat-first-failure (cdr checks)))
      (t (car checks)))))

(def island-compat-witness
  (lambda ()
    (let ((failure
            (island-compat-first-failure
              (list
                (island-compat-check
                  (quote semantic-id) (quote owner) (quote my-lisp))
                (island-compat-check
                  (quote semantic-id) (quote representation) (quote opaque-u8))
                (island-compat-check
                  (quote semantic-id) (quote kernel-interpretation) (quote forbidden))
                (island-compat-check
                  (quote execution-witness) (quote cardinality) (quote zero-or-more))
                (island-compat-check
                  (quote execution-witness) (quote multiple-kernels-per-sid) (quote allowed))
                (island-compat-check
                  (quote island-call) (quote producer-required) (quote yes))
                (island-compat-check
                  (quote island-call) (quote provenance-preserved) (quote yes))
                (island-compat-check
                  (quote island-call) (quote universal-result-coercion) (quote forbidden))
                (island-compat-check
                  (quote zero-results) (quote result-count) 0)
                (island-compat-check
                  (quote zero-results) (quote literal-empty-list-alias) (quote forbidden))
                (island-compat-check
                  (quote one-result) (quote result-count) 1)
                (island-compat-check
                  (quote many-results) (quote result-count) (quote many))
                (island-compat-check
                  (quote many-results) (quote multiplicity-preserved) (quote yes))
                (island-compat-check
                  (quote bridge) (quote missing-bridge) (quote legal))
                (island-compat-check
                  (quote bridge) (quote semantic-equivalence-assumed) (quote no))
                (island-compat-check
                  (quote missing-kernel) (quote legal) (quote yes))
                (island-compat-check
                  (quote missing-kernel) (quote changes-sid-meaning) (quote no))
                (island-compat-check
                  (quote missing-kernel) (quote changes-registry-numbering) (quote no))))))
      (cond
        ((eq? (island-compat-schema) (quote island-compat-contract/1))
         (cond
           ((atom? failure)
            (list (quote island-compat-witness)
                  (list (quote status) (quote pass))
                  (list (quote detail) (quote semantic-owner-island-mechanism))))
           (t
            (list (quote island-compat-witness)
                  (list (quote status) (quote fail))
                  (list (quote detail) failure)))))
        (t
         (list (quote island-compat-witness)
               (list (quote status) (quote fail))
               (list (quote detail)
                     (list (quote schema) (island-compat-schema)))))))))
