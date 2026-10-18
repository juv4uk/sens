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
(визначити canon-empty-list (як-є ()))

; QUOTE and COND are evaluation-control forms, not ordinary first-class values.
; Callable Canon primitives are first-class immutable operation handles.
;
; Keyboard-symbol surface (typed without leaving the Ukrainian layout):
;   '  .?  =?  :  :п  :р  ?:
; These are spellings of the same 0+7 identities, never additional primitives.

; --- Canon V2 result records ----------------------------------------------
; A law does not return universal TRUE/FALSE. It returns explicit Lisp data.
; Закон не повертає універсальні TRUE/FALSE, а явний Lisp-запис.

(визначити canon-law-result
  (функція (law status)
    (111
      (001 canon-law-result)
      (111 law (111 status (001 ()))))))

(визначити canon-law-satisfied
  (функція (law)
    (канон-закон-результат law (001 satisfied))))

(визначити canon-law-violated
  (функція (law)
    (канон-закон-результат law (001 violated))))

(визначити canon-law-status
  (функція (result)
    (100 (011 (011 result)))))

(визначити canon-conformance-result
  (функція (status)
    (111
      (001 canon-conformance)
      (111 status (001 ())))))

; --- Constitutive laws ----------------------------------------------------
; Кожна гілка використовує поточні D3:110 COND, D3:010 ATOM і D3:101 EQ
; через ратифіковані українські surface; керування лише точним D1 PredicateBit.
; Структурне () не є хибним предикатом.

(визначити canon-law-empty-list
  (функція ()
    (110
      ((101 канон-порожній-список (001 ()))
       (канон-закон-виконаний (001 empty-list)))
      (#d1:1
       (канон-закон-порушений (001 empty-list))))))

(визначити canon-law-atom-cons
  (функція (x y)
    (110
      ((010 (111 x y))
       (канон-закон-порушений (001 atom-cons)))
      (#d1:1
       (канон-закон-виконаний (001 atom-cons))))))

(визначити canon-law-car-cons
  (функція (x y)
    (110
      ((101 (100 (111 x y)) x)
       (канон-закон-виконаний (001 car-cons)))
      (#d1:1
       (канон-закон-порушений (001 car-cons))))))

(визначити canon-law-cdr-cons
  (функція (x y)
    (110
      ((101 (011 (111 x y)) y)
       (канон-закон-виконаний (001 cdr-cons)))
      (#d1:1
       (канон-закон-порушений (001 cdr-cons))))))

(визначити canon-law-eq-reflexive-atom
  (функція (x)
    (110
      ((010 x)
       (110
         ((101 x x)
          (канон-закон-виконаний (001 eq-reflexive-atom)))
         (#d1:1
          (канон-закон-порушений (001 eq-reflexive-atom)))))
      (#d1:1
       (канон-закон-порушений (001 eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(визначити canon-law-cdr-dotted
  (функція ()
    (110
      ((101
         (011 (111 (001 кіт) 42))
         42)
       (канон-закон-виконаний (001 cdr-dotted)))
      (#d1:1
       (канон-закон-порушений (001 cdr-dotted))))))

; EQ перевіряє тотожність допустимих атомів, включно зі структурним ().
; Завершення правильного списку доводимо явним EQ з ().
(визначити canon-law-cdr-proper
  (функція ()
    (110
      ((101 (100 (011 (001 (1 2 3)))) 2)
       (110
         ((101 (100 (011 (011 (001 (1 2 3))))) 3)
          (110
            ((101
               (011 (011 (011 (001 (1 2 3)))))
               (001 ()))
             (канон-закон-виконаний (001 cdr-proper)))
            (#d1:1
             (канон-закон-порушений (001 cdr-proper)))))
         (#d1:1
          (канон-закон-порушений (001 cdr-proper)))))
      (#d1:1
       (канон-закон-порушений (001 cdr-proper))))))

; EQ is atom-only, so the improper tail is checked through atom projections.
(визначити canon-law-cdr-improper
  (функція ()
    (110
      ((101 (100 (011 (001 (1 2 . 3)))) 2)
       (110
         ((101 (011 (011 (001 (1 2 . 3)))) 3)
          (канон-закон-виконаний (001 cdr-improper)))
         (#d1:1
          (канон-закон-порушений (001 cdr-improper)))))
      (#d1:1
       (канон-закон-порушений (001 cdr-improper))))))

; Evaluation-control laws: quoted/unselected unknown symbols must never be
; evaluated. If a host eagerly evaluates them, execution errors before a law
; record can be produced.
(визначити canon-law-quote-suppresses-evaluation
  (функція ()
    (110
      ((101 (001 never-defined-canon-symbol)
                  (001 never-defined-canon-symbol))
       (канон-закон-виконаний (001 quote-suppresses-evaluation)))
      (#d1:1
       (канон-закон-порушений (001 quote-suppresses-evaluation))))))

(визначити canon-law-cond-first-match-short-circuit
  (функція ()
    (110
      ((101
         (110
           (#d1:1 (001 selected))
           ((ніколи-не-визначений-канон-предикат) (001 forbidden)))
         (001 selected))
       (канон-закон-виконаний (001 cond-first-match-short-circuit)))
      (#d1:1
       (канон-закон-порушений (001 cond-first-match-short-circuit))))))

; The compact Ukrainian-keyboard surface denotes the same seven operations.
; Legacy witness name retained for compatibility; the law now executes
; exact D3 heads. Surface spelling parity belongs to projection checks.
; No historical T/NIL truthiness is admitted.
(визначити canon-law-symbolic-surface
  (функція ()
    (110
      ((101
         (110
           ((010 (001 атом))
            (110
              ((101 (100 (111 (001 ліве) (001 праве))) (001 ліве))
               (011 (111 (001 ліве) (001 праве)))))))
         (001 праве))
       (канон-закон-виконаний (001 symbolic-surface)))
      (#d1:1
       (канон-закон-порушений (001 symbolic-surface))))))

; Aggregate explicit law records recursively. The empty list terminates the
; result list structurally; it does not mean FALSE.
(визначити canon-conformance-from
  (функція (results)
    (110
      ((010 results)
       (110
         ((101 results (001 ()))
          (канон-відповідність-результат (001 satisfied)))
         (#d1:1
          (канон-відповідність-результат (001 violated)))))
      (#d1:1
       (110
         ((101
            (канон-закон-стан (100 results))
            (001 satisfied))
          (канон-відповідність-з (011 results)))
         (#d1:1
          (канон-відповідність-результат (001 violated))))))))

; One language-level explicit conformance record used by runtime observers.
(визначити canon-conforms?
  (функція ()
    (канон-відповідність-з
      (111
        (канон-закон-порожній-список)
        (111
          (канон-закон-атом-пара (001 x) (001 y))
          (111
            (канон-закон-перше-пара (001 x) (001 y))
            (111
              (канон-закон-решта-пара (001 x) (001 y))
              (111
                (канон-закон-рівність-рефлексивний-атом (001 x))
                (111
                  (канон-закон-решта-крапковий)
                  (111
                    (канон-закон-решта-правильний)
                    (111
                      (канон-закон-решта-неправильний)
                      (111
                        (канон-закон-цитування-пригнічує-обчислення)
                        (111
                          (канон-закон-умова-перший-збіг-короткий-ланцюг)
                          (111
                            (канон-закон-символьний-поверхня)
                            (001 ())))))))))))))))
