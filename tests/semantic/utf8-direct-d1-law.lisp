; Two executable SENS UTF-8 structural verdicts: no numeric coercion.
; Arithmetic byte boundaries need separately admitted D24+ operands, so they
; must not be presented as passing evidence by this witness.
; Wrong results select the impossible CAR(QUOTE EMPTY) branch.

(110
  ((тотожне? (усі-елементи-є-байтами-кодування-юнікод-8? (як-є не-список)) ні) так)
  (#d1:1 (100 (001 ()))))

(110
  ((тотожне? (усі-елементи-є-байтами-кодування-юнікод-8? (як-є ())) так) так)
  (#d1:1 (100 (001 ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити усі-елементи-є-байтами-кодування-юнікод-8? utf8-all-bytes?)
