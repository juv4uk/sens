; SENS owns the positive / negative truth decisions, not the Rust transport.
; Source-defined CLIPS helper has ratified D9:010110100 residence; direct
; D9 callability is NOT admitted yet, so its existing derived name is used
; only as the transitional binder. D3 COND / D3 EQ own the D1 self-verdict.
; In the mixed reader explicit #d1:0/1 preserve exact ONE-BIT identity.
; The final program flips only the expected D1 bit (1 -> 0) of the first.
(110
  ((тотожне? (кліпс-визначити-шаблон-форма? (як-є (deftemplate reading (slot sensor)))) так) так)
  (#d1:1 (#d1:0)))
(110
  ((тотожне? (кліпс-визначити-шаблон-форма? (як-є (deffacts init (planet earth)))) ні) так)
  (#d1:1 (#d1:0)))
(110
  ((тотожне? (кліпс-визначити-шаблон-форма? (як-є (deftemplate reading (slot sensor)))) ні) так)
  (#d1:1 (#d1:0)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити кліпс-визначити-шаблон-форма? clips-deftemplate-form?)
