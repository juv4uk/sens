; contracts/d1-d5-foundation-ratification.lisp
; OWNER-RATIFIED 2026-10-05 — issue #3331.
; Single current semantic foundation chain.
; Exact resident maps are delegated to the existing per-domain current
; authorities to avoid creating a second copied coordinate table.

(
  (schema . d1-d5-foundation-ratification/1)
  (status . owner-ratified)
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
       (legacy-non-authority . "SID8/Sens8/Function8 coordinates have zero current placement authority")
       (d5-no-duplicate . "D5 has 32 distinct residents and zero lower-domain semantic duplicates")
       (d5-no-global-suffix . "The fifth bit has local family meaning only")
       (d6-boundary . "D6-D8 are research; W6-W8 carrier existence does not grant semantic admission")))

  (supersedes-for-current-authority . (#3327-D3-D5-revocation))
  (preserves-as-research-boundary . (#3327-D6-D8-reset))
)
