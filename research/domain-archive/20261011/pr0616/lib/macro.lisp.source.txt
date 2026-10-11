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
; `визначити-макрос` (plus the historical `defmacro-derived` compatibility
; spelling). Thus no human surface is implemented as an alias of another.
;
; Necessary forms are selected by numeric semantic identity, not by an EN/UK
; spelling. `string->symbol` constructs the pure Symbol("0010") bootstrap
; LAMBDA datum and first-class `eval` evaluates that datum in the current
; environment. The bootstrap lambda uses the Lisp-family bare-symbol rest form
; (`args`) so the data->code boundary stays a proper list throughout. Its
; minimum-arity contract (name + parameter form) is preserved here in Lisp;
; `?:` and `.?` are language-neutral Canon spellings, and a deliberately
; wrong-arity `make-macro` call retains the named Arity failure class. The
; expansion emits pure Symbol("0010") / Symbol("0011") heads. No additional
; source spelling or reader syntax exists. Sanskrit remains explicitly missing.

(make-macro
  (eval
    (cons (string->symbol "0010")
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
              (cons (string->symbol "0011")
                (cons (car args)
                  (cons
                    (cons (quote make-macro)
                      (cons
                        (cons (string->symbol "0010")
                          (cons
                            (car (cdr args))
                            (cdr (cdr args))))
                        (quote ())))
                    (quote ()))))))))))))
