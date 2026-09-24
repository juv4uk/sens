; Повна українська peer-поверхня над тією самою semantic authority.
; ukr не має власного registry або SID: це canonical peer namespace.
;
; Більшість ukr назв уже резолвляться безпосередньо через
; semantic-registry.lisp. Цей thin layer materializes the full spelling that
; differs from the compact uk surface where a runtime binding is required.

(define порожній-текст? string-empty?)
