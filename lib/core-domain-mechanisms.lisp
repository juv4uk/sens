; Exact-domain execution-mechanism projection.
;
; Semantic occupancy is owned by the ratified Core domain maps/laws.
; This file only records which downstream executor mechanisms have evidence for
; an already-admitted exact domain identity. It never creates an identity.
;
; First bounded slice: Core.D5 01010 (PLUS).

(
  (schema core-domain-mechanisms/1)
  (authority "knowledge/d5-historical-full-map.json")
  (role mechanism-projection-only)
  (rows
    (01010 common-lisp bounded-exact-add)
    (01010 prolog bounded-exact-add)
    (01010 clips bounded-exact-add)
    (01010 datalog bounded-exact-add)))
