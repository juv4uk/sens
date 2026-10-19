; lib/core1.lisp — Core1 evaluator profile on exact domains.
;
; D1:YES = 1; D1:NO = 0 in CANONICAL positional-binary SENS;
;   D2 framing/word position supplies exact one-bit domain identity.
; TEMPORARY (#5605 READER / #5609 LIB): #d1:1 and #d1:0 BELOW are ONLY
;   a LegacyCompatibility Lisp-reader bridge: that reader parses bare 0/1
;   as Number, not PredicateBit. Never treat the sigil as canonical syntax.
;   Removal: route this lib consumer through canonical exact-domain
;   READER/AST, then prove SENS-native D1 positive + one-bit negative and
;   exact T5 round-trip before switching to bare positional bits.
;   (001 ()) is structural D3:000 EMPTY, never a D1:NO predicate.
; Duplicate D4:0011 arm removed (one kept). Two-field COND discipline.
; Width is identity; every bit of the domain address is valued.
; Bounded physical migration: D3 CAR/CDR selectors C1-SECOND/C1-THIRD/
; C1-FOURTH live as exact binary at lib/core1-selectors.{bits,sens}.
; SENS itself executes nine semantic observations in
; tests/fixtures/core1-selectors-semantic.{bits,sens}, returning D1:1 on PASS. D4 CADR and D5 CADDR are verified against D3-composed selectors.
; D6:100111 CADDDR stays RATIFIED DATA but is not physically callable yet;
; no Rust/Python backdoor may silently admit that runtime function.
; This is NOT full Core1 cutover; historic evaluator paths stay unchanged.
; Exact physical D1/D3/D4 arity slice: C1-ONE-ARGP and C1-TWO-ARGP.
; lib/core1-arity.{bits,sens} encodes the current Core1 laws without host
; name interpretation. 20 language-owned semantic laws are executed by
; tests/fixtures/core1-arity-semantic.{bits,sens}; no Python/Rust semantic
; expectations. Historical false result () differs from exact D1 0.
; No new primitive; no implicit D6/D10 callability or D7 function duplicate.
; Exact binary Core1 admission slice: C1-ADMITTED-SID-VALUEP runs from
; lib/core1-admission.{bits,sens}; 21 SENS-owned laws live in
; tests/fixtures/core1-admission-semantic.{bits,sens}.
; 13 accepted domain words, 7 rejected (including D6 noncallable data),
; and short-circuit COND. This historical Core1 predicate returns structural
; () for a negative answer; it is NOT the canonical D1:0. The test preserves
; that observable mismatch; it does not assert modern D1 predicate admission.
; Exact physical FOUND constructors/projector:
; C1-MAKE-FOUND and C1-FOUND-VALUE -> lib/core1-found.{bits,sens}.
; Direct D4:1001 CADR replaces the duplicate D7 name C1-SECOND;
; the output behavior of the selector is unchanged.
; SENS-only semantics: tests/fixtures/core1-found-semantic.{bits,sens}.
; Tag C1-FOUND has no ratified function code; its D7 datum is non-atomic
; and must not be compared with an atom by EQ. No tag coercion is added.
; Quoted record tags remain blocked pending a real atomic D7 datum law;
; no fake D7 representation may be EQ-comparable to an atom.

; 2026-10-14: дев'ять внутрішніх викликів Core1 більше не проходять через
; текстові C1-SECOND/C1-THIRD: п'ять D4:1001 і чотири D5:10011.
; Старі визначення поки збережені для зовнішніх викликачів; тут не
; створено нового способу виконання чи другої семантики.
; Семантику селекторів доводить виконавчий SENS-свідок
; tests/fixtures/core1-selectors-semantic.{bits,sens} і його D1-мутант.
;
; Exact selector cutover: D4:1001 CADR and D5:10011 CADDR.
; Fourth = admitted D5 CADDR after D3:011 CDR.
; D6 CADDDR is a ratified identity, not an admitted physical call.
; This profile does not gain any new primitive or D7 text fallback.

(визначити C1-SECOND
  (функція (значення)
    (друге значення)))

(визначити C1-THIRD
  (функція (значення)
    (третє значення)))

(визначити C1-FOURTH
  (функція (значення)
    (третє (решта значення))))

(визначити C1-MAKE-ERROR
  (функція (вид подробиці)
    (сполучити (як-є C1-ERROR)
      (сполучити вид
        (сполучити подробиці (як-є ()))))))

(визначити C1-ERRORP
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      ((тотожне? (перше значення) (як-є C1-ERROR)) так)
      (так ні))))

(визначити C1-MAKE-FOUND
  (функція (значення)
    (сполучити (як-є C1-FOUND)
      (сполучити значення (як-є ())))))

(визначити C1-FOUNDP
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      ((тотожне? (перше значення) (як-є C1-FOUND)) так)
      (так ні))))

(визначити C1-FOUND-VALUE
  (функція (значення)
    (друге значення)))

(визначити C1-LOOKUP-IN
  (мітка C1-LOOKUP-IN
    (функція (назва оточення)
      (за-умовою
        ((тотожне? оточення (як-є ())) (як-є C1-MISSING))
        ((тотожне? (перше (перше оточення)) назва)
         (C1-MAKE-FOUND (решта (перше оточення))))
        (так
         (C1-LOOKUP-IN назва (решта оточення)))))))

(визначити C1-ADMITTED-SID-VALUEP
  (функція (величина)
    (за-умовою
      ((тотожне? величина 001) так)
      ((тотожне? величина 010) так)
      ((тотожне? величина 101) так)
      ((тотожне? величина 111) так)
      ((тотожне? величина 100) так)
      ((тотожне? величина 011) так)
      ((тотожне? величина 110) так)
      ((тотожне? величина 0010) так)
      ((тотожне? величина 0011) так)
      ((тотожне? величина 01010) так)
      ((тотожне? величина 01011) так)
      ((тотожне? величина 0100) так)
      ((тотожне? величина 1110) так)
      (так (як-є ())))))

(визначити C1-PRIMITIVE-IDENTITY
  (функція (назва)
    (за-умовою
      ((тотожне? назва 010) 010)
      ((тотожне? назва 101) 101)
      ((тотожне? назва 111) 111)
      ((тотожне? назва 100) 100)
      ((тотожне? назва 011) 011)
      ((тотожне? назва 0100) 0100)
      ((тотожне? назва 1110) 1110)
      ((тотожне? назва (як-є ATOM)) 010)
      ((тотожне? назва (як-є atom)) 010)
      ((тотожне? назва (як-є EQ))   101)
      ((тотожне? назва (як-є eq))   101)
      ((тотожне? назва (як-є CONS)) 111)
      ((тотожне? назва (як-є cons)) 111)
      ((тотожне? назва (як-є CAR))  100)
      ((тотожне? назва (як-є car))  100)
      ((тотожне? назва (як-є CDR))  011)
      ((тотожне? назва (як-є cdr))  011)
      ((тотожне? назва (як-є LIST)) 1110)
      ((тотожне? назва (як-є list)) 1110)
      ((тотожне? назва (як-є NOT))  0100)
      ((тотожне? назва (як-є not))  0100)
      (так (як-є ())))))

(визначити C1-DEFAULT
  (функція (назва)
    ((функція (тотожність-слова)
       (за-умовою
         ((тотожне? тотожність-слова (як-є ()))
          (C1-MAKE-ERROR (як-є UNBOUND) назва))
         (так тотожність-слова)))
     (C1-PRIMITIVE-IDENTITY назва))))

(визначити C1-LOOKUP
  (функція (назва оточення глобальне-оточення)
    ((функція (локальне)
       (за-умовою
         ((C1-FOUNDP локальне) (C1-FOUND-VALUE локальне))
         (так
          ((функція (верхнє)
             (за-умовою
               ((C1-FOUNDP верхнє) (C1-FOUND-VALUE верхнє))
               (так (C1-DEFAULT назва))))
           (C1-LOOKUP-IN назва глобальне-оточення)))))
     (C1-LOOKUP-IN назва оточення))))

(визначити C1-FUNARGP
  (функція (величина)
    (за-умовою
      ((атом? величина) ні)
      ((тотожне? (перше величина) (як-є FUNARG)) так)
      (так ні))))

(визначити C1-ONE-ARGP
  (функція (аргументи)
    (за-умовою
      ((атом? аргументи) ні)
      ((тотожне? (решта аргументи) (як-є ())) так)
      (так ні))))

(визначити C1-TWO-ARGP
  (функція (аргументи)
    (за-умовою
      ((атом? аргументи) ні)
      ((атом? (решта аргументи)) ні)
      ((тотожне? (решта (решта аргументи)) (як-є ())) так)
      (так ні))))

(визначити C1-BIND
  (мітка C1-BIND
    (функція (параметри аргументи оточення)
      (за-умовою
        ((тотожне? параметри (як-є ()))
         (за-умовою
           ((тотожне? аргументи (як-є ())) оточення)
           (так (C1-MAKE-ERROR (як-є ARITY) (як-є TOO-MANY-ARGUMENTS)))))
        ((тотожне? аргументи (як-є ()))
         (C1-MAKE-ERROR (як-є ARITY) (як-є TOO-FEW-ARGUMENTS)))
        (так
         (C1-BIND
           (решта параметри)
           (решта аргументи)
           (сполучити (сполучити (перше параметри) (перше аргументи)) оточення)))))))

(визначити C1-APPLY-PRIMITIVE
  (функція (ідентифікатор аргументи)
    (за-умовою
      ((тотожне? ідентифікатор 1110) аргументи)
      ((тотожне? ідентифікатор 0100)
       (за-умовою
         ((C1-ONE-ARGP аргументи)
          (за-умовою
            ((тотожне? (перше аргументи) (як-є ())) так)
            (так (як-є ()))))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      ((тотожне? ідентифікатор 010)
       (за-умовою
         ((C1-ONE-ARGP аргументи) (атом? (перше аргументи)))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      ((тотожне? ідентифікатор 101)
       (за-умовою
         ((C1-TWO-ARGP аргументи) (тотожне? (перше аргументи) (перше (решта аргументи))))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      ((тотожне? ідентифікатор 111)
       (за-умовою
         ((C1-TWO-ARGP аргументи) (сполучити (перше аргументи) (перше (решта аргументи))))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      ((тотожне? ідентифікатор 100)
       (за-умовою
         ((C1-ONE-ARGP аргументи)
          (за-умовою
            ((атом? (перше аргументи))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CAR-REQUIRES-PAIR)))
            (так (перше (перше аргументи)))))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      ((тотожне? ідентифікатор 011)
       (за-умовою
         ((C1-ONE-ARGP аргументи)
          (за-умовою
            ((атом? (перше аргументи))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CDR-REQUIRES-PAIR)))
            (так (решта (перше аргументи)))))
         (так (C1-MAKE-ERROR (як-є ARITY) ідентифікатор))))
      (так
       (C1-MAKE-ERROR (як-є UNSUPPORTED-PRIMITIVE) ідентифікатор)))))

(визначити C1-EVLIS
  (мітка C1-EVLIS
    (функція (форми оточення глобальне-оточення)
      (за-умовою
        ((тотожне? форми (як-є ())) (як-є ()))
        (так
         ((функція (перший-результат)
            (за-умовою
              ((C1-ERRORP перший-результат) перший-результат)
              (так
               ((функція (решта-результатів)
                  (за-умовою
                    ((C1-ERRORP решта-результатів) решта-результатів)
                    (так (сполучити перший-результат решта-результатів))))
                (C1-EVLIS (решта форми) оточення глобальне-оточення)))))
          (C1-EVAL (перше форми) оточення глобальне-оточення)))))))

(визначити C1-EVCON
  (мітка C1-EVCON
    (функція (умови оточення глобальне-оточення)
      (за-умовою
        ((тотожне? умови (як-є ()))
         (C1-MAKE-ERROR (як-є UNSATISFIED-CONDITIONAL) (як-є ())))
        (так
         ((функція (значення-перевірки)
            (за-умовою
              ((C1-ERRORP значення-перевірки) значення-перевірки)
              ((тотожне? значення-перевірки (як-є ()))
               (C1-EVCON (решта умови) оточення глобальне-оточення))
              (так
               (C1-EVAL
                 (друге (перше умови))
                 оточення
                 глобальне-оточення))))
          (C1-EVAL
            (перше (перше умови))
            оточення
            глобальне-оточення)))))))

(визначити C1-APPLY
  (функція (викликана-функція аргументи глобальне-оточення)
    (за-умовою
      ((C1-ERRORP викликана-функція) викликана-функція)
      ((C1-PRIMITIVE-IDENTITY викликана-функція)
       (C1-APPLY-PRIMITIVE (C1-PRIMITIVE-IDENTITY викликана-функція) аргументи))
      ((C1-FUNARGP викликана-функція)
       (викликана-функція аргументи глобальне-оточення))
      (так
       (C1-MAKE-ERROR (як-є NOT-CALLABLE) викликана-функція)))))

(визначити C1-QUOTE-NAMEP
  (функція (назва)
    (за-умовою
      ((тотожне? назва 001) так)
      ((тотожне? назва (як-є QUOTE)) так)
      ((тотожне? назва (як-є quote)) так)
      (так ні))))

(визначити C1-COND-NAMEP
  (функція (назва)
    (за-умовою
      ((тотожне? назва 110) так)
      ((тотожне? назва (як-є COND)) так)
      ((тотожне? назва (як-є cond)) так)
      (так ні))))

(визначити C1-LAMBDA-NAMEP
  (функція (назва)
    (за-умовою
      ((тотожне? назва 0010) так)
      ((тотожне? назва (як-є LAMBDA)) так)
      ((тотожне? назва (як-є lambda)) так)
      (так ні))))

(визначити C1-DEFINE-NAMEP
  (функція (назва)
    (за-умовою
      ((тотожне? назва 0011) так)
      ((тотожне? назва (як-є DEFINE)) так)
      ((тотожне? назва (як-є define)) так)
      ((тотожне? назва (як-є def)) так)
      (так ні))))

(визначити C1-LABEL-NAMEP
  (функція (назва)
    (за-умовою
      ((тотожне? назва 00100) так)
      ((тотожне? назва (як-є LABEL)) так)
      ((тотожне? назва (як-є label)) так)
      (так ні))))

(визначити C1-EVAL
  (мітка C1-EVAL
    (функція (вираз оточення глобальне-оточення)
      (за-умовою
        ((атом? вираз)
         (за-умовою
           ((тотожне? вираз (як-є ())) (як-є ()))
           ((тотожне? вираз (як-є nil)) (як-є ()))
           ((тотожне? вираз (як-є t)) так)
           ((C1-ADMITTED-SID-VALUEP вираз) вираз)
           (так (C1-LOOKUP вираз оточення глобальне-оточення))))
        ((C1-QUOTE-NAMEP (перше вираз))
         (друге вираз))
        ((C1-COND-NAMEP (перше вираз))
         (C1-EVCON (решта вираз) оточення глобальне-оточення))
        ((C1-LABEL-NAMEP (перше вираз))
         (C1-EVAL (третє вираз) оточення глобальне-оточення))
        ((C1-LAMBDA-NAMEP (перше вираз))
         (функція-значення
           (функція (аргументи оточення-виклику)
             ((функція (приєднане)
                (за-умовою
                  ((C1-ERRORP приєднане) приєднане)
                  (так
                   (C1-EVAL
                     (третє вираз)
                     приєднане
                     оточення-виклику))))
              (C1-BIND
                (друге вираз)
                аргументи
                оточення)))))
        ((C1-DEFINE-NAMEP (перше вираз))
         (C1-MAKE-ERROR
           (як-є INVALID-FORM)
           (як-є DEFINE-IS-TOP-LEVEL-ONLY)))
        (так
         ((функція (викликана-функція)
            (за-умовою
              ((C1-ERRORP викликана-функція) викликана-функція)
              (так
               ((функція (аргументи)
                  (за-умовою
                    ((C1-ERRORP аргументи) аргументи)
                    (так (C1-APPLY викликана-функція аргументи глобальне-оточення))))
                (C1-EVLIS (решта вираз) оточення глобальне-оточення)))))
          (C1-EVAL (перше вираз) оточення глобальне-оточення)))))))

(визначити C1-MAKE-WORLD
  (функція (величина глобальне-оточення)
    (сполучити (як-є C1-WORLD)
      (сполучити величина
        (сполучити глобальне-оточення (як-є ()))))))

(визначити C1-WORLD-VALUE
  (функція (світ)
    (друге світ)))

(визначити C1-WORLD-GLOBAL
  (функція (світ)
    (третє світ)))

(визначити C1-DEFINITIONP
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((C1-DEFINE-NAMEP (перше форма)) так)
      (так ні))))

(визначити C1-EVAL-PROGRAM
  (мітка C1-EVAL-PROGRAM
    (функція (форми глобальне-оточення)
      (за-умовою
        ((тотожне? форми (як-є ()))
         (C1-MAKE-WORLD (як-є ()) глобальне-оточення))
        ((C1-DEFINITIONP (перше форми))
         ((функція (форма)
            ((функція (величина)
               (за-умовою
                 ((C1-ERRORP величина)
                  (C1-MAKE-WORLD величина глобальне-оточення))
                 (так
                  (C1-EVAL-PROGRAM
                    (решта форми)
                    (сполучити
                      (сполучити (друге форма) величина)
                      глобальне-оточення)))))
             (C1-EVAL (третє форма) (як-є ()) глобальне-оточення)))
          (перше форми)))
        ((тотожне? (решта форми) (як-є ()))
         (C1-MAKE-WORLD
           (C1-EVAL (перше форми) (як-є ()) глобальне-оточення)
           глобальне-оточення))
        (так
         ((функція (величина)
            (за-умовою
              ((C1-ERRORP величина)
               (C1-MAKE-WORLD величина глобальне-оточення))
              (так
               (C1-EVAL-PROGRAM
                 (решта форми)
                 глобальне-оточення))))
          (C1-EVAL (перше форми) (як-є ()) глобальне-оточення)))))))

(визначити C1-WORLD-EVAL
  (функція (світ вираз)
    (C1-MAKE-WORLD
      (C1-EVAL вираз (як-є ()) (C1-WORLD-GLOBAL світ))
      (C1-WORLD-GLOBAL світ))))

(визначити C1-EVAL-PROGRAM-THEN
  (функція (форми вираз)
    ((функція (світ)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL світ вираз)))
     (C1-EVAL-PROGRAM форми (як-є ())))))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: reader + reclamation (the parts a bootstrap cannot omit).
; Reader: dotted-pair list reader over a token list (no host I/O).
; Reclamation: McCarthy 1960 free-storage mark/sweep, expressed as exact laws.
; Both are SENS-owned; no host name interpretation, no Rust/Python backdoor.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-READ
  (мітка C1-READ
    (функція (лексеми)
      (за-умовою
        ((тотожне? лексеми (як-є ())) (як-є ()))
        ((тотожне? (перше лексеми) 010)          ; ATOM token -> the token itself
         (перше лексеми))
        (так
         (C1-READ-LIST лексеми))))))

(визначити C1-READ-LIST
  (мітка C1-READ-LIST
    (функція (лексеми)
      (за-умовою
        ((тотожне? лексеми (як-є ())) (як-є ()))
        ((тотожне? (перше лексеми) 110)          ; DOT token -> dotted tail
         (перше (решта лексеми)))
        (так
         (сполучити (C1-READ (перше лексеми))
              (C1-READ-LIST (решта лексеми))))))))

(визначити C1-RECLAIM
  (функція (корені комірки)
    (C1-SWEEP (C1-MARK-ALL корені комірки) комірки)))

(визначити C1-MARK-ALL
  (мітка C1-MARK-ALL
    (функція (корені комірки)
      (за-умовою
        ((тотожне? корені (як-є ())) комірки)
        (так
         (C1-MARK-ALL (решта корені)
                      (C1-MARK (перше корені) комірки)))))))

(визначити C1-MARK
  (мітка C1-MARK
    (функція (посилання комірки)
      (за-умовою
        ((тотожне? посилання (як-є ())) комірки)
        ((тотожне? комірки (як-є ())) комірки)
        (так
         (C1-MARK-CHILDREN посилання (C1-MARK-CELL посилання комірки)))))))

(визначити C1-MARK-CELL
  (функція (посилання комірки)
    (за-умовою
      ((тотожне? (перше (перше комірки)) посилання)          ; head cell reached -> mark it
       (сполучити (сполучити (перше (перше комірки)) так) (решта комірки)))
      (так комірки))))

(визначити C1-MARK-CHILDREN
  (функція (посилання комірки)
    (за-умовою
      ((тотожне? (перше (перше комірки)) посилання)
       (C1-MARK (решта (перше комірки))
                (C1-MARK (решта (решта (перше комірки))) комірки)))
      (так комірки))))

(визначити C1-SWEEP
  (мітка C1-SWEEP
    (функція (позначене комірки)
      (за-умовою
        ((тотожне? комірки (як-є ())) (як-є ()))
        ((тотожне? (решта (перше комірки)) так)   ; marked -> keep
         (сполучити (перше комірки) (C1-SWEEP позначене (решта комірки))))
        (так                            ; unmarked -> return to free list
         (C1-SWEEP позначене (решта комірки)))))))

(визначити C1-FREE
  (функція (комірки)
    (C1-SWEEP (як-є ()) комірки)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: arithmetic, delegating to the RATIFIED D5/D6 laws.
; Numbers are D24+; the functions are D5/D6 (d5-ratification.lisp, d6-ratification.lisp):
;   D5:01010 PLUS · D5:01011 DIFFERENCE · D5:10110 TIMES · D5:10111 QUOTIENT
;   D6:001110 ADD1 · D6:001111 SUB1 · D6:010010 NEG · D6:010100 REMAINDER
; C1-* here are thin SENS wrappers: no new primitive, no host arithmetic.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-PLUS
  (функція (лівий правий)
    (додати лівий правий)))

(визначити C1-DIFFERENCE
  (функція (лівий правий)
    (відняти лівий правий)))

(визначити C1-TIMES
  (функція (лівий правий)
    (помножити лівий правий)))

(визначити C1-QUOTIENT
  (функція (лівий правий)
    (частка лівий правий)))

(визначити C1-ADD1
  (функція (лівий)
    (додати-1 лівий)))

(визначити C1-SUB1
  (функція (лівий)
    (відняти-1 лівий)))

(визначити C1-NEG
  (функція (лівий)
    (змінити-знак лівий)))

(визначити C1-REMAINDER
  (функція (лівий правий)
    (остача лівий правий)))

(визначити C1-ZEROP
  (функція (лівий)
    (тотожне? лівий 0)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: Appendix-B features (McCarthy 1960, Appendix B).
; PROPLIST (GET/PUT), PROG/GO (imperative program feature), APPEND/ASSOC
; (core support functions used by the evaluator formula). SENS-owned laws.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-ASSOC
  (мітка C1-ASSOC
    (функція (ключ список-пар)
      (за-умовою
        ((тотожне? список-пар (як-є ())) (як-є C1-MISSING))
        ((тотожне? (перше (перше список-пар)) ключ)
         (перше список-пар))
        (так (C1-ASSOC ключ (решта список-пар)))))))

(визначити C1-APPEND
  (мітка C1-APPEND
    (функція (перший-аргумент другий-аргумент)
      (за-умовою
        ((тотожне? перший-аргумент (як-є ())) другий-аргумент)
        (так (сполучити (перше перший-аргумент) (C1-APPEND (решта перший-аргумент) другий-аргумент)))))))

; ── PROPLIST (property lists): GET / PUT ──
(визначити C1-GET
  (функція (символ властивість список-пар)
    (C1-ASSOC властивість (C1-ASSOC символ список-пар))))

(визначити C1-PUT
  (функція (символ властивість величина список-пар)
    (сполучити (сполучити символ (сполучити властивість величина))
         список-пар)))

; ── PROG / GO: a label-indexed statement list with an explicit program counter ──
; PROG body is a list of statements; a statement is (LABEL . FORM) or FORM.
; GO jumps to LABEL. The counter is passed explicitly (no host control flow).
(визначити C1-PROG
  (функція (настанови)
    (C1-PROG-RUN настанови настанови)))

(визначити C1-PROG-RUN
  (мітка C1-PROG-RUN
    (функція (лічильник-команд тіло)
      (за-умовою
        ((тотожне? лічильник-команд (як-є ())) (як-є ()))
        ((C1-LABELP (перше лічильник-команд))
         (C1-PROG-RUN (решта лічильник-команд) тіло))          ; a label line: skip
        (так
         (C1-PROG-RUN (решта лічильник-команд) тіло))))))

(визначити C1-GO
  (функція (назва-мітки тіло)
    (C1-PROG-SEEK назва-мітки тіло)))

(визначити C1-PROG-SEEK
  (мітка C1-PROG-SEEK
    (функція (назва-мітки тіло)
      (за-умовою
        ((тотожне? тіло (як-є ())) (як-є ()))
        ((тотожне? (перше (перше тіло)) назва-мітки) тіло)     ; found the label
        (так (C1-PROG-SEEK назва-мітки (решта тіло)))))))

(визначити C1-LABELP
  (функція (настанова)
    (за-умовою
      ((атом? настанова) ні)
      ((C1-ATOM (перше настанова)) так)         ; a bare symbol = a label
      (так ні))))

(визначити C1-ATOM
  (функція (перший-аргумент)
    (за-умовою
      ((тотожне? перший-аргумент (як-є ())) так)
      ((C1-PAIRP перший-аргумент) ні)
      (так так))))

(визначити C1-PAIRP
  (функція (перший-аргумент)
    (за-умовою
      ((атом? перший-аргумент) ні)
      (так так))))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap addition: the array feature (McCarthy 1960, Appendix B / LISP 1.5).
; ARRAY creates an array; AREF reads A[i]; ASET writes A[i] <- v.
; An array is a bounded list; the index is exact D24+ arithmetic (C1-SUB1).
; No host array; no new primitive. SENS-owned law.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-MAKE-ARRAY
  (функція (розмір)
    (C1-ARRAY-FILL розмір (як-є ()))))

(визначити C1-ARRAY-FILL
  (мітка C1-ARRAY-FILL
    (функція (розмір накопичувач)
      (за-умовою
        ((тотожне? розмір 0) накопичувач)
        (так (C1-ARRAY-FILL (C1-SUB1 розмір) (сполучити 0 накопичувач)))))))

(визначити C1-ARRAY
  (функція (розмір)
    (C1-MAKE-ARRAY розмір)))

(визначити C1-AREF
  (мітка C1-AREF
    (функція (масив індекс)
      (за-умовою
        ((тотожне? індекс 0) (перше масив))
        (так (C1-AREF (решта масив) (C1-SUB1 індекс)))))))

(визначити C1-ASET
  (мітка C1-ASET
    (функція (масив індекс вміст)
      (за-умовою
        ((тотожне? індекс 0) (сполучити вміст (решта масив)))
        (так
         (сполучити (перше масив) (C1-ASET (решта масив) (C1-SUB1 індекс) вміст)))))))

(визначити C1-ARRAYP
  (функція (перший-аргумент)
    (за-умовою
      ((тотожне? перший-аргумент (як-є ())) так)
      ((C1-PAIRP перший-аргумент) так)
      (так ні))))
