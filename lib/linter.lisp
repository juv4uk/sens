; lib/linter.lisp — Linter for my-lisp ASTs
; Analyzes size, nesting, complexity, globals, and effects.

;; Голова форми для розпізнавання. Лінтер обходить і хвости списків, тож
;; def/lambda/defmacro/let — лише коли у формі щонайменше три елементи;
;; коротші форми впізнаються тільки як quote/cond.
(0011 lint-form-head
  (0010 (ast)
    (110
      ((010 (011 ast)) 
       (110
         ((010 (011 (011 ast)))  (lint-head (100 ast)))
         ((010 ())  (lint-short-head (100 ast)))))
      ((010 ())  (100 ast)))))

(0011 lint-short-head
  (0010 (head)
    (110
      ; D3 EQ приймає лише атоми. Неатомарна голова — дані, без аварійного EQ.
      ((0100 (010 head)) head)
      ((101 head 001)  (001 quote))
      ((101 head 110)  (001 cond))
      ((010 ())  head))))

;; Точна міграція: D8 EQUAL (8 біт) → D3 EQ (3 біти) лише після
;; перевірки D3 ATOM / D4 NOT. Для Pair попередній fallback без змін.
;; Вісім головів-кандидатів заощаджують 8 × (8−3) = 40 біт у викликах;
;; охоронні D3/D4 голови додають 2 × (3+4) = 14 біт. Це лише підрахунок
;; кодів голів джерела (чистий 26 біт), НЕ фізична економія packed-файлу.
;; Класифікуємо AST за ратифікованою парою (домен, двійкове слово):
;; D3 QUOTE/COND, D4 DEFINE/LAMBDA, D6 LET/LET*. Довжина біта
;; належить домену; історичний 8-бітний код тут не є ідентичністю.
;; Складена макроформа не прирівнюється до окремого D5 MACRO.
(0011 lint-head
  (0010 (head)
    (110
      ; Неатоми не ототожнюємо з D3/D4/D6 координатами: вузька межа.
      ((0100 (010 head)) head)
      ((101 head 0011)  (001 def))
      ((101 head 0010)  (001 lambda))
      ((101 head 110)  (001 cond))
      ((101 head 001)  (001 quote))
      ((101 head 001000)  (001 let))
      ((101 head 001001)  (001 let*))
      ((010 ())  head))))

(0011 lint-max2
  (0010 (a b)
    (110
      ((11011 a b)  a)
      ((010 ()) b))))


; 1. Size: Total number of nodes (atoms + pairs)
(0011 lint-size
  (0010 (ast)
    (110
      
      ((010 ast)  1)
      ((010 ()) (01010 1 (01010 (lint-size (100 ast)) (lint-size (011 ast))))))))

; 2. Nesting: Maximum depth of pairs
(0011 lint-nesting
  (0010 (ast)
    (110
      
      ((010 ast)  0)
      ((010 ()) (lint-max2 (01010 1 (lint-nesting (100 ast)))
              (lint-nesting (011 ast)))))))

; 3. Complexity: Number of branching paths (cond clauses)
(0011 lint-complexity
  (0010 (ast)
    (110
      
      ((010 ast)  0)
      ((11110111 (lint-form-head ast) (001 cond))
       (101110 (0010 (acc clause) (01010 acc (lint-complexity clause)))
               (000000 (011 ast))
               (011 ast)))
      ((010 ()) (01010 (lint-complexity (100 ast))
            (lint-complexity (011 ast)))))))

; 4. Effects: Detect calls to side-effecting functions
(0011 effectful-primitives (001 ("print" "write-file" "process-run" "advise" "tell")))

(0011 lint-effects
  (0010 (ast)
    (110
      
      ((010 ast)  (001 ()))
      ((110101100 (100 ast))
       (110
         ((11101 (11101110 (100 ast)) effectful-primitives)
          (111 ast (lint-effects (011 ast))))
         ((010 ()) (1111 (lint-effects (100 ast)) (lint-effects (011 ast))))))
      ((010 ()) (1111 (lint-effects (100 ast)) (lint-effects (011 ast)))))))

; 5. Hidden globals: Identify free variables that are not explicitly passed as arguments
; (simplified: just collect all symbols used as variables that aren't in standard core)
; A true global dependency checker requires walking `let` and `lambda` bindings.
(0011 collect-free-vars-let*
  (0010 (ast bound-vars)
    (110
      ((0100 (010 (011 ast))) (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 ast))  (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((0100 (010 (011 (011 ast)))) (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 (011 ast)))  (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 ())
       (001000 ((bindings (100 (011 ast)))
             (body (100 (011 (011 ast)))))
         (110
           ((11110111 bindings (001 ()))
            (collect-free-vars body bound-vars))
           ((010 ())
            (001000 ((binding (100 bindings)))
              (1111
                (collect-free-vars (1001 binding) bound-vars)
                (collect-free-vars-let*
                  (1110 (001 let*) (011 bindings) body)
                  (111 (11101110 (100 binding))
                        bound-vars)))))))))))

(0011 collect-free-vars-letrec
  (0010 (ast bound-vars)
    (110
      ((0100 (010 (011 ast))) (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 ast))  (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((0100 (010 (011 (011 ast)))) (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 (011 (011 ast)))  (1111 (collect-free-vars (100 ast) bound-vars)
               (collect-free-vars (011 ast) bound-vars)))
      ((010 ())
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

(0011 collect-free-vars
  (0010 (ast bound-vars)
    (110
      ((0100 (110111011 (010 ast)))  (110
         ((110101100 ast)
          (110
            ((11101 (11101110 ast) bound-vars) (001 ()))
            ((11101 (11101110 ast) (001 ("t" "def" "defmacro" "lambda" "let" "let*" "letrec" "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom" "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval"))) (001 ()))
            ((010 ()) (1110 ast))))
         ))
      ((11110111 (lint-form-head ast) (001 quote)) (001 ()))
      ((11110111 (lint-form-head ast) (001 def))
       (collect-free-vars (100 (011 (011 ast))) bound-vars))
      ((11110111 (lint-form-head ast) (001 lambda))
       (001000 ((params (100 (011 ast)))
             (body (100 (011 (011 ast)))))
         (001000 ((param-names (110 ((110101100 params) (1110 (11101110 params)))
                                  ((010 ()) (101000 (0010 (p) (11101110 p)) params)))))
           (collect-free-vars body (1111 param-names bound-vars)))))
      ((11110111 (lint-form-head ast) (001 defmacro))
       (001000 ((params (100 (011 (011 ast))))
             (body (100 (011 (011 (011 ast))))))
         (001000 ((param-names (110 ((110101100 params) (1110 (11101110 params)))
                                  ((010 ()) (101000 (0010 (p) (11101110 p)) params)))))
           (collect-free-vars body (1111 param-names bound-vars)))))
      ((11110111 (lint-form-head ast) (001 let))
       (110
         ((0100 (110111011 (010 (011 ast))))  (1111 (collect-free-vars (100 ast) bound-vars)
                  (collect-free-vars (011 ast) bound-vars)))
         ((110101100 (100 (011 ast)))
          ; Named let
          (001000 ((name (11101110 (100 (011 ast))))
                (bindings (100 (011 (011 ast))))
                (body (100 (011 (011 (011 ast))))))
            (001000 ((new-bound (111 name (1111 (101000 (0010 (b) (11101110 (100 b))) bindings) bound-vars))))
              (1111 (101110 append (001 ()) (101000 (0010 (b) (collect-free-vars (1001 b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))
         ((010 ())
          ; Basic let
          (001000 ((bindings (100 (011 ast)))
                (body (100 (011 (011 ast)))))
            (001000 ((new-bound (1111 (101000 (0010 (b) (11101110 (100 b))) bindings) bound-vars)))
              (1111 (101110 append (001 ()) (101000 (0010 (b) (collect-free-vars (1001 b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))))
      ((11110111 (lint-form-head ast) (001 let*))
       (collect-free-vars-let* ast bound-vars))
      ((11110111 (lint-form-head ast) (001 letrec))
       (collect-free-vars-letrec ast bound-vars))
      ((010 ()) (1111 (collect-free-vars (100 ast) bound-vars)
                 (collect-free-vars (011 ast) bound-vars))))))

(0011 lint-globals
  (0010 (ast)
    (101110
      (0010 (unique item)
        (110
          ((11101 item unique) unique)
          ((010 ()) (111 item unique))))
      (001 ())
      (collect-free-vars ast (001 ())))))

(0011 lint-all
  (0010 (ast)
    (1110 (1110 (001 size) (lint-size ast))
          (1110 (001 nesting) (lint-nesting ast))
          (1110 (001 complexity) (lint-complexity ast))
          (1110 (001 effects) (lint-effects ast))
          (1110 (001 free-vars) (lint-globals ast)))))

(0011 get-threshold
  (0010 (key thresholds default)
    (110
      ((11110111 thresholds (001 ())) default)
      ((11110111 (100 (100 thresholds)) key) (011 (100 thresholds)))
      ((010 ()) (get-threshold key (011 thresholds) default)))))

(0011 lint-check
  (0010 (ast thresholds)
    (001000 ((metrics (lint-all ast)))
      (001000 ((size (1001 (100 metrics)))
            (nesting (1001 (1001 metrics)))
            (complexity (1001 (10011 metrics)))
            (effects (1001 (100111 metrics)))
            (globals (1001 (110110101 metrics))))
        (1111
          (110 ((11011 size (get-threshold (001 max-size) thresholds 99999)) 
                 (1110 (1110 (001 size-exceeded) size))) )
          (1111
            (110 ((11011 nesting (get-threshold (001 max-nesting) thresholds 99999)) 
                   (1110 (1110 (001 nesting-exceeded) nesting))) )
            (1111
              (110 ((11011 complexity (get-threshold (001 max-complexity) thresholds 99999)) 
                     (1110 (1110 (001 complexity-exceeded) complexity))) )
              (1111
                (110 ((11011 (000000 globals) (get-threshold (001 max-globals) thresholds 99999)) 
                       (1110 (1110 (001 globals-exceeded) globals))) )
                (110 ((11011 (000000 effects) (get-threshold (001 max-effects) thresholds 99999)) 
                       (1110 (1110 (001 effects-exceeded) effects))) )))))))))
