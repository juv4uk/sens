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

(0011 translation-symbol-boundary-rows
  (0010 ()
    (001001 ((symbol-refusal
             (001
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 unsupported-translation)))
           (non-symbol-refusal
             (001
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 42)))
           (invalid-module-review
             (translation-review 42 symbol-refusal))
           (symbol-refusal-review
             (translation-review (001 corpus) symbol-refusal))
           (non-symbol-refusal-review
             (translation-review (001 corpus) non-symbol-refusal)))
      (1110
        (1110
          (001 non-symbol-module-is-invalid)
          (1110
            (translation-review-status invalid-module-review)
            (translation-review-code invalid-module-review))
          (001 (rejected invalid-module)))
        (1110
          (001 symbolic-refusal-is-recordable)
          (1110
            (translation-review-status symbol-refusal-review)
            (translation-review-code symbol-refusal-review))
          (001 (rejected translator-rejected)))
        (1110
          (001 non-symbol-refusal-is-invalid)
          (1110
            (translation-review-status non-symbol-refusal-review)
            (translation-review-code non-symbol-refusal-review))
          (001 (rejected invalid-rejection)))))))

(0011 translation-symbol-boundary-check
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (translation-symbol-boundary-witness (status pass))))
      ((010 rows) (1)
       (1110
         (001 translation-symbol-boundary-witness)
         (1110 (001 status) (001 fail))
         (1110 (001 case) (001 malformed-row-tail))
         (1110 (001 actual) rows)))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) (1)
            (translation-symbol-boundary-check (011 rows)))
           ((11110111 (1001 row) (10011 row)) (0)
            (1110
              (001 translation-symbol-boundary-witness)
              (1110 (001 status) (001 fail))
              (1110 (001 case) (100 row))
              (1110 (001 actual) (1001 row))
              (1110 (001 expected) (10011 row))))))))))

(0011 translation-symbol-boundary-witness
  (0010 ()
    (translation-symbol-boundary-check
      (translation-symbol-boundary-rows))))

(translation-symbol-boundary-witness)
