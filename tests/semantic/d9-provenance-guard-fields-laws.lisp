; D9:000010011 GUARD-REFERENCE-FIELD, D9:000001111 PROVENANCE-RULE,
; D9:000010110 PROVENANCE-GOAL, D9:000011100 PROVENANCE-DERIVED-FROM,
; D9:000101001 PROVENANCE-SOURCE.
; Structural donor: lib/reason.lisp canonical (statement goal (source ...) ...)
; and lib/guard.lisp tagged (guard-finding (field value) ...) records.
; One exact D1:1 for each of eight positive / negative observations.
((0010 (походження захист)
  (список
    (equal? (походження-ціль походження) (001 мета))
    (equal? (походження-правило походження) (001 правило))
    (equal? (походження-джерело походження) (001 факт))
    (equal? (походження-похідний-з походження)
            (список (001 дитина)))
    (equal? (захист-еталон-поле (001 decision) захист)
            (001 allow))
    (equal? (захист-еталон-поле (001 evidence-status) захист)
            (001 confirmed))
    (порожнє? (захист-еталон-поле (001 відсутнє) захист))
    (хибне? (equal? (походження-правило походження) (001 помилка)))))
 (список
   (001 statement) (001 мета)
   (список (001 source) (001 факт))
   (список (001 rule) (001 правило))
   (список (001 derived-from) (список (001 дитина))))
 (список
   (001 guard-finding)
   (список (001 decision) (001 allow))
   (список (001 evidence-status) (001 confirmed))))
