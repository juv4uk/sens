; contracts/d1-d7-foundation-ratification.lisp
; OWNER-RATIFIED 2026-10-05 — issue #3572.
; Single current semantic foundation chain through D7.
; Exact resident maps are delegated to per-domain current authorities.

(
  (schema . d1-d7-foundation-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3572)
  (date . "2026-10-05")
  (current-domains . (D1 D2 D3 D4 D5 D6 D7))
  (research-domains . (D8))

  (authorities
    . ((D1 #1699)
       (D2 #1702)
       (D3 #3202 "contracts/bija3-l1-l5-ratification.lisp")
       (D4 #3272 "knowledge/d4-cleanroom.json")
       (D5 #3305 #3330 "contracts/d5-ratification.lisp" "knowledge/d5-ratified.json")
       (D6 #3393 "contracts/d6-ratification.lisp" "knowledge/d6-ratified.json")
       (D7 #3572 "contracts/d7-ratification.lisp" "knowledge/d7-ratified.json")))

  (laws
    . ((svarupa . "exact bits + exact domain + admitted/proved or owner-ratified law")
       (legacy-non-authority . "legacy flat 8-bit coordinates have zero current semantic placement authority")
       (runtime-separation . "Semantic residency does not imply callable mechanism; missing mechanisms fail closed")
       (d7-occupancy . "D7 has 126 owner-ratified residents and two owner-reserved/pinned coordinates: 0100001 and 0101010")
       (d7-role-boundary . "Sound/Text, LocalOrdinal and Number remain role-distinct even when raw W7 payloads match")
       (d7-d14-boundary . "43/43 hakardvitva belongs to D14 grammar topology and has zero D7 coordinate effect")
       (d8-boundary . "D8 remains research; W8 carrier existence does not grant semantic admission")))

  (supersedes-for-current-authority . (#3393-D1-D6-foundation))
  (preserves-as-research-boundary . (D8))
)
