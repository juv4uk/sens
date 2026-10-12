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
(0011 make-request
  (0010 (expr-str)
    (001000 ((quoted-source (11110100 expr-str)))
      (110011110
        (110011110
          (110011110 "(request (op oracle-eval) (id \"batch\") (source " quoted-source)
          ") (contract-version (3 0)))")
        "\n"))))

(0011 oracle-eval
  (0010 (expr-str)
    (001000 ((request (make-request expr-str)))
      (001000 ((socket (tcp-connect "100.113.68.50" 9999)))
        (001000 ((sent (110110011 socket request)))
          (001000 ((response (110111110 socket)))
            (001000 ((closed (tcp-close socket)))
              (11101010 response))))))))

(0011 emit-result
  (0010 (id result)
    (11011011 (1110 (001 oracle-result)
                 (111 (001 id) id)
                 (111 (001 result) result)))))

(0011 fixtures-only
  (0010 (entries)
    (110
      ((010 entries) (001 ()))
      ; inventory.lisp's own last top-level form is a bare () -- the CLI's
      ; auto-printed final script return value, captured by the shell
      ; redirect that originally generated the file, not a real record.
      ; (car (car entries)) on that entry would car an atom and error, so
      ; skip any non-Pair top-level form defensively instead of assuming
      ; every entry is shaped like a tagged record.
      ((010 (100 entries)) (fixtures-only (011 entries)))
      ((010 (001 ())) (110
           ((101 (100 (100 entries)) (001 fixture))
            (111 (100 entries) (fixtures-only (011 entries))))
           ((010 (001 ())) (fixtures-only (011 entries))))))))

; Walk inventory.lisp's (fixture ...) records and conformance.lisp's raw
; ((expr . ...) ...) records in lockstep -- same position, same fixture.
(0011 process-pair
  (0010 (inventory-remaining conformance-remaining)
    (110
      ((010 inventory-remaining) (001 ()))
      ((010 conformance-remaining) (001 ()))
      ((010 (001 ()))
       (001001 ((inventory-fixture (100 inventory-remaining))
              (id (011 (11100 (001 id) (011 inventory-fixture))))
              (conformance-fixture (100 conformance-remaining))
              (expr-str (011 (11100 (001 expr) conformance-fixture)))
              (result (oracle-eval expr-str))
              (emitted (emit-result id result)))
         (process-pair (011 inventory-remaining) (011 conformance-remaining)))))))

(11011011 (111 (001 about) "oracle-results.lisp — oracle-eval results for every tests/fixtures/inventory.lisp fixture, via the canonical TCP Oracle :9999, keyed by stable F-ID."))
(11011011 (111 (001 generated) "Run: my-lisp scripts/oracle-batch.lisp > tests/fixtures/oracle-results.lisp"))

(process-pair
  (fixtures-only (110101001 (110110111 "tests/fixtures/inventory.lisp")))
  (110101001 (110110111 "tests/fixtures/conformance.lisp")))

(001 ())
