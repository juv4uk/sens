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
(def canon-empty-list (quote ()))

; QUOTE and COND are evaluation-control forms, not ordinary first-class values.
; Callable Canon primitives are first-class immutable operation handles.
;
; Keyboard-symbol surface (typed without leaving the Ukrainian layout):
;   '  .?  =?  :  :п  :р  ?:
; These are spellings of the same 0+7 identities, never additional primitives.

; --- Canon V2 result records ----------------------------------------------
; A law does not return universal TRUE/FALSE. It returns explicit Lisp data.
; Закон не повертає універсальні TRUE/FALSE, а явний Lisp-запис.

(def canon-law-result
  (lambda (law status)
    (сполучити
      (quote canon-law-result)
      (сполучити law (сполучити status (quote ()))))))

(def canon-law-satisfied
  (lambda (law)
    (canon-law-result law (quote satisfied))))

(def canon-law-violated
  (lambda (law)
    (canon-law-result law (quote violated))))

(def canon-law-status
  (lambda (result)
    (перше (решта (решта result)))))

(def canon-conformance-result
  (lambda (status)
    (сполучити
      (quote canon-conformance)
      (сполучити status (quote ())))))

; --- Constitutive laws ----------------------------------------------------
; Every branch below uses canonical #217 explicit-result dispatch. `()` is
; structural data / Canon 0 and is never consumed as FALSE.

(def canon-law-empty-list
  (lambda ()
    (за-умовою
      ((тотожне? canon-empty-list (quote ()))
       (1)
       (canon-law-satisfied (quote empty-list)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote empty-list))))))

(def canon-law-atom-cons
  (lambda (x y)
    (за-умовою
      ((атом? (сполучити x y))
       (0)
       (canon-law-satisfied (quote atom-cons)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote atom-cons))))))

(def canon-law-car-cons
  (lambda (x y)
    (за-умовою
      ((тотожне? (перше (сполучити x y)) x)
       (1)
       (canon-law-satisfied (quote car-cons)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote car-cons))))))

(def canon-law-cdr-cons
  (lambda (x y)
    (за-умовою
      ((тотожне? (решта (сполучити x y)) y)
       (1)
       (canon-law-satisfied (quote cdr-cons)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote cdr-cons))))))

(def canon-law-eq-reflexive-atom
  (lambda (x)
    (за-умовою
      ((атом? x) (1)
       (за-умовою
         ((тотожне? x x) (1)
          (canon-law-satisfied (quote eq-reflexive-atom)))
         ((quote canon-fallback) canon-fallback
          (canon-law-violated (quote eq-reflexive-atom)))))
      ((атом? x) ()
       (за-умовою
         ((тотожне? x x) (1)
          (canon-law-satisfied (quote eq-reflexive-atom)))
         ((quote canon-fallback) canon-fallback
          (canon-law-violated (quote eq-reflexive-atom)))))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote eq-reflexive-atom))))))

; `решта` must be a pair projection, not a human-language "second element".
(def canon-law-cdr-dotted
  (lambda ()
    (за-умовою
      ((тотожне?
         (решта (сполучити (quote кіт) 42))
         42)
       (1)
       (canon-law-satisfied (quote cdr-dotted)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote cdr-dotted))))))

; EQ is atom-only. The proper-list witness therefore checks projected atom
; values and recognizes final `()` through its structural-kind result.
(def canon-law-cdr-proper
  (lambda ()
    (за-умовою
      ((тотожне? (перше (решта (як-є (1 2 3)))) 2)
       (1)
       (за-умовою
         ((тотожне? (перше (решта (решта (як-є (1 2 3))))) 3)
          (1)
          (за-умовою
            ((атом? (решта (решта (решта (як-є (1 2 3))))))
             ()
             (canon-law-satisfied (quote cdr-proper)))
            ((quote canon-fallback) canon-fallback
             (canon-law-violated (quote cdr-proper)))))
         ((quote canon-fallback) canon-fallback
          (canon-law-violated (quote cdr-proper)))))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote cdr-proper))))))

; EQ is atom-only, so the improper tail is checked through atom projections.
(def canon-law-cdr-improper
  (lambda ()
    (за-умовою
      ((тотожне? (перше (решта (як-є (1 2 . 3)))) 2)
       (1)
       (за-умовою
         ((тотожне? (решта (решта (як-є (1 2 . 3)))) 3)
          (1)
          (canon-law-satisfied (quote cdr-improper)))
         ((quote canon-fallback) canon-fallback
          (canon-law-violated (quote cdr-improper)))))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote cdr-improper))))))

; Evaluation-control laws: quoted/unselected unknown symbols must never be
; evaluated. If a host eagerly evaluates them, execution errors before a law
; record can be produced.
(def canon-law-quote-suppresses-evaluation
  (lambda ()
    (за-умовою
      ((тотожне? (як-є never-defined-canon-symbol)
                  (quote never-defined-canon-symbol))
       (1)
       (canon-law-satisfied (quote quote-suppresses-evaluation)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote quote-suppresses-evaluation))))))

(def canon-law-cond-first-match-short-circuit
  (lambda ()
    (за-умовою
      ((тотожне?
         (за-умовою
           ((quote selected) selected (як-є selected))
           ((never-defined-canon-predicate) impossible (як-є forbidden)))
         (quote selected))
       (1)
       (canon-law-satisfied (quote cond-first-match-short-circuit)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote cond-first-match-short-circuit))))))

; The compact Ukrainian-keyboard surface denotes the same seven operations.
; This vertical witness exercises quote, atom, eq, cons, car, cdr, and cond
; without relying on historical T/NIL truthiness.
(def canon-law-symbolic-surface
  (lambda ()
    (за-умовою
      ((тотожне?
         (?:
           ((.? 'атом) (1)
            (?:
              ((=? (:п (: 'ліве 'праве)) 'ліве)
               (1)
               (:р (: 'ліве 'праве))))))
         (quote праве))
       (1)
       (canon-law-satisfied (quote symbolic-surface)))
      ((quote canon-fallback) canon-fallback
       (canon-law-violated (quote symbolic-surface))))))

; Aggregate explicit law records recursively. The empty list terminates the
; result list structurally; it does not mean FALSE.
(def canon-conformance-from
  (lambda (results)
    (за-умовою
      ((атом? results) ()
       (canon-conformance-result (quote satisfied)))
      ((canon-law-status (перше results)) satisfied
       (canon-conformance-from (решта results)))
      ((quote canon-fallback) canon-fallback
       (canon-conformance-result (quote violated))))))

; One language-level explicit conformance record used by runtime observers.
(def canon-conforms?
  (lambda ()
    (canon-conformance-from
      (сполучити
        (canon-law-empty-list)
        (сполучити
          (canon-law-atom-cons (quote x) (quote y))
          (сполучити
            (canon-law-car-cons (quote x) (quote y))
            (сполучити
              (canon-law-cdr-cons (quote x) (quote y))
              (сполучити
                (canon-law-eq-reflexive-atom (quote x))
                (сполучити
                  (canon-law-cdr-dotted)
                  (сполучити
                    (canon-law-cdr-proper)
                    (сполучити
                      (canon-law-cdr-improper)
                      (сполучити
                        (canon-law-quote-suppresses-evaluation)
                        (сполучити
                          (canon-law-cond-first-match-short-circuit)
                          (сполучити
                            (canon-law-symbolic-surface)
                            (quote ())))))))))))))))
