; contracts/d1-d5-foundation-ratification.lisp
; РАТИФІКОВАНО ВЛАСНИКОМ 2026-10-05 — issue #3331.
; Історичний власницьки ратифікований зріз основи; замінено як чинну владу #3393 / Контрактом 11.5.
; Точні карти резидентів делеговано наявним поточним
; владам відповідних доменів, щоб не створювати другої скопійованої координатної таблиці.

(
  (schema . d1-d5-foundation-ratification/1)
  (status . superseded-by-#3393)
  (owner-ratification . #3331)
  (date . "2026-10-05")
  (current-domains . (D1 D2 D3 D4 D5))
  (research-domains . (D6 D7 D8))

  (authorities
    . ((D1 #1699)
       (D2 #1702)
       (D3 #3202 "contracts/bija3-l1-l5-ratification.lisp")
       (D4 #3272 "knowledge/d4-cleanroom.json")
       (D5 #3305 #3330 "contracts/d5-ratification.lisp" "knowledge/d5-ratified.json")))

  (laws
    . ((svarupa . "exact bits + exact domain + admitted/proved law")
       (legacy-non-authority . "legacy flat 8-bit coordinates have zero current placement authority")
       (d5-no-duplicate . "D5 has 32 distinct residents and zero lower-domain semantic duplicates")
       (d5-no-global-suffix . "The fifth bit has local family meaning only")
       (d6-boundary . "D6-D8 are research; W6-W8 carrier existence does not grant semantic admission")))

  (supersedes-for-current-authority . (#3327-D3-D5-revocation))
  (preserves-as-research-boundary . (#3327-D6-D8-reset))
)
