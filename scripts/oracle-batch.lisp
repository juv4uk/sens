; scripts/oracle-batch.lisp — run every constitutional fixture through the
; canonical TCP Oracle (:9999) and emit one machine-readable result per
; fixture, keyed by its stable inventory ID.
;
; tests/fixtures/inventory.lisp carries the stable F-<hash> IDs but not the
; expression text; tests/fixtures/conformance.lisp carries the expression
; text but no stable ID. Both are a straight positional walk over the same
; underlying fixture list (build-inventory.lisp's emit-all processes
; conformance.lisp's fixtures in file order, one inventory record per
; fixture, no filtering/reordering) -- so the Nth (fixture ...) record in
; inventory.lisp and the Nth raw record in conformance.lisp are the same
; fixture, and are read here in parallel to pair `id` with `expr`.
;
; Run: my-lisp scripts/oracle-batch.lisp > tests/fixtures/oracle-results.lisp

; expr-str is the fixture's own original source text (already a string,
; straight from conformance.lisp). It is sent as-is, WITHOUT a local
; read/write-to-string round trip: some fixtures (e.g. the S3
; 1e100001/1e-100001 NumericOverflow cases) are only meaningful because
; their source text does not survive local parsing at all -- re-reading
; them here would abort the whole batch on the local reader's own
; resource bound before the oracle ever saw the request. The only local
; step needed is quoting expr-str as a WSM string literal for embedding
; in the request text.
(def make-request
  (lambda (expr-str)
    (let ((quoted-source (write-to-string expr-str)))
      (string-append
        (string-append
          (string-append "(request (op oracle-eval) (id \"batch\") (source " quoted-source)
          ") (contract-version (3 0)))")
        "\n"))))

(def oracle-eval
  (lambda (expr-str)
    (let ((request (make-request expr-str)))
      (let ((socket (tcp-connect "100.113.68.50" 9999)))
        (let ((sent (tcp-write socket request)))
          (let ((response (tcp-read socket)))
            (let ((closed (tcp-close socket)))
              (read response))))))))

(def emit-result
  (lambda (id result)
    (print (list (quote oracle-result)
                 (cons (quote id) id)
                 (cons (quote result) result)))))

(def fixtures-only
  (lambda (entries)
    (cond
      ((atom? entries) (quote ()))
      ; inventory.lisp's own last top-level form is a bare () -- the CLI's
      ; auto-printed final script return value, captured by the shell
      ; redirect that originally generated the file, not a real record.
      ; (car (car entries)) on that entry would car an atom and error, so
      ; skip any non-Pair top-level form defensively instead of assuming
      ; every entry is shaped like a tagged record.
      ((atom? (car entries)) (fixtures-only (cdr entries)))
      (t (cond
           ((eq? (car (car entries)) (quote fixture))
            (cons (car entries) (fixtures-only (cdr entries))))
           (t (fixtures-only (cdr entries))))))))

; Walk inventory.lisp's (fixture ...) records and conformance.lisp's raw
; ((expr . ...) ...) records in lockstep -- same position, same fixture.
(def process-pair
  (lambda (inventory-remaining conformance-remaining)
    (cond
      ((atom? inventory-remaining) (quote ()))
      ((atom? conformance-remaining) (quote ()))
      (t
       (let* ((inventory-fixture (car inventory-remaining))
              (id (cdr (assoc (quote id) (cdr inventory-fixture))))
              (conformance-fixture (car conformance-remaining))
              (expr-str (cdr (assoc (quote expr) conformance-fixture)))
              (result (oracle-eval expr-str))
              (emitted (emit-result id result)))
         (process-pair (cdr inventory-remaining) (cdr conformance-remaining)))))))

(print (cons (quote about) "oracle-results.lisp — oracle-eval results for every tests/fixtures/inventory.lisp fixture, via the canonical TCP Oracle :9999, keyed by stable F-ID."))
(print (cons (quote generated) "Run: my-lisp scripts/oracle-batch.lisp > tests/fixtures/oracle-results.lisp"))

(process-pair
  (fixtures-only (read-all (read-file "tests/fixtures/inventory.lisp")))
  (read-all (read-file "tests/fixtures/conformance.lisp")))

(quote ())
