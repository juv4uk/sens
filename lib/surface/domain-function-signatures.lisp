; Exact-domain tooling metadata.
;
; Authority is domain identity + admitted domain law. This file carries only
; tooling metadata (kind/arity/signature/documentation) for already-ratified
; residents. It never mints occupancy and never names a legacy Function8 byte.
;
; Row:
;   (width "bits" (kind builtin|syntax) (arity N|(at-least N))
;      (sig "...") (doc "..."))
(
  (#b11 "001" (kind syntax) (arity 1) (sig "(quote value)") (doc "Return value unevaluated"))
  (#b11 "010" (kind builtin) (arity 1) (sig "(atom? value)") (doc "Test whether value is not a pair"))
  (#b11 "011" (kind syntax) (arity (at-least 0)) (sig "(cond (test result) ...)") (doc "Evaluate the first matching clause"))
  (#b11 "100" (kind builtin) (arity #b10) (sig "(cons head tail)") (doc "Create a pair"))
  (#b11 "101" (kind builtin) (arity 1) (sig "(car pair)") (doc "Return the first element of a pair"))
  (#b11 "110" (kind builtin) (arity 1) (sig "(cdr pair)") (doc "Return the tail of a pair"))
  (#b11 "111" (kind builtin) (arity #b10) (sig "(eq? left right)") (doc "Test structural or identity equality"))

  (#b100 "0010" (kind syntax) (arity (at-least #b10)) (sig "(lambda (params) body ...)") (doc "Create an anonymous function"))
  (#b100 "0011" (kind syntax) (arity #b10) (sig "(define name value)") (doc "Bind name in the current scope"))
  (#b100 "1010" (kind builtin) (arity 1) (sig "(caar pair)") (doc "Compose CAR after CAR"))
  (#b100 "1011" (kind builtin) (arity 1) (sig "(cadr pair)") (doc "Compose CAR after CDR"))
  (#b100 "1100" (kind builtin) (arity 1) (sig "(cdar pair)") (doc "Compose CDR after CAR"))
  (#b100 "1101" (kind builtin) (arity 1) (sig "(cddr pair)") (doc "Compose CDR after CDR"))

  (#b101 "01010" (kind builtin) (arity (at-least 0)) (sig "(+ number ...)") (doc "Sum all arguments"))
  (#b101 "01011" (kind builtin) (arity (at-least 1)) (sig "(- number ...)") (doc "Subtract or negate"))
  (#b101 "01110" (kind builtin) (arity (at-least 1)) (sig "(< number ...)") (doc "Less-than chain comparison"))
  (#b101 "01111" (kind builtin) (arity (at-least 1)) (sig "(> number ...)") (doc "Greater-than chain comparison"))
  (#b101 "10010" (kind builtin) (arity (at-least 0)) (sig "(* number ...)") (doc "Multiply all arguments"))
  (#b101 "10011" (kind builtin) (arity (at-least 1)) (sig "(/ number ...)") (doc "Perform exact rational division"))
)
