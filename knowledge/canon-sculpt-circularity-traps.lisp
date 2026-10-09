; #419 negative criteria for claims that a semantic primitive is derivable.
; Audit data only; not language authority.

(canon-sculpt-circularity-traps
  (schema-version 1)

  (trap
    (name direct-self-call)
    (reject "candidate definition directly invokes the identity being claimed derivable"))
  (trap
    (name surface-alias-self-call)
    (reject "candidate invokes another EN/UK/SA or compatibility surface resolving to the same semantic identity"))
  (trap
    (name registry-roundtrip-self-call)
    (reject "candidate resolves the same semantic identity through semantic registry/function-table lookup and invokes it indirectly"))
  (trap
    (name host-representation-oracle)
    (reject "candidate asks Rust/host runtime tags, pointer identity, enum variants, or equivalent representation facts to supply the semantic answer"))
  (trap
    (name stronger-hidden-primitive)
    (reject "candidate replaces the named primitive with an undeclared stronger primitive that already contains the operation being derived"))
  (trap
    (name backend-only-proof)
    (reject "candidate is called derived only because one backend can lower it efficiently; lowering is mechanism, not semantic derivation"))

  (acceptance-law
    (name lower-concept-closure)
    (statement "Every operation used by a derivation must be explicitly listed as lower, independently available, and unable to resolve back to the candidate identity."))
  (acceptance-law
    (name observable-parity)
    (statement "A derivation must preserve ordinary, edge, first-class/surface, meta-eval, and backend-relevant observations where those observations exist."))
  (acceptance-law
    (name uncertainty-wins)
    (statement "If circularity cannot be mechanically excluded, classify insufficient-evidence rather than derivable.")))
