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

(0011 genealogy-depends-on 11110000)

; One edge means: SOURCE is directly used by an executable laboratory
; reconstruction of TARGET.  Relation meaning lives in this experiment, not in
; the bit pattern itself.
(0011 function-genealogy
  (1110
    (1110 00000100 genealogy-depends-on 00101110)
    (1110 00000001 genealogy-depends-on 00101110)

    (1110 00000101 genealogy-depends-on 00101111)
    (1110 00000110 genealogy-depends-on 00101111)

    (1110 00000101 genealogy-depends-on 00110000)
    (1110 00000110 genealogy-depends-on 00110000)

    (1110 00000101 genealogy-depends-on 00110001)
    (1110 00000110 genealogy-depends-on 00110001)

    (1110 00000101 genealogy-depends-on 00110010)
    (1110 00000110 genealogy-depends-on 00110010)

    (1110 00000101 genealogy-depends-on 00110011)

    (1110 00000101 genealogy-depends-on 00110100)
    (1110 00000110 genealogy-depends-on 00110100)

    (1110 00000110 genealogy-depends-on 00110101)))

; Laboratory reconstructions.  The names are intentionally not registry names:
; the existing functions remain untouched while we test sufficiency.

(0011 experiment-pair
  (0010 (left right)
    (111 left (111 right (001 ())))))

(0011 experiment-second
  (0010 (values)
    (100 (011 values))))

(0011 experiment-third
  (0010 (values)
    (100 (011 (011 values)))))

(0011 experiment-fourth
  (0010 (values)
    (100 (011 (011 (011 values))))))

(0011 experiment-fifth
  (0010 (values)
    (100 (011 (011 (011 (011 values)))))))

(0011 experiment-caar
  (0010 (values)
    (100 (100 values))))

(0011 experiment-cadr
  (0010 (values)
    (100 (011 values))))

(0011 experiment-cddr
  (0010 (values)
    (011 (011 values))))

; Explicit result records keep () available as ordinary data.
(0011 genealogy-check
  (0010 (identity observed expected)
    (110
      ((11110111 observed expected) (1)
       (1110 identity (001 reproduced)))
      ((11110111 observed expected) (0)
       (1110 identity (001 diverged))))))

(0011 function-genealogy-witness
  (0010 ()
    (001000 ((flat (001 (a b c d e))))
      (001000 ((nested (001 ((left inner) right))))
        (1110
          (genealogy-check
            00101110
            (experiment-pair (001 left) (001 right))
            (11111101 (001 left) (001 right)))
          (genealogy-check 00101111 (experiment-second flat) (1001 flat))
          (genealogy-check 00110000 (experiment-third flat) (10011 flat))
          (genealogy-check 00110001 (experiment-fourth flat) (100111 flat))
          (genealogy-check 00110010 (experiment-fifth flat) (110110101 flat))
          (genealogy-check 00110011 (experiment-caar nested) (1000 nested))
          (genealogy-check 00110100 (experiment-cadr flat) (1001 flat))
          (genealogy-check 00110101 (experiment-cddr flat) (0111 flat)))))))

; Graph queries over the experimental genealogy.  They are directed:
; "what targets directly depend on SOURCE?"  We intentionally return every
; matching target rather than choosing one.

(0011 genealogy-direct-targets
  (0010 (graph source)
    (110
      ((010 graph) ()
       (001 ()))
      ((010 graph) (0)
       (001000 ((edge (100 graph)))
         (110
           ((101 (100 edge) source) (1)
            (111
              (10011 edge)
              (genealogy-direct-targets (011 graph) source)))
           ((101 (100 edge) source) (0)
            (genealogy-direct-targets (011 graph) source)))))
      ((010 graph) (1)
       (001 ())))))

(0011 function-genealogy-observation
  (0010 ()
    (1110
      (1110
        (001 from-cons)
        (genealogy-direct-targets function-genealogy 00000100))
      (1110
        (001 from-car)
        (genealogy-direct-targets function-genealogy 00000101))
      (1110
        (001 from-cdr)
        (genealogy-direct-targets function-genealogy 00000110))
      (1110
        (001 reproductions)
        (function-genealogy-witness)))))


; ---------------------------------------------------------------------------
; Experimental identity-overlap probes.
;
; The registry can contain distinct identities whose current Lisp
; implementations are observationally indistinguishable on a chosen domain.
; That does NOT automatically collapse their semantic identities.  It produces
; candidate-equivalence evidence for later experiments.

(0011 genealogy-observes-like 11110001)

(0011 observation-pair
  (0010 (left right)
    (1110 left right)))

(0011 observation-same?
  (0010 (left right)
    (11110111 left right)))

(0011 sample-equivalent-two-unary?
  (0010 (f g sample-a sample-b)
    (110
      ((observation-same? (f sample-a) (g sample-a)) (1)
       (110
         ((observation-same? (f sample-b) (g sample-b)) (1)
          (001 (1)))
         ((observation-same? (f sample-b) (g sample-b)) (0)
          (001 (0)))))
      ((observation-same? (f sample-a) (g sample-a)) (0)
       (001 (0))))))

; Distinct registry identities:
;   second  = 00101111
;   cadr    = 00110100
;   fourth  = 00110001
;   cadddr  = 00110110
;
; Current core implementation:
;   second and cadr have identical bodies;
;   cadddr is literally defined as the same closure object as fourth.
(0011 function-overlap-candidates
  (1110
    (1110 00101111 genealogy-observes-like 00110100)
    (1110 00110001 genealogy-observes-like 00110110)))

(0011 function-overlap-witness
  (0010 ()
    (001000 ((sample-a (001 (a b c d e))))
      (001000 ((sample-b (001 ((x y) (p q) r s t))))
        (1110
          (1110
            (001 second-vs-cadr)
            (sample-equivalent-two-unary?
              second cadr sample-a sample-b))
          (1110
            (001 fourth-vs-cadddr)
            (sample-equivalent-two-unary?
              fourth cadddr sample-a sample-b))
          ; A deliberately weaker overlap: pair and list agree on exactly two
          ; arguments, but LIST is variadic, so this is only overlap evidence,
          ; never an equivalence claim.
          (1110
            (001 pair-vs-list-two-args)
            (observation-same?
              (11111101 (001 left) (001 right))
              (1110 (001 left) (001 right)))))))))

; ---------------------------------------------------------------------------
; Unification island.
;
; Here "generation" is a dependency hypergraph: a target may require several
; registered identities together. Internal helpers stay apparatus and are not
; assigned synthetic semantic identities.

(0011 genealogy-requires 11110010)

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

(0011 unification-genealogy
  (1110
    ; logic-var = list + quote/data construction
    (1110 00100111 genealogy-requires 10001000)

    ; var? depends structurally on atom/car/eq/cond
    (1110 00000010 genealogy-requires 10001001)
    (1110 00000101 genealogy-requires 10001001)
    (1110 00000011 genealogy-requires 10001001)
    (1110 00000111 genealogy-requires 10001001)

    ; walk uses var? plus structural substitution lookup
    (1110 10001001 genealogy-requires 10001011)

    ; occurs-check recursively needs walk/var?/equal?/second/car/cdr
    (1110 10001011 genealogy-requires 10001100)
    (1110 10001001 genealogy-requires 10001100)
    (1110 00100010 genealogy-requires 10001100)
    (1110 00101111 genealogy-requires 10001100)
    (1110 00000101 genealogy-requires 10001100)
    (1110 00000110 genealogy-requires 10001100)

    ; apply-subst dereferences via walk and reconstructs terms with cons/car/cdr
    (1110 10001011 genealogy-requires 10001010)
    (1110 00000100 genealogy-requires 10001010)
    (1110 00000101 genealogy-requires 10001010)
    (1110 00000110 genealogy-requires 10001010)

    ; unify itself is centered around walk, var?, occurs-check, equal?
    (1110 10001011 genealogy-requires 10000111)
    (1110 10001001 genealogy-requires 10000111)
    (1110 10001100 genealogy-requires 10000111)
    (1110 00100010 genealogy-requires 10000111)))

(0011 genealogy-sources-for
  (0010 (graph target)
    (110
      ((010 graph) ()
       (001 ()))
      ((010 graph) (0)
       (001000 ((edge (100 graph)))
         (110
           ((101 (10011 edge) target) (1)
            (111
              (100 edge)
              (genealogy-sources-for (011 graph) target)))
           ((101 (10011 edge) target) (0)
            (genealogy-sources-for (011 graph) target)))))
      ((010 graph) (1)
       (001 ())))))

(0011 unification-genealogy-witness
  (0010 ()
    (1110
      (1110
        (001 walk-needs)
        (genealogy-sources-for unification-genealogy 10001011))
      (1110
        (001 occurs-check-needs)
        (genealogy-sources-for unification-genealogy 10001100))
      (1110
        (001 apply-subst-needs)
        (genealogy-sources-for unification-genealogy 10001010))
      (1110
        (001 unify-needs)
        (genealogy-sources-for unification-genealogy 10000111))
      ; Executable behavioral probe showing UNIFY creates a substitution that
      ; APPLY-SUBST can consume. This is a dynamic relation, not just static
      ; dependency metadata.
      (1110
        (001 unify-produces-for-apply-subst)
        (001000 ((subst
                (101010000
                  (1110 (001 parent) (001 alice) (101110010 (001 x)))
                  (1110 (001 parent) (001 alice) (001 bob))
                  (001 ()))))
          (101101001 (101110010 (001 x)) subst))))))

(0011 function-laboratory-witness
  (0010 ()
    (1110
      (1110 (001 structural-genealogy) (function-genealogy-observation))
      (1110 (001 overlap-candidates) (function-overlap-witness))
      (1110 (001 unification-island) (unification-genealogy-witness)))))
