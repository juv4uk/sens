; #369 — external translation boundary outcomes are preserved as Lisp-owned
; evidence before the historical symbol? producer is retired.
;
; These rows cover the public boundary cases:
;   non-symbol module name -> rejected/invalid-module
;   symbolic translator refusal -> rejected/translator-rejected
;   non-symbol refusal payload -> rejected/invalid-rejection

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
      ((atom rows) t)
      ((equal? (second (car rows)) (third (car rows)))
       (translation-symbol-boundary-check (cdr rows)))
      (t
       (list
         (quote translation-symbol-boundary-witness)
         (list (quote status) (quote fail))
         (list (quote case) (car (car rows)))
         (list (quote actual) (second (car rows)))
         (list (quote expected) (third (car rows))))))))

(def translation-symbol-boundary-witness
  (lambda ()
    (translation-symbol-boundary-check
      (translation-symbol-boundary-rows))))

(cond
  ((equal? (translation-symbol-boundary-witness)
            (quote ())))
  (t
   (translation-symbol-boundary-witness)))
