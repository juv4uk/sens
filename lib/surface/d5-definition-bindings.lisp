; D5 definition-to-identity mechanism projection.
; Projection only: semantic authority is #3331 / #3305.
; Existing Lisp definition names supply mechanisms for already-ratified exact D5 identities.
; They do not choose or create semantic meaning.
;
; Row format:
; (row "SOURCE-NAME" "D5-BITS")

(d5-definition-bindings
  (schema d5-definition-bindings/1)
  (status projection-only)
  (authority "#3331/#3305")
  (row "reverse" "10100")
  (row "reverse-onto" "10101")
  (row "quotient" "10111")
  (row "assoc" "11100")
  (row "member?" "11101")
  (row "subst" "11111")
)
