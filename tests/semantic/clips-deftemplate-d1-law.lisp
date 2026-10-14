; SENS owns the truth test. Host code only loads these executable forms.
; D9:010110100 is the ratified clips-deftemplate-form? derived coordinate.
; Each successful law returns exact D1:1. The last form changes only
; the expected D1 bit of the positive law (1 -> 0), thus invokes D1:0.
(110
  ((101 (010110100 (001 (deftemplate reading (slot sensor)))) 1) 1)
  (1 (0)))
(110
  ((101 (010110100 (001 (deffacts init (planet earth)))) 0) 1)
  (1 (0)))
(110
  ((101 (010110100 (001 (deftemplate reading (slot sensor)))) 0) 1)
  (1 (0)))
