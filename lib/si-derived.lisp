; lib/si-derived.lisp — exact constants derived only from the 7 SI defining constants
; Точні похідні константи, виведені лише з 7 визначальних констант SI
;
; Migrated: pure exact-rational composition. No host truthiness. No COND.
; No decimal approximations. Width is identity; every bit valued.
;
; Reuses (2000+ surface):
;   si:avogadro-constant, si:elementary-charge, si:boltzmann-constant,
;   si:planck-constant (lib/si.lisp defining records),
;   exact multiply (D5:10110) and exact rational quotient (D5:10111).
;
; No decimal approximations are stored here. Every value below is an exact
; Rational expression over exact SI defining constants from lib/si.lisp.
; Якщо результат має нескінченний десятковий запис, він усе одно лишається
; точним як раціональне число.
;
; This file intentionally excludes quantities that require an experimentally
; measured constant (for example alpha) or an irrational constant such as pi.

; Faraday constant: F = N_A * e
; Exact: 120606665154137523 / 1250000000000 C mol^-1
(визначити si:faraday-constant
  (помножити si:avogadro-constant
     si:elementary-charge))

; Molar gas constant: R = N_A * k_B
; Exact: 207861565453831 / 25000000000000 J mol^-1 K^-1
(визначити si:molar-gas-constant
  (помножити si:avogadro-constant
     si:boltzmann-constant))

; Josephson constant: K_J = 2e / h
; Exact: 21362355120000000000000 / 44173801 Hz V^-1
(визначити si:josephson-constant
  (частка (помножити 2 si:elementary-charge)
     si:planck-constant))

; von Klitzing constant: R_K = h / e^2
; Exact: 5521725125000000000000 / 213914163877964163 ohm
(визначити si:von-klitzing-constant
  (частка si:planck-constant
     (помножити si:elementary-charge si:elementary-charge)))

; Magnetic flux quantum: Phi_0 = h / (2e)
; Exact: 44173801 / 21362355120000000000000 Wb
(визначити si:magnetic-flux-quantum
  (частка si:planck-constant
     (помножити 2 si:elementary-charge)))

; Conductance quantum: G_0 = 2e^2 / h
; Exact: 213914163877964163 / 2760862562500000000000 S
(визначити si:conductance-quantum
  (частка (помножити 2 si:elementary-charge si:elementary-charge)
     si:planck-constant))

; Molar Planck constant: N_A * h
; Exact: 19951563564467157 / 50000000000000000000000000 J s mol^-1
(визначити si:molar-planck-constant
  (помножити si:avogadro-constant
     si:planck-constant))
