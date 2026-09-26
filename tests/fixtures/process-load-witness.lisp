; #771: focused Lisp-owned witness for post-core process loading and
; registry-driven peer identity. If lib/process.lisp cannot load under the
; current core, this fixture is never reached; the identity check then proves
; the stable Ukrainian peer was materialized from the same semantic ID.

(def process-load-witness
  (lambda ()
    (cond
      ((eq? process-run запустити-процес)
       (1)
       (quote (process-load-witness (status pass))))
      ((eq? process-run запустити-процес)
       (0)
       (quote (process-load-witness (status fail)))))))

(process-load-witness)
