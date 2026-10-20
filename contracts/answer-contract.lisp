; #1804 / #3161 — мінімальний спільний закон відповіді та керування.
;
; Це чисті дані Lisp, які визначають авторитет спільного контракту.
; Предметна математика й міркування мають окремі контракти
; і не перевизначають спільного закону предикатів та керування.
;
; Спільний закон:
;   D1:1      = ТАК
;   D1:0      = НІ
;   D3:000 () = структурна порожнеча / немає свідка, а не хиба предиката
;   COND      = рівно (test expression)
;               D1:1 -> вибрати
;               D1:0 -> перейти далі з явною відповіддю НІ
;               D3:000 -> перейти далі без свідка
;               вичерпання варіантів -> D3:000
;
; Важлива відмінність:
;   control(D1:0)   = продовжити
;   control(D3:000) = продовжити
;   але D1:0 != D3:000
;
; Людські написання залишаються мовними проєкціями.
; Канонічну тотожність задають точний домен, точні біти й допущений закон.
; Розгорнутий запис класифікатора не є відповіддю предиката.
; Історичне трактування T/NIL як істини не має нормативної сили.

(answer-contract/3

  ((identity . D3:000)
   (domain-owner . D3)
   (result-form . empty-structure/no-witness)
   (predicate-answer . no)
   (false-sentinel . no)
   (list-ground . yes)
   (control-force . non-selection)
   (distinct-from-D1-zero . yes))

  ((identity . D3:001)
   (domain-owner . D3)
   (result-form . data))

  ((identity . D3:111)
   (domain-owner . D3)
   (result-form . pair))

  ((identity . D3:100)
   (domain-owner . D3)
   (input-domain . pair)
   (result-form . value))

  ((identity . D3:011)
   (domain-owner . D3)
   (input-domain . pair)
   (result-form . value))

  ((identity . D3:010)
   (domain-owner . D3)
   (result-domain . D1)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (empty-structure-result . one)
   (pair-result . zero)
   (non-pair-result . one)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . D3:101)
   (domain-owner . D3)
   (input-domain . (admitted-atom admitted-atom))
   (result-domain . (D1 D3:000))
   (result-form . partial-predicate)
   (yes . one)
   (no . zero)
   (same-atom-result . one)
   (distinct-atom-result . zero)
   (outside-domain . D3:000)
   (outside-domain-meaning . no-witness)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . D3:110)
   (domain-owner . D3)
   (clause-shape . (test expression))
   (test-domain . (D1:1 D1:0 D3:000))
   (select-on . D1:1)
   (skip-explicit-no . D1:0)
   (skip-no-witness . D3:000)
   (zero-equals-empty . forbidden)
   (exhaustion-result . D3:000)
   (three-part-clause . forbidden)
   (explicit-result-match . forbidden)
   (generic-truthiness . forbidden)
   (host-bool-authority . forbidden)))
