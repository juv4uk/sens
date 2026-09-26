; lib/si-derived.lisp — exact constants derived only from the 7 SI defining constants
; Точні похідні константи, виведені лише з 7 визначальних констант SI
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
(00001001 si:faraday-constant
  (00001110 si:avogadro-constant
     si:elementary-charge))

; Molar gas constant: R = N_A * k_B
; Exact: 207861565453831 / 25000000000000 J mol^-1 K^-1
(00001001 si:molar-gas-constant
  (00001110 si:avogadro-constant
     si:boltzmann-constant))

; Josephson constant: K_J = 2e / h
; Exact: 21362355120000000000000 / 44173801 Hz V^-1
(00001001 si:josephson-constant
  (00001111 (00001110 2 si:elementary-charge)
     si:planck-constant))

; von Klitzing constant: R_K = h / e^2
; Exact: 5521725125000000000000 / 213914163877964163 ohm
(00001001 si:von-klitzing-constant
  (00001111 si:planck-constant
     (00001110 si:elementary-charge si:elementary-charge)))

; Magnetic flux quantum: Phi_0 = h / (2e)
; Exact: 44173801 / 21362355120000000000000 Wb
(00001001 si:magnetic-flux-quantum
  (00001111 si:planck-constant
     (00001110 2 si:elementary-charge)))

; Conductance quantum: G_0 = 2e^2 / h
; Exact: 213914163877964163 / 2760862562500000000000 S
(00001001 si:conductance-quantum
  (00001111 (00001110 2 si:elementary-charge si:elementary-charge)
     si:planck-constant))

; Molar Planck constant: N_A * h
; Exact: 19951563564467157 / 50000000000000000000000000 J s mol^-1
(00001001 si:molar-planck-constant
  (00001110 si:avogadro-constant
     si:planck-constant))
