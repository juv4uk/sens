; #604 — regenerate encoder coverage from Lisp-owned derived machine coverage inputs.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(за-умовою
  ((encoder-coverage-index-valid?)
   ((функція ()
      (записати-файл
        "lib/machine/encoding/coverage.lisp"
        (encoder-coverage-render))
      (друкувати
        (список
          (як-є encoder-coverage-generate)
          (як-є (status written))
          (список (як-є forms) encoder-coverage-form-count)
          (список (як-є partial) (довжина encoder-coverage-partials)))))))
  (encoder-coverage-d1-yes
   (друкувати
     (перше (читати-всі "(encoder-coverage-generate (status rejected) (reason invalid-coverage-input-projection))")))))
