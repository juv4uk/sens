; lib/linter.lisp — Linter for my-lisp ASTs
; Analyzes size, nesting, complexity, globals, and effects.

;; Голова форми для розпізнавання. Лінтер обходить і хвости списків, тож
;; def/lambda/defmacro/let — лише коли у формі щонайменше три елементи;
;; коротші форми впізнаються тільки як quote/cond.
(00001001 lint-form-head
  (00001000 (ast)
    (00000111
      ((00000010 (00000110 ast)) 
       (00000111
         ((00000010 (00000110 (00000110 ast)))  (lint-head (00000101 ast)))
         (t  (lint-short-head (00000101 ast)))))
      (t  (00000101 ast)))))

(00001001 lint-short-head
  (00001000 (head)
    (00000111
      ((00100010 head 00000001)  (00000001 quote))
      ((00100010 head 00000111)  (00000001 cond))
      (t  head))))

;; Голова форми: код СЕНС -> та сама форма, що й за назвою. Лінтер
;; розпізнає def/lambda/cond/... і тоді, коли код записано кодами СЕНС.
(00001001 lint-head
  (00001000 (head)
    (00000111
      ((00100010 head 00001001)  (00000001 def))
      ((00100010 head 00001011)  (00000001 def))
      ((00100010 head 00001000)  (00000001 lambda))
      ((00100010 head 00000111)  (00000001 cond))
      ((00100010 head 00000001)  (00000001 quote))
      ((00100010 head 00001010)  (00000001 defmacro))
      ((00100010 head 10011100)  (00000001 let))
      ((00100010 head 10011101)  (00000001 let*))
      (t  head))))

(00001001 lint-max2
  (00001000 (a b)
    (00000111
      ((00011011 a b)  a)
      (t b))))


; 1. Size: Total number of nodes (atoms + pairs)
(00001001 lint-size
  (00001000 (ast)
    (00000111
      
      ((00000010 ast)  1)
      (t (00001100 1 (00001100 (lint-size (00000101 ast)) (lint-size (00000110 ast))))))))

; 2. Nesting: Maximum depth of pairs
(00001001 lint-nesting
  (00001000 (ast)
    (00000111
      
      ((00000010 ast)  0)
      (t (lint-max2 (00001100 1 (lint-nesting (00000101 ast)))
              (lint-nesting (00000110 ast)))))))

; 3. Complexity: Number of branching paths (cond clauses)
(00001001 lint-complexity
  (00001000 (ast)
    (00000111
      
      ((00000010 ast)  0)
      ((00100010 (lint-form-head ast) (00000001 cond))
       (00111001 (00001000 (acc clause) (00001100 acc (lint-complexity clause)))
               (00101000 (00000110 ast))
               (00000110 ast)))
      (t (00001100 (lint-complexity (00000101 ast))
            (lint-complexity (00000110 ast)))))))

; 4. Effects: Detect calls to side-effecting functions
(00001001 effectful-primitives (00000001 ("print" "write-file" "process-run" "advise" "tell")))

(00001001 lint-effects
  (00001000 (ast)
    (00000111
      
      ((00000010 ast)  (00000001 ()))
      ((00100011 (00000101 ast))
       (00000111
         ((00101100 (01000010 (00000101 ast)) effectful-primitives)
          (00000100 ast (lint-effects (00000110 ast))))
         (t (00101001 (lint-effects (00000101 ast)) (lint-effects (00000110 ast))))))
      (t (00101001 (lint-effects (00000101 ast)) (lint-effects (00000110 ast)))))))

; 5. Hidden globals: Identify free variables that are not explicitly passed as arguments
; (simplified: just collect all symbols used as variables that aren't in standard core)
; A true global dependency checker requires walking `let` and `lambda` bindings.
(00001001 collect-free-vars-let*
  (00001000 (ast bound-vars)
    (00000111
      ((0100 (00000010 (00000110 ast))) (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((00000010 (00000110 ast))  (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((0100 (00000010 (00000110 (00000110 ast)))) (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((00000010 (00000110 (00000110 ast)))  (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      (t
       (10011100 ((bindings (00000101 (00000110 ast)))
             (body (00000101 (00000110 (00000110 ast)))))
         (00000111
           ((00100010 bindings (00000001 ()))
            (collect-free-vars body bound-vars))
           (t
            (10011100 ((binding (00000101 bindings)))
              (00101001
                (collect-free-vars (00101111 binding) bound-vars)
                (collect-free-vars-let*
                  (00100111 (00000001 let*) (00000110 bindings) body)
                  (00000100 (01000010 (00000101 binding))
                        bound-vars)))))))))))

(00001001 collect-free-vars-letrec
  (00001000 (ast bound-vars)
    (00000111
      ((0100 (00000010 (00000110 ast))) (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((00000010 (00000110 ast))  (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((0100 (00000010 (00000110 (00000110 ast)))) (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      ((00000010 (00000110 (00000110 ast)))  (00101001 (collect-free-vars (00000101 ast) bound-vars)
               (collect-free-vars (00000110 ast) bound-vars)))
      (t
       (10011100 ((bindings (00000101 (00000110 ast)))
             (body (00000101 (00000110 (00000110 ast)))))
         (10011100 ((all-names
                 (00110111 (00001000 (b) (01000010 (00000101 b))) bindings)))
           (10011100 ((new-bound (00101001 all-names bound-vars)))
             (00101001
               (00111001 append (00000001 ())
                       (00110111 (00001000 (b)
                              (collect-free-vars (00101111 b) new-bound))
                            bindings))
               (collect-free-vars body new-bound)))))))))

(00001001 collect-free-vars
  (00001000 (ast bound-vars)
    (00000111
      ((00100001 (10110001 (00000010 ast)))  (00000111
         ((00100011 ast)
          (00000111
            ((00101100 (01000010 ast) bound-vars) (00000001 ()))
            ((00101100 (01000010 ast) (00000001 ("t" "def" "defmacro" "lambda" "let" "let*" "letrec" "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom" "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval"))) (00000001 ()))
            (t (00100111 ast))))
         (t (00000001 ()))))
      ((00100010 (lint-form-head ast) (00000001 quote)) (00000001 ()))
      ((00100010 (lint-form-head ast) (00000001 def))
       (collect-free-vars (00000101 (00000110 (00000110 ast))) bound-vars))
      ((00100010 (lint-form-head ast) (00000001 lambda))
       (10011100 ((params (00000101 (00000110 ast)))
             (body (00000101 (00000110 (00000110 ast)))))
         (10011100 ((param-names (00000111 ((00100011 params) (00100111 (01000010 params)))
                                  (t (00110111 (00001000 (p) (01000010 p)) params)))))
           (collect-free-vars body (00101001 param-names bound-vars)))))
      ((00100010 (lint-form-head ast) (00000001 defmacro))
       (10011100 ((params (00000101 (00000110 (00000110 ast))))
             (body (00000101 (00000110 (00000110 (00000110 ast))))))
         (10011100 ((param-names (00000111 ((00100011 params) (00100111 (01000010 params)))
                                  (t (00110111 (00001000 (p) (01000010 p)) params)))))
           (collect-free-vars body (00101001 param-names bound-vars)))))
      ((00100010 (lint-form-head ast) (00000001 let))
       (00000111
         ((00100001 (10110001 (00000010 (00000110 ast))))  (00101001 (collect-free-vars (00000101 ast) bound-vars)
                  (collect-free-vars (00000110 ast) bound-vars)))
         ((00100011 (00000101 (00000110 ast)))
          ; Named let
          (10011100 ((name (01000010 (00000101 (00000110 ast))))
                (bindings (00000101 (00000110 (00000110 ast))))
                (body (00000101 (00000110 (00000110 (00000110 ast))))))
            (10011100 ((new-bound (00000100 name (00101001 (00110111 (00001000 (b) (01000010 (00000101 b))) bindings) bound-vars))))
              (00101001 (00111001 append (00000001 ()) (00110111 (00001000 (b) (collect-free-vars (00101111 b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))
         (t
          ; Basic let
          (10011100 ((bindings (00000101 (00000110 ast)))
                (body (00000101 (00000110 (00000110 ast)))))
            (10011100 ((new-bound (00101001 (00110111 (00001000 (b) (01000010 (00000101 b))) bindings) bound-vars)))
              (00101001 (00111001 append (00000001 ()) (00110111 (00001000 (b) (collect-free-vars (00101111 b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))))
      ((00100010 (lint-form-head ast) (00000001 let*))
       (collect-free-vars-let* ast bound-vars))
      ((00100010 (lint-form-head ast) (00000001 letrec))
       (collect-free-vars-letrec ast bound-vars))
      (t (00101001 (collect-free-vars (00000101 ast) bound-vars)
                 (collect-free-vars (00000110 ast) bound-vars))))))

(00001001 lint-globals
  (00001000 (ast)
    (00111001
      (00001000 (unique item)
        (00000111
          ((00101100 item unique) unique)
          (t (00000100 item unique))))
      (00000001 ())
      (collect-free-vars ast (00000001 ())))))

(00001001 lint-all
  (00001000 (ast)
    (00100111 (00100111 (00000001 size) (lint-size ast))
          (00100111 (00000001 nesting) (lint-nesting ast))
          (00100111 (00000001 complexity) (lint-complexity ast))
          (00100111 (00000001 effects) (lint-effects ast))
          (00100111 (00000001 free-vars) (lint-globals ast)))))

(00001001 get-threshold
  (00001000 (key thresholds default)
    (00000111
      ((00100010 thresholds (00000001 ())) default)
      ((00100010 (00000101 (00000101 thresholds)) key) (00000110 (00000101 thresholds)))
      (t (get-threshold key (00000110 thresholds) default)))))

(00001001 lint-check
  (00001000 (ast thresholds)
    (10011100 ((metrics (lint-all ast)))
      (10011100 ((size (00101111 (00000101 metrics)))
            (nesting (00101111 (00101111 metrics)))
            (complexity (00101111 (00110000 metrics)))
            (effects (00101111 (00110001 metrics)))
            (globals (00101111 (00110010 metrics))))
        (00101001
          (00000111 ((00011011 size (get-threshold (00000001 max-size) thresholds 99999)) 
                 (00100111 (00100111 (00000001 size-exceeded) size))) (t (00000001 ())))
          (00101001
            (00000111 ((00011011 nesting (get-threshold (00000001 max-nesting) thresholds 99999)) 
                   (00100111 (00100111 (00000001 nesting-exceeded) nesting))) (t (00000001 ())))
            (00101001
              (00000111 ((00011011 complexity (get-threshold (00000001 max-complexity) thresholds 99999)) 
                     (00100111 (00100111 (00000001 complexity-exceeded) complexity))) (t (00000001 ())))
              (00101001
                (00000111 ((00011011 (00101000 globals) (get-threshold (00000001 max-globals) thresholds 99999)) 
                       (00100111 (00100111 (00000001 globals-exceeded) globals))) (t (00000001 ())))
                (00000111 ((00011011 (00101000 effects) (get-threshold (00000001 max-effects) thresholds 99999)) 
                       (00100111 (00100111 (00000001 effects-exceeded) effects))) (t (00000001 ())))))))))))
