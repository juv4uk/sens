; Canonical human-readable domain table.
; D3: exact-width 3-bit keys only.
; The binary key width is the domain address.
; Columns: ук → укр → san → en → LISP → sym
; Predicate marker rule: ук/укр/en end in ?, Sanskrit does not.
; Empty/missing: ()

(domain-table/1
  (000 (ук ()) (укр ()) (san ()) (en ()) (LISP ()) (sym ()))
  (001 (ук як-є) (укр як-є) (san svarūpa) (en quote) (LISP QUOTE) (sym "'"))
  (010 (ук атом?) (укр атом?) (san aṇu) (en atom?) (LISP ATOM) (sym .?))
  (011 (ук решта) (укр решта) (san śeṣa) (en cdr) (LISP CDR) (sym :р))
  (100 (ук перше) (укр перше) (san ādi) (en car) (LISP CAR) (sym :п))
  (101 (ук тотожне?) (укр тотожне?) (san abheda) (en eq?) (LISP EQ) (sym =?))
  (110 (ук за-умовою) (укр за-умовою) (san krama) (en cond) (LISP COND) (sym ?:))
  (111 (ук сполучити) (укр сполучити) (san saṃyuj) (en cons) (LISP CONS) (sym ()))
)
