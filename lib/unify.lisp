; A small symbolic-AI primitive: unification, the pattern-matching engine
; underneath backward-chaining/Prolog-style reasoning.
;
; Migrated: COND else / truth carriers (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. Failure remains atom fail as data.
; Reuses: var?, lookup-subst, walk, unify-walked, occurs-check, thread-conjunction.
; Semantic witness: tests/fixtures/unify-d1-witness.lisp
;
; Logic variables: (var name). occurs-check prevents infinite structures.

(визначити unify-equal?
  (функція (a b)
    (за-умовою
      ((атом? a)
       (за-умовою
         ((атом? b) (тотожне? a b))
         ((атом? (як-є ())) (атом? (як-є (ні))))))
      ((атом? b) (атом? (як-є (ні))))
      ((unify-equal? (перше a) (перше b))
       (unify-equal? (решта a) (решта b)))
      ((атом? (як-є ())) (атом? (як-є (ні)))))))

(визначити logic-var
  (функція (name)
    (список (як-є var) name)))

(визначити var?
  (функція (term)
    (за-умовою
      ((атом? term) (атом? (як-є (ні))))
      ((атом? (перше term))
       (за-умовою
         ((тотожне? (перше term) (як-є var)) (атом? (як-є ())))
         ((атом? (як-є ())) (атом? (як-є (ні))))))
      ((атом? (як-є ())) (атом? (як-є (ні)))))))

(визначити lookup-subst
  (функція (variable bindings)
    (за-умовою
      ((порожній? bindings) (як-є ()))
      ((unify-equal? variable (перше (перше bindings)))
       (решта (перше bindings)))
      ((атом? (як-є ()))
       (отримати-значення-з-підстановки variable (решта bindings))))))

(визначити extend-subst
  (функція (variable term bindings)
    (сполучити (сполучити variable term) bindings)))

(визначити walk
  (функція (term bindings)
    (обійти-розв'язаний (resolve-once term bindings) bindings)))

(визначити resolve-once
  (функція (term bindings)
    (за-умовою
      ((змінна? term)
       (нехай ((found (отримати-значення-з-підстановки term bindings)))
         (за-умовою
           ((порожній? found) term)
           ((атом? (як-є ())) found))))
      ((атом? (як-є ())) term))))

(визначити walk-resolved
  (функція (term bindings)
    (за-умовою
      ((змінна? term)
       (нехай ((found (отримати-значення-з-підстановки term bindings)))
         (за-умовою
           ((порожній? found) term)
           ((атом? (як-є ())) (обійти-розв'язаний found bindings)))))
      ((атом? (як-є ())) term))))

(визначити unify
  (функція (a b bindings)
    (уніфікувати-обійдений (пройти a bindings) (пройти b bindings) bindings)))

(визначити failed-subst?
  (функція (bindings)
    (за-умовою
      ((атом? bindings) (тотожне? bindings (як-є fail)))
      (так ні))))

(визначити unify-walked
  (функція (a b bindings)
    (за-умовою
      ((підстановка-позначає-невдачу? bindings) (як-є fail))
      ((unify-equal? a b) bindings)
      ((змінна? a) (уніфікувати-змінна a b bindings))
      ((змінна? b) (уніфікувати-змінна b a bindings))
      ((атом? a)
       (за-умовою
         ((атом? b)
          (за-умовою ((тотожне? a b) bindings) ((атом? (як-є ())) (як-є fail))))
         ((атом? (як-є ())) (як-є fail))))
      ((атом? b) (як-є fail))
      ((атом? (як-є ()))
       (нехай ((car-b (уніфікувати (перше a) (перше b) bindings)))
         (за-умовою
           ((підстановка-позначає-невдачу? car-b) (як-є fail))
           ((атом? (як-є ()))
            (уніфікувати (решта a) (решта b) car-b))))))))

(визначити occurs-check?
  (функція (variable term bindings)
    (нехай ((resolved (пройти term bindings)))
      (за-умовою
        ((unify-equal? variable resolved) (атом? (як-є ())))
        ((змінна? resolved) (атом? (як-є (ні))))
        ((атом? resolved) (атом? (як-є (ні))))
        ((атом? (як-є ()))
         (за-умовою
           ((входить-перевірити? variable (перше resolved) bindings) (атом? (як-є ())))
           ((атом? (як-є ()))
            (входить-перевірити? variable (решта resolved) bindings))))))))

(визначити occurs-check входить-перевірити?)

(визначити unify-var
  (функція (variable term bindings)
    (за-умовою
      ((входить-перевірити? variable term bindings) (як-є fail))
      ((атом? (як-є ()))
       (extend-subst variable term bindings)))))

(визначити apply-subst
  (функція (term bindings)
    (apply-subst-walked (пройти term bindings) bindings)))

(визначити apply-subst-walked
  (функція (term bindings)
    (за-умовою
      ((атом? term) term)
      ((змінна? term) term)
      ((атом? (як-є ()))
       (сполучити (застосувати-підстановка (перше term) bindings)
            (застосувати-підстановка (решта term) bindings))))))

(визначити thread-conjunction
  (функція (conditions state try-one)
    (за-умовою
      ((атом? conditions) (список state))
      ((атом? (як-є ()))
       (потік-виконання-кон'юнкція-гілки
         (решта conditions)
         try-one
         (try-one (перше conditions) state))))))

(визначити thread-conjunction-branches
  (функція (remaining try-one states)
    (за-умовою
      ((атом? states) (як-є ()))
      ((атом? (як-є ()))
       (приєднати (потік-виконання-кон'юнкція remaining (перше states) try-one)
             (потік-виконання-кон'юнкція-гілки remaining try-one (решта states)))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити застосувати-підстановка apply-subst)
(визначити підстановка-позначає-невдачу? failed-subst?)
(визначити отримати-значення-з-підстановки lookup-subst)
(визначити входить-перевірити? occurs-check?)
(визначити потік-виконання-кон'юнкція thread-conjunction)
(визначити потік-виконання-кон'юнкція-гілки thread-conjunction-branches)
(визначити уніфікувати unify)
(визначити уніфікувати-змінна unify-var)
(визначити уніфікувати-обійдений unify-walked)
(визначити змінна? var?)
(визначити пройти walk)
(визначити обійти-розв'язаний walk-resolved)
