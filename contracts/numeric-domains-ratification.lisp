; Ratified directly by owner 2026-10-11: D24/D48/D96/D192/... = full SENS domains.
; Peers of D1-D9; not out-of-domain Number24 storage tiers. The exact domain
; is mandatory to interpret an exact binary word. No numeric literals required.
(
  (schema . numeric-domains-ratification/1)
  (status . owner-ratified)
  (owner-ratification . "owner direct decision 2026-10-11")
  (date . "2026-10-11")
  (family . numeric)
  (rank . peer-of-D1-D9)
  (first-domain . D24)
  (initial-width . #d24)
  (next-width . double)
  (canonical-domain-names . (D24 D48 D96 D192))
  (domain-rule . "D(24 * 2^n), n >= 0")
  (normative-map . "knowledge/number-width-ratified.json")
  (laws
    . ((identity . "exact binary bits + explicit numeric domain + domain law")
       (equal-rank . "D24/D48/... are semantic domains with equal ontology rank to D1-D9")
       (role-distinction . "numeric domain laws do not collapse into D1 predicates, D2 structure, D7 text or function domains")
       (no-inference . "bits, width alone, human literals, and host storage cannot confer numeric-domain membership")
       (non-collapse . "D24 and D48 remain distinct domain identities even if payload magnitude coincides")
       (no-literals-required . "numeric source tokens are optional projection, not semantic identity")
       (admission-scope . "domain names, equal rank, and exact widths only: no proof of full resident occupancy")
       (deferred . "signedness, rational field layout, overflow policy, implicit widening/bridges, decimal lowering")
       (runtime-status . "normalized BinaryNumber is not yet a certified exact-width D24/D48/... domain identity")))
)
