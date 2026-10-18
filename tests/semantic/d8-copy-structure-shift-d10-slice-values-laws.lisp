; D8:10101111 COPY-STRUCTURE; D8:10110101 ARITHMETIC-SHIFT;
; D10:0000110110 VECTOR-SLICE; D10:0000011000 MULTIPLE-VALUE-LIST.
; 7 true laws + 1 false-result falsifier, every result exact D1:1.
; D24-qualified math; deep CONS-tree only; no numeric call-heads.
(список
  (equal? (копіювати-структуру (quote ())) (quote ()))
  (equal? (копіювати-структуру (список (quote а) (список (quote б) (quote в)))) (список (quote а) (список (quote б) (quote в))))
  (equal? (копіювати-структуру (сполучити (список (quote а)) (quote б))) (сполучити (список (quote а)) (quote б)))
  (хибне? (equal? (копіювати-структуру (список (quote а) (quote б))) (список (quote б) (quote а))))
  (equal? (арифметично-зсунути #d24:000000000000000000000011 #d24:000000000000000000000010) #d24:000000000000000000001100)
  (equal? (арифметично-зсунути #d24:000000000000000000000101 #d24:000000000000000000000000) #d24:000000000000000000000101)
  (equal? (зріз-вектора (list (quote а) (quote б) (quote в) (quote г)) #d24:000000000000000000000001 #d24:000000000000000000000011) (list (quote б) (quote в)))
  (equal? (список-усіх-значень (список (quote а) (quote б))) (список (quote а) (quote б))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
