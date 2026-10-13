; CANON 0+7 — semantic laws with exact D3 call-head coordinates.
; CANON 0+7 — виконуваний семантичний контракт, написаний самою my-lisp.
;
; Authority rule:
;   the language states the laws; host runtimes implement mechanisms and
;   must conform to these laws. This file is semantic evidence over an already
;   existing immutable Canon; it must never create or rebind Canon spellings.
;
; Binary admission companion: tests/fixtures/canon-ladder-logic.sens
; All callable D3 heads in these laws are canonical exact three-bit words;
; quoted ordinary names remain projected symbols until D7/T5 admission.
;
; Contract 6.0 boundary:
;   (), quote/як-є/svarūpa, atom/атом?/aṇu, eq/тотожне?/abheda,
;   cons/сполучити/saṃyuj, car/перше/ādi, cdr/решта/śeṣa and
;   cond/за-умовою/anukrama are supplied by the immutable Canon resolver.
;   This file only names witnesses and laws above that foundation.

; Canon 0 has no lexical alias as part of Canon itself. This ordinary witness
; is intentionally outside the reserved set and is used only by the laws below.
(0011 canon-empty-list (001 ()))

; QUOTE and COND are evaluation-control forms, not ordinary first-class values.
; Callable Canon primitives are first-class immutable operation handles.
;
; Keyboard-symbol surface (typed without leaving the Ukrainian layout):
;   '  .?  =?  :  :п  :р  ?:
; These are spellings of the same 0+7 identities, never additional primitives.

; --- Canon V2 result records ----------------------------------------------
; A law does not return universal TRUE/FALSE. It returns explicit Lisp data.
; Закон не повертає універсальні TRUE/FALSE, а явний Lisp-запис.

(0011 canon-law-result
  (0010 (law status)
    (111
      (001 canon-law-result)
      (111 law (111 status (001 ()))))))

(0011 canon-law-satisfied
  (0010 (law)
    (canon-law-result law (001 satisfied))))

(0011 canon-law-violated
  (0010 (law)
    (canon-law-result law (001 violated))))

(0011 canon-law-status
  (0010 (result)
    (100 (011 (011 result)))))

(0011 canon-conformance-result
  (0010 (status)
    (111
      (001 canon-conformance)
      (111 status (001 ())))))

; --- Constitutive laws ----------------------------------------------------
; Кожна гілка використовує поточні D3:110 COND, D3:010 ATOM і D3:101 EQ
; через ратифіковані українські surface; керування лише точним D1 PredicateBit.
; Структурне () не є хибним предикатом.

(0011 canon-law-empty-list
  (0010 ()
    (110
      ((101 canon-empty-list (001 ()))
       (canon-law-satisfied (001 empty-list)))
      (#d1:1
       (canon-law-violated (001 empty-list))))))

(0011 canon-law-atom-cons
  (0010 (x y)
    (110
      ((010 (111 x y))
       (canon-law-violated (001 atom-cons)))
      (#d1:1
       (canon-law-satisfied (001 atom-cons))))))

(0011 canon-law-car-cons
  (0010 (x y)
    (110
      ((101 (100 (111 x y)) x)
       (canon-law-satisfied (001 car-cons)))
      (#d1:1
       (canon-law-violated (001 car-cons))))))

(0011 canon-law-cdr-cons
  (0010 (x y)
    (110
      ((101 (011 (111 x y)) y)
       (canon-law-satisfied (001 cdr-cons)))
      (#d1:1
       (canon-law-violated (001 cdr-cons))))))

(0011 canon-law-eq-reflexive-atom
  (0010 (x)
    (110
      ((010 x)
       (110
         ((101 x x)
          (canon-law-satisfied (001 eq-reflexive-atom)))
         (#d1:1
          (canon-law-violated (001 eq-reflexive-atom)))))
      (#d1:1
       (canon-law-violated (001 eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(0011 canon-law-cdr-dotted
  (0010 ()
    (110
      ((101
         (011 (111 (001 кіт) 42))
         42)
       (canon-law-satisfied (001 cdr-dotted)))
      (#d1:1
       (canon-law-violated (001 cdr-dotted))))))

; EQ перевіряє тотожність допустимих атомів, включно зі структурним ().
; Завершення правильного списку доводимо явним EQ з ().
(0011 canon-law-cdr-proper
  (0010 ()
    (110
      ((101 (100 (011 (001 (1 2 3)))) 2)
       (110
         ((101 (100 (011 (011 (001 (1 2 3))))) 3)
          (110
            ((101
               (011 (011 (011 (001 (1 2 3)))))
               (001 ()))
             (canon-law-satisfied (001 cdr-proper)))
            (#d1:1
             (canon-law-violated (001 cdr-proper)))))
         (#d1:1
          (canon-law-violated (001 cdr-proper)))))
      (#d1:1
       (canon-law-violated (001 cdr-proper))))))

; EQ is atom-only, so the improper tail is checked through atom projections.
(0011 canon-law-cdr-improper
  (0010 ()
    (110
      ((101 (100 (011 (001 (1 2 . 3)))) 2)
       (110
         ((101 (011 (011 (001 (1 2 . 3)))) 3)
          (canon-law-satisfied (001 cdr-improper)))
         (#d1:1
          (canon-law-violated (001 cdr-improper)))))
      (#d1:1
       (canon-law-violated (001 cdr-improper))))))

; Evaluation-control laws: quoted/unselected unknown symbols must never be
; evaluated. If a host eagerly evaluates them, execution errors before a law
; record can be produced.
(0011 canon-law-quote-suppresses-evaluation
  (0010 ()
    (110
      ((101 (001 never-defined-canon-symbol)
                  (001 never-defined-canon-symbol))
       (canon-law-satisfied (001 quote-suppresses-evaluation)))
      (#d1:1
       (canon-law-violated (001 quote-suppresses-evaluation))))))

(0011 canon-law-cond-first-match-short-circuit
  (0010 ()
    (110
      ((101
         (110
           (#d1:1 (001 selected))
           ((never-defined-canon-predicate) (001 forbidden)))
         (001 selected))
       (canon-law-satisfied (001 cond-first-match-short-circuit)))
      (#d1:1
       (canon-law-violated (001 cond-first-match-short-circuit))))))

; The compact Ukrainian-keyboard surface denotes the same seven operations.
; Legacy witness name retained for compatibility; the law now executes
; exact D3 heads. Surface spelling parity belongs to projection checks.
; No historical T/NIL truthiness is admitted.
(0011 canon-law-symbolic-surface
  (0010 ()
    (110
      ((101
         (110
           ((010 (001 атом))
            (110
              ((101 (100 (111 (001 ліве) (001 праве))) (001 ліве))
               (011 (111 (001 ліве) (001 праве)))))))
         (001 праве))
       (canon-law-satisfied (001 symbolic-surface)))
      (#d1:1
       (canon-law-violated (001 symbolic-surface))))))

; Aggregate explicit law records recursively. The empty list terminates the
; result list structurally; it does not mean FALSE.
(0011 canon-conformance-from
  (0010 (results)
    (110
      ((010 results)
       (110
         ((101 results (001 ()))
          (canon-conformance-result (001 satisfied)))
         (#d1:1
          (canon-conformance-result (001 violated)))))
      (#d1:1
       (110
         ((101
            (canon-law-status (100 results))
            (001 satisfied))
          (canon-conformance-from (011 results)))
         (#d1:1
          (canon-conformance-result (001 violated))))))))

; One language-level explicit conformance record used by runtime observers.
(0011 canon-conforms?
  (0010 ()
    (canon-conformance-from
      (111
        (canon-law-empty-list)
        (111
          (canon-law-atom-cons (001 x) (001 y))
          (111
            (canon-law-car-cons (001 x) (001 y))
            (111
              (canon-law-cdr-cons (001 x) (001 y))
              (111
                (canon-law-eq-reflexive-atom (001 x))
                (111
                  (canon-law-cdr-dotted)
                  (111
                    (canon-law-cdr-proper)
                    (111
                      (canon-law-cdr-improper)
                      (111
                        (canon-law-quote-suppresses-evaluation)
                        (111
                          (canon-law-cond-first-match-short-circuit)
                          (111
                            (canon-law-symbolic-surface)
                            (001 ())))))))))))))))
