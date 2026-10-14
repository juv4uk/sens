; A small symbolic-AI primitive: unification, the pattern-matching engine
; underneath backward-chaining/Prolog-style reasoning — the kind of symbolic
; inference McCarthy's 1958 "Advice Taker" proposal was written for, before
; Lisp itself even existed to build it in.
;
; Logic variables are represented as `(var name)` — a two-element list, not
; a bare symbol — because `eq` only accepts atoms, and there is no
; symbol?/numberp? primitive to ask "is this atom a variable by naming
; convention" (see lib/meta-eval.lisp's header comment for the same
; constraint solved a different way). `(var name)` sidesteps it: `var?`
; checks `(eq (car term) 'var)`, always atom-safe; two variables compare by
; `(equal? (second a) (second b))`, comparing their names, which might be
; symbols or structured pairs (like `(x . 3)` when standardizing apart).
; Construct one with `(logic-var 'x)`.
;
; With occurs-check: unifying `?x` with a term containing `?x` (e.g. `(f ?x)`)
; correctly fails, preventing infinite structures from being generated and
; preserving the engine's stability during complex logic inference.
;
; Невеликий примітив символьного AI: unification — механізм зіставлення з
; шаблоном, що лежить під backward-chaining/Prolog-подібними міркуваннями —
; той самий вид символьного висновування, для якого писалась пропозиція
; "Advice Taker" Маккарті 1958 року, ще до появи самого Lisp, яким її можна
; було б побудувати.
;
; Reasoning-local structural equality with exact D1 result.
; It deliberately avoids the legacy Core equal? result carrier while the
; separate Core PredicateBit cutover remains evidence-gated.
;
; Migrated: COND else / truth carriers (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. Failure remains atom fail as data. Reuses 2000+ surface:
; var?, lookup-subst, unify-walked, occurs-check, thread-conjunction.
; Semantic witness: tests/fixtures/unify-d1-witness.lisp

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
      ((010 (100 term)) (010 (001 (0))))
      ((101 (100 term) (001 var)) (010 (001 ())))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 lookup-subst
  (0010 (variable bindings)
    (110
      ((0101 bindings) (001 ()))
      ((101 variable (100 (100 bindings)))
       (011 (100 bindings)))
      ((010 (001 ()))
       (lookup-subst variable (011 bindings))))))

(0011 resolve
  (0010 (term bindings)
    (110
      ((var? term)
       (001000 ((found (lookup-subst term bindings)))
         (110
           ((0101 found) term)
           ((010 (001 ())) found))))
      ((010 (001 ())) term))))

(0011 resolve-deep
  (0010 (term bindings)
    (001000 ((resolved (resolve term bindings)))
      (110
        ((var? resolved) resolved)
        ((010 resolved) resolved)
        ((010 (001 ()))
         (101110100 resolved bindings))))))

(0011 unify
  (0010 (a b bindings)
    (unify-walked (resolve a bindings) (resolve b bindings) bindings)))

(0011 unify-walked
  (0010 (a b bindings)
    (110
      ((101 a b) bindings)
      ((var? a) (bind-var a b bindings))
      ((var? b) (bind-var b a bindings))
      ((010 a)
       (110
         ((010 b)
          (110
            ((101 a b) bindings)
            ((010 (001 ())) (001 fail))))
         ((010 (001 ())) (001 fail))))
      ((010 b) (001 fail))
      ((010 (001 ()))
       (001000 ((car-bindings (unify-walked (100 a) (100 b) bindings)))
         (110
           ((101 car-bindings (001 fail)) (001 fail))
           ((010 (001 ()))
            (unify-walked (011 a) (011 b) car-bindings))))))))

(0011 occurs-check
  (0010 (variable term bindings)
    (001000 ((resolved (resolve term bindings)))
      (110
        ((101 variable resolved) (010 (001 ())))
        ((var? resolved) (010 (001 (0))))
        ((010 resolved) (010 (001 (0))))
        ((010 (001 ()))
         (110
           ((occurs-check variable (100 resolved) bindings) (010 (001 ())))
           ((010 (001 ()))
            (occurs-check variable (011 resolved) bindings))))))))

(0011 bind-var
  (0010 (variable term bindings)
    (110
      ((occurs-check variable term bindings) (001 fail))
      ((010 (001 ()))
       (111 (111 variable term) bindings)))))

(0011 extend-subst
  (0010 (variable term bindings)
    (111 (111 variable term) bindings)))

(0011 apply-subst
  (0010 (term bindings)
    (001000 ((resolved (resolve term bindings)))
      (110
        ((010 resolved) resolved)
        ((var? resolved) resolved)
        ((010 (001 ()))
         (111 (apply-subst (100 resolved) bindings)
              (apply-subst (011 resolved) bindings)))))))

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
