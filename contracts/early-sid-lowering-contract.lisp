; #1115 — Lisp-owned early SID lowering boundary.
;
; Surface spelling is resolved before the backend boundary. The backend receives
; identity + arguments + a portable contract, never a human surface spelling.
;
; This is a contract artifact, not a new semantic identity.

(early-sid-lowering-contract/1
  ((resolution
     (owner sens)
     (source canonical-semantic-registry)
     (input surface-name)
     (output exact-eight-bit-sid)
     (peer-surfaces-same-sid yes))
   (backend-entry
     (required-fields (sid arguments contract))
     (surface-name forbidden)
     (native-operator-name forbidden)
     (sid-reinterpretation forbidden))
   (data-separation
     (quoted-symbol-remains-data yes)
     (string-remains-data yes))
   (failure
     (unadmitted-surface rejected)
     (unadmitted-sid rejected)
     (backend-surface-routing rejected))
   (round-trip
     (sid-preserved yes)
     (leading-zeroes-preserved yes))))