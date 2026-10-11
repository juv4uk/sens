; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(0011 started (01011010))
(0011 registry-text (110110111 "lib/surface/semantic-registry.lisp"))
(0011 after-read (01011010))
(0011 registry-form (100 (110101001 registry-text)))
(0011 after-parse (01011010))

(11011011
  (1110 (001 eco-lisp-script-perf/read-semantic-registry)
        (1110 (001 read-file-ns) (01011 after-read started))
        (1110 (001 read-all-ns) (01011 after-parse after-read))
        (1110 (001 total-ns) (01011 after-parse started))
        (1110 (001 root) (100 registry-form))))
