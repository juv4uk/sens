; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 11.4 — D1/D2-only semantic authority reset.
; Owner reset: #3327.
;
; Current semantic authority:
;   D1 PredicateBit
;   D2 racanā2 structure
;
; D3-D8 exact-width carriers and all former maps/laws remain research/evidence
; only until independently re-derived and explicitly re-ratified.

((major . #d11) (minor . 4)
 (status . current-d1-d2-only-authority)
 (owner-reset . #3327)
 (note . "Only D1 and D2 are currently ratified. D3-D8 semantic ratifications are revoked; prior contracts, maps, witnesses, benchmarks and implementations remain research/provenance only.")
 (invariants
   . ((binary-domain-identity
       . "Semantic identity requires exact bits + exact domain + current admitted/proved law. Width or payload alone never mints semantics.")
      (domain-non-inference
       . "A mechanically valid W1-W8 word does not acquire semantic residency, occupancy or callability from width, prefix, packed value, old table position or historical name.")
      (legacy-sens8-non-authority
       . "Sens8/Sid8/Function8 remain compatibility/provenance mechanisms only and never mint current semantic identity.")
      (predicate-one-bit
       . "Core.D1 PredicateBit is RATIFIED: exact one bit, 0 = NO and 1 = YES.")
      (structure-two-bit
       . "Core.D2 racanā2 is RATIFIED: 00 separator, 01 close, 10 open, 11 dot.")
      (higher-domains-research
       . "D3, D4, D5, D6, D7 and D8 are UNRATIFIED / RESEARCH under #3327.")
      (higher-domain-callability
       . "No D3-D8 exact word is a current Core-operation identity solely from a revoked map. Semantic admission fails closed until new owner ratification.")
      (mechanical-carriers
       . "W1-W8 exact-width carriers remain mechanically parseable, packable, serializable and benchmarkable. Carrier existence is not semantic admission.")
      (rebuild-order
       . "Rebuild upward only from current lower-domain authority: D1+D2 -> derive D3 -> derive D4 -> derive D5 -> continue.")
      (evidence-preservation
       . "Revocation deletes no evidence. Former D3-D8 ratification files remain provenance and may later be independently re-derived.")
      (cross-domain-non-collapse
       . "Equal packed payloads in distinct widths/domains never imply semantic equality."))))