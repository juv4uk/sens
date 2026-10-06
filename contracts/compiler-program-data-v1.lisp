; contracts/compiler-program-data-v1.lisp
; sens#3838 — canonical program-data transport for the self-host fixed point.
;
; This contract RATIFIES the existing SW\x01 syntax wire as transport.  It does
; not define compiler meaning.  The host may encode/decode this representation
; mechanically; role/proof selection remains owned by executable SENS laws.

(
  (schema . compiler-program-data/1)
  (issue . #3838)
  (parent . #3837)
  (transport . sens-syntax-wire/1)
  (wire-magic . "SW\\x01")

  (input-stage . current-lowered-program)

  (identity-law
    . ((domain-width-preserved . required)
       (packed-payload-preserved . required)
       (same-payload-different-domain . distinct)
       (sid8-substitution . forbidden)
       (human-name-roundtrip . forbidden)))

  (domain-call-law
    . ((transport-shape . source-shaped-list)
       (head . exact-domain-identity)
       (children . ordered)
       (host-role-selection . forbidden)))

  (allowed-host-work
    . (wire-decode
       wire-encode
       byte-transport
       file-io
       process-io))

  (forbidden-host-work
    . (identity-to-compiler-role
       proof-selection
       sid8-semantic-normalization
       backend-mechanism-selection))

  (d8
    . ((transport . representable)
       (compiler-admission . fail-closed)))

  (fixed-point-law
    . ((c1-input-program-data . byte-identical-to-declared-bundle)
       (c2-input-program-data . same-declared-bundle)
       (preexisting-c2-artifact . forbidden))))
