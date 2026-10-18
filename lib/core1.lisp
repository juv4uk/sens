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
  (функція (X)
    (друге X)))

(визначити C1-THIRD
  (функція (X)
    (10011 X)))

(визначити C1-FOURTH
  (функція (X)
    (10011 (011 X))))

(визначити C1-MAKE-ERROR
  (функція (KIND DETAIL)
    (сполучити (як-є C1-ERROR)
      (сполучити KIND
        (сполучити DETAIL (як-є ()))))))

(визначити C1-ERRORP
  (функція (VALUE)
    (за-умовою
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 C1-ERROR)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-MAKE-FOUND
  (функція (VALUE)
    (сполучити (як-є C1-FOUND)
      (сполучити VALUE (як-є ())))))

(визначити C1-FOUNDP
  (функція (VALUE)
    (за-умовою
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 C1-FOUND)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-FOUND-VALUE
  (функція (VALUE)
    (друге VALUE)))

(визначити C1-LOOKUP-IN
  (00100 C1-LOOKUP-IN
    (0010 (NAME ENV)
      (110
        ((101 ENV (001 ())) (001 C1-MISSING))
        ((101 (100 (100 ENV)) NAME)
         (C1-MAKE-FOUND (011 (100 ENV))))
        (#d1:1
         (C1-LOOKUP-IN NAME (011 ENV)))))))

(визначити C1-ADMITTED-SID-VALUEP
  (функція (VALUE)
    (за-умовою
      ((101 VALUE 001) #d1:1)
      ((101 VALUE 010) #d1:1)
      ((101 VALUE 101) #d1:1)
      ((101 VALUE 111) #d1:1)
      ((101 VALUE 100) #d1:1)
      ((101 VALUE 011) #d1:1)
      ((101 VALUE 110) #d1:1)
      ((101 VALUE 0010) #d1:1)
      ((101 VALUE 0011) #d1:1)
      ((101 VALUE 01010) #d1:1)
      ((101 VALUE 01011) #d1:1)
      ((101 VALUE 0100) #d1:1)
      ((101 VALUE 1110) #d1:1)
      (#d1:1 (001 ())))))

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
      (#d1:1 (001 ())))))

(визначити C1-DEFAULT
  (функція (NAME)
    ((функція (IDENTITY)
       (за-умовою
         ((тотожне? IDENTITY (як-є ()))
          (C1-MAKE-ERROR (як-є UNBOUND) NAME))
         (#d1:1 IDENTITY)))
     (C1-PRIMITIVE-IDENTITY NAME))))

(визначити C1-LOOKUP
  (функція (NAME ENV GLOBAL)
    ((функція (LOCAL)
       (за-умовою
         ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
         (#d1:1
          ((функція (TOP)
             (за-умовою
               ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
               (#d1:1 (C1-DEFAULT NAME))))
           (C1-LOOKUP-IN NAME GLOBAL)))))
     (C1-LOOKUP-IN NAME ENV))))

(визначити C1-FUNARGP
  (функція (VALUE)
    (за-умовою
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 FUNARG)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-ONE-ARGP
  (функція (ARGS)
    (за-умовою
      ((010 ARGS) #d1:0)
      ((101 (011 ARGS) (001 ())) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-TWO-ARGP
  (функція (ARGS)
    (за-умовою
      ((010 ARGS) #d1:0)
      ((010 (011 ARGS)) #d1:0)
      ((101 (011 (011 ARGS)) (001 ())) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-BIND
  (00100 C1-BIND
    (0010 (PARAMS ARGS ENV)
      (110
        ((101 PARAMS (001 ()))
         (110
           ((101 ARGS (001 ())) ENV)
           (#d1:1 (C1-MAKE-ERROR (001 ARITY) (001 TOO-MANY-ARGUMENTS)))))
        ((101 ARGS (001 ()))
         (C1-MAKE-ERROR (001 ARITY) (001 TOO-FEW-ARGUMENTS)))
        (#d1:1
         (C1-BIND
           (011 PARAMS)
           (011 ARGS)
           (111 (111 (100 PARAMS) (100 ARGS)) ENV)))))))

(визначити C1-APPLY-PRIMITIVE
  (функція (SID ARGS)
    (за-умовою
      ((тотожне? SID 1110) ARGS)
      ((тотожне? SID 0100)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((101 (100 ARGS) (001 ())) #d1:1)
            (#d1:1 (001 ()))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((тотожне? SID 010)
       (за-умовою
         ((C1-ONE-ARGP ARGS) (атом? (перше ARGS)))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((тотожне? SID 101)
       (за-умовою
         ((C1-TWO-ARGP ARGS) (тотожне? (перше ARGS) (перше (решта ARGS))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((тотожне? SID 111)
       (за-умовою
         ((C1-TWO-ARGP ARGS) (сполучити (перше ARGS) (перше (решта ARGS))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((тотожне? SID 100)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((атом? (перше ARGS))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CAR-REQUIRES-PAIR)))
            (#d1:1 (100 (100 ARGS)))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((тотожне? SID 011)
       (за-умовою
         ((C1-ONE-ARGP ARGS)
          (за-умовою
            ((атом? (перше ARGS))
             (C1-MAKE-ERROR (як-є TYPE) (як-є CDR-REQUIRES-PAIR)))
            (#d1:1 (011 (100 ARGS)))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      (#d1:1
       (C1-MAKE-ERROR (як-є UNSUPPORTED-PRIMITIVE) SID)))))

(визначити C1-EVLIS
  (00100 C1-EVLIS
    (0010 (FORMS ENV GLOBAL)
      (110
        ((101 FORMS (001 ())) (001 ()))
        (#d1:1
         ((0010 (FIRST)
            (110
              ((C1-ERRORP FIRST) FIRST)
              (#d1:1
               ((0010 (REST)
                  (110
                    ((C1-ERRORP REST) REST)
                    (#d1:1 (111 FIRST REST))))
                (C1-EVLIS (011 FORMS) ENV GLOBAL)))))
          (C1-EVAL (100 FORMS) ENV GLOBAL)))))))

(визначити C1-EVCON
  (00100 C1-EVCON
    (0010 (CLAUSES ENV GLOBAL)
      (110
        ((101 CLAUSES (001 ()))
         (C1-MAKE-ERROR (001 UNSATISFIED-CONDITIONAL) (001 ())))
        (#d1:1
         ((0010 (TEST-VALUE)
            (110
              ((C1-ERRORP TEST-VALUE) TEST-VALUE)
              ((101 TEST-VALUE (001 ()))
               (C1-EVCON (011 CLAUSES) ENV GLOBAL))
              (#d1:1
               (C1-EVAL
                 (1001 (100 CLAUSES))
                 ENV
                 GLOBAL))))
          (C1-EVAL
            (100 (100 CLAUSES))
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
      (#d1:1
       (C1-MAKE-ERROR (як-є NOT-CALLABLE) FN)))))

(визначити C1-QUOTE-NAMEP
  (функція (NAME)
    (за-умовою
      ((101 NAME 001) #d1:1)
      ((101 NAME (001 QUOTE)) #d1:1)
      ((101 NAME (001 quote)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-COND-NAMEP
  (функція (NAME)
    (за-умовою
      ((101 NAME 110) #d1:1)
      ((101 NAME (001 COND)) #d1:1)
      ((101 NAME (001 cond)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-LAMBDA-NAMEP
  (функція (NAME)
    (за-умовою
      ((101 NAME 0010) #d1:1)
      ((101 NAME (001 LAMBDA)) #d1:1)
      ((101 NAME (001 lambda)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-DEFINE-NAMEP
  (функція (NAME)
    (за-умовою
      ((101 NAME 0011) #d1:1)
      ((101 NAME (001 DEFINE)) #d1:1)
      ((101 NAME (001 define)) #d1:1)
      ((101 NAME (001 def)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-LABEL-NAMEP
  (функція (NAME)
    (за-умовою
      ((101 NAME 00100) #d1:1)
      ((101 NAME (001 LABEL)) #d1:1)
      ((101 NAME (001 label)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-EVAL
  (00100 C1-EVAL
    (0010 (EXPR ENV GLOBAL)
      (110
        ((010 EXPR)
         (110
           ((101 EXPR (001 ())) (001 ()))
           ((101 EXPR (001 nil)) (001 ()))
           ((101 EXPR (001 t)) #d1:1)
           ((C1-ADMITTED-SID-VALUEP EXPR) EXPR)
           (#d1:1 (C1-LOOKUP EXPR ENV GLOBAL))))
        ((C1-QUOTE-NAMEP (100 EXPR))
         (1001 EXPR))
        ((C1-COND-NAMEP (100 EXPR))
         (C1-EVCON (011 EXPR) ENV GLOBAL))
        ((C1-LABEL-NAMEP (100 EXPR))
         (C1-EVAL (10011 EXPR) ENV GLOBAL))
        ((C1-LAMBDA-NAMEP (100 EXPR))
         (00001
           (0010 (ARGS GLOBAL-AT-CALL)
             ((0010 (BOUND)
                (110
                  ((C1-ERRORP BOUND) BOUND)
                  (#d1:1
                   (C1-EVAL
                     (10011 EXPR)
                     BOUND
                     GLOBAL-AT-CALL))))
              (C1-BIND
                (1001 EXPR)
                ARGS
                ENV)))))
        ((C1-DEFINE-NAMEP (100 EXPR))
         (C1-MAKE-ERROR
           (001 INVALID-FORM)
           (001 DEFINE-IS-TOP-LEVEL-ONLY)))
        (#d1:1
         ((0010 (FN)
            (110
              ((C1-ERRORP FN) FN)
              (#d1:1
               ((0010 (ARGS)
                  (110
                    ((C1-ERRORP ARGS) ARGS)
                    (#d1:1 (C1-APPLY FN ARGS GLOBAL))))
                (C1-EVLIS (011 EXPR) ENV GLOBAL)))))
          (C1-EVAL (100 EXPR) ENV GLOBAL)))))))

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
    (10011 WORLD)))

(визначити C1-DEFINITIONP
  (функція (FORM)
    (за-умовою
      ((010 FORM) #d1:0)
      ((C1-DEFINE-NAMEP (100 FORM)) #d1:1)
      (#d1:1 #d1:0))))

(визначити C1-EVAL-PROGRAM
  (00100 C1-EVAL-PROGRAM
    (0010 (FORMS GLOBAL)
      (110
        ((101 FORMS (001 ()))
         (C1-MAKE-WORLD (001 ()) GLOBAL))
        ((C1-DEFINITIONP (100 FORMS))
         ((0010 (FORM)
            ((0010 (VALUE)
               (110
                 ((C1-ERRORP VALUE)
                  (C1-MAKE-WORLD VALUE GLOBAL))
                 (#d1:1
                  (C1-EVAL-PROGRAM
                    (011 FORMS)
                    (111
                      (111 (1001 FORM) VALUE)
                      GLOBAL)))))
             (C1-EVAL (10011 FORM) (001 ()) GLOBAL)))
          (100 FORMS)))
        ((101 (011 FORMS) (001 ()))
         (C1-MAKE-WORLD
           (C1-EVAL (100 FORMS) (001 ()) GLOBAL)
           GLOBAL))
        (#d1:1
         ((0010 (VALUE)
            (110
              ((C1-ERRORP VALUE)
               (C1-MAKE-WORLD VALUE GLOBAL))
              (#d1:1
               (C1-EVAL-PROGRAM
                 (011 FORMS)
                 GLOBAL))))
          (C1-EVAL (100 FORMS) (001 ()) GLOBAL)))))))

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
  (00100 C1-READ
    (функція (TOKENS)
      (за-умовою
        ((тотожне? TOKENS (як-є ())) (як-є ()))
        ((тотожне? (перше TOKENS) 010)          ; ATOM token -> the token itself
         (перше TOKENS))
        (#d1:1
         (C1-READ-LIST TOKENS))))))

(визначити C1-READ-LIST
  (00100 C1-READ-LIST
    (функція (TOKENS)
      (за-умовою
        ((тотожне? TOKENS (як-є ())) (як-є ()))
        ((тотожне? (перше TOKENS) 110)          ; DOT token -> dotted tail
         (перше (решта TOKENS)))
        (#d1:1
         (сполучити (C1-READ (перше TOKENS))
              (C1-READ-LIST (решта TOKENS))))))))

(визначити C1-RECLAIM
  (функція (ROOTS CELLS)
    (C1-SWEEP (C1-MARK-ALL ROOTS CELLS) CELLS)))

(визначити C1-MARK-ALL
  (00100 C1-MARK-ALL
    (функція (ROOTS CELLS)
      (за-умовою
        ((тотожне? ROOTS (як-є ())) CELLS)
        (#d1:1
         (C1-MARK-ALL (решта ROOTS)
                      (C1-MARK (перше ROOTS) CELLS)))))))

(визначити C1-MARK
  (00100 C1-MARK
    (функція (REF CELLS)
      (за-умовою
        ((тотожне? REF (як-є ())) CELLS)
        ((тотожне? CELLS (як-є ())) CELLS)
        (#d1:1
         (C1-MARK-CHILDREN REF (C1-MARK-CELL REF CELLS)))))))

(визначити C1-MARK-CELL
  (функція (REF CELLS)
    (за-умовою
      ((тотожне? (перше (перше CELLS)) REF)          ; head cell reached -> mark it
       (111 (111 (100 (100 CELLS)) #d1:1) (011 CELLS)))
      (#d1:1 CELLS))))

(визначити C1-MARK-CHILDREN
  (функція (REF CELLS)
    (за-умовою
      ((тотожне? (перше (перше CELLS)) REF)
       (C1-MARK (решта (перше CELLS))
                (C1-MARK (решта (решта (перше CELLS))) CELLS)))
      (#d1:1 CELLS))))

(визначити C1-SWEEP
  (00100 C1-SWEEP
    (функція (MARKED CELLS)
      (за-умовою
        ((тотожне? CELLS (як-є ())) (як-є ()))
        ((101 (011 (100 CELLS)) #d1:1)   ; marked -> keep
         (сполучити (перше CELLS) (C1-SWEEP MARKED (решта CELLS))))
        (#d1:1                            ; unmarked -> return to free list
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
    (01010 A B)))

(визначити C1-DIFFERENCE
  (функція (A B)
    (01011 A B)))

(визначити C1-TIMES
  (функція (A B)
    (10110 A B)))

(визначити C1-QUOTIENT
  (функція (A B)
    (10111 A B)))

(визначити C1-ADD1
  (функція (A)
    (001110 A)))

(визначити C1-SUB1
  (функція (A)
    (001111 A)))

(визначити C1-NEG
  (функція (A)
    (010010 A)))

(визначити C1-REMAINDER
  (функція (A B)
    (010100 A B)))

(визначити C1-ZEROP
  (функція (A)
    (тотожне? A 0)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: Appendix-B features (McCarthy 1960, Appendix B).
; PROPLIST (GET/PUT), PROG/GO (imperative program feature), APPEND/ASSOC
; (core support functions used by the evaluator formula). SENS-owned laws.
; ─────────────────────────────────────────────────────────────────────────────

(визначити C1-ASSOC
  (00100 C1-ASSOC
    (функція (KEY ALIST)
      (за-умовою
        ((тотожне? ALIST (як-є ())) (як-є C1-MISSING))
        ((тотожне? (перше (перше ALIST)) KEY)
         (перше ALIST))
        (#d1:1 (C1-ASSOC KEY (011 ALIST)))))))

(визначити C1-APPEND
  (00100 C1-APPEND
    (функція (X Y)
      (за-умовою
        ((тотожне? X (як-є ())) Y)
        (#d1:1 (111 (100 X) (C1-APPEND (011 X) Y)))))))

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
  (00100 C1-PROG-RUN
    (функція (PC BODY)
      (за-умовою
        ((тотожне? PC (як-є ())) (як-є ()))
        ((C1-LABELP (перше PC))
         (C1-PROG-RUN (решта PC) BODY))          ; a label line: skip
        (#d1:1
         (C1-PROG-RUN (решта PC) BODY))))))

(визначити C1-GO
  (функція (LABEL BODY)
    (C1-PROG-SEEK LABEL BODY)))

(визначити C1-PROG-SEEK
  (00100 C1-PROG-SEEK
    (функція (LABEL BODY)
      (за-умовою
        ((тотожне? BODY (як-є ())) (як-є ()))
        ((тотожне? (перше (перше BODY)) LABEL) BODY)     ; found the label
        (#d1:1 (C1-PROG-SEEK LABEL (011 BODY)))))))

(визначити C1-LABELP
  (функція (STATEMENT)
    (за-умовою
      ((010 STATEMENT) #d1:0)
      ((C1-ATOM (100 STATEMENT)) #d1:1)         ; a bare symbol = a label
      (#d1:1 #d1:0))))

(визначити C1-ATOM
  (функція (X)
    (за-умовою
      ((101 X (001 ())) #d1:1)
      ((C1-PAIRP X) #d1:0)
      (#d1:1 #d1:1))))

(визначити C1-PAIRP
  (функція (X)
    (за-умовою
      ((010 X) #d1:0)
      (#d1:1 #d1:1))))

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
  (00100 C1-ARRAY-FILL
    (функція (SIZE ACC)
      (за-умовою
        ((тотожне? SIZE 0) ACC)
        (#d1:1 (C1-ARRAY-FILL (C1-SUB1 SIZE) (111 0 ACC)))))))

(визначити C1-ARRAY
  (функція (SIZE)
    (C1-MAKE-ARRAY SIZE)))

(визначити C1-AREF
  (00100 C1-AREF
    (функція (ARR IDX)
      (за-умовою
        ((тотожне? IDX 0) (перше ARR))
        (#d1:1 (C1-AREF (011 ARR) (C1-SUB1 IDX)))))))

(визначити C1-ASET
  (00100 C1-ASET
    (функція (ARR IDX VAL)
      (за-умовою
        ((тотожне? IDX 0) (сполучити VAL (решта ARR)))
        (#d1:1
         (сполучити (перше ARR) (C1-ASET (решта ARR) (C1-SUB1 IDX) VAL)))))))

(визначити C1-ARRAYP
  (функція (X)
    (за-умовою
      ((101 X (001 ())) #d1:1)
      ((C1-PAIRP X) #d1:1)
      (#d1:1 #d1:0))))
