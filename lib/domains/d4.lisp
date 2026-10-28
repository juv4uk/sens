; Канонічна людиночитана таблиця четвертого домену.
; Д4: ключі рівно чотирибітної ширини.
; Ширина двійкового ключа визначає доменну адресу.
; Колонки: ук → укр → san → en → LISP → sym.
; Предикати в ук/укр/en закінчуються на ?, у санскритській проєкції — ні.
; Відсутню або порожню поверхню позначено ().

(domain-table-1
  (0000 (ук застосувати) (укр застосувати) (san prayoga) (en apply) (LISP APPLY) (sym "№"))
  (0001 (ук обчислити) (укр обчислити) (san vicāraṇa) (en eval) (LISP EVAL) (sym "!"))
  (0010 (ук функція) (укр функція) (san phalana) (en lambda) (LISP LAMBDA) (sym ()))
  (0011 (ук визначити) (укр визначити) (san nirvacana) (en define) (LISP DEFINE) (sym ":="))
  (0100 (ук хибне?) (укр хибне?) (san niṣedha) (en not?) (LISP NOT) (sym ":?"))
  (0101 (ук порожнє?) (укр порожній?) (san śūnya-parīkṣā) (en null?) (LISP NULL) (sym "0?"))
  (0110 (ук решта-першого) (укр решта-першого) (san śeṣa-ādi) (en cdar) (LISP CDAR) (sym ":рп"))
  (0111 (ук решта-решти) (укр решта-решти) (san śeṣa-śeṣa) (en cddr) (LISP CDDR) (sym ":рр"))
  (1000 (ук перше-першого) (укр перше-першого) (san ādi-ādi) (en caar) (LISP CAAR) (sym ":пп"))
  (1001 (ук друге) (укр друге) (san ādi-śeṣa) (en cadr) (LISP CADR) (sym ":пр"))
  (1010 (ук знайти) (укр знайти) (san anveṣaṇa) (en lookup) (LISP LOOKUP) (sym ":;"))
  (1011 (ук зв'язати) (укр зв'язати) (san bandha) (en bind) (LISP BIND) (sym "::"))
  (1100 (ук обчислити-умови) (укр обчислити-умови) (san krama-vicāraṇa) (en evcon) (LISP EVCON) (sym "??"))
  (1101 (ук обчислити-список) (укр обчислити-список) (san śreṇī-vicāraṇa) (en evlis) (LISP EVLIS) (sym "!!"))
  (1110 (ук список) (укр список) (san śreṇī) (en list) (LISP LIST) (sym ","))
  (1111 (ук приєднати) (укр приєднати) (san saṅkalana) (en append) (LISP APPEND) (sym "++"))
)
