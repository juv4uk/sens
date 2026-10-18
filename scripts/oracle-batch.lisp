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
(визначити make-request
  (функція (expr-str)
    (001000 ((quoted-source (11110100 expr-str)))
      (110011110
        (110011110
          (110011110 "(request (op oracle-eval) (id \"batch\") (source " quoted-source)
          ") (contract-version (3 0)))")
        "\n"))))

(визначити oracle-eval
  (функція (expr-str)
    (001000 ((request (make-request expr-str)))
      (001000 ((socket (tcp-connect "100.113.68.50" 9999)))
        (001000 ((sent (110110011 socket request)))
          (001000 ((response (110111110 socket)))
            (001000 ((closed (tcp-close socket)))
              (11101010 response))))))))

(визначити emit-result
  (функція (id result)
    (11011011 (список (як-є oracle-result)
                 (сполучити (як-є id) id)
                 (сполучити (як-є result) result)))))

(визначити fixtures-only
  (функція (entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      ; inventory.lisp's own last top-level form is a bare () -- the CLI's
      ; auto-printed final script return value, captured by the shell
      ; redirect that originally generated the file, not a real record.
      ; (car (car entries)) on that entry would car an atom and error, so
      ; skip any non-Pair top-level form defensively instead of assuming
      ; every entry is shaped like a tagged record.
      ((атом? (перше entries)) (fixtures-only (решта entries)))
      ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше (перше entries)) (як-є fixture))
            (сполучити (перше entries) (fixtures-only (решта entries))))
           ((атом? (як-є ())) (fixtures-only (решта entries))))))))

; Walk inventory.lisp's (fixture ...) records and conformance.lisp's raw
; ((expr . ...) ...) records in lockstep -- same position, same fixture.
(визначити process-pair
  (функція (inventory-remaining conformance-remaining)
    (за-умовою
      ((атом? inventory-remaining) (як-є ()))
      ((атом? conformance-remaining) (як-є ()))
      ((атом? (як-є ()))
       (001001 ((inventory-fixture (перше inventory-remaining))
              (id (решта (11100 (як-є id) (решта inventory-fixture))))
              (conformance-fixture (перше conformance-remaining))
              (expr-str (решта (11100 (як-є expr) conformance-fixture)))
              (result (oracle-eval expr-str))
              (emitted (emit-result id result)))
         (process-pair (решта inventory-remaining) (решта conformance-remaining)))))))

(11011011 (сполучити (як-є about) "oracle-results.lisp — oracle-eval results for every tests/fixtures/inventory.lisp fixture, via the canonical TCP Oracle :9999, keyed by stable F-ID."))
(11011011 (сполучити (як-є generated) "Run: my-lisp scripts/oracle-batch.lisp > tests/fixtures/oracle-results.lisp"))

(process-pair
  (fixtures-only (110101001 (110110111 "tests/fixtures/inventory.lisp")))
  (110101001 (110110111 "tests/fixtures/conformance.lisp")))

(як-є ())
