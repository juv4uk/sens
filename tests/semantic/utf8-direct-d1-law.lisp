; Two executable SENS UTF-8 structural verdicts: no numeric coercion.
; Arithmetic byte boundaries need separately admitted D24+ operands, so they
; must not be presented as passing evidence by this witness.
; Wrong results select the impossible CAR(QUOTE EMPTY) branch.

(110
  ((101 (utf8-all-bytes? (001 не-список)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-all-bytes? (001 ())) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))
