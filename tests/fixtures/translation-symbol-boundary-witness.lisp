; #369 — external translation decisions must survive the symbol? result-domain
; migration without preserving the historical t/() predicate sentinel.
;
; These are public boundary outcomes: a non-symbol module name is invalid, a
; translator refusal with a symbolic reason is recordable evidence, and a
; refusal carrying a non-symbol reason is rejected as malformed.

(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/forward.lisp")
(load "lib/knowledge.lisp")
(load "lib/result-status.lisp")
(load "lib/translation.lisp")

(00001001 translation-symbol-boundary-rows
  (00001000 ()
    (10011101 ((symbol-refusal
             (00000001
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 unsupported-translation)))
           (non-symbol-refusal
             (00000001
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 42)))
           (invalid-module-review
             (translation-review 42 symbol-refusal))
           (symbol-refusal-review
             (translation-review (00000001 corpus) symbol-refusal))
           (non-symbol-refusal-review
             (translation-review (00000001 corpus) non-symbol-refusal)))
      (00100111
        (00100111
          (00000001 non-symbol-module-is-invalid)
          (00100111
            (translation-review-status invalid-module-review)
            (translation-review-code invalid-module-review))
          (00000001 (rejected invalid-module)))
        (00100111
          (00000001 symbolic-refusal-is-recordable)
          (00100111
            (translation-review-status symbol-refusal-review)
            (translation-review-code symbol-refusal-review))
          (00000001 (rejected translator-rejected)))
        (00100111
          (00000001 non-symbol-refusal-is-invalid)
          (00100111
            (translation-review-status non-symbol-refusal-review)
            (translation-review-code non-symbol-refusal-review))
          (00000001 (rejected invalid-rejection)))))))

(00001001 translation-symbol-boundary-check
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (translation-symbol-boundary-witness (status pass))))
      ((00000010 rows) (1)
       (00100111
         (00000001 translation-symbol-boundary-witness)
         (00100111 (00000001 status) (00000001 fail))
         (00100111 (00000001 case) (00000001 malformed-row-tail))
         (00100111 (00000001 actual) rows)))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row))
            (translation-symbol-boundary-check (00000110 rows)))
           ((00100010 (00100010 (00101111 row) (00110000 row))
     (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
            (00100111
              (00000001 translation-symbol-boundary-witness)
              (00100111 (00000001 status) (00000001 fail))
              (00100111 (00000001 case) (00000101 row))
              (00100111 (00000001 actual) (00101111 row))
              (00100111 (00000001 expected) (00110000 row))))))))))

(00001001 translation-symbol-boundary-witness
  (00001000 ()
    (translation-symbol-boundary-check
      (translation-symbol-boundary-rows))))

(translation-symbol-boundary-witness)
