; #305 / TASK-001 — the empty metacircular program is a Lisp-owned law.
; An empty form list must preserve the supplied environment exactly and return
; empty as the program result. Ukrainian projection only.

(load "lib/meta-eval.lisp")

(визначити meta-eval-empty-program-check
  (функція ()
    (нехай ((env-ref (список (сполучити (як-є sentinel) 42))))
      (нехай ((loaded (обчислити-послідовність-форм (як-є ()) env-ref)))
        (за-умовою
          ((тотожне? (перше loaded) env-ref)
           (за-умовою
             ((тотожне? (решта loaded) (як-є ()))
              (як-є (meta-eval-empty-program-witness (status pass))))
             (так
              (список
                (як-є meta-eval-empty-program-witness)
                (як-є (status fail))
                (як-є (law empty-result))
                (список (як-є actual) (решта loaded))))))
          (так
           (список
             (як-є meta-eval-empty-program-witness)
             (як-є (status fail))
             (як-є (law environment-preserved))
             (список (як-є actual) (перше loaded)))))))))

(meta-eval-empty-program-check)
