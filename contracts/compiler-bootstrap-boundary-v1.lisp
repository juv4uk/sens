; contracts/compiler-bootstrap-boundary-v1.lisp
; sens#3805 — machine-readable compiler-in-language bootstrap firewall.
;
; This contract does not define SENS meaning. It classifies current helpers by
; ownership so the compiler nucleus can move into SENS without silently moving
; semantic decisions back into host code.

(
  (schema . compiler-bootstrap-boundary/1)
  (status . current-implementation-contract)
  (issue . #3805)
  (parent . #3759)

  (production-law
    . ((semantic-owner . sens)
       (host-may-transport . yes)
       (host-may-load . yes)
       (host-may-run-sens . yes)
       (host-may-record-provenance . yes)
       (host-may-select-identity-meaning . no)
       (host-may-normalize-sid8-to-meaning . no)
       (backend-may-infer-meaning . no)))

  (components
    . ((component
        (path . "crates/sens/src/compiler_bootstrap.rs")
        (symbol . domain_identity_shape_mechanism)
        (owner . host-mechanism)
        (role . exact-domain-representation-only)
        (production . allowed)
        (semantic-decision . no))
       (component
        (path . "crates/sens/src/compiler_language.rs")
        (symbol . compiler_execution_role_from_sens)
        (owner . host-adapter)
        (role . load-transport-execute-sens-and-convert-result)
        (production . allowed)
        (semantic-decision . no))
       (component
        (path . "crates/sens/src/compiler_role.rs")
        (symbol . compiler_execution_role)
        (owner . bootstrap-oracle)
        (role . differential-reference-only)
        (production . forbidden)
        (semantic-decision . bootstrap-only))
       (component
        (path . "knowledge/bija3-l1-l5-structure-projection.json")
        (owner . generated-law-data)
        (role . provenance-bound-structural-projection)
        (production . allowed)
        (compiler-role-table . no))
       (component
        (path . "lib/compiler-nucleus.lisp")
        (owner . sens)
        (role . bounded-production-compiler-semantics)
        (production . required)
        (semantic-decision . yes))
       (component
        (path . "lib/core1-compiler-prelude.lisp")
        (owner . historical-donor)
        (role . core1-bootstrap-provenance)
        (production-current-nucleus . no))))

  (guards
    . ((production-adapter-direct-rust-role-oracle . forbidden)
       (production-adapter-sid8-sens8-semantic-route . forbidden)
       (production-adapter-core1-prelude-dependency . forbidden)
       (shape-mechanism-role-enum-dependency . forbidden)
       (generated-law-compiler-role-table . forbidden)
       (d8-production-admission . forbidden)))

  (retirement
    . ((rust-role-oracle
        . "retain only while differential evidence remains useful; never production authority")
       (historical-core1-prelude
        . "donor/provenance only; not part of current compiler nucleus"))))
