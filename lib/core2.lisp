; Core2 profile marker.
;
; Core2 no longer owns a private T/NIL, ATOM, EQ or COND wrapper layer.
; The selected-Core signal remains a mechanical profile fact; the shared
; language foundation is owned once by SENS:
;
;   predicate -> exact one bit (0 / 1)
;   ATOM      -> shared Function8 law
;   EQ        -> shared Function8 law
;   COND      -> exactly (test expression)
;
; Historical Contract-6 behavior remains available in git history only.
; This file stays as the explicit Core2 loader source so the host does not
; need a compatibility shim or a special case.
