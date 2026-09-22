; Core1 S3 compiler prelude.
;
; This file is an explicit Lisp-owned mechanism for compiling the existing
; Core1 NOT law before wsm-my-lisp/lib/compiler.lisp.
;
; Semantic authority does not originate here. The law is already present in:
;   lib/core1.lisp                       C1-APPLY-PRIMITIVE / NOT
;   contracts/core1-historical-sid-map.lisp  SID 00100001 -> historical NOT
;
; Core1 truth is historical T/NIL. Do not replace this result domain with
; Core4 identity-relation / structural-kind records.
;
; The definition intentionally uses only historical two-part COND + QUOTE.
; It does not require CML to invent a NOT primitive or to know Core1 meaning.
;
; CML may key this definition/call by SID 00100001 as a compilation mechanism,
; but the selected law remains Core1-owned.

(def not
  (lambda (value)
    (cond
      (value (quote ()))
      ((quote T) (quote T)))))

(quote core1-s3-compiler-prelude-ready)
