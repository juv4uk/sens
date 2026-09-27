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
(00001001 make-request
  (00001000 (expr-str)
    (10011100 ((quoted-source (01001100 expr-str)))
      (00111010
        (00111010
          (00111010 "(request (op oracle-eval) (id \"batch\") (source " quoted-source)
          ") (contract-version (3 0)))")
        "\n"))))

(00001001 oracle-eval
  (00001000 (expr-str)
    (10011100 ((request (make-request expr-str)))
      (10011100 ((socket (tcp-connect "100.113.68.50" 9999)))
        (10011100 ((sent (10100100 socket request)))
          (10011100 ((response (10100011 socket)))
            (10011100 ((closed (tcp-close socket)))
              (01001010 response))))))))

(00001001 emit-result
  (00001000 (id result)
    (01001000 (00100111 (00000001 oracle-result)
                 (00000100 (00000001 id) id)
                 (00000100 (00000001 result) result)))))

(00001001 fixtures-only
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ; inventory.lisp's own last top-level form is a bare () -- the CLI's
      ; auto-printed final script return value, captured by the shell
      ; redirect that originally generated the file, not a real record.
      ; (car (car entries)) on that entry would car an atom and error, so
      ; skip any non-Pair top-level form defensively instead of assuming
      ; every entry is shaped like a tagged record.
      ((00000010 (00000101 entries)) () (fixtures-only (00000110 entries)))
      ((00000010 (00000101 entries)) (1) (fixtures-only (00000110 entries)))
      (t (00000111
           ((00000011 (00000101 (00000101 entries)) (00000001 fixture))
            (00000100 (00000101 entries) (fixtures-only (00000110 entries))))
           (t (fixtures-only (00000110 entries))))))))

; Walk inventory.lisp's (fixture ...) records and conformance.lisp's raw
; ((expr . ...) ...) records in lockstep -- same position, same fixture.
(00001001 process-pair
  (00001000 (inventory-remaining conformance-remaining)
    (00000111
      ((00000010 inventory-remaining) () (00000001 ()))
      ((00000010 inventory-remaining) (1) (00000001 ()))
      ((00000010 conformance-remaining) () (00000001 ()))
      ((00000010 conformance-remaining) (1) (00000001 ()))
      (t
       (10011101 ((inventory-fixture (00000101 inventory-remaining))
              (id (00000110 (00101101 (00000001 id) (00000110 inventory-fixture))))
              (conformance-fixture (00000101 conformance-remaining))
              (expr-str (00000110 (00101101 (00000001 expr) conformance-fixture)))
              (result (oracle-eval expr-str))
              (emitted (emit-result id result)))
         (process-pair (00000110 inventory-remaining) (00000110 conformance-remaining)))))))

(01001000 (00000100 (00000001 about) "oracle-results.lisp — oracle-eval results for every tests/fixtures/inventory.lisp fixture, via the canonical TCP Oracle :9999, keyed by stable F-ID."))
(01001000 (00000100 (00000001 generated) "Run: my-lisp scripts/oracle-batch.lisp > tests/fixtures/oracle-results.lisp"))

(process-pair
  (fixtures-only (01001011 (10100110 "tests/fixtures/inventory.lisp")))
  (01001011 (10100110 "tests/fixtures/conformance.lisp")))

(00000001 ())
