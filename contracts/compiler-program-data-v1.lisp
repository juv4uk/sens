; contracts/compiler-program-data-v1.lisp
; sens#3838 — канонічний транспорт програмних даних для самокомпіляції.
;
; Контракт ратифікує наявний дротовий синтаксис SW\\x01 як транспорт.
; Він не визначає семантику компілятора. Зовнішній виконавець
; може механічно кодувати й декодувати це подання, проте вибір
; ролей і доказів визначають лише виконувані закони СЕНС.

(
  (schema . compiler-program-data/1)
  (issue . #3838)
  (parent . #3837)
  (transport . sens-syntax-wire-1)
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
