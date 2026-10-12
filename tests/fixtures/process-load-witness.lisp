; #771: focused Lisp-owned witness for post-core process loading and
; registry-driven peer identity. If lib/process.lisp cannot load under the
; current core, this fixture is never reached; the identity check then proves
; the stable Ukrainian peer was materialized from the same semantic ID.

(0011 process-load-witness
  (0010 ()
    (110
      ((101 process-run запустити-процес)
       (1)
       (001 (process-load-witness (status pass))))
      ((101 process-run запустити-процес)
       (0)
       (001 (process-load-witness (status fail)))))))

(process-load-witness)
