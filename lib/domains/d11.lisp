; D11 testing vocabulary — exact-width 11-bit keys, 2048 capacity.
; Authority: knowledge/d11-testing-vocabulary-ratified.json
; Ratified by owner for binary SENS semantic tests.
; Columns: ук → укр → san → en → LISP → sym
; Predicate marker: ? in ук/укр/en; Sanskrit marker-free.

(domain-table/1
  (00000000000 (ук прочитати-файл) (укр прочитати-файл) (san paṭhana-sañcikā) (en read-file) (LISP READ-FILE) (sym ()))
  (00000000001 (ук прочитати-sens) (укр прочитати-sens) (san paṭhana-sens) (en read-sens) (LISP READ-SENS) (sym ()))
  (00000000010 (ук декодувати-t5) (укр декодувати-t5) (san vikodana-t5) (en decode-t5) (LISP DECODE-T5) (sym ()))
  (00000000011 (ук довжина) (укр довжина) (san pramāṇa) (en length) (LISP LENGTH) (sym ()))
  (00000000100 (ук порахувати) (укр порахувати) (san saṃkhyā) (en count) (LISP COUNT) (sym ()))
  (00000000101 (ук рівні?) (укр рівні?) (san samāna?) (en equal?) (LISP EQUAL?) (sym ()))
  (00000000110 (ук друкувати) (укр друкувати) (san mudraṇa) (en print) (LISP PRINT) (sym ()))
  (00000000111 (ук зріз) (укр зріз) (san khaṇḍa) (en slice) (LISP SLICE) (sym ()))
  (00000001000 (ук взяти) (укр взяти) (san grahaṇa) (en take) (LISP TAKE) (sym ()))
  (00000001001 (ук скинути) (укр скинути) (san tyāga) (en drop) (LISP DROP) (sym ()))
  (00000001010 (ук істина) (укр істина) (san satya) (en t) (LISP T) (sym ()))
  (00000001011 (ук хиба) (укр хиба) (san asatya) (en nil) (LISP NIL) (sym ()))
  (00000001100 (ук якщо) (укр якщо) (san yadi) (en if) (LISP IF) (sym ()))
  (00000001101 (ук якщо-то-інакше) (укр якщо-то-інакше) (san anyathā) (en if-else) (LISP IF-ELSE) (sym ()))
  (00000001110 (ук стверджувати) (укр стверджувати) (san pratijñā) (en assert) (LISP ASSERT) (sym ()))
  (00000001111 (ук провал) (укр провал) (san patana) (en fail) (LISP FAIL) (sym ()))