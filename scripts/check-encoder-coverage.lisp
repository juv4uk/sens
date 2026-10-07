; #604 temporary shape probe: raw first coverage row, no predicate calls.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(def encoder-coverage-first-coverage-row
  (car (cdr (cdr (cdr encoder-coverage-committed-form)))))

(list
  (quote encoder-coverage-first-row-shape)
  (list (quote raw) encoder-coverage-first-coverage-row)
  (list (quote first) (car encoder-coverage-first-coverage-row))
  (list (quote second) (second encoder-coverage-first-coverage-row))
  (list (quote second-car) (car (second encoder-coverage-first-coverage-row)))
  (list (quote second-second) (second (second encoder-coverage-first-coverage-row)))
  (list (quote third) (third encoder-coverage-first-coverage-row))
  (list (quote fourth) (fourth encoder-coverage-first-coverage-row))
  (list (quote fifth) (fifth encoder-coverage-first-coverage-row)))
