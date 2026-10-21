; #1115 — історичний контракт раннього зниження SID засобами Lisp.
;
; Людське написання розв'язується до межі зовнішнього виконавця.
; Виконавець отримує тотожність, аргументи та переносимий контракт,
; але не людську назву мовної проєкції.
;
; Це запис контракту, а не нова семантична тотожність.

(early-sid-lowering-contract-1
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