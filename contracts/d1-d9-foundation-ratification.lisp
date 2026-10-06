; contracts/d1-d9-foundation-ratification.lisp
; OWNER-RATIFIED 2026-10-07 — issue #4008.
; Single current semantic foundation chain through D9.
; Exact resident maps are delegated to per-domain current authorities.

(
  (schema . d1-d9-foundation-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #4008)
  (date . "2026-10-07")
  (current-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))
  (research-domains . ())

  (authorities
    . ((D1 #1699)
       (D2 #1702)
       (D3 #3202 "contracts/bija3-l1-l5-ratification.lisp")
       (D4 #3272 "knowledge/d4-cleanroom.json")
       (D5 #3305 #3330 "contracts/d5-ratification.lisp" "knowledge/d5-ratified.json")
       (D6 #3393 "contracts/d6-ratification.lisp" "knowledge/d6-ratified.json")
       (D7 #3572 "contracts/d7-ratification.lisp" "knowledge/d7-ratified.json")
       (D8 #3960 "contracts/d8-ratification.lisp" "knowledge/d8-ratified.json")
       (D9 #4008 "contracts/d9-ratification.lisp" "knowledge/d9-ratified.json")))

  (laws
    . ((svarupa . "exact bits + exact domain + admitted/proved or owner-ratified law")
       (legacy-non-authority . "legacy flat coordinates and source-registry codes have zero current semantic placement authority")
       (runtime-separation . "semantic residency does not imply callable mechanism; missing mechanisms fail closed")
       (d7-occupancy . "D7 has 126 owner-ratified residents and two owner-reserved/pinned coordinates: 0100001 and 0101010")
       (d8-occupancy . "D8 has 256 owner-ratified distinct residents under #3960")
       (d9-occupancy . "D9 has 512 owner-ratified distinct residents under #4008")
       (d9-gauge-boundary . "128 D9 selector coordinates are theorem-forced; 384 residual coordinates are owner-ratified S4 gauge choices")
       (d9-runtime-boundary . "D9 residency is current semantic authority; callable mechanisms remain separately admitted")))

  (supersedes-for-current-authority . (#3960-D1-D8-foundation))
  (preserves-as-provenance . (D9-pre-ratification-research D9-S2 D9-S3 D9-S4))
)
