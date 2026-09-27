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

(00001001 genealogy-depends-on 11110000)

; One edge means: SOURCE is directly used by an executable laboratory
; reconstruction of TARGET.  Relation meaning lives in this experiment, not in
; the bit pattern itself.
(00001001 function-genealogy
  (00100111
    (00100111 00000100 genealogy-depends-on 00101110)
    (00100111 00000001 genealogy-depends-on 00101110)

    (00100111 00000101 genealogy-depends-on 00101111)
    (00100111 00000110 genealogy-depends-on 00101111)

    (00100111 00000101 genealogy-depends-on 00110000)
    (00100111 00000110 genealogy-depends-on 00110000)

    (00100111 00000101 genealogy-depends-on 00110001)
    (00100111 00000110 genealogy-depends-on 00110001)

    (00100111 00000101 genealogy-depends-on 00110010)
    (00100111 00000110 genealogy-depends-on 00110010)

    (00100111 00000101 genealogy-depends-on 00110011)

    (00100111 00000101 genealogy-depends-on 00110100)
    (00100111 00000110 genealogy-depends-on 00110100)

    (00100111 00000110 genealogy-depends-on 00110101)))

; Laboratory reconstructions.  The names are intentionally not registry names:
; the existing functions remain untouched while we test sufficiency.

(00001001 experiment-pair
  (00001000 (left right)
    (00000100 left (00000100 right (00000001 ())))))

(00001001 experiment-second
  (00001000 (values)
    (00000101 (00000110 values))))

(00001001 experiment-third
  (00001000 (values)
    (00000101 (00000110 (00000110 values)))))

(00001001 experiment-fourth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 values))))))

(00001001 experiment-fifth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 (00000110 values)))))))

(00001001 experiment-caar
  (00001000 (values)
    (00000101 (00000101 values))))

(00001001 experiment-cadr
  (00001000 (values)
    (00000101 (00000110 values))))

(00001001 experiment-cddr
  (00001000 (values)
    (00000110 (00000110 values))))

; Explicit result records keep () available as ordinary data.
(00001001 genealogy-check
  (00001000 (identity observed expected)
    (00000111
      ((00100010 observed expected) (1)
       (00100111 identity (00000001 reproduced)))
      ((00100010 observed expected) (0)
       (00100111 identity (00000001 diverged))))))

(00001001 function-genealogy-witness
  (00001000 ()
    (10011100 ((flat (00000001 (a b c d e))))
      (10011100 ((nested (00000001 ((left inner) right))))
        (00100111
          (genealogy-check
            00101110
            (experiment-pair (00000001 left) (00000001 right))
            (00101110 (00000001 left) (00000001 right)))
          (genealogy-check 00101111 (experiment-second flat) (00101111 flat))
          (genealogy-check 00110000 (experiment-third flat) (00110000 flat))
          (genealogy-check 00110001 (experiment-fourth flat) (00110001 flat))
          (genealogy-check 00110010 (experiment-fifth flat) (00110010 flat))
          (genealogy-check 00110011 (experiment-caar nested) (00110011 nested))
          (genealogy-check 00110100 (experiment-cadr flat) (00110100 flat))
          (genealogy-check 00110101 (experiment-cddr flat) (00110101 flat)))))))

; Graph queries over the experimental genealogy.  They are directed:
; "what targets directly depend on SOURCE?"  We intentionally return every
; matching target rather than choosing one.

(00001001 genealogy-direct-targets
  (00001000 (graph source)
    (00000111
      ((00000010 graph) ()
       (00000001 ()))
      ((00000010 graph) (0)
       (10011100 ((edge (00000101 graph)))
         (00000111
           ((00000011 (00000101 edge) source) (1)
            (00000100
              (00110000 edge)
              (genealogy-direct-targets (00000110 graph) source)))
           ((00000011 (00000101 edge) source) (0)
            (genealogy-direct-targets (00000110 graph) source)))))
      ((00000010 graph) (1)
       (00000001 ())))))

(00001001 function-genealogy-observation
  (00001000 ()
    (00100111
      (00100111
        (00000001 from-cons)
        (genealogy-direct-targets function-genealogy 00000100))
      (00100111
        (00000001 from-car)
        (genealogy-direct-targets function-genealogy 00000101))
      (00100111
        (00000001 from-cdr)
        (genealogy-direct-targets function-genealogy 00000110))
      (00100111
        (00000001 reproductions)
        (function-genealogy-witness)))))


; ---------------------------------------------------------------------------
; Experimental identity-overlap probes.
;
; The registry can contain distinct identities whose current Lisp
; implementations are observationally indistinguishable on a chosen domain.
; That does NOT automatically collapse their semantic identities.  It produces
; candidate-equivalence evidence for later experiments.

(00001001 genealogy-observes-like 11110001)

(00001001 observation-pair
  (00001000 (left right)
    (00100111 left right)))

(00001001 observation-same?
  (00001000 (left right)
    (00100010 left right)))

(00001001 sample-equivalent-two-unary?
  (00001000 (f g sample-a sample-b)
    (00000111
      ((observation-same? (f sample-a) (g sample-a)) (1)
       (00000111
         ((observation-same? (f sample-b) (g sample-b)) (1)
          (00000001 (1)))
         ((observation-same? (f sample-b) (g sample-b)) (0)
          (00000001 (0)))))
      ((observation-same? (f sample-a) (g sample-a)) (0)
       (00000001 (0))))))

; Distinct registry identities:
;   second  = 00101111
;   cadr    = 00110100
;   fourth  = 00110001
;   cadddr  = 00110110
;
; Current core implementation:
;   second and cadr have identical bodies;
;   cadddr is literally defined as the same closure object as fourth.
(00001001 function-overlap-candidates
  (00100111
    (00100111 00101111 genealogy-observes-like 00110100)
    (00100111 00110001 genealogy-observes-like 00110110)))

(00001001 function-overlap-witness
  (00001000 ()
    (10011100 ((sample-a (00000001 (a b c d e))))
      (10011100 ((sample-b (00000001 ((x y) (p q) r s t))))
        (00100111
          (00100111
            (00000001 second-vs-cadr)
            (sample-equivalent-two-unary?
              second cadr sample-a sample-b))
          (00100111
            (00000001 fourth-vs-cadddr)
            (sample-equivalent-two-unary?
              fourth cadddr sample-a sample-b))
          ; A deliberately weaker overlap: pair and list agree on exactly two
          ; arguments, but LIST is variadic, so this is only overlap evidence,
          ; never an equivalence claim.
          (00100111
            (00000001 pair-vs-list-two-args)
            (observation-same?
              (00101110 (00000001 left) (00000001 right))
              (00100111 (00000001 left) (00000001 right)))))))))

; ---------------------------------------------------------------------------
; Unification island.
;
; Here "generation" is a dependency hypergraph: a target may require several
; registered identities together. Internal helpers stay apparatus and are not
; assigned synthetic semantic identities.

(00001001 genealogy-requires 11110010)

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

(00001001 unification-genealogy
  (00100111
    ; logic-var = list + quote/data construction
    (00100111 00100111 genealogy-requires 10001000)

    ; var? depends structurally on atom/car/eq/cond
    (00100111 00000010 genealogy-requires 10001001)
    (00100111 00000101 genealogy-requires 10001001)
    (00100111 00000011 genealogy-requires 10001001)
    (00100111 00000111 genealogy-requires 10001001)

    ; walk uses var? plus structural substitution lookup
    (00100111 10001001 genealogy-requires 10001011)

    ; occurs-check recursively needs walk/var?/equal?/second/car/cdr
    (00100111 10001011 genealogy-requires 10001100)
    (00100111 10001001 genealogy-requires 10001100)
    (00100111 00100010 genealogy-requires 10001100)
    (00100111 00101111 genealogy-requires 10001100)
    (00100111 00000101 genealogy-requires 10001100)
    (00100111 00000110 genealogy-requires 10001100)

    ; apply-subst dereferences via walk and reconstructs terms with cons/car/cdr
    (00100111 10001011 genealogy-requires 10001010)
    (00100111 00000100 genealogy-requires 10001010)
    (00100111 00000101 genealogy-requires 10001010)
    (00100111 00000110 genealogy-requires 10001010)

    ; unify itself is centered around walk, var?, occurs-check, equal?
    (00100111 10001011 genealogy-requires 10000111)
    (00100111 10001001 genealogy-requires 10000111)
    (00100111 10001100 genealogy-requires 10000111)
    (00100111 00100010 genealogy-requires 10000111)))

(00001001 genealogy-sources-for
  (00001000 (graph target)
    (00000111
      ((00000010 graph) ()
       (00000001 ()))
      ((00000010 graph) (0)
       (10011100 ((edge (00000101 graph)))
         (00000111
           ((00000011 (00110000 edge) target) (1)
            (00000100
              (00000101 edge)
              (genealogy-sources-for (00000110 graph) target)))
           ((00000011 (00110000 edge) target) (0)
            (genealogy-sources-for (00000110 graph) target)))))
      ((00000010 graph) (1)
       (00000001 ())))))

(00001001 unification-genealogy-witness
  (00001000 ()
    (00100111
      (00100111
        (00000001 walk-needs)
        (genealogy-sources-for unification-genealogy 10001011))
      (00100111
        (00000001 occurs-check-needs)
        (genealogy-sources-for unification-genealogy 10001100))
      (00100111
        (00000001 apply-subst-needs)
        (genealogy-sources-for unification-genealogy 10001010))
      (00100111
        (00000001 unify-needs)
        (genealogy-sources-for unification-genealogy 10000111))
      ; Executable behavioral probe showing UNIFY creates a substitution that
      ; APPLY-SUBST can consume. This is a dynamic relation, not just static
      ; dependency metadata.
      (00100111
        (00000001 unify-produces-for-apply-subst)
        (10011100 ((subst
                (10000111
                  (00100111 (00000001 parent) (00000001 alice) (10001000 (00000001 x)))
                  (00100111 (00000001 parent) (00000001 alice) (00000001 bob))
                  (00000001 ()))))
          (10001010 (10001000 (00000001 x)) subst))))))

(00001001 function-laboratory-witness
  (00001000 ()
    (00100111
      (00100111 (00000001 structural-genealogy) (function-genealogy-observation))
      (00100111 (00000001 overlap-candidates) (function-overlap-witness))
      (00100111 (00000001 unification-island) (unification-genealogy-witness)))))
