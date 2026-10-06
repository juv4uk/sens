; Canonical human-readable domain table.
; D2: exact-width 2-bit keys only.
; The binary key width is the domain address.
; Columns: ук → укр → san → en → LISP → sym
; Predicate marker rule: ук/укр/en end in ?, Sanskrit does not.
; Empty/missing: ()

(domain-table/1
  (00 (ук пропуск) (укр пропуск) (san antarāla) (en separator) (LISP ()) (sym ()))
  (01 (ук закрити) (укр закрити) (san samāpana) (en close) (LISP ()) (sym ()))
  (10 (ук відкрити) (укр відкрити) (san udghāṭana) (en open) (LISP ()) (sym ()))
  (11 (ук крапка) (укр крапка) (san bindu) (en dot) (LISP ()) (sym ()))
)
