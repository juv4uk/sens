; SENS owns the positive / negative truth decisions, not the Rust transport.
; Source-defined CLIPS helper has ratified D9:010110100 residence; direct
; D9 callability is NOT admitted yet, so its existing derived name is used
; only as the transitional binder. D3 COND / D3 EQ own the D1 self-verdict.
; In the mixed reader explicit #d1:0/1 preserve exact ONE-BIT identity.
; The final program flips only the expected D1 bit (1 -> 0) of the first.
(110
  ((101 (clips-deftemplate-form? (001 (deftemplate reading (slot sensor)))) #d1:1) #d1:1)
  (#d1:1 (#d1:0)))
(110
  ((101 (clips-deftemplate-form? (001 (deffacts init (planet earth)))) #d1:0) #d1:1)
  (#d1:1 (#d1:0)))
(110
  ((101 (clips-deftemplate-form? (001 (deftemplate reading (slot sensor)))) #d1:0) #d1:1)
  (#d1:1 (#d1:0)))
