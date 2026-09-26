; #74 real workload harvested from #76 Python -> my-lisp migration.
; Measure the exact heavy phase profiled in PR #317, but split it into the
; public Lisp-owned read-file path and read-all parser phase. Do not call
; core.lisp's recursive string-length here: on a registry-sized String that is
; a separate non-tail recursion benchmark and can overflow the host stack.

(00001001 started (01011010))
(00001001 registry-text (10100110 "lib/surface/semantic-registry.lisp"))
(00001001 after-read (01011010))
(00001001 registry-form (00000101 (01001011 registry-text)))
(00001001 after-parse (01011010))

(01001000
  (00100111 (00000001 eco-lisp-script-perf/read-semantic-registry)
        (00100111 (00000001 read-file-ns) (00001101 after-read started))
        (00100111 (00000001 read-all-ns) (00001101 after-parse after-read))
        (00100111 (00000001 total-ns) (00001101 after-parse started))
        (00100111 (00000001 root) (00000101 registry-form))))
