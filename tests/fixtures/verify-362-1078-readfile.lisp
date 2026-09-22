; Verification-only witness for #362/#1125 as blocker of #1078.
; This is intentionally NOT mechanism-selector semantic evidence. It isolates
; the exact hot prefix that timed out before #1078 could execute its witness.

(def verify-362-registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def verify-362-mechanisms
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(quote (verify-362-1078-readfile (status pass)))
