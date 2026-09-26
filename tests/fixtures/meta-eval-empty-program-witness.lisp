; #305 / TASK-001 — the empty metacircular program is a Lisp-owned law.
; An empty form list must preserve the supplied environment exactly and return
; Canon 0 as the program result.  Rust observes only the named pass envelope.

(load "lib/meta-eval.lisp")

(def meta-eval-empty-program-check
  (lambda ()
    (let ((env (list (cons (quote sentinel) 42))))
      (let ((loaded (my-eval-program (quote ()) env)))
        (cond
          ((equal? (car loaded) env) (1)
           (cond
             ((equal? (cdr loaded) (quote ())) (1)
              (quote (meta-eval-empty-program-witness (status pass))))
             ((equal? (cdr loaded) (quote ())) (0)
              (list
                (quote meta-eval-empty-program-witness)
                (quote (status fail))
                (quote (law empty-result))
                (list (quote actual) (cdr loaded))))))
          ((equal? (car loaded) env) (0)
           (list
             (quote meta-eval-empty-program-witness)
             (quote (status fail))
             (quote (law environment-preserved))
             (list (quote actual) (car loaded)))))))))

(meta-eval-empty-program-check)
