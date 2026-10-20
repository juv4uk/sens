; #771: focused Lisp-owned witness for post-core process loading and
; registry-driven peer identity. If lib/process.lisp cannot load under the
; current core, this fixture is never reached; the identity check then proves
; the stable Ukrainian peer was materialized from the same semantic ID.

(визначити process-load-witness
  (функція ()
    (за-умовою
      ((тотожне? process-run запустити-процес)
       (як-є (process-load-witness (status pass))))
      (так
       (як-є (process-load-witness (status fail)))))))

(process-load-witness)
