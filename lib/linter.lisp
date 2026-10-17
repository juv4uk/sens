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
    (110
      ((010 (011 ast))
       (110
         ((010 (011 (011 ast))) (lint-head (100 ast)))
         ((010 (001 ())) (lint-short-head (100 ast)))))
      ((010 (001 ())) (100 ast)))))

(визначити lint-short-head
  (функція (head)
    (110
      ((0100 (010 head)) head)
      ((101 head 001) (001 quote))
      ((101 head 110) (001 cond))
      ((010 (001 ())) head))))

(визначити lint-head
  (функція (head)
    (110
      ((0100 (010 head)) head)
      ((101 head 0011) (001 def))
      ((101 head 0010) (001 lambda))
      ((101 head 110) (001 cond))
      ((101 head 001) (001 quote))
      ((101 head 001000) (001 let))
      ((101 head 001001) (001 let*))
      ((010 (001 ())) head))))

(визначити lint-max2
  (функція (a b)
    (110
      ((11011 a b) a)
      ((010 (001 ())) b))))

(визначити lint-size
  (функція (ast)
    (110
      ((010 ast) 1)
      ((010 (001 ()))
       (01010 1 (01010 (lint-size (100 ast)) (lint-size (011 ast))))))))

(визначити lint-nesting
  (функція (ast)
    (110
      ((010 ast) 0)
      ((010 (001 ()))
       (lint-max2 (01010 1 (lint-nesting (100 ast)))
                  (lint-nesting (011 ast)))))))

(визначити lint-complexity
  (функція (ast)
    (110
      ((010 ast) 0)
      ((110
         ((010 (lint-form-head ast))
          (101 (lint-form-head ast) (001 cond)))
         (#d1:1 #d1:0))
       (101110 (0010 (acc clause) (01010 acc (lint-complexity clause)))
               (000000 (011 ast))
               (011 ast)))
      ((010 (001 ()))
       (01010 (lint-complexity (100 ast))
              (lint-complexity (011 ast)))))))

(визначити effectful-primitives
  (001 ("print" "write-file" "process-run" "advise" "tell")))

(визначити lint-effects
  (функція (ast)
    (110
      ((010 ast) (001 ()))
      ((110101100 (100 ast))
       (110
         ((11101 (11101110 (100 ast)) effectful-primitives)
          (111 ast (lint-effects (011 ast))))
         ((010 (001 ()))
          (1111 (lint-effects (100 ast)) (lint-effects (011 ast))))))
      ((010 (001 ()))
       (1111 (lint-effects (100 ast)) (lint-effects (011 ast)))))))

(визначити collect-free-vars-let*
  (функція (ast bound-vars)
    (110
      ((0100 (010 (011 ast)))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 ast))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((0100 (010 (011 (011 ast))))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 (011 ast)))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (001 ()))
       (001000 ((bindings (100 (011 ast)))
              (body (100 (011 (011 ast)))))
         (110
           ((0101 bindings)
            (collect-free-vars body bound-vars))
           ((010 (001 ()))
            ((функція (binding)
               (1111
                (collect-free-vars (1001 binding) bound-vars)
                (collect-free-vars-let*
                  (1110 (001 let*) (011 bindings) body)
                  (111 (11101110 (100 binding)) bound-vars))))
             (100 bindings)))))))))

(визначити collect-free-vars-letrec
  (функція (ast bound-vars)
    (110
      ((0100 (010 (011 ast)))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 ast))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((0100 (010 (011 (011 ast))))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 (011 ast)))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars)))
      ((010 (001 ()))
       (001000 ((bindings (100 (011 ast)))
              (body (100 (011 (011 ast)))))
         (001000 ((all-names
                 (101000 (0010 (b) (11101110 (100 b))) bindings)))
           (001000 ((new-bound (1111 all-names bound-vars)))
             (1111
               (101110 append (001 ())
                       (101000 (0010 (b)
                              (collect-free-vars (1001 b) new-bound))
                            bindings))
               (collect-free-vars body new-bound)))))))))

(визначити collect-free-vars
  (функція (ast bound-vars)
    (110
      ((0100 (110111011 (010 ast)))
       (110
         ((110101100 ast)
          (110
            ((11101 (11101110 ast) bound-vars) (001 ()))
            ((11101 (11101110 ast)
                    (001 ("t" "def" "defmacro" "lambda" "let" "let*" "letrec"
                          "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom"
                          "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval")))
             (001 ()))
            ((010 (001 ())) (1110 ast))))))
      ((11110111 (lint-form-head ast) (001 quote)) (001 ()))
      ((11110111 (lint-form-head ast) (001 def))
       (collect-free-vars (100 (011 (011 ast))) bound-vars))
      ((11110111 (lint-form-head ast) (001 lambda))
       (001000 ((params (100 (011 ast)))
              (body (100 (011 (011 ast)))))
         (001000 ((param-names
                 (110
                   ((110101100 params) (1110 (11101110 params)))
                   ((010 (001 ()))
                    (101000 (0010 (p) (11101110 p)) params)))))
           (collect-free-vars body (1111 param-names bound-vars)))))
      ((11110111 (lint-form-head ast) (001 defmacro))
       (001000 ((params (100 (011 (011 ast))))
              (body (100 (011 (011 (011 ast))))))
         (001000 ((param-names
                 (110
                   ((110101100 params) (1110 (11101110 params)))
                   ((010 (001 ()))
                    (101000 (0010 (p) (11101110 p)) params)))))
           (collect-free-vars body (1111 param-names bound-vars)))))
      ((11110111 (lint-form-head ast) (001 let))
       (110
         ((0100 (110111011 (010 (011 ast))))
          (1111 (collect-free-vars (100 ast) bound-vars)
                (collect-free-vars (011 ast) bound-vars)))
         ((110101100 (100 (011 ast)))
          (001000 ((name (11101110 (100 (011 ast))))
                 (bindings (100 (011 (011 ast))))
                 (body (100 (011 (011 (011 ast))))))
            (001000 ((new-bound
                    (111 name
                         (1111 (101000 (0010 (b) (11101110 (100 b))) bindings)
                               bound-vars))))
              (1111 (101110 append (001 ())
                           (101000 (0010 (b)
                                  (collect-free-vars (1001 b) bound-vars))
                                bindings))
                      (collect-free-vars body new-bound)))))
         ((010 (001 ()))
          (001000 ((bindings (100 (011 ast)))
                 (body (100 (011 (011 ast)))))
            (001000 ((new-bound
                    (1111 (101000 (0010 (b) (11101110 (100 b))) bindings)
                          bound-vars)))
              (1111 (101110 append (001 ())
                           (101000 (0010 (b)
                                  (collect-free-vars (1001 b) bound-vars))
                                bindings))
                      (collect-free-vars body new-bound)))))))
      ((11110111 (lint-form-head ast) (001 let*))
       (collect-free-vars-let* ast bound-vars))
      ((11110111 (lint-form-head ast) (001 letrec))
       (collect-free-vars-letrec ast bound-vars))
      ((010 (001 ()))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars))))))

(визначити lint-globals
  (функція (ast)
    (101110
      (функція (unique item)
        (110
          ((11101 item unique) unique)
          ((010 (001 ())) (111 item unique))))
      (001 ())
      (collect-free-vars ast (001 ())))))

(визначити lint-all
  (функція (ast)
    (1110 (1110 (001 size) (lint-size ast))
          (1110 (001 nesting) (lint-nesting ast))
          (1110 (001 complexity) (lint-complexity ast))
          (1110 (001 effects) (lint-effects ast))
          (1110 (001 free-vars) (lint-globals ast)))))

(визначити get-threshold
  (функція (key thresholds default)
    (110
      ((0101 thresholds) default)
      ((11110111 (100 (100 thresholds)) key) (011 (100 thresholds)))
      ((010 (001 ())) (get-threshold key (011 thresholds) default)))))

(визначити lint-check
  (функція (ast thresholds)
    (001000 ((metrics (lint-all ast)))
      (001000 ((size (1001 (100 metrics)))
             (nesting (1001 (1001 metrics)))
             (complexity (1001 (10011 metrics)))
             (effects (1001 (100111 metrics)))
             (globals (1001 (110110101 metrics))))
        (1111
          (110 ((11011 size (get-threshold (001 max-size) thresholds 99999))
                (1110 (1110 (001 size-exceeded) size))))
          (1111
            (110 ((11011 nesting (get-threshold (001 max-nesting) thresholds 99999))
                  (1110 (1110 (001 nesting-exceeded) nesting))))
            (1111
              (110 ((11011 complexity (get-threshold (001 max-complexity) thresholds 99999))
                    (1110 (1110 (001 complexity-exceeded) complexity))))
              (1111
                (110 ((11011 (000000 globals) (get-threshold (001 max-globals) thresholds 99999))
                      (1110 (1110 (001 globals-exceeded) globals))))
                (110 ((11011 (000000 effects) (get-threshold (001 max-effects) thresholds 99999))
                      (1110 (1110 (001 effects-exceeded) effects)))))))))))))

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
