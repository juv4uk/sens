; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(визначити started (монотонний-наносекунди))
(визначити registry-text (читати-файл "lib/surface/semantic-registry.lisp"))
(визначити after-read (монотонний-наносекунди))
(визначити registry-form (перше (читати-всі registry-text)))
(визначити after-parse (монотонний-наносекунди))

(друкувати
  (список (як-є eco-lisp-script-perf/read-semantic-registry)
        (список (як-є read-file-ns) (відняти after-read started))
        (список (як-є read-all-ns) (відняти after-parse after-read))
        (список (як-є total-ns) (відняти after-parse started))
        (список (як-є root) (перше registry-form))))
