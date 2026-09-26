; #771: focused Lisp-owned witness for post-core process loading and
; registry-driven peer identity. If lib/process.lisp cannot load under the
; current core, this fixture is never reached; the identity check then proves
; the stable Ukrainian peer was materialized from the same semantic ID.

(00001001 process-load-witness
  (00001000 ()
    (00000111
      ((00000011 process-run запустити-процес)
       (1)
       (00000001 (process-load-witness (status pass))))
      ((00000011 process-run запустити-процес)
       (0)
       (00000001 (process-load-witness (status fail)))))))

(process-load-witness)
