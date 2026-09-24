; #1180 — Core1 compiler-facing SID8 resolver.
;
; This file owns no name->SID table. Core1 already owns the admitted primitive
; projection in C1-PRIMITIVE-IDENTITY. Compiler/bootstrap consumers use this
; stable entrypoint instead of copying that projection downstream.
;
; Result:
;   admitted Core1 primitive surface -> exact bare SID8
;   unadmitted/unknown surface        -> NIL
;
; In particular, + and - remain unadmitted here until Core1 itself admits and
; executes them. No quoted/string SID compatibility representation is accepted.

(DEFINE C1-COMPILER-SID-FOR-SURFACE
  (LAMBDA (NAME)
    (C1-PRIMITIVE-IDENTITY NAME)))
