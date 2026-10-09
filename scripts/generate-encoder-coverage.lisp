; #604 — regenerate encoder coverage from Lisp-owned derived machine coverage inputs.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(110
  ((encoder-coverage-index-valid?)
   ((0010 ()
      (110111100
        "lib/machine/encoding/coverage.lisp"
        (encoder-coverage-render))
      (11011011
        (1110
          (001 encoder-coverage-generate)
          (001 (status written))
          (1110 (001 forms) encoder-coverage-form-count)
          (1110 (001 partial) (000000 encoder-coverage-partials)))))))
  (encoder-coverage-d1-yes
   (11011011
     (100 (110101001 "(encoder-coverage-generate (status rejected) (reason invalid-coverage-input-projection))")))))
