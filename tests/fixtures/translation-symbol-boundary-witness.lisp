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

(def translation-symbol-boundary-rows
  (lambda ()
    (let* ((symbol-refusal
             (quote
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 unsupported-translation)))
           (non-symbol-refusal
             (quote
               (translation/1 rejected clause
                 "Colorless green ideas sleep furiously."
                 42)))
           (invalid-module-review
             (translation-review 42 symbol-refusal))
           (symbol-refusal-review
             (translation-review (quote corpus) symbol-refusal))
           (non-symbol-refusal-review
             (translation-review (quote corpus) non-symbol-refusal)))
      (list
        (list
          (quote non-symbol-module-is-invalid)
          (list
            (translation-review-status invalid-module-review)
            (translation-review-code invalid-module-review))
          (quote (rejected invalid-module)))
        (list
          (quote symbolic-refusal-is-recordable)
          (list
            (translation-review-status symbol-refusal-review)
            (translation-review-code symbol-refusal-review))
          (quote (rejected translator-rejected)))
        (list
          (quote non-symbol-refusal-is-invalid)
          (list
            (translation-review-status non-symbol-refusal-review)
            (translation-review-code non-symbol-refusal-review))
          (quote (rejected invalid-rejection)))))))

(def translation-symbol-boundary-check
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (translation-symbol-boundary-witness (status pass))))
      ((atom rows) (structural-kind atom)
       (list
         (quote translation-symbol-boundary-witness)
         (list (quote status) (quote fail))
         (list (quote case) (quote malformed-row-tail))
         (list (quote actual) rows)))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (translation-symbol-boundary-check (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (list
              (quote translation-symbol-boundary-witness)
              (list (quote status) (quote fail))
              (list (quote case) (car row))
              (list (quote actual) (second row))
              (list (quote expected) (third row))))))))))

(def translation-symbol-boundary-witness
  (lambda ()
    (translation-symbol-boundary-check
      (translation-symbol-boundary-rows))))

(translation-symbol-boundary-witness)
