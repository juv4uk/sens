; A small symbolic-AI primitive: unification, the pattern-matching engine
; underneath backward-chaining/Prolog-style reasoning.
;
; Migrated: COND else / truth carriers (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. Failure remains atom fail as data.
; Reuses: var?, lookup-subst, walk, unify-walked, occurs-check, thread-conjunction.
; Semantic witness: tests/fixtures/unify-d1-witness.lisp
;
; Logic variables: (var name). occurs-check prevents infinite structures.

(0011 unify-equal?
  (функція (a b)
    (за-умовою
      ((атом? a)
       (за-умовою
         ((атом? b) (тотожне? a b))
         ((010 (001 ())) (010 (001 (0))))))
      ((010 b) (010 (001 (0))))
      ((unify-equal? (перше a) (перше b))
       (unify-equal? (решта a) (решта b)))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 logic-var
  (функція (name)
    (список (як-є var) name)))

(0011 var?
  (функція (term)
    (за-умовою
      ((010 term) (010 (001 (0))))
      ((атом? (перше term))
       (за-умовою
         ((тотожне? (перше term) (як-є var)) (атом? (як-є ())))
         ((010 (001 ())) (010 (001 (0))))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 lookup-subst
  (функція (variable bindings)
    (за-умовою
      ((порожній? bindings) (як-є ()))
      ((unify-equal? variable (перше (перше bindings)))
       (решта (перше bindings)))
      ((атом? (як-є ()))
       (lookup-subst variable (решта bindings))))))

(0011 extend-subst
  (функція (variable term bindings)
    (сполучити (сполучити variable term) bindings)))

(0011 walk
  (функція (term bindings)
    (walk-resolved (resolve-once term bindings) bindings)))

(0011 resolve-once
  (функція (term bindings)
    (за-умовою
      ((var? term)
       (001000 ((found (lookup-subst term bindings)))
         (за-умовою
           ((порожній? found) term)
           ((атом? (як-є ())) found))))
      ((атом? (як-є ())) term))))

(0011 walk-resolved
  (функція (term bindings)
    (за-умовою
      ((var? term)
       (001000 ((found (lookup-subst term bindings)))
         (за-умовою
           ((порожній? found) term)
           ((атом? (як-є ())) (walk-resolved found bindings)))))
      ((атом? (як-є ())) term))))

(0011 unify
  (функція (a b bindings)
    (unify-walked (walk a bindings) (walk b bindings) bindings)))

(0011 failed-subst?
  (функція (bindings)
    (за-умовою
      ((атом? bindings) (тотожне? bindings (як-є fail)))
      (#d1:1 #d1:0))))

(0011 unify-walked
  (функція (a b bindings)
    (за-умовою
      ((failed-subst? bindings) (як-є fail))
      ((unify-equal? a b) bindings)
      ((var? a) (unify-var a b bindings))
      ((var? b) (unify-var b a bindings))
      ((атом? a)
       (за-умовою
         ((атом? b)
          (за-умовою ((тотожне? a b) bindings) ((атом? (як-є ())) (як-є fail))))
         ((атом? (як-є ())) (як-є fail))))
      ((атом? b) (як-є fail))
      ((атом? (як-є ()))
       (001000 ((car-b (unify (100 a) (100 b) bindings)))
         (за-умовою
           ((failed-subst? car-b) (як-є fail))
           ((атом? (як-є ()))
            (unify (решта a) (решта b) car-b))))))))

(0011 occurs-check?
  (функція (variable term bindings)
    (001000 ((resolved (walk term bindings)))
      (за-умовою
        ((unify-equal? variable resolved) (атом? (як-є ())))
        ((var? resolved) (010 (001 (0))))
        ((010 resolved) (010 (001 (0))))
        ((атом? (як-є ()))
         (за-умовою
           ((occurs-check? variable (перше resolved) bindings) (атом? (як-є ())))
           ((атом? (як-є ()))
            (occurs-check? variable (решта resolved) bindings))))))))

(0011 occurs-check occurs-check?)

(0011 unify-var
  (функція (variable term bindings)
    (за-умовою
      ((occurs-check? variable term bindings) (як-є fail))
      ((атом? (як-є ()))
       (extend-subst variable term bindings)))))

(0011 apply-subst
  (функція (term bindings)
    (apply-subst-walked (walk term bindings) bindings)))

(0011 apply-subst-walked
  (функція (term bindings)
    (за-умовою
      ((атом? term) term)
      ((var? term) term)
      ((атом? (як-є ()))
       (сполучити (apply-subst (перше term) bindings)
            (apply-subst (решта term) bindings))))))

(0011 thread-conjunction
  (функція (conditions state try-one)
    (за-умовою
      ((атом? conditions) (список state))
      ((атом? (як-є ()))
       (thread-conjunction-branches
         (решта conditions)
         try-one
         (try-one (перше conditions) state))))))

(0011 thread-conjunction-branches
  (функція (remaining try-one states)
    (за-умовою
      ((атом? states) (як-є ()))
      ((атом? (як-є ()))
       (приєднати (thread-conjunction remaining (перше states) try-one)
             (thread-conjunction-branches remaining try-one (решта states)))))))
