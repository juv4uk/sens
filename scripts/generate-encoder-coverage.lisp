; #487 — regenerate encoder coverage with Lisp-owned policy.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(cond
  ((encoder-coverage-same? encoder-coverage-index-valid? t)
   ((lambda ()
      (write-file
        "lib/machine/encoding/coverage.lisp"
        (encoder-coverage-render))
      (print
        (list
          (quote encoder-coverage-generate)
          (quote (status written))
          (list (quote forms) encoder-coverage-form-count)
          (list (quote partial) (length encoder-coverage-partials)))))))
  (t
   (print
     (quote
       (encoder-coverage-generate
         (status rejected)
         (reason invalid-admitted-iclass-index))))))
