; contracts/compiler-program-data-v1.lisp
; sens#3838 — canonical transport data passed from bootstrap host to executable C1.
;
; This contract owns representation only. It contains no compiler-role table,
; proof selection, backend mechanism, target opcode, or callability decision.

(compiler-program-data-contract
  (schema . sens-compiler-program-data/1)
  (status . current-transport)
  (authority . representation-only)
  (semantic-authority . compiler-nucleus-and-current-domain-laws)
  (backend-policy . none)
  (legacy-sid8-fallback . forbidden)
  (human-name-routing . forbidden)

  ; Runtime value shape:
  ;
  ; (sens-compiler-program-data/1
  ;   (<node> ...))
  ;
  ; Node forms:
  ;   (domain-call <exact-domain-identity> (<node> ...))
  ;   (local <exact-depth> <exact-index>)
  ;   (literal <ordinary-sens-atom>)
  ;   (list (<node> ...))
  ;   (pair <node> <node>)
  ;
  ; "domain-call" is a transport shape, not semantic admission. The exact
  ; DomainIdentity is preserved even when downstream compiler semantics reject
  ; it (for example D8 research identity).

  (node-vocabulary
    (domain-call exact-domain-identity ordered-children)
    (local lexical-depth lexical-index)
    (literal number rational binary-number domain-identity string symbol)
    (list ordered-children)
    (pair head tail))

  (invariants
    (domain-width-preserved . yes)
    (child-order-preserved . yes)
    (d8-transport-representable . yes)
    (d8-admission-implied . no)
    (sid8-sens8-substitution . no)
    (target-mechanism-names . none)
    (deterministic-canonical-wire . yes))

  ; Same packed payload under different widths remains different transport data.
  (width-fixture
    (d3 . 001)
    (d4 . 0001)
    (same-packed-payload . yes)
    (same-identity . no)))
