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
  (0010 (a b)
    (110
      ((010 a)
       (110
         ((010 b) (101 a b))
         ((010 (001 ())) (010 (001 (0))))))
      ((010 b) (010 (001 (0))))
      ((unify-equal? (100 a) (100 b))
       (unify-equal? (011 a) (011 b)))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 logic-var
  (0010 (name)
    (1110 (001 var) name)))

(0011 var?
  (0010 (term)
    (110
      ((010 term) (010 (001 (0))))
      ((010 (100 term))
       (110
         ((101 (100 term) (001 var)) (010 (001 ())))
         ((010 (001 ())) (010 (001 (0))))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 lookup-subst
  (0010 (variable bindings)
    (110
      ((0101 bindings) (001 ()))
      ((unify-equal? variable (100 (100 bindings)))
       (011 (100 bindings)))
      ((010 (001 ()))
       (lookup-subst variable (011 bindings))))))

(0011 extend-subst
  (0010 (variable term bindings)
    (111 (111 variable term) bindings)))

(0011 walk
  (0010 (term bindings)
    (walk-resolved (resolve-once term bindings) bindings)))

(0011 resolve-once
  (0010 (term bindings)
    (110
      ((var? term)
       (001000 ((found (lookup-subst term bindings)))
         (110
           ((0101 found) term)
           ((010 (001 ())) found))))
      ((010 (001 ())) term))))

(0011 walk-resolved
  (0010 (term bindings)
    (110
      ((var? term)
       (001000 ((found (lookup-subst term bindings)))
         (110
           ((0101 found) term)
           ((010 (001 ())) (walk-resolved found bindings)))))
      ((010 (001 ())) term))))

(0011 unify
  (0010 (a b bindings)
    (unify-walked (walk a bindings) (walk b bindings) bindings)))

(0011 failed-subst?
  (0010 (bindings)
    (110
      ((010 bindings) (101 bindings (001 fail)))
      (#d1:1 #d1:0))))

(0011 unify-walked
  (0010 (a b bindings)
    (110
      ((failed-subst? bindings) (001 fail))
      ((unify-equal? a b) bindings)
      ((var? a) (unify-var a b bindings))
      ((var? b) (unify-var b a bindings))
      ((010 a)
       (110
         ((010 b)
          (110 ((101 a b) bindings) ((010 (001 ())) (001 fail))))
         ((010 (001 ())) (001 fail))))
      ((010 b) (001 fail))
      ((010 (001 ()))
       (001000 ((car-b (unify-walked (100 a) (100 b) bindings)))
         (110
           ((failed-subst? car-b) (001 fail))
           ((010 (001 ()))
            (unify-walked (011 a) (011 b) car-b))))))))

(0011 occurs-check?
  (0010 (variable term bindings)
    (001000 ((resolved (walk term bindings)))
      (110
        ((unify-equal? variable resolved) (010 (001 ())))
        ((var? resolved) (010 (001 (0))))
        ((010 resolved) (010 (001 (0))))
        ((010 (001 ()))
         (110
           ((occurs-check? variable (100 resolved) bindings) (010 (001 ())))
           ((010 (001 ()))
            (occurs-check? variable (011 resolved) bindings))))))))

(0011 occurs-check occurs-check?)

(0011 unify-var
  (0010 (variable term bindings)
    (110
      ((occurs-check? variable term bindings) (001 fail))
      ((010 (001 ()))
       (extend-subst variable term bindings)))))

(0011 apply-subst
  (0010 (term bindings)
    (apply-subst-walked (walk term bindings) bindings)))

(0011 apply-subst-walked
  (0010 (term bindings)
    (110
      ((010 term) term)
      ((var? term) term)
      ((010 (001 ()))
       (111 (apply-subst-walked (100 term) bindings)
            (apply-subst-walked (011 term) bindings))))))

(0011 thread-conjunction
  (0010 (conditions state try-one)
    (110
      ((010 conditions) (1110 state))
      ((010 (001 ()))
       (thread-conjunction-branches
         (011 conditions)
         try-one
         (try-one (100 conditions) state))))))

(0011 thread-conjunction-branches
  (0010 (remaining try-one states)
    (110
      ((010 states) (001 ()))
      ((010 (001 ()))
       (1111 (thread-conjunction remaining (100 states) try-one)
             (thread-conjunction-branches remaining try-one (011 states)))))))
