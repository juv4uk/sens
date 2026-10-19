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
    (функція (NAME ENV)
      (за-умовою
        ((тотожне? ENV (як-є ())) (як-є C1-MISSING))
        ((тотожне? (перше (перше ENV)) NAME)
         (C1-MAKE-FOUND (решта (перше ENV))))
        (так
         (C1-LOOKUP-IN NAME (решта ENV)))))))

(визначити C1-ADMITTED-SID-VALUEP
  (функція (VALUE)
    (за-умовою
      ((тотожне? VALUE 001) так)
      ((тотожне? VALUE 010) так)
      ((тотожне? VALUE 101) так)
      ((тотожне? VALUE 111) так)
      ((тотожне? VALUE 100) так)
      ((тотожне? VALUE 011) так)
      ((тотожне? VALUE 110) так)
      ((тотожне? VALUE 0010) так)
      ((тотожне? VALUE 0011) так)
      ((тотожне? VALUE 01010) так)
      ((тотожне? VALUE 01011) так)
      ((тотожне? VALUE 0100) так)
      ((тотожне? VALUE 1110) так)
      (так (як-є ())))))

(визначити C1-PRIMITIVE-IDENTITY
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 010) 010)
      ((тотожне? NAME 101) 101)
      ((тотожне? NAME 111) 111)
      ((тотожне? NAME 100) 100)
      ((тотожне? NAME 011) 011)
      ((тотожне? NAME 0100) 0100)
      ((тотожне? NAME 1110) 1110)
      ((тотожне? NAME (як-є ATOM)) 010)
      ((тотожне? NAME (як-є atom)) 010)
      ((тотожне? NAME (як-є EQ))   101)
      ((тотожне? NAME (як-є eq))   101)
      ((тотожне? NAME (як-є CONS)) 111)
      ((тотожне? NAME (як-є cons)) 111)
      ((тотожне? NAME (як-є CAR))  100)
      ((тотожне? NAME (як-є car))  100)
      ((тотожне? NAME (як-є CDR))  011)
      ((тотожне? NAME (як-є cdr))  011)
      ((тотожне? NAME (як-є LIST)) 1110)
      ((тотожне? NAME (як-є list)) 1110)
      ((тотожне? NAME (як-є NOT))  0100)
      ((тотожне? NAME (як-є not))  0100)
      (так (як-є ())))))

(визначити C1-DEFAULT
  (функція (NAME)
    ((функція (IDENTITY)
       (за-умовою
         ((тотожне? IDENTITY (як-є ()))
          (C1-MAKE-ERROR (як-є UNBOUND) NAME))
         (так IDENTITY)))
     (C1-PRIMITIVE-IDENTITY NAME))))

(визначити C1-LOOKUP
  (функція (NAME ENV GLOBAL)
    ((функція (LOCAL)
       (за-умовою
         ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
         (так
          ((функція (TOP)
             (за-умовою
               ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
               (так (C1-DEFAULT NAME))))
           (C1-LOOKUP-IN NAME GLOBAL)))))
     (C1-LOOKUP-IN NAME ENV))))

(визначити C1-FUNARGP
  (функція (VALUE)
    (за-умовою
      ((атом? VALUE) ні)
      ((тотожне? (перше VALUE) (як-є FUNARG)) так)
      (так ні))))

(визначити C1-ONE-ARGP
  (функція (ARGS)
    (за-умовою
      ((атом? ARGS) ні)
      ((тотожне? (решта ARGS) (як-є ())) так)
      (так ні))))

(визначити C1-TWO-ARGP
  (функція (ARGS)
    (за-умовою
      ((атом? ARGS) ні)
      ((атом? (решта ARGS)) ні)
      ((тотожне? (решта (решта ARGS)) (як-є ())) так)
      (так ні))))

(визначити C1-BIND
  (мітка C1-BIND
    (функція (PARAMS ARGS ENV)
      (за-умовою
        ((тотожне? PARAMS (як-є ()))
         (за-умовою
           ((тотожне? ARGS (як-є ())) ENV)
           (так (C1-MAKE-ERROR (як-є ARITY) (як-є TOO-MANY-ARGUMENTS)))))
        ((тотожне? ARGS (як-є ()))
         (C1-MAKE-ERROR (як-є ARITY) (як-є TOO-FEW-ARGUMENTS)))
        (так
         (C1-BIND
           (решта PARAMS)
           (решта ARGS)
           (сполучити (сполучити (перше PARAMS) (перше ARGS)) ENV)))))))

(визначити C1-APPLY-PRIMITIVE
  (функція (SID ARGS)
    (за-умовою
      ((тотожне? SID 1110) ARGS)
      ((тотожне? SID 0100)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((тотожне? (перше ARGS) (як-є ())) так)
            (так (як-є ()))))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      ((тотожне? SID 010)
       (за-умовою
         ((C1-ONE-ARGP ARGS) (атом? (перше ARGS)))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      ((тотожне? SID 101)
       (за-умовою
         ((C1-TWO-ARGP ARGS) (тотожне? (перше ARGS) (перше (решта ARGS))))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      ((тотожне? SID 111)
       (за-умовою
         ((C1-TWO-ARGP ARGS) (сполучити (перше ARGS) (перше (решта ARGS))))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      ((тотожне? SID 100)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((атом? (перше ARGS))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CAR-REQUIRES-PAIR)))
            (так (перше (перше ARGS)))))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      ((тотожне? SID 011)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((атом? (перше ARGS))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CDR-REQUIRES-PAIR)))
            (так (решта (перше ARGS)))))
         (так (C1-MAKE-ERROR (як-є ARITY) SID))))
      (так
       (C1-MAKE-ERROR (як-є UNSUPPORTED-PRIMITIVE) SID)))))

(визначити C1-EVLIS
  (мітка C1-EVLIS
    (функція (FORMS ENV GLOBAL)
      (за-умовою
        ((тотожне? FORMS (як-є ())) (як-є ()))
        (так
         ((функція (FIRST)
            (за-умовою
              ((C1-ERRORP FIRST) FIRST)
              (так
               ((функція (REST)
                  (за-умовою
                    ((C1-ERRORP REST) REST)
                    (так (сполучити FIRST REST))))
                (C1-EVLIS (решта FORMS) ENV GLOBAL)))))
          (C1-EVAL (перше FORMS) ENV GLOBAL)))))))

(визначити C1-EVCON
  (мітка C1-EVCON
    (функція (CLAUSES ENV GLOBAL)
      (за-умовою
        ((тотожне? CLAUSES (як-є ()))
         (C1-MAKE-ERROR (як-є UNSATISFIED-CONDITIONAL) (як-є ())))
        (так
         ((функція (TEST-VALUE)
            (за-умовою
              ((C1-ERRORP TEST-VALUE) TEST-VALUE)
              ((тотожне? TEST-VALUE (як-є ()))
               (C1-EVCON (решта CLAUSES) ENV GLOBAL))
              (так
               (C1-EVAL
                 (друге (перше CLAUSES))
                 ENV
                 GLOBAL))))
          (C1-EVAL
            (перше (перше CLAUSES))
            ENV
            GLOBAL)))))))

(визначити C1-APPLY
  (функція (FN ARGS GLOBAL)
    (за-умовою
      ((C1-ERRORP FN) FN)
      ((C1-PRIMITIVE-IDENTITY FN)
       (C1-APPLY-PRIMITIVE (C1-PRIMITIVE-IDENTITY FN) ARGS))
      ((C1-FUNARGP FN)
       (FN ARGS GLOBAL))
      (так
       (C1-MAKE-ERROR (як-є NOT-CALLABLE) FN)))))

(визначити C1-QUOTE-NAMEP
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 001) так)
      ((тотожне? NAME (як-є QUOTE)) так)
      ((тотожне? NAME (як-є quote)) так)
      (так ні))))

(визначити C1-COND-NAMEP
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 110) так)
      ((тотожне? NAME (як-є COND)) так)
      ((тотожне? NAME (як-є cond)) так)
      (так ні))))

(визначити C1-LAMBDA-NAMEP
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 0010) так)
      ((тотожне? NAME (як-є LAMBDA)) так)
      ((тотожне? NAME (як-є lambda)) так)
      (так ні))))

(визначити C1-DEFINE-NAMEP
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 0011) так)
      ((тотожне? NAME (як-є DEFINE)) так)
      ((тотожне? NAME (як-є define)) так)
      ((тотожне? NAME (як-є def)) так)
      (так ні))))

(визначити C1-LABEL-NAMEP
  (функція (NAME)
    (за-умовою
      ((тотожне? NAME 00100) так)
      ((тотожне? NAME (як-є LABEL)) так)
      ((тотожне? NAME (як-є label)) так)
      (так ні))))

(визначити C1-EVAL
  (мітка C1-EVAL
    (функція (EXPR ENV GLOBAL)
      (за-умовою
        ((атом? EXPR)
         (за-умовою
           ((тотожне? EXPR (як-є ())) (як-є ()))
           ((тотожне? EXPR (як-є nil)) (як-є ()))
           ((тотожне? EXPR (як-є t)) так)
           ((C1-ADMITTED-SID-VALUEP EXPR) EXPR)
           (так (C1-LOOKUP EXPR ENV GLOBAL))))
        ((C1-QUOTE-NAMEP (перше EXPR))
         (друге EXPR))
        ((C1-COND-NAMEP (перше EXPR))
         (C1-EVCON (решта EXPR) ENV GLOBAL))
        ((C1-LABEL-NAMEP (перше EXPR))
         (C1-EVAL (третє EXPR) ENV GLOBAL))
        ((C1-LAMBDA-NAMEP (перше EXPR))
         (функція-значення
           (функція (ARGS GLOBAL-AT-CALL)
             ((функція (BOUND)
                (за-умовою
                  ((C1-ERRORP BOUND) BOUND)
                  (так
                   (C1-EVAL
                     (третє EXPR)
                     BOUND
                     GLOBAL-AT-CALL))))
              (C1-BIND
                (друге EXPR)
                ARGS
                ENV)))))
        ((C1-DEFINE-NAMEP (перше EXPR))
         (C1-MAKE-ERROR
           (як-є INVALID-FORM)
           (як-є DEFINE-IS-TOP-LEVEL-ONLY)))
        (так
         ((функція (FN)
            (за-умовою
              ((C1-ERRORP FN) FN)
              (так
               ((функція (ARGS)
                  (за-умовою
                    ((C1-ERRORP ARGS) ARGS)
                    (так (C1-APPLY FN ARGS GLOBAL))))
                (C1-EVLIS (решта EXPR) ENV GLOBAL)))))
          (C1-EVAL (перше EXPR) ENV GLOBAL)))))))

(визначити C1-MAKE-WORLD
  (функція (VALUE GLOBAL)
    (сполучити (як-є C1-WORLD)
      (сполучити VALUE
        (сполучити GLOBAL (як-є ()))))))

(визначити C1-WORLD-VALUE
  (функція (WORLD)
    (друге WORLD)))

(визначити C1-WORLD-GLOBAL
  (функція (WORLD)
    (третє WORLD)))

(визначити C1-DEFINITIONP
  (функція (FORM)
    (за-умовою
      ((атом? FORM) ні)
      ((C1-DEFINE-NAMEP (перше FORM)) так)
      (так ні))))

(визначити C1-EVAL-PROGRAM
  (мітка C1-EVAL-PROGRAM
    (функція (FORMS GLOBAL)
      (за-умовою
        ((тотожне? FORMS (як-є ()))
         (C1-MAKE-WORLD (як-є ()) GLOBAL))
        ((C1-DEFINITIONP (перше FORMS))
         ((функція (FORM)
            ((функція (VALUE)
               (за-умовою
                 ((C1-ERRORP VALUE)
                  (C1-MAKE-WORLD VALUE GLOBAL))
                 (так
                  (C1-EVAL-PROGRAM
                    (решта FORMS)
                    (сполучити
                      (сполучити (друге FORM) VALUE)
                      GLOBAL)))))
             (C1-EVAL (третє FORM) (як-є ()) GLOBAL)))
          (перше FORMS)))
        ((тотожне? (решта FORMS) (як-є ()))
         (C1-MAKE-WORLD
           (C1-EVAL (перше FORMS) (як-є ()) GLOBAL)
           GLOBAL))
        (так
         ((функція (VALUE)
            (за-умовою
              ((C1-ERRORP VALUE)
               (C1-MAKE-WORLD VALUE GLOBAL))
              (так
               (C1-EVAL-PROGRAM
                 (решта FORMS)
                 GLOBAL))))
          (C1-EVAL (перше FORMS) (як-є ()) GLOBAL)))))))

(визначити C1-WORLD-EVAL
  (функція (WORLD EXPR)
    (C1-MAKE-WORLD
      (C1-EVAL EXPR (як-є ()) (C1-WORLD-GLOBAL WORLD))
      (C1-WORLD-GLOBAL WORLD))))

(визначити C1-EVAL-PROGRAM-THEN
  (функція (FORMS EXPR)
    ((функція (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM FORMS (як-є ())))))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: reader + reclamation (the parts a bootstrap cannot omit).
; Reader: dotted-pair list reader over a token list (no host I/O).
; Reclamation: McCarthy 1960 free-storage mark/sweep, expressed as exact laws.
; Both are SENS-owned; no host name interpretation, no Rust/Python backdoor.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-READ
  (мітка C1-READ
    (функція (TOKENS)
      (за-умовою
        ((тотожне? TOKENS (як-є ())) (як-є ()))
        ((тотожне? (перше TOKENS) 010)          ; ATOM token -> the token itself
         (перше TOKENS))
        (так
         (C1-READ-LIST TOKENS))))))

(визначити C1-READ-LIST
  (мітка C1-READ-LIST
    (функція (TOKENS)
      (за-умовою
        ((тотожне? TOKENS (як-є ())) (як-є ()))
        ((тотожне? (перше TOKENS) 110)          ; DOT token -> dotted tail
         (перше (решта TOKENS)))
        (так
         (сполучити (C1-READ (перше TOKENS))
              (C1-READ-LIST (решта TOKENS))))))))

(визначити C1-RECLAIM
  (функція (ROOTS CELLS)
    (C1-SWEEP (C1-MARK-ALL ROOTS CELLS) CELLS)))

(визначити C1-MARK-ALL
  (мітка C1-MARK-ALL
    (функція (ROOTS CELLS)
      (за-умовою
        ((тотожне? ROOTS (як-є ())) CELLS)
        (так
         (C1-MARK-ALL (решта ROOTS)
                      (C1-MARK (перше ROOTS) CELLS)))))))

(визначити C1-MARK
  (мітка C1-MARK
    (функція (REF CELLS)
      (за-умовою
        ((тотожне? REF (як-є ())) CELLS)
        ((тотожне? CELLS (як-є ())) CELLS)
        (так
         (C1-MARK-CHILDREN REF (C1-MARK-CELL REF CELLS)))))))

(визначити C1-MARK-CELL
  (функція (REF CELLS)
    (за-умовою
      ((тотожне? (перше (перше CELLS)) REF)          ; head cell reached -> mark it
       (сполучити (сполучити (перше (перше CELLS)) так) (решта CELLS)))
      (так CELLS))))

(визначити C1-MARK-CHILDREN
  (функція (REF CELLS)
    (за-умовою
      ((тотожне? (перше (перше CELLS)) REF)
       (C1-MARK (решта (перше CELLS))
                (C1-MARK (решта (решта (перше CELLS))) CELLS)))
      (так CELLS))))

(визначити C1-SWEEP
  (мітка C1-SWEEP
    (функція (MARKED CELLS)
      (за-умовою
        ((тотожне? CELLS (як-є ())) (як-є ()))
        ((тотожне? (решта (перше CELLS)) так)   ; marked -> keep
         (сполучити (перше CELLS) (C1-SWEEP MARKED (решта CELLS))))
        (так                            ; unmarked -> return to free list
         (C1-SWEEP MARKED (решта CELLS)))))))

(визначити C1-FREE
  (функція (CELLS)
    (C1-SWEEP (як-є ()) CELLS)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: arithmetic, delegating to the RATIFIED D5/D6 laws.
; Numbers are D24+; the functions are D5/D6 (d5-ratification.lisp, d6-ratification.lisp):
;   D5:01010 PLUS · D5:01011 DIFFERENCE · D5:10110 TIMES · D5:10111 QUOTIENT
;   D6:001110 ADD1 · D6:001111 SUB1 · D6:010010 NEG · D6:010100 REMAINDER
; C1-* here are thin SENS wrappers: no new primitive, no host arithmetic.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-PLUS
  (функція (A B)
    (додати A B)))

(визначити C1-DIFFERENCE
  (функція (A B)
    (відняти A B)))

(визначити C1-TIMES
  (функція (A B)
    (помножити A B)))

(визначити C1-QUOTIENT
  (функція (A B)
    (частка A B)))

(визначити C1-ADD1
  (функція (A)
    (додати-1 A)))

(визначити C1-SUB1
  (функція (A)
    (відняти-1 A)))

(визначити C1-NEG
  (функція (A)
    (змінити-знак A)))

(визначити C1-REMAINDER
  (функція (A B)
    (остача A B)))

(визначити C1-ZEROP
  (функція (A)
    (тотожне? A 0)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: Appendix-B features (McCarthy 1960, Appendix B).
; PROPLIST (GET/PUT), PROG/GO (imperative program feature), APPEND/ASSOC
; (core support functions used by the evaluator formula). SENS-owned laws.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-ASSOC
  (мітка C1-ASSOC
    (функція (KEY ALIST)
      (за-умовою
        ((тотожне? ALIST (як-є ())) (як-є C1-MISSING))
        ((тотожне? (перше (перше ALIST)) KEY)
         (перше ALIST))
        (так (C1-ASSOC KEY (решта ALIST)))))))

(визначити C1-APPEND
  (мітка C1-APPEND
    (функція (X Y)
      (за-умовою
        ((тотожне? X (як-є ())) Y)
        (так (сполучити (перше X) (C1-APPEND (решта X) Y)))))))

; ── PROPLIST (property lists): GET / PUT ──
(визначити C1-GET
  (функція (SYM PROP ALIST)
    (C1-ASSOC PROP (C1-ASSOC SYM ALIST))))

(визначити C1-PUT
  (функція (SYM PROP VALUE ALIST)
    (сполучити (сполучити SYM (сполучити PROP VALUE))
         ALIST)))

; ── PROG / GO: a label-indexed statement list with an explicit program counter ──
; PROG body is a list of statements; a statement is (LABEL . FORM) or FORM.
; GO jumps to LABEL. The counter is passed explicitly (no host control flow).
(визначити C1-PROG
  (функція (STATEMENTS)
    (C1-PROG-RUN STATEMENTS STATEMENTS)))

(визначити C1-PROG-RUN
  (мітка C1-PROG-RUN
    (функція (PC BODY)
      (за-умовою
        ((тотожне? PC (як-є ())) (як-є ()))
        ((C1-LABELP (перше PC))
         (C1-PROG-RUN (решта PC) BODY))          ; a label line: skip
        (так
         (C1-PROG-RUN (решта PC) BODY))))))

(визначити C1-GO
  (функція (LABEL BODY)
    (C1-PROG-SEEK LABEL BODY)))

(визначити C1-PROG-SEEK
  (мітка C1-PROG-SEEK
    (функція (LABEL BODY)
      (за-умовою
        ((тотожне? BODY (як-є ())) (як-є ()))
        ((тотожне? (перше (перше BODY)) LABEL) BODY)     ; found the label
        (так (C1-PROG-SEEK LABEL (решта BODY)))))))

(визначити C1-LABELP
  (функція (STATEMENT)
    (за-умовою
      ((атом? STATEMENT) ні)
      ((C1-ATOM (перше STATEMENT)) так)         ; a bare symbol = a label
      (так ні))))

(визначити C1-ATOM
  (функція (X)
    (за-умовою
      ((тотожне? X (як-є ())) так)
      ((C1-PAIRP X) ні)
      (так так))))

(визначити C1-PAIRP
  (функція (X)
    (за-умовою
      ((атом? X) ні)
      (так так))))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap addition: the array feature (McCarthy 1960, Appendix B / LISP 1.5).
; ARRAY creates an array; AREF reads A[i]; ASET writes A[i] <- v.
; An array is a bounded list; the index is exact D24+ arithmetic (C1-SUB1).
; No host array; no new primitive. SENS-owned law.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-MAKE-ARRAY
  (функція (SIZE)
    (C1-ARRAY-FILL SIZE (як-є ()))))

(визначити C1-ARRAY-FILL
  (мітка C1-ARRAY-FILL
    (функція (SIZE ACC)
      (за-умовою
        ((тотожне? SIZE 0) ACC)
        (так (C1-ARRAY-FILL (C1-SUB1 SIZE) (сполучити 0 ACC)))))))

(визначити C1-ARRAY
  (функція (SIZE)
    (C1-MAKE-ARRAY SIZE)))

(визначити C1-AREF
  (мітка C1-AREF
    (функція (ARR IDX)
      (за-умовою
        ((тотожне? IDX 0) (перше ARR))
        (так (C1-AREF (решта ARR) (C1-SUB1 IDX)))))))

(визначити C1-ASET
  (мітка C1-ASET
    (функція (ARR IDX VAL)
      (за-умовою
        ((тотожне? IDX 0) (сполучити VAL (решта ARR)))
        (так
         (сполучити (перше ARR) (C1-ASET (решта ARR) (C1-SUB1 IDX) VAL)))))))

(визначити C1-ARRAYP
  (функція (X)
    (за-умовою
      ((тотожне? X (як-є ())) так)
      ((C1-PAIRP X) так)
      (так ні))))
