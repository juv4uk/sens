; Eight D1 one-bit negative controls, each independent.
; Compared line-wise to meta-eval-lexical-shadow-d1-law.lisp.
; Same live calls, same quoted data; only EQ expected D1 flips.

; case=1 quoted-reference-is-inert
(за-умовою ((тотожне? (вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (як-є (як-є target)) (як-є target)) так) так) (так (ні)))
; case=2 unquoted-reference-is-visible
(за-умовою ((тотожне? (вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (як-є target) (як-є target)) ні) так) (так (ні)))
; case=3 lambda-binder-shadows
(за-умовою ((тотожне? (вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (як-є (функція (target) target)) (як-є target)) так) так) (так (ні)))
; case=4 other-binder-leaves-free-reference
(за-умовою ((тотожне? (вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (як-є (функція (other) target)) (як-є target)) ні) так) (так (ні)))
; case=5 quoted-datum-inside-lambda-is-inert
(за-умовою ((тотожне? (вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (як-є (функція (other) (як-є target))) (як-є target)) так) так) (так (ні)))
; case=6 defined-lambda-binder-shadows
(за-умовою ((тотожне? (визначення-посилається-на-ім'я? (як-є (визначити fn (функція (target) target))) (як-є target)) так) так) (так (ні)))
; case=7 defined-lambda-free-reference
(за-умовою ((тотожне? (визначення-посилається-на-ім'я? (як-є (визначити fn (функція (other) target))) (як-є target)) ні) так) (так (ні)))
; case=8 defined-lambda-quoted-reference-is-inert
(за-умовою ((тотожне? (визначення-посилається-на-ім'я? (як-є (визначити fn (функція (other) (як-є target)))) (як-є target)) так) так) (так (ні)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? my-form-references-name?)
(визначити визначення-посилається-на-ім'я? my-lambda-def-references-name?)
