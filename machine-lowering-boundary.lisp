; Машинно-читана межа повноважень між змістом мови та фізичною ціллю.
; Цей файл навмисно не містить мнемонік цільової машини, регістрів,
; кодів операцій або назв наборів машинних інструкцій.
; СЕНС визначає зміст мови й семантичні ідентичності. Специфікації
; обладнання визначають машинні інструкції. СЕНС може представляти
; та кодувати ці відомості. CML залишається оптимізатором, а зовнішнє
; середовище забезпечує лише механізми виклику та виконувану пам'ять.
;
; Допуск машинного виконання визначається властивостями, а не
; історичним шляхом до файла чи назвою реалізації.
; Файл кодера або асемблера — лише замінний носій механізму.

(machine-lowering-boundary
  (schema machine-lowering-boundary/2)
  (semantic-authority sens)
  (isa-authority hardware-specification)
  (isa-source intel-xed/intel-sdm)
  (isa-representation sens)
  (instruction-encoding sens)
  (optimization-authority cml)
  (portable-monotonic-observation 1075)
  (semantic-id-allocation explicit-language-contract-only)
  (semantic-id-from-isa forbidden)
  (lowering-direction semantic-to-machine)
  (canonical-machine-effect-layer lib/machine/effect-boundary.lisp)
  (lowering-stage semantic-to-machine-effect required)
  (semantic-to-machine-effect-owner lib/machine/lowering/semantic-effects.lisp)
  (lowering-stage machine-effect-to-target-projection required)
  (target-specific-data-before-machine-effect forbidden)
  (machine-effect-semantic-authority forbidden)
  (reverse-authority forbidden)

  ; Допускається тільки замкнена підмножина з перевіреними свідченнями.
  ; Її не визначає назва asm-x86.lisp, x86-64.lisp чи іншого носія.
  (machine-authority-basis admitted-subset-properties)
  (admitted-subset-owner sens)
  (admitted-subset-closed required)
  (admitted-subset-machine-readable required)
  (admitted-subset-witnessed required)
  (admitted-subset-implementation replaceable)
  (implementation-file-path authority-forbidden)
  (unadmitted-machine-form reject-before-host)
  (canonical-raw-byte-vector-api forbidden)
  (host-execution-input admitted-output-only)

  (raw-execution-mechanism host)
  (machine-text projection-only)
  (machine-bytes lisp-owned-target-product)
  ; Ідентичність 1153 короткочасно потрапила до main з експерименту
  ; компілятора. Її остаточно вилучено з ужитку: не призначати
  ; іншому мовному значенню та не додавати до активного реєстру,
  ; бо мовний контракт ніколи не допускав відповідну операцію.
  (retired-semantic-id 1153))
