; lib/macro.lisp — macro definition derived inside my-lisp.
; lib/macro.lisp — визначення макросів, виведене всередині my-lisp.
;
; This file is the executable reduction proof for DEFMACRO:
;
;   DEFMACRO = DEFINE + LAMBDA + MAKE_MACRO + list construction
;
; `make-macro` is the narrow host substrate Closure -> Macro. The behavior of
; macro definition is still constructed here in the language itself.
;
; This source deliberately binds NO human surface name. It evaluates to one
; first-class Macro value; the bootstrap loader then exposes that same value
; directly under the ratified peer spellings `defmacro` and
; `визначити-макрос`. Thus no human surface is implemented as an alias of another.
;
; Necessary forms are selected by semantic identity after ordinary source
; resolution. Byte SID text is metadata and is deliberately NOT executable
; spelling, so this data->code boundary uses the admitted source spellings
; `lambda` and `define`; the evaluator resolves them through the registry to
; SIDs 8 and 9 before selecting mechanisms. They are not host semantic constants.
; The bootstrap lambda uses the Lisp-family bare-symbol rest form (`args`) so
; the data->code boundary stays a proper list throughout. Its minimum-arity
; contract (name + parameter form) is preserved here in Lisp; `?:` and `.?`
; are language-neutral Canon spellings, and a deliberately wrong-arity
; `make-macro` call retains the named Arity failure class.

(make-macro
  (eval
    (cons (quote lambda)
      (cons (quote args)
        (quote
          ((?:
             ((.? args)
              (structural-kind empty-list)
              (make-macro))
             ((.? (cdr args))
              (structural-kind empty-list)
              (make-macro))
             (t
              t
              (cons (quote define)
                (cons (car args)
                  (cons
                    (cons (quote make-macro)
                      (cons
                        (cons (quote lambda)
                          (cons
                            (car (cdr args))
                            (cdr (cdr args))))
                        (quote ())))
                    (quote ()))))))))))))
