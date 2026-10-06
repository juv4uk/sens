; Canonical human-readable domain table.
; D1: exact-width 1-bit keys only.
; The binary key width is the domain address.
; Columns: ук → укр → san → en → LISP → sym
; Predicate marker rule: ук/укр/en end in ?, Sanskrit does not.
; Empty/missing: ()

(domain-table/1
  (0 (ук ні) (укр ні) (san na) (en no) (LISP NIL) (sym ()))
  (1 (ук так) (укр так) (san ām) (en yes) (LISP T) (sym ()))
)
