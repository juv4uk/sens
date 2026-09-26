; lib/linter.lisp — Linter for my-lisp ASTs
; Analyzes size, nesting, complexity, globals, and effects.

(def lint-max2
  (lambda (a b)
    (cond
      ((> a b) 1 a)
      (t b))))


; 1. Size: Total number of nodes (atoms + pairs)
(def lint-size
  (lambda (ast)
    (cond
      ((atom? ast) () 1)
      ((atom? ast) (1) 1)
      (t (+ 1 (+ (lint-size (car ast)) (lint-size (cdr ast))))))))

; 2. Nesting: Maximum depth of pairs
(def lint-nesting
  (lambda (ast)
    (cond
      ((atom? ast) () 0)
      ((atom? ast) (1) 0)
      (t (lint-max2 (+ 1 (lint-nesting (car ast)))
              (lint-nesting (cdr ast)))))))

; 3. Complexity: Number of branching paths (cond clauses)
(def lint-complexity
  (lambda (ast)
    (cond
      ((atom? ast) () 0)
      ((atom? ast) (1) 0)
      ((equal? (car ast) (quote cond))
       (reduce (lambda (acc clause) (+ acc (lint-complexity clause)))
               (length (cdr ast))
               (cdr ast)))
      (t (+ (lint-complexity (car ast))
            (lint-complexity (cdr ast)))))))

; 4. Effects: Detect calls to side-effecting functions
(def effectful-primitives (quote ("print" "write-file" "process-run" "advise" "tell")))

(def lint-effects
  (lambda (ast)
    (cond
      ((atom? ast) () (quote ()))
      ((atom? ast) (1) (quote ()))
      ((symbol? (car ast))
       (cond
         ((member? (symbol->string (car ast)) effectful-primitives)
          (cons ast (lint-effects (cdr ast))))
         (t (append (lint-effects (car ast)) (lint-effects (cdr ast))))))
      (t (append (lint-effects (car ast)) (lint-effects (cdr ast)))))))

; 5. Hidden globals: Identify free variables that are not explicitly passed as arguments
; (simplified: just collect all symbols used as variables that aren't in standard core)
; A true global dependency checker requires walking `let` and `lambda` bindings.
(def collect-free-vars-let*
  (lambda (ast bound-vars)
    (cond
      ((atom? (cdr ast)) () (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr ast)) (1) (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr (cdr ast))) () (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr (cdr ast))) (1) (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      (t
       (let ((bindings (car (cdr ast)))
             (body (car (cdr (cdr ast)))))
         (cond
           ((equal? bindings (quote ()))
            (collect-free-vars body bound-vars))
           (t
            (let ((binding (car bindings)))
              (append
                (collect-free-vars (second binding) bound-vars)
                (collect-free-vars-let*
                  (list (quote let*) (cdr bindings) body)
                  (cons (symbol->string (car binding))
                        bound-vars)))))))))))

(def collect-free-vars-letrec
  (lambda (ast bound-vars)
    (cond
      ((atom? (cdr ast)) () (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr ast)) (1) (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr (cdr ast))) () (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      ((atom? (cdr (cdr ast))) (1) (append (collect-free-vars (car ast) bound-vars)
               (collect-free-vars (cdr ast) bound-vars)))
      (t
       (let ((bindings (car (cdr ast)))
             (body (car (cdr (cdr ast)))))
         (let ((all-names
                 (map (lambda (b) (symbol->string (car b))) bindings)))
           (let ((new-bound (append all-names bound-vars)))
             (append
               (reduce append (quote ())
                       (map (lambda (b)
                              (collect-free-vars (second b) new-bound))
                            bindings))
               (collect-free-vars body new-bound)))))))))

(def collect-free-vars
  (lambda (ast bound-vars)
    (cond
      ((atom? ast) () (cond
         ((symbol? ast)
          (cond
            ((member? (symbol->string ast) bound-vars) (quote ()))
            ((member? (symbol->string ast) (quote ("t" "def" "defmacro" "lambda" "let" "let*" "letrec" "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom" "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval"))) (quote ()))
            (t (list ast))))
         (t (quote ()))))
      ((atom? ast) (1) (cond
         ((symbol? ast)
          (cond
            ((member? (symbol->string ast) bound-vars) (quote ()))
            ((member? (symbol->string ast) (quote ("t" "def" "defmacro" "lambda" "let" "let*" "letrec" "cond" "quote" "list" "car" "cdr" "cons" "eq" "atom" "+" "-" "*" "/" "<" ">" "=" "<=" ">=" "print" "read" "eval"))) (quote ()))
            (t (list ast))))
         (t (quote ()))))
      ((equal? (car ast) (quote quote)) (quote ()))
      ((equal? (car ast) (quote def))
       (collect-free-vars (car (cdr (cdr ast))) bound-vars))
      ((equal? (car ast) (quote lambda))
       (let ((params (car (cdr ast)))
             (body (car (cdr (cdr ast)))))
         (let ((param-names (cond ((symbol? params) (list (symbol->string params)))
                                  (t (map (lambda (p) (symbol->string p)) params)))))
           (collect-free-vars body (append param-names bound-vars)))))
      ((equal? (car ast) (quote defmacro))
       (let ((params (car (cdr (cdr ast))))
             (body (car (cdr (cdr (cdr ast))))))
         (let ((param-names (cond ((symbol? params) (list (symbol->string params)))
                                  (t (map (lambda (p) (symbol->string p)) params)))))
           (collect-free-vars body (append param-names bound-vars)))))
      ((equal? (car ast) (quote let))
       (cond
         ((atom? (cdr ast)) () (append (collect-free-vars (car ast) bound-vars)
                  (collect-free-vars (cdr ast) bound-vars)))
         ((atom? (cdr ast)) (1) (append (collect-free-vars (car ast) bound-vars)
                  (collect-free-vars (cdr ast) bound-vars)))
         ((symbol? (car (cdr ast)))
          ; Named let
          (let ((name (symbol->string (car (cdr ast))))
                (bindings (car (cdr (cdr ast))))
                (body (car (cdr (cdr (cdr ast))))))
            (let ((new-bound (cons name (append (map (lambda (b) (symbol->string (car b))) bindings) bound-vars))))
              (append (reduce append (quote ()) (map (lambda (b) (collect-free-vars (second b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))
         (t
          ; Basic let
          (let ((bindings (car (cdr ast)))
                (body (car (cdr (cdr ast)))))
            (let ((new-bound (append (map (lambda (b) (symbol->string (car b))) bindings) bound-vars)))
              (append (reduce append (quote ()) (map (lambda (b) (collect-free-vars (second b) bound-vars)) bindings))
                      (collect-free-vars body new-bound)))))))
      ((equal? (car ast) (quote let*))
       (collect-free-vars-let* ast bound-vars))
      ((equal? (car ast) (quote letrec))
       (collect-free-vars-letrec ast bound-vars))
      (t (append (collect-free-vars (car ast) bound-vars)
                 (collect-free-vars (cdr ast) bound-vars))))))

(def lint-globals
  (lambda (ast)
    (reduce
      (lambda (unique item)
        (cond
          ((member? item unique) unique)
          (t (cons item unique))))
      (quote ())
      (collect-free-vars ast (quote ())))))

(def lint-all
  (lambda (ast)
    (list (list (quote size) (lint-size ast))
          (list (quote nesting) (lint-nesting ast))
          (list (quote complexity) (lint-complexity ast))
          (list (quote effects) (lint-effects ast))
          (list (quote free-vars) (lint-globals ast)))))

(def get-threshold
  (lambda (key thresholds default)
    (cond
      ((equal? thresholds (quote ())) default)
      ((equal? (car (car thresholds)) key) (cdr (car thresholds)))
      (t (get-threshold key (cdr thresholds) default)))))

(def lint-check
  (lambda (ast thresholds)
    (let ((metrics (lint-all ast)))
      (let ((size (second (car metrics)))
            (nesting (second (second metrics)))
            (complexity (second (third metrics)))
            (effects (second (fourth metrics)))
            (globals (second (fifth metrics))))
        (append
          (cond ((> size (get-threshold (quote max-size) thresholds 99999)) 1
                 (list (list (quote size-exceeded) size))) (t (quote ())))
          (append
            (cond ((> nesting (get-threshold (quote max-nesting) thresholds 99999)) 1
                   (list (list (quote nesting-exceeded) nesting))) (t (quote ())))
            (append
              (cond ((> complexity (get-threshold (quote max-complexity) thresholds 99999)) 1
                     (list (list (quote complexity-exceeded) complexity))) (t (quote ())))
              (append
                (cond ((> (length globals) (get-threshold (quote max-globals) thresholds 99999)) 1
                       (list (list (quote globals-exceeded) globals))) (t (quote ())))
                (cond ((> (length effects) (get-threshold (quote max-effects) thresholds 99999)) 1
                       (list (list (quote effects-exceeded) effects))) (t (quote ())))))))))))
