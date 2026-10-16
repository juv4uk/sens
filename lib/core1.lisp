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

(0011 C1-SECOND
  (0010 (X)
    (1001 X)))

(0011 C1-THIRD
  (0010 (X)
    (10011 X)))

(0011 C1-FOURTH
  (0010 (X)
    (10011 (011 X))))

(0011 C1-MAKE-ERROR
  (0010 (KIND DETAIL)
    (111 (001 C1-ERROR)
      (111 KIND
        (111 DETAIL (001 ()))))))

(0011 C1-ERRORP
  (0010 (VALUE)
    (110
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 C1-ERROR)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-MAKE-FOUND
  (0010 (VALUE)
    (111 (001 C1-FOUND)
      (111 VALUE (001 ())))))

(0011 C1-FOUNDP
  (0010 (VALUE)
    (110
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 C1-FOUND)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-FOUND-VALUE
  (0010 (VALUE)
    (1001 VALUE)))

(0011 C1-LOOKUP-IN
  (00100 C1-LOOKUP-IN
    (0010 (NAME ENV)
      (110
        ((101 ENV (001 ())) (001 C1-MISSING))
        ((101 (100 (100 ENV)) NAME)
         (C1-MAKE-FOUND (011 (100 ENV))))
        (#d1:1
         (C1-LOOKUP-IN NAME (011 ENV)))))))

(0011 C1-ADMITTED-SID-VALUEP
  (0010 (VALUE)
    (110
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

(0011 C1-PRIMITIVE-IDENTITY
  (0010 (NAME)
    (110
      ((101 NAME 010) 010)
      ((101 NAME 101) 101)
      ((101 NAME 111) 111)
      ((101 NAME 100) 100)
      ((101 NAME 011) 011)
      ((101 NAME 0100) 0100)
      ((101 NAME 1110) 1110)
      ((101 NAME (001 ATOM)) 010)
      ((101 NAME (001 atom)) 010)
      ((101 NAME (001 EQ))   101)
      ((101 NAME (001 eq))   101)
      ((101 NAME (001 CONS)) 111)
      ((101 NAME (001 cons)) 111)
      ((101 NAME (001 CAR))  100)
      ((101 NAME (001 car))  100)
      ((101 NAME (001 CDR))  011)
      ((101 NAME (001 cdr))  011)
      ((101 NAME (001 LIST)) 1110)
      ((101 NAME (001 list)) 1110)
      ((101 NAME (001 NOT))  0100)
      ((101 NAME (001 not))  0100)
      (#d1:1 (001 ())))))

(0011 C1-DEFAULT
  (0010 (NAME)
    ((0010 (IDENTITY)
       (110
         ((101 IDENTITY (001 ()))
          (C1-MAKE-ERROR (001 UNBOUND) NAME))
         (#d1:1 IDENTITY)))
     (C1-PRIMITIVE-IDENTITY NAME))))

(0011 C1-LOOKUP
  (0010 (NAME ENV GLOBAL)
    ((0010 (LOCAL)
       (110
         ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
         (#d1:1
          ((0010 (TOP)
             (110
               ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
               (#d1:1 (C1-DEFAULT NAME))))
           (C1-LOOKUP-IN NAME GLOBAL)))))
     (C1-LOOKUP-IN NAME ENV))))

(0011 C1-FUNARGP
  (0010 (VALUE)
    (110
      ((010 VALUE) #d1:0)
      ((101 (100 VALUE) (001 FUNARG)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-ONE-ARGP
  (0010 (ARGS)
    (110
      ((010 ARGS) #d1:0)
      ((101 (011 ARGS) (001 ())) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-TWO-ARGP
  (0010 (ARGS)
    (110
      ((010 ARGS) #d1:0)
      ((010 (011 ARGS)) #d1:0)
      ((101 (011 (011 ARGS)) (001 ())) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-BIND
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

(0011 C1-APPLY-PRIMITIVE
  (0010 (SID ARGS)
    (110
      ((101 SID 1110) ARGS)
      ((101 SID 0100)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((101 (100 ARGS) (001 ())) #d1:1)
            (#d1:1 (001 ()))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 010)
       (110
         ((C1-ONE-ARGP ARGS) (010 (100 ARGS)))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 101)
       (110
         ((C1-TWO-ARGP ARGS) (101 (100 ARGS) (100 (011 ARGS))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 111)
       (110
         ((C1-TWO-ARGP ARGS) (111 (100 ARGS) (100 (011 ARGS))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 100)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((010 (100 ARGS))
             (C1-MAKE-ERROR (001 TYPE) (001 CAR-REQUIRES-PAIR)))
            (#d1:1 (100 (100 ARGS)))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 011)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((010 (100 ARGS))
             (C1-MAKE-ERROR (001 TYPE) (001 CDR-REQUIRES-PAIR)))
            (#d1:1 (011 (100 ARGS)))))
         (#d1:1 (C1-MAKE-ERROR (001 ARITY) SID))))
      (#d1:1
       (C1-MAKE-ERROR (001 UNSUPPORTED-PRIMITIVE) SID)))))

(0011 C1-EVLIS
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

(0011 C1-EVCON
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

(0011 C1-APPLY
  (0010 (FN ARGS GLOBAL)
    (110
      ((C1-ERRORP FN) FN)
      ((C1-PRIMITIVE-IDENTITY FN)
       (C1-APPLY-PRIMITIVE (C1-PRIMITIVE-IDENTITY FN) ARGS))
      ((C1-FUNARGP FN)
       (FN ARGS GLOBAL))
      (#d1:1
       (C1-MAKE-ERROR (001 NOT-CALLABLE) FN)))))

(0011 C1-QUOTE-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 001) #d1:1)
      ((101 NAME (001 QUOTE)) #d1:1)
      ((101 NAME (001 quote)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-COND-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 110) #d1:1)
      ((101 NAME (001 COND)) #d1:1)
      ((101 NAME (001 cond)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-LAMBDA-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 0010) #d1:1)
      ((101 NAME (001 LAMBDA)) #d1:1)
      ((101 NAME (001 lambda)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-DEFINE-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 0011) #d1:1)
      ((101 NAME (001 DEFINE)) #d1:1)
      ((101 NAME (001 define)) #d1:1)
      ((101 NAME (001 def)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-LABEL-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 00100) #d1:1)
      ((101 NAME (001 LABEL)) #d1:1)
      ((101 NAME (001 label)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-EVAL
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

(0011 C1-MAKE-WORLD
  (0010 (VALUE GLOBAL)
    (111 (001 C1-WORLD)
      (111 VALUE
        (111 GLOBAL (001 ()))))))

(0011 C1-WORLD-VALUE
  (0010 (WORLD)
    (1001 WORLD)))

(0011 C1-WORLD-GLOBAL
  (0010 (WORLD)
    (10011 WORLD)))

(0011 C1-DEFINITIONP
  (0010 (FORM)
    (110
      ((010 FORM) #d1:0)
      ((C1-DEFINE-NAMEP (100 FORM)) #d1:1)
      (#d1:1 #d1:0))))

(0011 C1-EVAL-PROGRAM
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

(0011 C1-WORLD-EVAL
  (0010 (WORLD EXPR)
    (C1-MAKE-WORLD
      (C1-EVAL EXPR (001 ()) (C1-WORLD-GLOBAL WORLD))
      (C1-WORLD-GLOBAL WORLD))))

(0011 C1-EVAL-PROGRAM-THEN
  (0010 (FORMS EXPR)
    ((0010 (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM FORMS (001 ())))))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: reader + reclamation (the parts a bootstrap cannot omit).
; Reader: dotted-pair list reader over a token list (no host I/O).
; Reclamation: McCarthy 1960 free-storage mark/sweep, expressed as exact laws.
; Both are SENS-owned; no host name interpretation, no Rust/Python backdoor.
; ─────────────────────────────────────────────────────────────────────────────

(0011 C1-READ
  (00100 C1-READ
    (0010 (TOKENS)
      (110
        ((101 TOKENS (001 ())) (001 ()))
        ((101 (100 TOKENS) 010)          ; ATOM token -> the token itself
         (100 TOKENS))
        (#d1:1
         (C1-READ-LIST TOKENS))))))

(0011 C1-READ-LIST
  (00100 C1-READ-LIST
    (0010 (TOKENS)
      (110
        ((101 TOKENS (001 ())) (001 ()))
        ((101 (100 TOKENS) 110)          ; DOT token -> dotted tail
         (100 (011 TOKENS)))
        (#d1:1
         (111 (C1-READ (100 TOKENS))
              (C1-READ-LIST (011 TOKENS))))))))

(0011 C1-RECLAIM
  (0010 (ROOTS CELLS)
    (C1-SWEEP (C1-MARK-ALL ROOTS CELLS) CELLS)))

(0011 C1-MARK-ALL
  (00100 C1-MARK-ALL
    (0010 (ROOTS CELLS)
      (110
        ((101 ROOTS (001 ())) CELLS)
        (#d1:1
         (C1-MARK-ALL (011 ROOTS)
                      (C1-MARK (100 ROOTS) CELLS)))))))

(0011 C1-MARK
  (00100 C1-MARK
    (0010 (REF CELLS)
      (110
        ((101 REF (001 ())) CELLS)
        ((101 CELLS (001 ())) CELLS)
        (#d1:1
         (C1-MARK-CHILDREN REF (C1-MARK-CELL REF CELLS)))))))

(0011 C1-MARK-CELL
  (0010 (REF CELLS)
    (110
      ((101 (100 (100 CELLS)) REF)          ; head cell reached -> mark it
       (111 (111 (100 (100 CELLS)) #d1:1) (011 CELLS)))
      (#d1:1 CELLS))))

(0011 C1-MARK-CHILDREN
  (0010 (REF CELLS)
    (110
      ((101 (100 (100 CELLS)) REF)
       (C1-MARK (011 (100 CELLS))
                (C1-MARK (011 (011 (100 CELLS))) CELLS)))
      (#d1:1 CELLS))))

(0011 C1-SWEEP
  (00100 C1-SWEEP
    (0010 (MARKED CELLS)
      (110
        ((101 CELLS (001 ())) (001 ()))
        ((101 (011 (100 CELLS)) #d1:1)   ; marked -> keep
         (111 (100 CELLS) (C1-SWEEP MARKED (011 CELLS))))
        (#d1:1                            ; unmarked -> return to free list
         (C1-SWEEP MARKED (011 CELLS)))))))

(0011 C1-FREE
  (0010 (CELLS)
    (C1-SWEEP (001 ()) CELLS)))

; ─────────────────────────────────────────────────────────────────────────────
; Bootstrap additions: arithmetic, delegating to the RATIFIED D5/D6 laws.
; Numbers are D24+; the functions are D5/D6 (d5-ratification.lisp, d6-ratification.lisp):
;   D5:01010 PLUS · D5:01011 DIFFERENCE · D5:10110 TIMES · D5:10111 QUOTIENT
;   D6:001110 ADD1 · D6:001111 SUB1 · D6:010010 NEG · D6:010100 REMAINDER
; C1-* here are thin SENS wrappers: no new primitive, no host arithmetic.
; ─────────────────────────────────────────────────────────────────────────────

(0011 C1-PLUS
  (0010 (A B)
    (01010 A B)))

(0011 C1-DIFFERENCE
  (0010 (A B)
    (01011 A B)))

(0011 C1-TIMES
  (0010 (A B)
    (10110 A B)))

(0011 C1-QUOTIENT
  (0010 (A B)
    (10111 A B)))

(0011 C1-ADD1
  (0010 (A)
    (001110 A)))

(0011 C1-SUB1
  (0010 (A)
    (001111 A)))

(0011 C1-NEG
  (0010 (A)
    (010010 A)))

(0011 C1-REMAINDER
  (0010 (A B)
    (010100 A B)))

(0011 C1-ZEROP
  (0010 (A)
    (101 A 0)))
