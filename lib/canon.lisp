; CANON 0+7 — executable semantic contract written in my-lisp.
; CANON 0+7 — виконуваний семантичний контракт, написаний самою my-lisp.
;
; Authority rule:
;   the language states the laws; host runtimes implement mechanisms and
;   must conform to these laws. This file is semantic evidence over an already
;   existing immutable Canon; it must never create or rebind Canon spellings.
;
; Contract 6.0 boundary:
;   (), quote/як-є/svarūpa, atom/атом?/aṇu, eq/тотожне?/abheda,
;   cons/сполучити/saṃyuj, car/перше/ādi, cdr/решта/śeṣa and
;   cond/за-умовою/anukrama are supplied by the immutable Canon resolver.
;   This file only names witnesses and laws above that foundation.

; Canon 0 has no lexical alias as part of Canon itself. This ordinary witness
; is intentionally outside the reserved set and is used only by the laws below.
(00001001 canon-empty-list (00000001 ()))

; QUOTE and COND are evaluation-control forms, not ordinary first-class values.
; Callable Canon primitives are first-class immutable operation handles.
;
; Keyboard-symbol surface (typed without leaving the Ukrainian layout):
;   '  .?  =?  :  :п  :р  ?:
; These are spellings of the same 0+7 identities, never additional primitives.

; --- Canon V2 result records ----------------------------------------------
; A law does not return universal TRUE/FALSE. It returns explicit Lisp data.
; Закон не повертає універсальні TRUE/FALSE, а явний Lisp-запис.

(00001001 canon-law-result
  (00001000 (law status)
    (00000100
      (00000001 canon-law-result)
      (00000100 law (00000100 status (00000001 ()))))))

(00001001 canon-law-satisfied
  (00001000 (law)
    (canon-law-result law (00000001 satisfied))))

(00001001 canon-law-violated
  (00001000 (law)
    (canon-law-result law (00000001 violated))))

(00001001 canon-law-status
  (00001000 (result)
    (00000101 (00000110 (00000110 result)))))

(00001001 canon-conformance-result
  (00001000 (status)
    (00000100
      (00000001 canon-conformance)
      (00000100 status (00000001 ())))))

; --- Constitutive laws ----------------------------------------------------
; Exact D1 predicate queries use two-part migration-compatible COND;
; non-predicate queries retain #217 explicit results. `()` is not D1:0.

(00001001 canon-law-empty-list
  (00001000 ()
    (00000111
      ((00000011 canon-empty-list (00000001 ()))
       (canon-law-satisfied (00000001 empty-list)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 empty-list))))))

(00001001 canon-law-atom-cons
  (00001000 (x y)
    (00000111
      ((00000011 (00000010 (00000100 x y))
                   (00000011 (00000001 ліве) (00000001 праве)))
       (canon-law-satisfied (00000001 atom-cons)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 atom-cons))))))

(00001001 canon-law-car-cons
  (00001000 (x y)
    (00000111
      ((00000011 (00000101 (00000100 x y)) x)
       (canon-law-satisfied (00000001 car-cons)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 car-cons))))))

(00001001 canon-law-cdr-cons
  (00001000 (x y)
    (00000111
      ((00000011 (00000110 (00000100 x y)) y)
       (canon-law-satisfied (00000001 cdr-cons)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 cdr-cons))))))

(00001001 canon-law-eq-reflexive-atom
  (00001000 (x)
    (00000111
      ((00000010 x)
       (00000111
         ((00000011 x x)
          (canon-law-satisfied (00000001 eq-reflexive-atom)))
         ((00000001 canon-fallback) canon-fallback
          (canon-law-violated (00000001 eq-reflexive-atom)))))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(00001001 canon-law-cdr-dotted
  (00001000 ()
    (00000111
      ((00000011
         (00000110 (00000100 (00000001 кіт) 42))
         42)
       (canon-law-satisfied (00000001 cdr-dotted)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 cdr-dotted))))))

; EQ is atom-only. The proper-list witness therefore checks projected atom
; values and recognizes final `()` through its structural-kind result.
(00001001 canon-law-cdr-proper
  (00001000 ()
    (00000111
      ((00000011 (00000101 (00000110 (00000001 (1 2 3)))) 2)
       (00000111
         ((00000011 (00000101 (00000110 (00000110 (00000001 (1 2 3))))) 3)
          (00000111
            ((00000010 (00000110 (00000110 (00000110 (00000001 (1 2 3))))))
             (canon-law-satisfied (00000001 cdr-proper)))
            ((00000001 canon-fallback) canon-fallback
             (canon-law-violated (00000001 cdr-proper)))))
         ((00000001 canon-fallback) canon-fallback
          (canon-law-violated (00000001 cdr-proper)))))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 cdr-proper))))))

; EQ is atom-only, so the improper tail is checked through atom projections.
(00001001 canon-law-cdr-improper
  (00001000 ()
    (00000111
      ((00000011 (00000101 (00000110 (00000001 (1 2 . 3)))) 2)
       (00000111
         ((00000011 (00000110 (00000110 (00000001 (1 2 . 3)))) 3)
          (canon-law-satisfied (00000001 cdr-improper)))
         ((00000001 canon-fallback) canon-fallback
          (canon-law-violated (00000001 cdr-improper)))))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 cdr-improper))))))

; Evaluation-control laws: quoted/unselected unknown symbols must never be
; evaluated. If a host eagerly evaluates them, execution errors before a law
; record can be produced.
(00001001 canon-law-quote-suppresses-evaluation
  (00001000 ()
    (00000111
      ((00000011 (00000001 never-defined-canon-symbol)
                  (00000001 never-defined-canon-symbol))
       (canon-law-satisfied (00000001 quote-suppresses-evaluation)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 quote-suppresses-evaluation))))))

(00001001 canon-law-cond-first-match-short-circuit
  (00001000 ()
    (00000111
      ((00000011
         (00000111
           ((00000001 selected) selected (00000001 selected))
           ((never-defined-canon-predicate) impossible (00000001 forbidden)))
         (00000001 selected))
       (canon-law-satisfied (00000001 cond-first-match-short-circuit)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 cond-first-match-short-circuit))))))

; The compact Ukrainian-keyboard surface denotes the same seven operations.
; This vertical witness exercises quote, atom, eq, cons, car, cdr, and cond
; without relying on historical T/NIL truthiness.
(00001001 canon-law-symbolic-surface
  (00001000 ()
    (00000111
      ((00000011
         (00000111
           ((00000010 'атом)
            (00000111
              ((00000011 (00000101 (00000100 'ліве 'праве)) 'ліве)
               (00000110 (00000100 'ліве 'праве))))))
         (00000001 праве))
       (canon-law-satisfied (00000001 symbolic-surface)))
      ((00000001 canon-fallback) canon-fallback
       (canon-law-violated (00000001 symbolic-surface))))))

; Aggregate explicit law records recursively. The empty list terminates the
; result list structurally; it does not mean FALSE.
(00001001 canon-conformance-from
  (00001000 (results)
    (00000111
      ((00000010 results)
       (canon-conformance-result (00000001 satisfied)))
      ((canon-law-status (00000101 results)) satisfied
       (canon-conformance-from (00000110 results)))
      ((00000001 canon-fallback) canon-fallback
       (canon-conformance-result (00000001 violated))))))

; One language-level explicit conformance record used by runtime observers.
(00001001 canon-conforms?
  (00001000 ()
    (canon-conformance-from
      (00000100
        (canon-law-empty-list)
        (00000100
          (canon-law-atom-cons (00000001 x) (00000001 y))
          (00000100
            (canon-law-car-cons (00000001 x) (00000001 y))
            (00000100
              (canon-law-cdr-cons (00000001 x) (00000001 y))
              (00000100
                (canon-law-eq-reflexive-atom (00000001 x))
                (00000100
                  (canon-law-cdr-dotted)
                  (00000100
                    (canon-law-cdr-proper)
                    (00000100
                      (canon-law-cdr-improper)
                      (00000100
                        (canon-law-quote-suppresses-evaluation)
                        (00000100
                          (canon-law-cond-first-match-short-circuit)
                          (00000100
                            (canon-law-symbolic-surface)
                            (00000001 ())))))))))))))))
