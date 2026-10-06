; Canonical human-readable domain table.
; D4: exact-width 4-bit keys only.
; The binary key width is the domain address.
; Columns: ук → укр → san → en → LISP → sym
; Predicate marker rule: ук/укр/en end in ?, Sanskrit does not.
; Empty/missing: ()

(domain-table/1
  (0000 (ук застосувати) (укр застосувати) (san prayoga) (en apply) (LISP APPLY) (sym ()))
  (0001 (ук обчислити) (укр обчислити) (san vicāraṇa) (en eval) (LISP EVAL) (sym ()))
  (0010 (ук функція) (укр функція) (san phalana) (en lambda) (LISP LAMBDA) (sym ()))
  (0011 (ук визначити) (укр визначити) (san nirvacana) (en define) (LISP DEFINE) (sym ()))
  (0100 (ук хибне?) (укр хибне?) (san niṣedha) (en not?) (LISP NOT) (sym ()))
  (0101 (ук порожнє?) (укр порожній?) (san śūnya-parīkṣā) (en null?) (LISP NULL) (sym ()))
  (0110 (ук решта-від-першого) (укр решта-від-першого) (san śeṣa-ādi) (en cdar) (LISP CDAR) (sym ()))
  (0111 (ук решта-від-решти) (укр решта-від-решти) (san śeṣa-śeṣa) (en cddr) (LISP CDDR) (sym ()))
  (1000 (ук перше-від-першого) (укр перше-від-першого) (san ādi-ādi) (en caar) (LISP CAAR) (sym ()))
  (1001 (ук перше-від-решти) (укр перше-від-решти) (san ādi-śeṣa) (en cadr) (LISP CADR) (sym ()))
  (1010 (ук знайти) (укр знайти) (san anveṣaṇa) (en lookup) (LISP LOOKUP) (sym ()))
  (1011 (ук зв'язати) (укр зв'язати) (san bandha) (en bind) (LISP BIND) (sym ()))
  (1100 (ук обчислити-умови) (укр обчислити-умови) (san krama-vicāraṇa) (en evcon) (LISP EVCON) (sym ()))
  (1101 (ук обчислити-список) (укр обчислити-список) (san śreṇī-vicāraṇa) (en evlis) (LISP EVLIS) (sym ()))
  (1110 (ук список) (укр список) (san śreṇī) (en list) (LISP LIST) (sym ()))
  (1111 (ук приєднати) (укр приєднати) (san saṅkalana) (en append) (LISP APPEND) (sym ()))
)
