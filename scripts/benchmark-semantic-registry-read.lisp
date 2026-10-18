; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(визначити started (01011010))
(визначити registry-text (110110111 "lib/surface/semantic-registry.lisp"))
(визначити after-read (01011010))
(визначити registry-form (перше (110101001 registry-text)))
(визначити after-parse (01011010))

(11011011
  (список (як-є eco-lisp-script-perf/read-semantic-registry)
        (список (як-є read-file-ns) (01011 after-read started))
        (список (як-є read-all-ns) (01011 after-parse after-read))
        (список (як-є total-ns) (01011 after-parse started))
        (список (як-є root) (перше registry-form))))
