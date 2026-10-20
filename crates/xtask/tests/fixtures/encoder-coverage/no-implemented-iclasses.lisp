; Мінімальний файл-свідчення фікстури (лише тест #176): допускає ICLASS, яких
; курований частково реалізований набір (RET_NEAR, MOV, ADD) не містить.
(xed-machine-evidence/1
  (pinned-commit "0000000000000000000000000000000000000000")
  (source-digest "sha256:0")
  (form-count 1)
  (form
    (extension X86-BASE)
    (xed-extension BASE)
    (iclass "NOP")
    (category "NOP")
    (isa-set ())
    (form-count 1)
    (operand-summary "")
    (source-file "fixture")))
