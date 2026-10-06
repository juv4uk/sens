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
  ;   (domain-call "<width>" "<exact-bits>" (<node> ...))
  ;   (local "<depth>" "<index>")
  ;   (domain-value "<width>" "<exact-bits>")
  ;   (symbol "<exact-symbol-text>")
  ;   (string "<exact-string-text>")
  ;   (list (<node> ...))
  ;   (pair <node> <node>)
  ;
  ; Width/bits are strings on the serialized boundary deliberately. Ordinary
  ; SENS read/write must not reinterpret 001 as numeric 1 or detach leading
  ; zeroes from the domain width. A host adapter may mechanically reconstruct
  ; DomainIdentity(width,bits), but may not select compiler meaning/role.
  ;
  ; "domain-call" is a transport shape, not semantic admission. D8 is therefore
  ; representable here and remains rejectable by compiler semantics downstream.

  (node-vocabulary
    (domain-call exact-domain-width exact-domain-bits ordered-children)
    (local lexical-depth lexical-index)
    (domain-value exact-domain-width exact-domain-bits)
    (symbol exact-text)
    (string exact-text)
    (list ordered-children)
    (pair head tail))

  (invariants
    (domain-width-preserved . yes)
    (child-order-preserved . yes)
    (ordinary-sens-data . yes)
    (d8-transport-representable . yes)
    (d8-admission-implied . no)
    (sid8-sens8-substitution . no)
    (target-mechanism-names . none)
    (deterministic-canonical-wire . yes))

  ; Same packed payload under different widths remains different transport data.
  (width-fixture
    (d3-width . "3")
    (d3-bits . "001")
    (d4-width . "4")
    (d4-bits . "0001")
    (same-packed-payload . yes)
    (same-identity . no)))
