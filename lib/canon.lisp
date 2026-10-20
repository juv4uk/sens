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
(визначити канон-порожній-список (як-є ()))

; QUOTE and COND are evaluation-control forms, not ordinary first-class values.
; Callable Canon primitives are first-class immutable operation handles.
;
; Keyboard-symbol surface (typed without leaving the Ukrainian layout):
;   '  .?  =?  :  :п  :р  ?:
; These are spellings of the same 0+7 identities, never additional primitives.

; --- Canon V2 result records ----------------------------------------------
; A law does not return universal TRUE/FALSE. It returns explicit Lisp data.
; Закон не повертає універсальні TRUE/FALSE, а явний Lisp-запис.

(визначити канон-закон-результат
  (функція (закон стан)
    (сполучити
      (як-є canon-law-result)
      (сполучити закон (сполучити стан (як-є ()))))))

(визначити канон-закон-виконаний
  (функція (закон)
    (канон-закон-результат закон (як-є satisfied))))

(визначити канон-закон-порушений
  (функція (закон)
    (канон-закон-результат закон (як-є violated))))

(визначити канон-закон-стан
  (функція (результат)
    (перше (решта (решта результат)))))

(визначити канон-відповідність-результат
  (функція (стан)
    (сполучити
      (як-є canon-conformance)
      (сполучити стан (як-є ())))))

; --- Constitutive laws ----------------------------------------------------
; Кожна гілка використовує поточні D3:110 COND, D3:010 ATOM і D3:101 EQ
; через ратифіковані українські surface; керування лише точним D1 PredicateBit.
; Структурне () не є хибним предикатом.

(визначити канон-закон-порожній-список
  (функція ()
    (за-умовою
      ((тотожне? канон-порожній-список (як-є ()))
       (канон-закон-виконаний (як-є empty-list)))
      (так
       (канон-закон-порушений (як-є empty-list))))))

(визначити канон-закон-атом-пара
  (функція (ліве праве)
    (за-умовою
      ((атом? (сполучити ліве праве))
       (канон-закон-порушений (як-є atom-cons)))
      (так
       (канон-закон-виконаний (як-є atom-cons))))))

(визначити канон-закон-перше-пара
  (функція (ліве праве)
    (за-умовою
      ((тотожне? (перше (сполучити ліве праве)) ліве)
       (канон-закон-виконаний (як-є car-cons)))
      (так
       (канон-закон-порушений (як-є car-cons))))))

(визначити канон-закон-решта-пара
  (функція (ліве праве)
    (за-умовою
      ((тотожне? (решта (сполучити ліве праве)) праве)
       (канон-закон-виконаний (як-є cdr-cons)))
      (так
       (канон-закон-порушений (як-є cdr-cons))))))

(визначити канон-закон-рівність-рефлексивний-атом
  (функція (атом-значення)
    (за-умовою
      ((атом? атом-значення)
       (за-умовою
         ((тотожне? атом-значення атом-значення)
          (канон-закон-виконаний (як-є eq-reflexive-atom)))
         (так
          (канон-закон-порушений (як-є eq-reflexive-atom)))))
      (так
       (канон-закон-порушений (як-є eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(визначити канон-закон-решта-крапковий
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
(визначити канон-закон-решта-правильний
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
(визначити канон-закон-решта-неправильний
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
(визначити канон-закон-цитування-пригнічує-обчислення
  (функція ()
    (за-умовою
      ((тотожне? (як-є never-defined-canon-symbol)
                  (як-є never-defined-canon-symbol))
       (канон-закон-виконаний (як-є quote-suppresses-evaluation)))
      (так
       (канон-закон-порушений (як-є quote-suppresses-evaluation))))))

(визначити канон-закон-умова-перший-збіг-короткий-ланцюг
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
(визначити канон-закон-символьний-поверхня
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
(визначити канон-відповідність-з
  (функція (результати)
    (за-умовою
      ((атом? результати)
       (за-умовою
         ((тотожне? результати (як-є ()))
          (канон-відповідність-результат (як-є satisfied)))
         (так
          (канон-відповідність-результат (як-є violated)))))
      (так
       (за-умовою
         ((тотожне?
            (канон-закон-стан (перше результати))
            (як-є satisfied))
          (канон-відповідність-з (решта результати)))
         (так
          (канон-відповідність-результат (як-є violated))))))))

; One language-level explicit conformance record used by runtime observers.
(визначити канон-відповідає?
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

; Історичні англомовні імена лишаються сумісними зв'язуваннями того самого значення.
; Основні DEFINE вище — повні ратифіковані українські імена дев'ятого домену.
(визначити canon-empty-list канон-порожній-список)
(визначити canon-law-result канон-закон-результат)
(визначити canon-law-satisfied канон-закон-виконаний)
(визначити canon-law-violated канон-закон-порушений)
(визначити canon-law-status канон-закон-стан)
(визначити canon-conformance-result канон-відповідність-результат)
(визначити canon-law-empty-list канон-закон-порожній-список)
(визначити canon-law-atom-cons канон-закон-атом-пара)
(визначити canon-law-car-cons канон-закон-перше-пара)
(визначити canon-law-cdr-cons канон-закон-решта-пара)
(визначити canon-law-eq-reflexive-atom канон-закон-рівність-рефлексивний-атом)
(визначити canon-law-cdr-dotted канон-закон-решта-крапковий)
(визначити canon-law-cdr-proper канон-закон-решта-правильний)
(визначити canon-law-cdr-improper канон-закон-решта-неправильний)
(визначити canon-law-quote-suppresses-evaluation канон-закон-цитування-пригнічує-обчислення)
(визначити canon-law-cond-first-match-short-circuit канон-закон-умова-перший-збіг-короткий-ланцюг)
(визначити canon-law-symbolic-surface канон-закон-символьний-поверхня)
(визначити canon-conformance-from канон-відповідність-з)
(визначити canon-conforms? канон-відповідає?)
