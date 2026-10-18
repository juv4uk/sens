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

(визначити genealogy-depends-on 11110000)

; One edge means: SOURCE is directly used by an executable laboratory
; reconstruction of TARGET.  Relation meaning lives in this experiment, not in
; the bit pattern itself.
(визначити function-genealogy
  (список
    (список 00000100 genealogy-depends-on 00101110)
    (список 00000001 genealogy-depends-on 00101110)

    (список 00000101 genealogy-depends-on 00101111)
    (список 00000110 genealogy-depends-on 00101111)

    (список 00000101 genealogy-depends-on 00110000)
    (список 00000110 genealogy-depends-on 00110000)

    (список 00000101 genealogy-depends-on 00110001)
    (список 00000110 genealogy-depends-on 00110001)

    (список 00000101 genealogy-depends-on 00110010)
    (список 00000110 genealogy-depends-on 00110010)

    (список 00000101 genealogy-depends-on 00110011)

    (список 00000101 genealogy-depends-on 00110100)
    (список 00000110 genealogy-depends-on 00110100)

    (список 00000110 genealogy-depends-on 00110101)))

; Laboratory reconstructions.  The names are intentionally not registry names:
; the existing functions remain untouched while we test sufficiency.

(визначити experiment-pair
  (функція (left right)
    (сполучити left (сполучити right (як-є ())))))

(визначити experiment-second
  (функція (values)
    (перше (решта values))))

(визначити experiment-third
  (функція (values)
    (перше (решта (решта values)))))

(визначити experiment-fourth
  (функція (values)
    (перше (решта (решта (решта values))))))

(визначити experiment-fifth
  (функція (values)
    (перше (решта (решта (решта (решта values)))))))

(визначити experiment-caar
  (функція (values)
    (перше (перше values))))

(визначити experiment-cadr
  (функція (values)
    (перше (решта values))))

(визначити experiment-cddr
  (функція (values)
    (решта (решта values))))

; Explicit result records keep () available as ordinary data.
(визначити genealogy-check
  (функція (identity observed expected)
    (за-умовою
      ((11110111 observed expected) (1)
       (список identity (як-є reproduced)))
      ((11110111 observed expected) (0)
       (список identity (як-є diverged))))))

(визначити function-genealogy-witness
  (функція ()
    (001000 ((flat (001 (a b c d e))))
      (001000 ((nested (001 ((left inner) right))))
        (список
          (genealogy-check
            00101110
            (experiment-pair (як-є left) (як-є right))
            (11111101 (001 left) (001 right)))
          (genealogy-check 00101111 (experiment-second flat) (друге flat))
          (genealogy-check 00110000 (experiment-third flat) (10011 flat))
          (genealogy-check 00110001 (experiment-fourth flat) (100111 flat))
          (genealogy-check 00110010 (experiment-fifth flat) (110110101 flat))
          (genealogy-check 00110011 (experiment-caar nested) (1000 nested))
          (genealogy-check 00110100 (experiment-cadr flat) (друге flat))
          (genealogy-check 00110101 (experiment-cddr flat) (0111 flat)))))))

; Graph queries over the experimental genealogy.  They are directed:
; "what targets directly depend on SOURCE?"  We intentionally return every
; matching target rather than choosing one.

(визначити genealogy-direct-targets
  (функція (graph source)
    (за-умовою
      ((атом? graph) ()
       (як-є ()))
      ((атом? graph) (0)
       (001000 ((edge (100 graph)))
         (за-умовою
           ((тотожне? (перше edge) source) (1)
            (сполучити
              (10011 edge)
              (genealogy-direct-targets (решта graph) source)))
           ((тотожне? (перше edge) source) (0)
            (genealogy-direct-targets (решта graph) source)))))
      ((атом? graph) (1)
       (як-є ())))))

(визначити function-genealogy-observation
  (функція ()
    (список
      (список
        (як-є from-cons)
        (genealogy-direct-targets function-genealogy 00000100))
      (список
        (як-є from-car)
        (genealogy-direct-targets function-genealogy 00000101))
      (список
        (як-є from-cdr)
        (genealogy-direct-targets function-genealogy 00000110))
      (список
        (як-є reproductions)
        (function-genealogy-witness)))))


; ---------------------------------------------------------------------------
; Experimental identity-overlap probes.
;
; The registry can contain distinct identities whose current Lisp
; implementations are observationally indistinguishable on a chosen domain.
; That does NOT automatically collapse their semantic identities.  It produces
; candidate-equivalence evidence for later experiments.

(визначити genealogy-observes-like 11110001)

(визначити observation-pair
  (функція (left right)
    (список left right)))

(визначити observation-same?
  (функція (left right)
    (11110111 left right)))

(визначити sample-equivalent-two-unary?
  (функція (f g sample-a sample-b)
    (за-умовою
      ((observation-same? (f sample-a) (g sample-a)) (1)
       (за-умовою
         ((observation-same? (f sample-b) (g sample-b)) (1)
          (як-є (1)))
         ((observation-same? (f sample-b) (g sample-b)) (0)
          (як-є (0)))))
      ((observation-same? (f sample-a) (g sample-a)) (0)
       (як-є (0))))))

; Distinct registry identities:
;   second  = 00101111
;   cadr    = 00110100
;   fourth  = 00110001
;   cadddr  = 00110110
;
; Current core implementation:
;   second and cadr have identical bodies;
;   cadddr is literally defined as the same closure object as fourth.
(визначити function-overlap-candidates
  (список
    (список 00101111 genealogy-observes-like 00110100)
    (список 00110001 genealogy-observes-like 00110110)))

(визначити function-overlap-witness
  (функція ()
    (001000 ((sample-a (001 (a b c d e))))
      (001000 ((sample-b (001 ((x y) (p q) r s t))))
        (список
          (список
            (як-є second-vs-cadr)
            (sample-equivalent-two-unary?
              second cadr sample-a sample-b))
          (список
            (як-є fourth-vs-cadddr)
            (sample-equivalent-two-unary?
              fourth cadddr sample-a sample-b))
          ; A deliberately weaker overlap: pair and list agree on exactly two
          ; arguments, but LIST is variadic, so this is only overlap evidence,
          ; never an equivalence claim.
          (список
            (як-є pair-vs-list-two-args)
            (observation-same?
              (11111101 (001 left) (001 right))
              (список (як-є left) (як-є right)))))))))

; ---------------------------------------------------------------------------
; Unification island.
;
; Here "generation" is a dependency hypergraph: a target may require several
; registered identities together. Internal helpers stay apparatus and are not
; assigned synthetic semantic identities.

(визначити genealogy-requires 11110010)

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

(визначити unification-genealogy
  (список
    ; logic-var = list + quote/data construction
    (список 00100111 genealogy-requires 10001000)

    ; var? depends structurally on atom/car/eq/cond
    (список 00000010 genealogy-requires 10001001)
    (список 00000101 genealogy-requires 10001001)
    (список 00000011 genealogy-requires 10001001)
    (список 00000111 genealogy-requires 10001001)

    ; walk uses var? plus structural substitution lookup
    (список 10001001 genealogy-requires 10001011)

    ; occurs-check recursively needs walk/var?/equal?/second/car/cdr
    (список 10001011 genealogy-requires 10001100)
    (список 10001001 genealogy-requires 10001100)
    (список 00100010 genealogy-requires 10001100)
    (список 00101111 genealogy-requires 10001100)
    (список 00000101 genealogy-requires 10001100)
    (список 00000110 genealogy-requires 10001100)

    ; apply-subst dereferences via walk and reconstructs terms with cons/car/cdr
    (список 10001011 genealogy-requires 10001010)
    (список 00000100 genealogy-requires 10001010)
    (список 00000101 genealogy-requires 10001010)
    (список 00000110 genealogy-requires 10001010)

    ; unify itself is centered around walk, var?, occurs-check, equal?
    (список 10001011 genealogy-requires 10000111)
    (список 10001001 genealogy-requires 10000111)
    (список 10001100 genealogy-requires 10000111)
    (список 00100010 genealogy-requires 10000111)))

(визначити genealogy-sources-for
  (функція (graph target)
    (за-умовою
      ((атом? graph) ()
       (як-є ()))
      ((атом? graph) (0)
       (001000 ((edge (100 graph)))
         (за-умовою
           ((101 (10011 edge) target) (1)
            (сполучити
              (перше edge)
              (genealogy-sources-for (решта graph) target)))
           ((101 (10011 edge) target) (0)
            (genealogy-sources-for (решта graph) target)))))
      ((атом? graph) (1)
       (як-є ())))))

(визначити unification-genealogy-witness
  (функція ()
    (список
      (список
        (як-є walk-needs)
        (genealogy-sources-for unification-genealogy 10001011))
      (список
        (як-є occurs-check-needs)
        (genealogy-sources-for unification-genealogy 10001100))
      (список
        (як-є apply-subst-needs)
        (genealogy-sources-for unification-genealogy 10001010))
      (список
        (як-є unify-needs)
        (genealogy-sources-for unification-genealogy 10000111))
      ; Executable behavioral probe showing UNIFY creates a substitution that
      ; APPLY-SUBST can consume. This is a dynamic relation, not just static
      ; dependency metadata.
      (список
        (як-є unify-produces-for-apply-subst)
        (001000 ((subst
                (101010000
                  (1110 (001 parent) (001 alice) (101110010 (001 x)))
                  (список (як-є parent) (як-є alice) (як-є bob))
                  (як-є ()))))
          (101101001 (101110010 (001 x)) subst))))))

(визначити function-laboratory-witness
  (функція ()
    (список
      (список (як-є structural-genealogy) (function-genealogy-observation))
      (список (як-є overlap-candidates) (function-overlap-witness))
      (список (як-є unification-island) (unification-genealogy-witness)))))
