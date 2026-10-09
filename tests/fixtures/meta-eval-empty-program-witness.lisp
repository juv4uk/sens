; #305 / TASK-001 — the empty metacircular program is a Lisp-owned law.
; An empty form list must preserve the supplied environment exactly and return
; Canon 0 as the program result.  Rust observes only the named pass envelope.

(load "lib/meta-eval.lisp")

(00001001 meta-eval-empty-program-check
  (00001000 ()
    (10011100 ((env-ref (00100111 (00000100 (00000001 sentinel) 42))))
      (10011100 ((loaded (my-eval-program (00000001 ()) env-ref)))
        (00000111
          ((00100010 (00000101 loaded) env-ref)
           (00000111
             ((00100010 (00000110 loaded) (00000001 ()))
              (00000001 (meta-eval-empty-program-witness (status pass))))
             ((00100010
                (00100010 (00000110 loaded) (00000001 ()))
                (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
              (00100111
                (00000001 meta-eval-empty-program-witness)
                (00000001 (status fail))
                (00000001 (law empty-result))
                (00100111 (00000001 actual) (00000110 loaded))))))
          ((00100010
             (00100010 (00000101 loaded) env-ref)
             (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
           (00100111
             (00000001 meta-eval-empty-program-witness)
             (00000001 (status fail))
             (00000001 (law environment-preserved))
             (00100111 (00000001 actual) (00000101 loaded)))))))))

(meta-eval-empty-program-check)
