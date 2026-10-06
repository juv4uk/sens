; contracts/compiler-program-ast-transport-v1.lisp
; sens#3837 — bootstrap-only canonical parser transport into the SENS-written
; whole-program compiler body. This schema describes representation, not
; identity->meaning semantics.

(
  (schema . compiler-program-ast-transport/1)
  (status . bounded-selfhost-bootstrap)
  (parent . #3837)

  (node-shapes
    . ((leaf . ())
       (children . (children (<node> ...)))
       (domain-call . (domain-call <exact-domain-identity> (<node> ...)))))

  (host-owns
    . (parse-source
       preserve-tree-order
       preserve-exact-domain-identity
       construct-node-shape))

  (sens-owns
    . (domain-role-selection
       proof-selection
       quote-child-opacity
       deterministic-preorder-request-sequence
       unsupported-identity-fail-closed))

  (guards
    . ((role-names-in-transport . forbidden)
       (sid8-sens8-fallback . forbidden)
       (backend-mechanism-in-transport . forbidden)
       (d8-admission . forbidden)
       (same-payload-cross-domain-collapse . forbidden)))

  (result
    . ((success . (compiler-compilation-artifact/1 (<semantic-request> ...)))
       (failure . compiler-failure)))

  (scope . exact-current-compiler-nucleus-only))
