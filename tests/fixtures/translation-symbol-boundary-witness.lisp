; #369 — external translation decisions must survive the symbol? result-domain
; migration without preserving the historical t/() predicate sentinel.
; Ukrainian projection only.

(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/forward.lisp")
(load "lib/knowledge.lisp")
(load "lib/result-status.lisp")
(load "lib/translation.lisp")

(визначити translation-symbol-boundary-rows
  (функція ()
    (нехай ((symbol-refusal
             (як-є
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 unsupported-translation)))
           (non-symbol-refusal
             (як-є
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 42)))
           (invalid-module-review
             (translation-review 42 symbol-refusal))
           (symbol-refusal-review
             (translation-review (як-є corpus) symbol-refusal))
           (non-symbol-refusal-review
             (translation-review (як-є corpus) non-symbol-refusal)))
      (список
        (список
          (як-є non-symbol-module-is-invalid)
          (список
            (translation-review-status invalid-module-review)
            (translation-review-code invalid-module-review))
          (як-є (rejected invalid-module)))
        (список
          (як-є symbolic-refusal-is-recordable)
          (список
            (translation-review-status symbol-refusal-review)
            (translation-review-code symbol-refusal-review))
          (як-є (rejected translator-rejected)))
        (список
          (як-є non-symbol-refusal-is-invalid)
          (список
            (translation-review-status non-symbol-refusal-review)
            (translation-review-code non-symbol-refusal-review))
          (як-є (rejected invalid-rejection)))))))

(визначити translation-symbol-boundary-check
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (translation-symbol-boundary-witness (status pass))))
      (так
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (друге row) (третє row))
            (translation-symbol-boundary-check (решта rows)))
           (так
            (список
              (як-є translation-symbol-boundary-witness)
              (список (як-є status) (як-є fail))
              (список (як-є case) (перше row))
              (список (як-є actual) (друге row))
              (список (як-є expected) (третє row))))))))))

(визначити translation-symbol-boundary-witness
  (функція ()
    (translation-symbol-boundary-check
      (translation-symbol-boundary-rows))))

(translation-symbol-boundary-witness)
