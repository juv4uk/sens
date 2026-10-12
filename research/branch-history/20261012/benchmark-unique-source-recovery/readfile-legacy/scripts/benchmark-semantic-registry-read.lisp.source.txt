; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(def started (mono-ns))
(def registry-text (read-file "lib/surface/semantic-registry.lisp"))
(def after-read (mono-ns))
(def registry-form (car (read-all registry-text)))
(def after-parse (mono-ns))

(print
  (list (quote eco-lisp-script-perf/read-semantic-registry)
        (list (quote read-file-ns) (- after-read started))
        (list (quote read-all-ns) (- after-parse after-read))
        (list (quote total-ns) (- after-parse started))
        (list (quote root) (car registry-form))))
