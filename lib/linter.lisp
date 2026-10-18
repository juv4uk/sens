; lib/linter.lisp — Linter for SENS ASTs.
; Analyzes size, nesting, complexity, globals, and effects.
; Exact migration: list-empty tests D8:11110111 EQUAL -> D4:0101 NULL;
; conditional head match D8:11110111 -> guarded D3:101 EQ.
; Only these proved narrower laws are substituted. Remaining D8 EQUAL calls
; retain their independent D8 identity; no universal SID8-to-D3 coercion.
; Exact D1 verdicts are 1 and 0; a pair is never passed to D3 EQ.
;
; Migrated: COND else (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. Full surface restored (no truncation).
; Semantic witness: tests/fixtures/linter-d1-witness.lisp

;; Голова форми для розпізнавання.
(визначити lint-form-head
  (функція (ast)
    (за-умовою
      ((атом? (решта ast))
       (за-умовою
         ((атом? (решта (решта ast))) (lint-head (перше ast)))
         ((атом? (як-є ())) (lint-short-head (перше ast)))))
      ((атом? (як-є ())) (перше ast)))))

(визначити lint-short-head
  (функція (head)
    (за-умовою
      ((хибне? (атом? head)) head)
      ((тотожне? head 001) (як-є quote))
      ((тотожне? head 110) (як-є cond))
      ((атом? (як-є ())) head))))

(визначити lint-head
  (функція (head)
    (за-умовою
      ((хибне? (атом? head)) head)
      ((тотожне? head 0011) (як-є def))
      ((тотожне? head 0010) (як-є lambda))
      ((тотожне? head 110) (як-є cond))
      ((тотожне? head 001) (як-є quote))
      ((тотожне? head 001000) (як-є let))
      ((тотожне? head 001001) (як-є let*))
      ((атом? (як-є ())) head))))

(визначити lint-max2
  (функція (a b)
    (за-умовою
      ((більше? a b) a)
      ((атом? (як-є ())) b))))

(визначити lint-size
  (функція (ast)
    (за-умовою
      ((атом? ast) 1)
      ((атом? (як-є ()))
       (додати 1 (додати (аналіз-розмір (перше ast)) (аналіз-розмір (решта ast))))))))

(визначити lint-nesting
  (функція (ast)
    (за-умовою
      ((атом? ast) 0)
      ((атом? (як-є ()))
       (lint-max2 (додати 1 (lint-nesting (перше ast)))
                  (lint-nesting (решта ast)))))))

(визначити lint-complexity
  (функція (ast)
    (за-умовою
      ((атом? ast) 0)
      ((за-умовою
         ((атом? (lint-form-head ast))
          (тотожне? (lint-form-head ast) (як-є cond)))
         (так ні))
       (згорнути (функція (acc clause) (додати acc (lint-complexity clause)))
               (довжина (решта ast))
               (решта ast)))
      ((атом? (як-є ()))
       (додати (lint-complexity (перше ast))
              (lint-complexity (решта ast)))))))

(визначити effectful-primitives
  (як-є ("print" "write-file" "process-run" "advise" "tell")))

(визначити lint-effects
  (функція (ast)
    (за-умовою
      ((атом? ast) (як-є ()))
      ((символ? (перше ast))
       (за-умовою
         ((значення-у-списку? (символ-у-текст (перше ast)) effectful-primitives)
          (сполучити ast (lint-effects (решта ast))))
         ((атом? (як-є ()))
          (приєднати (lint-effects (перше ast)) (lint-effects (решта ast))))))
      ((атом? (як-є ()))
       (приєднати (lint-effects (перше ast)) (lint-effects (решта ast)))))))

(визначити collect-free-vars-let*
  (функція (ast bound-vars)
    (за-умовою
      ((хибне? (атом? (решта ast)))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (решта ast))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((хибне? (атом? (решта (решта ast))))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (решта (решта ast)))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (як-є ()))
       (нехай ((bindings (перше (решта ast)))
              (body (перше (решта (решта ast)))))
         (за-умовою
           ((порожній? bindings)
            (collect-free-vars body bound-vars))
           ((атом? (як-є ()))
            ((функція (binding)
               (приєднати
                (collect-free-vars (друге binding) bound-vars)
                (зібрати-вільні-змінні-з-послідовного-зв'язування
                  (список (як-є let*) (решта bindings) body)
                  (сполучити (символ-у-текст (перше binding)) bound-vars))))
             (перше bindings)))))))))

(визначити collect-free-vars-letrec
  (функція (ast bound-vars)
    (за-умовою
      ((хибне? (атом? (решта ast)))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (решта ast))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((хибне? (атом? (решта (решта ast))))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (решта (решта ast)))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars)))
      ((атом? (як-є ()))
       (нехай ((bindings (перше (решта ast)))
              (body (перше (решта (решта ast)))))
         (нехай ((all-names
                 (відобразити (функція (b) (символ-у-текст (перше b))) bindings)))
           (нехай ((new-bound (приєднати all-names bound-vars)))
             (приєднати
               (згорнути append (як-є ())
                       (відобразити (функція (b)
                              (collect-free-vars (друге b) new-bound))
                            bindings))
               (collect-free-vars body new-bound)))))))))

(визначити collect-free-vars
  (функція (ast bound-vars)
    (за-умовою
      ((хибне? (відповідь-не (атом? ast)))
       (за-умовою
         ((символ? ast)
          (за-умовою
            ((значення-у-списку? (символ-у-текст ast) bound-vars) (як-є ()))
            ((значення-у-списку? (символ-у-текст ast)
                    (як-є ("t" "def" "defmacro" "lambda" "let" "let*" "letrec"
                          "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom"
                          "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval")))
             (як-є ()))
            ((атом? (як-є ())) (список ast))))))
      ((однакові? (lint-form-head ast) (як-є quote)) (як-є ()))
      ((однакові? (lint-form-head ast) (як-є def))
       (collect-free-vars (перше (решта (решта ast))) bound-vars))
      ((однакові? (lint-form-head ast) (як-є lambda))
       (нехай ((params (перше (решта ast)))
              (body (перше (решта (решта ast)))))
         (нехай ((param-names
                 (за-умовою
                   ((символ? params) (список (символ-у-текст params)))
                   ((атом? (як-є ()))
                    (відобразити (функція (p) (символ-у-текст p)) params)))))
           (collect-free-vars body (приєднати param-names bound-vars)))))
      ((однакові? (lint-form-head ast) (як-є defmacro))
       (нехай ((params (перше (решта (решта ast))))
              (body (перше (решта (решта (решта ast))))))
         (нехай ((param-names
                 (за-умовою
                   ((символ? params) (список (символ-у-текст params)))
                   ((атом? (як-є ()))
                    (відобразити (функція (p) (символ-у-текст p)) params)))))
           (collect-free-vars body (приєднати param-names bound-vars)))))
      ((однакові? (lint-form-head ast) (як-є let))
       (за-умовою
         ((хибне? (відповідь-не (атом? (решта ast))))
          (приєднати (collect-free-vars (перше ast) bound-vars)
                (collect-free-vars (решта ast) bound-vars)))
         ((символ? (перше (решта ast)))
          (нехай ((name (символ-у-текст (перше (решта ast))))
                 (bindings (перше (решта (решта ast))))
                 (body (перше (решта (решта (решта ast))))))
            (нехай ((new-bound
                    (сполучити name
                         (приєднати (відобразити (функція (b) (символ-у-текст (перше b))) bindings)
                               bound-vars))))
              (приєднати (згорнути append (як-є ())
                           (відобразити (функція (b)
                                  (collect-free-vars (друге b) bound-vars))
                                bindings))
                      (collect-free-vars body new-bound)))))
         ((атом? (як-є ()))
          (нехай ((bindings (перше (решта ast)))
                 (body (перше (решта (решта ast)))))
            (нехай ((new-bound
                    (приєднати (відобразити (функція (b) (символ-у-текст (перше b))) bindings)
                          bound-vars)))
              (приєднати (згорнути append (як-є ())
                           (відобразити (функція (b)
                                  (collect-free-vars (друге b) bound-vars))
                                bindings))
                      (collect-free-vars body new-bound)))))))
      ((однакові? (lint-form-head ast) (як-є let*))
       (зібрати-вільні-змінні-з-послідовного-зв'язування ast bound-vars))
      ((однакові? (lint-form-head ast) (як-є letrec))
       (зібрати-вільні-змінні-з-рекурсивного-зв'язування ast bound-vars))
      ((атом? (як-є ()))
       (приєднати (collect-free-vars (перше ast) bound-vars)
             (collect-free-vars (решта ast) bound-vars))))))

(визначити lint-globals
  (функція (ast)
    (згорнути
      (функція (unique item)
        (за-умовою
          ((значення-у-списку? item unique) unique)
          ((атом? (як-є ())) (сполучити item unique))))
      (як-є ())
      (collect-free-vars ast (як-є ())))))

(визначити lint-all
  (функція (ast)
    (список (список (як-є size) (аналіз-розмір ast))
          (список (як-є nesting) (lint-nesting ast))
          (список (як-є complexity) (lint-complexity ast))
          (список (як-є effects) (lint-effects ast))
          (список (як-є free-vars) (lint-globals ast)))))

(визначити get-threshold
  (функція (key thresholds default)
    (за-умовою
      ((порожній? thresholds) default)
      ((однакові? (перше (перше thresholds)) key) (решта (перше thresholds)))
      ((атом? (як-є ())) (get-threshold key (решта thresholds) default)))))

(визначити lint-check
  (функція (ast thresholds)
    (нехай ((metrics (lint-all ast)))
      (нехай ((size (друге (перше metrics)))
             (nesting (друге (друге metrics)))
             (complexity (друге (третє metrics)))
             (effects (друге (четверте metrics)))
             (globals (друге (п'ятий metrics))))
        (приєднати
          (за-умовою ((більше? size (get-threshold (як-є max-size) thresholds 99999))
                (список (список (як-є size-exceeded) size))))
          (приєднати
            (за-умовою ((більше? nesting (get-threshold (як-є max-nesting) thresholds 99999))
                  (список (список (як-є nesting-exceeded) nesting))))
            (приєднати
              (за-умовою ((більше? complexity (get-threshold (як-є max-complexity) thresholds 99999))
                    (список (список (як-є complexity-exceeded) complexity))))
              (приєднати
                (за-умовою ((більше? (довжина globals) (get-threshold (як-є max-globals) thresholds 99999))
                      (список (список (як-є globals-exceeded) globals))))
                (за-умовою ((більше? (довжина effects) (get-threshold (як-є max-effects) thresholds 99999))
                      (список (список (як-є effects-exceeded) effects))))))))))))

; D9: ratified lint functions harvested from their living SENS/Lisp owners.
; Exact nine-bit identity = lib/domains/d9.lisp; no new native opcodes.
; Existing closures carry semantics. Old donor names remain compatibility only.
; D9:001000111 аналіз-форма-голова
(визначити аналіз-форма-голова lint-form-head)
; D9:010011010 аналіз-голова
(визначити аналіз-голова lint-head)
; D9:010100100 аналіз-вкладеність
(визначити аналіз-вкладеність lint-nesting)
; D9:101000001 аналіз-складність
(визначити аналіз-складність lint-complexity)
; D9:010010010 аналіз-ефекти
(визначити аналіз-ефекти lint-effects)
; D9:010111111 зібрати-вільні-змінні
(визначити зібрати-вільні-змінні collect-free-vars)
; D9:001000011 аналіз-глобальні
(визначити аналіз-глобальні lint-globals)
; D9:010001110 аналіз-всі
(визначити аналіз-всі lint-all)
; D9:010000110 аналіз-перевірити
(визначити аналіз-перевірити lint-check)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити зібрати-вільні-змінні-з-послідовного-зв'язування collect-free-vars-let*)
(визначити зібрати-вільні-змінні-з-рекурсивного-зв'язування collect-free-vars-letrec)
(визначити аналіз-розмір lint-size)
