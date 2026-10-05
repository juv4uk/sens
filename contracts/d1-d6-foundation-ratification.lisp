; contracts/d1-d6-foundation-ratification.lisp
; OWNER-RATIFIED 2026-10-05 — issue #3393.
; Single current semantic foundation chain through D6.
; Exact resident maps are delegated to per-domain current authorities.

(
  (schema . d1-d6-foundation-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3393)
  (date . "2026-10-05")
  (current-domains . (D1 D2 D3 D4 D5 D6))
  (research-domains . (D7 D8))

  (authorities
    . ((D1 #1699)
       (D2 #1702)
       (D3 #3202 "contracts/bija3-l1-l5-ratification.lisp")
       (D4 #3272 "knowledge/d4-cleanroom.json")
       (D5 #3305 #3330 "contracts/d5-ratification.lisp" "knowledge/d5-ratified.json")
       (D6 #3393 "contracts/d6-ratification.lisp" "knowledge/d6-ratified.json")))

  (laws
    . ((svarupa . "exact bits + exact domain + admitted/proved or owner-ratified law")
       (legacy-non-authority . "legacy flat 8-bit coordinates and historical D6 maps have zero current placement authority")
       (d5-no-duplicate . "D5 has 32 distinct residents and zero lower-domain semantic duplicates")
       (d5-no-global-suffix . "The fifth bit has local family meaning only")
       (d6-full-compact . "D6 has 64 distinct owner-ratified residents under #3393")
       (d6-gauge-boundary . "Owner-ratified S4 gauge coordinates are normative identities but remain distinguished from pre-ratification derivation proofs")
       (runtime-separation . "Semantic residency does not imply callable mechanism; missing mechanisms fail closed")
       (d7-d8-boundary . "D7-D8 remain research; W7-W8 carrier existence does not grant semantic admission")))

  (supersedes-for-current-authority . (#3331-D1-D5-foundation #3327-D6-reset))
  (preserves-as-research-boundary . (D7-D8))
)
