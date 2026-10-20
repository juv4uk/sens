; tests/fixtures/semantic/runner.lisp — #1709 LISP-SEMANTIC-WITNESSES-1
; мінімальний протокол тверджень, українська проєкція.
; Host транспортує actual; expected і порівняння — у Lisp.

(визначити semantic-pass-answer (однакові? 1 1))
(визначити semantic-fail-answer (однакові? 1 2))

(визначити semantic-row-expect (функція (row) (решта (знайти-за-ключем (як-є expect) row))))
(визначити semantic-row-expected (функція (row) (решта (знайти-за-ключем (як-є expected) row))))
(визначити semantic-row-name (функція (row) (решта (знайти-за-ключем (як-є name) row))))

(визначити semantic-row-active?
  (функція (row)
    (однакові? (решта (знайти-за-ключем (як-є active) row)) (як-є t))))

(визначити semantic-actual-datum
  (функція (actual)
    (список (перше actual) (прочитати (друге actual)))))

(визначити semantic-verdict
  (функція (row actual)
    (однакові? (semantic-row-expected row) (semantic-actual-datum actual))))

(визначити semantic-verdict-label
  (функція (row actual)
    (решта (знайти-за-ключем (semantic-verdict row actual)
      (як-є (((1) . pass) ((0) . fail)))))))

(визначити semantic-layer-id
  (функція () (як-є "LISP-SEMANTIC-WITNESSES-1")))
