; contracts/d7-ratification.lisp
; OWNER-RATIFIED 2026-10-05 — issue #3572.
; Normative D7 cut: 126 admitted residents + 2 owner-reserved/pinned coordinates.
; Full exact map: knowledge/d7-ratified.json

(
  (schema . d7-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3572)
  (date . "2026-10-05")
  (domain . D7)
  (width . 7)
  (capacity . 128)
  (occupancy . 126)
  (owner-reserved-pinned . ("0100001" "0101010"))
  (normative-map . "knowledge/d7-ratified.json")

  (occupancy-basis
    . ((baseline-recovered . 107)
       (owner-admitted-same-coordinate-shiva-overlays . 19)
       (owner-ratified-residents . 126)
       (owner-reserved-pinned . 2)))

  (role-counts
    . ((phonology-eligible-recovered . 75)
       (baseline-non-phonological-recovered . 32)
       (text-digits . 10)
       (text-modifiers . 2)
       (text-punctuation . 7)))

  (laws
    . ((identity . "exact seven-bit coordinate + D7 role/law admitted by #3572")
       (report-labels . "human names, glyphs and report labels are projections/provenance only")
       (digits . "D7 text digits are Text and never arithmetic Number")
       (local-ordinal . "LocalOrdinal is a separate W7 role and does not consume Sound/Text occupancy")
       (runtime-separation . "D7 residency does not imply generic Core callability; missing mechanisms fail closed")
       (no-d6-prefix . "D7 has no automatic D6-prefix or parent||bit semantic inheritance")
       (reserved . "0100001 and 0101010 remain owner-reserved/pinned, not free allocation slots")))

  (d14-boundary
    . ((d7-coordinate-effect . NONE)
       (unique-sound-ceiling . "39/43")
       (dual-h-grammar-path . "43/43")
       (interpretation . "h1/h2 are grammar-node multiplicity in D14; this does not prove two D7 phonemes")))

  (candidate-d
    . ((status . NOT-RATIFIED)
       (issue . #3432)
       (h . ("0110100" "0100001"))
       (r . ("0101110" "0101010"))
       (l . ("0101111" "0101110"))
       (candidate-occupancy . 124)
       (rule . "Any Text7 identity migration requires a separate owner decision")))
)
