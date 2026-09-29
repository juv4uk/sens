; #1698 — structure is not a fourth SENS payload domain.
; Inventory only: no runtime type, tag, coercion, or new semantic identity.
;
; Canonical payload remains Function8 | Number | Text7.
; Predicate1 is contextual output. Structure is Control2 composition.

(structure-not-ontology/1
  ((representation . empty-structure)
   (class . structural)
   (projection . control2-open-close)
   (law . not-payload))

  ((representation . pair-or-list)
   (class . structural)
   (projection . control2-composition)
   (dot . human-reader-only)
   (law . no-symbol-required))

  ((representation . numeric-buffer)
   (class . mechanism-layout)
   (projects-to . number-sequence)
   (evidence . crates/sens/tests/exact_number_boundaries.rs)
   (law . no-independent-meaning))

  ((representation . vector)
   (class . derived-value)
   (projects-to . ordered-structure)
   (evidence . crates/sens/tests/vectors.rs)
   (law . no-fourth-payload))

  ((representation . map)
   (class . derived-value)
   (projects-to . key-value-structure)
   (evidence . crates/sens/tests/persistent_map.rs)
   (law . no-fourth-payload))

  ((representation . record-claim-observation)
   (class . derived-value)
   (projects-to . structural-data)
   (law . no-fourth-payload))

  ((representation . island-native-result)
   (class . boundary-data)
   (projection . explicit-admission-or-remain-external)
   (evidence . contracts/island-compat-contract.lisp)
   (law . no-universal-result-ontology))

  ((representation . machine-byte-or-opcode-layout)
   (class . mechanism-layout)
   (projection . backend-only)
   (evidence . lib/machine/capability-axis.lisp)
   (law . never-language-payload)))
