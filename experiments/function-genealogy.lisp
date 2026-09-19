; Function genealogy experiment.
; The semantic registry supplies opaque BitPattern8 identities.  This file asks
; a deliberately empirical question: which registered operations are sufficient
; to reconstruct other registered operations using ordinary Lisp?
;
; This is NOT a new authority table.  Edges below are experimental evidence
; backed by executable redefinitions in this file.
;
; Registry identities used here:
;   quote   00000001
;   cons    00000100
;   car     00000101
;   cdr     00000110
;   pair    00101110
;   second  00101111
;   third   00110000
;   fourth  00110001
;   fifth   00110010
;   caar    00110011
;   cadr    00110100
;   cddr    00110101

(def genealogy-depends-on 11110000)

; One edge means: SOURCE is directly used by an executable laboratory
; reconstruction of TARGET.  Relation meaning lives in this experiment, not in
; the bit pattern itself.
(def function-genealogy
  (list
    (list 00000100 genealogy-depends-on 00101110)
    (list 00000001 genealogy-depends-on 00101110)

    (list 00000101 genealogy-depends-on 00101111)
    (list 00000110 genealogy-depends-on 00101111)

    (list 00000101 genealogy-depends-on 00110000)
    (list 00000110 genealogy-depends-on 00110000)

    (list 00000101 genealogy-depends-on 00110001)
    (list 00000110 genealogy-depends-on 00110001)

    (list 00000101 genealogy-depends-on 00110010)
    (list 00000110 genealogy-depends-on 00110010)

    (list 00000101 genealogy-depends-on 00110011)

    (list 00000101 genealogy-depends-on 00110100)
    (list 00000110 genealogy-depends-on 00110100)

    (list 00000110 genealogy-depends-on 00110101)))

; Laboratory reconstructions.  The names are intentionally not registry names:
; the existing functions remain untouched while we test sufficiency.

(def experiment-pair
  (lambda (left right)
    (cons left (cons right (quote ())))))

(def experiment-second
  (lambda (values)
    (car (cdr values))))

(def experiment-third
  (lambda (values)
    (car (cdr (cdr values)))))

(def experiment-fourth
  (lambda (values)
    (car (cdr (cdr (cdr values))))))

(def experiment-fifth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr values)))))))

(def experiment-caar
  (lambda (values)
    (car (car values))))

(def experiment-cadr
  (lambda (values)
    (car (cdr values))))

(def experiment-cddr
  (lambda (values)
    (cdr (cdr values))))

; Explicit result records keep () available as ordinary data.
(def genealogy-check
  (lambda (identity observed expected)
    (cond
      ((equal? observed expected) (structural-relation same)
       (list identity (quote reproduced)))
      ((equal? observed expected) (structural-relation distinct)
       (list identity (quote diverged))))))

(def function-genealogy-witness
  (lambda ()
    (let ((flat (quote (a b c d e))))
      (let ((nested (quote ((left inner) right))))
        (list
          (genealogy-check
            00101110
            (experiment-pair (quote left) (quote right))
            (pair (quote left) (quote right)))
          (genealogy-check 00101111 (experiment-second flat) (second flat))
          (genealogy-check 00110000 (experiment-third flat) (third flat))
          (genealogy-check 00110001 (experiment-fourth flat) (fourth flat))
          (genealogy-check 00110010 (experiment-fifth flat) (fifth flat))
          (genealogy-check 00110011 (experiment-caar nested) (caar nested))
          (genealogy-check 00110100 (experiment-cadr flat) (cadr flat))
          (genealogy-check 00110101 (experiment-cddr flat) (cddr flat)))))))

; Graph queries over the experimental genealogy.  They are directed:
; "what targets directly depend on SOURCE?"  We intentionally return every
; matching target rather than choosing one.

(def genealogy-direct-targets
  (lambda (graph source)
    (cond
      ((atom graph) (structural-kind empty-list)
       (quote ()))
      ((atom graph) (structural-kind pair)
       (let ((edge (car graph)))
         (cond
           ((eq (car edge) source) (identity-relation same)
            (cons
              (third edge)
              (genealogy-direct-targets (cdr graph) source)))
           ((eq (car edge) source) (identity-relation distinct)
            (genealogy-direct-targets (cdr graph) source)))))
      ((atom graph) (structural-kind atom)
       (quote ())))))

(def function-genealogy-observation
  (lambda ()
    (list
      (list
        (quote from-cons)
        (genealogy-direct-targets function-genealogy 00000100))
      (list
        (quote from-car)
        (genealogy-direct-targets function-genealogy 00000101))
      (list
        (quote from-cdr)
        (genealogy-direct-targets function-genealogy 00000110))
      (list
        (quote reproductions)
        (function-genealogy-witness)))))


; ---------------------------------------------------------------------------
; Experimental identity-overlap probes.
;
; The registry can contain distinct identities whose current Lisp
; implementations are observationally indistinguishable on a chosen domain.
; That does NOT automatically collapse their semantic identities.  It produces
; candidate-equivalence evidence for later experiments.

(def genealogy-observes-like 11110001)

(def observation-pair
  (lambda (left right)
    (list left right)))

(def observation-same?
  (lambda (left right)
    (equal? left right)))

(def sample-equivalent-two-unary?
  (lambda (f g sample-a sample-b)
    (cond
      ((observation-same? (f sample-a) (g sample-a)) (structural-relation same)
       (cond
         ((observation-same? (f sample-b) (g sample-b)) (structural-relation same)
          (quote (structural-relation same)))
         ((observation-same? (f sample-b) (g sample-b)) (structural-relation distinct)
          (quote (structural-relation distinct)))))
      ((observation-same? (f sample-a) (g sample-a)) (structural-relation distinct)
       (quote (structural-relation distinct))))))

; Distinct registry identities:
;   second  = 00101111
;   cadr    = 00110100
;   fourth  = 00110001
;   cadddr  = 00110110
;
; Current core implementation:
;   second and cadr have identical bodies;
;   cadddr is literally defined as the same closure object as fourth.
(def function-overlap-candidates
  (list
    (list 00101111 genealogy-observes-like 00110100)
    (list 00110001 genealogy-observes-like 00110110)))

(def function-overlap-witness
  (lambda ()
    (let ((sample-a (quote (a b c d e))))
      (let ((sample-b (quote ((x y) (p q) r s t))))
        (list
          (list
            (quote second-vs-cadr)
            (sample-equivalent-two-unary?
              second cadr sample-a sample-b))
          (list
            (quote fourth-vs-cadddr)
            (sample-equivalent-two-unary?
              fourth cadddr sample-a sample-b))
          ; A deliberately weaker overlap: pair and list agree on exactly two
          ; arguments, but LIST is variadic, so this is only overlap evidence,
          ; never an equivalence claim.
          (list
            (quote pair-vs-list-two-args)
            (observation-same?
              (pair (quote left) (quote right))
              (list (quote left) (quote right)))))))))

; ---------------------------------------------------------------------------
; Unification island.
;
; Here "generation" is a dependency hypergraph: a target may require several
; registered identities together. Internal helpers stay apparatus and are not
; assigned synthetic semantic identities.

(def genealogy-requires 11110010)

; Registry IDs:
; logic-var   10001000
; var?        10001001
; apply-subst 10001010
; walk        10001011
; occurs-check 10001100
; unify       10000111
;
; Core/list identities used by those implementations:
; atom   00000010
; eq     00000011
; cons   00000100
; car    00000101
; cdr    00000110
; cond   00000111
; list   00100111
; second 00101111
; equal? 00100010

(def unification-genealogy
  (list
    ; logic-var = list + quote/data construction
    (list 00100111 genealogy-requires 10001000)

    ; var? depends structurally on atom/car/eq/cond
    (list 00000010 genealogy-requires 10001001)
    (list 00000101 genealogy-requires 10001001)
    (list 00000011 genealogy-requires 10001001)
    (list 00000111 genealogy-requires 10001001)

    ; walk uses var? plus structural substitution lookup
    (list 10001001 genealogy-requires 10001011)

    ; occurs-check recursively needs walk/var?/equal?/second/car/cdr
    (list 10001011 genealogy-requires 10001100)
    (list 10001001 genealogy-requires 10001100)
    (list 00100010 genealogy-requires 10001100)
    (list 00101111 genealogy-requires 10001100)
    (list 00000101 genealogy-requires 10001100)
    (list 00000110 genealogy-requires 10001100)

    ; apply-subst dereferences via walk and reconstructs terms with cons/car/cdr
    (list 10001011 genealogy-requires 10001010)
    (list 00000100 genealogy-requires 10001010)
    (list 00000101 genealogy-requires 10001010)
    (list 00000110 genealogy-requires 10001010)

    ; unify itself is centered around walk, var?, occurs-check, equal?
    (list 10001011 genealogy-requires 10000111)
    (list 10001001 genealogy-requires 10000111)
    (list 10001100 genealogy-requires 10000111)
    (list 00100010 genealogy-requires 10000111)))

(def genealogy-sources-for
  (lambda (graph target)
    (cond
      ((atom graph) (structural-kind empty-list)
       (quote ()))
      ((atom graph) (structural-kind pair)
       (let ((edge (car graph)))
         (cond
           ((eq (third edge) target) (identity-relation same)
            (cons
              (car edge)
              (genealogy-sources-for (cdr graph) target)))
           ((eq (third edge) target) (identity-relation distinct)
            (genealogy-sources-for (cdr graph) target)))))
      ((atom graph) (structural-kind atom)
       (quote ())))))

(def unification-genealogy-witness
  (lambda ()
    (list
      (list
        (quote walk-needs)
        (genealogy-sources-for unification-genealogy 10001011))
      (list
        (quote occurs-check-needs)
        (genealogy-sources-for unification-genealogy 10001100))
      (list
        (quote apply-subst-needs)
        (genealogy-sources-for unification-genealogy 10001010))
      (list
        (quote unify-needs)
        (genealogy-sources-for unification-genealogy 10000111))
      ; Executable behavioral probe showing UNIFY creates a substitution that
      ; APPLY-SUBST can consume. This is a dynamic relation, not just static
      ; dependency metadata.
      (list
        (quote unify-produces-for-apply-subst)
        (let ((subst
                (unify
                  (list (quote parent) (quote alice) (logic-var (quote x)))
                  (list (quote parent) (quote alice) (quote bob))
                  (quote ()))))
          (apply-subst (logic-var (quote x)) subst))))))

(def function-laboratory-witness
  (lambda ()
    (list
      (list (quote structural-genealogy) (function-genealogy-observation))
      (list (quote overlap-candidates) (function-overlap-witness))
      (list (quote unification-island) (unification-genealogy-witness)))))
