; Повна українська peer-поверхня поверх тієї самої semantic authority.
; ukr не має власного registry: усі numeric identities беруться з
; lib/surface/semantic-registry.lisp. Цей шар додає лише stable full spellings,
; яких немає у компактному uk-шарі.
;
; uk  = компактна українська форма.
; ukr = повна українська форма тієї самої identity.
;
; 00111100: string-empty? / текст-порожній? / порожній-текст?
; Обидва українські імені позначають ту саму semantic identity.
(define порожній-текст? string-empty?)
