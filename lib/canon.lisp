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
    (сполучити
      (як-є canon-law-result)
      (сполучити law (сполучити status (як-є ()))))))

(визначити canon-law-satisfied
  (функція (law)
    (канон-закон-результат law (як-є satisfied))))

(визначити canon-law-violated
  (функція (law)
    (канон-закон-результат law (як-є violated))))

(визначити canon-law-status
  (функція (result)
    (перше (решта (решта result)))))

(визначити canon-conformance-result
  (функція (status)
    (сполучити
      (як-є canon-conformance)
      (сполучити status (як-є ())))))

; --- Constitutive laws ----------------------------------------------------
; Кожна гілка використовує поточні D3:110 COND, D3:010 ATOM і D3:101 EQ
; через ратифіковані українські surface; керування лише точним D1 PredicateBit.
; Структурне () не є хибним предикатом.

(визначити canon-law-empty-list
  (функція ()
    (за-умовою
      ((тотожне? канон-порожній-список (як-є ()))
       (канон-закон-виконаний (як-є empty-list)))
      (так
       (канон-закон-порушений (як-є empty-list))))))

(визначити canon-law-atom-cons
  (функція (x y)
    (за-умовою
      ((атом? (сполучити x y))
       (канон-закон-порушений (як-є atom-cons)))
      (так
       (канон-закон-виконаний (як-є atom-cons))))))

(визначити canon-law-car-cons
  (функція (x y)
    (за-умовою
      ((тотожне? (перше (сполучити x y)) x)
       (канон-закон-виконаний (як-є car-cons)))
      (так
       (канон-закон-порушений (як-є car-cons))))))

(визначити canon-law-cdr-cons
  (функція (x y)
    (за-умовою
      ((тотожне? (решта (сполучити x y)) y)
       (канон-закон-виконаний (як-є cdr-cons)))
      (так
       (канон-закон-порушений (як-є cdr-cons))))))

(визначити canon-law-eq-reflexive-atom
  (функція (x)
    (за-умовою
      ((атом? x)
       (за-умовою
         ((тотожне? x x)
          (канон-закон-виконаний (як-є eq-reflexive-atom)))
         (так
          (канон-закон-порушений (як-є eq-reflexive-atom)))))
      (так
       (канон-закон-порушений (як-є eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(визначити canon-law-cdr-dotted
  (функція ()
    (за-умовою
      ((тотожне?
         (решта (сполучити (як-є кіт) 42))
         42)
       (канон-закон-виконаний (як-є cdr-dotted)))
      (так
       (канон-закон-порушений (як-є cdr-dotted))))))

; EQ перевіряє тотожність допустимих атомів, включно зі структурним ().
; Завершення правильного списку доводимо явним EQ з ().
(визначити canon-law-cdr-proper
  (функція ()
    (за-умовою
      ((тотожне? (перше (решта (як-є (1 2 3)))) 2)
       (за-умовою
         ((тотожне? (перше (решта (решта (як-є (1 2 3))))) 3)
          (за-умовою
            ((тотожне?
               (решта (решта (решта (як-є (1 2 3)))))
               (як-є ()))
             (канон-закон-виконаний (як-є cdr-proper)))
            (так
             (канон-закон-порушений (як-є cdr-proper)))))
         (так
          (канон-закон-порушений (як-є cdr-proper)))))
      (так
       (канон-закон-порушений (як-є cdr-proper))))))

; EQ is atom-only, so the improper tail is checked through atom projections.
(визначити canon-law-cdr-improper
  (функція ()
    (за-умовою
      ((тотожне? (перше (решта (як-є (1 2 . 3)))) 2)
       (за-умовою
         ((тотожне? (решта (решта (як-є (1 2 . 3)))) 3)
          (канон-закон-виконаний (як-є cdr-improper)))
         (так
          (канон-закон-порушений (як-є cdr-improper)))))
      (так
       (канон-закон-порушений (як-є cdr-improper))))))

; Evaluation-control laws: quoted/unselected unknown symbols must never be
; evaluated. If a host eagerly evaluates them, execution errors before a law
; record can be produced.
(визначити canon-law-quote-suppresses-evaluation
  (функція ()
    (за-умовою
      ((тотожне? (як-є never-defined-canon-symbol)
                  (як-є never-defined-canon-symbol))
       (канон-закон-виконаний (як-є quote-suppresses-evaluation)))
      (так
       (канон-закон-порушений (як-є quote-suppresses-evaluation))))))

(визначити canon-law-cond-first-match-short-circuit
  (функція ()
    (за-умовою
      ((тотожне?
         (за-умовою
           (так (як-є selected))
           ((ніколи-не-визначений-канон-предикат) (як-є forbidden)))
         (як-є selected))
       (канон-закон-виконаний (як-є cond-first-match-short-circuit)))
      (так
       (канон-закон-порушений (як-є cond-first-match-short-circuit))))))

; The compact Ukrainian-keyboard surface denotes the same seven operations.
; Legacy witness name retained for compatibility; the law now executes
; exact D3 heads. Surface spelling parity belongs to projection checks.
; No historical T/NIL truthiness is admitted.
(визначити canon-law-symbolic-surface
  (функція ()
    (за-умовою
      ((тотожне?
         (за-умовою
           ((атом? (як-є атом))
            (за-умовою
              ((тотожне? (перше (сполучити (як-є ліве) (як-є праве))) (як-є ліве))
               (решта (сполучити (як-є ліве) (як-є праве)))))))
         (як-є праве))
       (канон-закон-виконаний (як-є symbolic-surface)))
      (так
       (канон-закон-порушений (як-є symbolic-surface))))))

; Aggregate explicit law records recursively. The empty list terminates the
; result list structurally; it does not mean FALSE.
(визначити canon-conformance-from
  (функція (results)
    (за-умовою
      ((атом? results)
       (за-умовою
         ((тотожне? results (як-є ()))
          (канон-відповідність-результат (як-є satisfied)))
         (так
          (канон-відповідність-результат (як-є violated)))))
      (так
       (за-умовою
         ((тотожне?
            (канон-закон-стан (перше results))
            (як-є satisfied))
          (канон-відповідність-з (решта results)))
         (так
          (канон-відповідність-результат (як-є violated))))))))

; One language-level explicit conformance record used by runtime observers.
(визначити canon-conforms?
  (функція ()
    (канон-відповідність-з
      (сполучити
        (канон-закон-порожній-список)
        (сполучити
          (канон-закон-атом-пара (як-є x) (як-є y))
          (сполучити
            (канон-закон-перше-пара (як-є x) (як-є y))
            (сполучити
              (канон-закон-решта-пара (як-є x) (як-є y))
              (сполучити
                (канон-закон-рівність-рефлексивний-атом (як-є x))
                (сполучити
                  (канон-закон-решта-крапковий)
                  (сполучити
                    (канон-закон-решта-правильний)
                    (сполучити
                      (канон-закон-решта-неправильний)
                      (сполучити
                        (канон-закон-цитування-пригнічує-обчислення)
                        (сполучити
                          (канон-закон-умова-перший-збіг-короткий-ланцюг)
                          (сполучити
                            (канон-закон-символьний-поверхня)
                            (як-є ())))))))))))))))
