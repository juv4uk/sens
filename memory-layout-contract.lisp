; Історичний опис механізму розміщення значень у пам'яті.
; Цей файл є свідченням конструкції, а НЕ семантичною онтологією СЕНС.
;
; Записано пропозицію 64-бітного подання IEEE 754 з маркуванням NaN.
; Ширини та порядкові номери тегів — лише відомості реалізації:
; вони не визначають ідентичність значень СЕНС, домени вмісту або
; канонічні закони мови.
; Молодші 32 біти проєктувалися відповідно до структури VALUE WORD
; у fpga-lisp. Незалежні виконавці можуть по-різному представляти
; однакові мовні значення.

((kind . memory-layout-design)
 (version . (1 0))
 (authority . mechanism-private)
 (lifecycle . historical-transition)
 (format . nan-boxing-64)

 (nan-marker . ((bits . 12) (position . (63 52)) (value . #xfff)))

 (fpga-lisp-compatibility .
  "The lower 32-bit layout mirrors the fpga-lisp VALUE WORD shape only.
   bits (31 28) = tag
   bits (27 0) = payload
   This does not make tag ordinals or FPGA instruction opcodes language semantics.")

 (layout . ((float . "IEEE-754 64-bit double (when exponent is not all 1s)")
            (tagged . ((nan-marker . (63 52))
                       (extended-payload . (51 32))
                       (tag . (31 28))
                       (payload . (27 0))))))

 (tags . ((fixnum . 0)
          (cons . 1)
          (symbol . 2)
          (nil . 3)
          (true . 4)
          (primitive . 5)
          (string . 6)    ; Нове: extended-payload + payload = 48-бітний вказівник на купу
          (rational . 7)  ; Нове: extended-payload + payload = 48-бітний вказівник на купу
          (closure . 8)   ; Нове: extended-payload + payload = 48-бітний вказівник на купу
          (tcp-conn . 9))) ; Нове: дескриптор ресурсу зовнішнього середовища

 (heap-representation .
  ((string . "null-terminated UTF-8 byte array")
   (rational . "two consecutive 64-bit pointers (numerator, denominator) to BigInt blocks")
   (closure . "two consecutive 64-bit pointers (environment, compiled-code-pointer)")))

 (notes . "Mechanism/history evidence only. Current SENS semantics must not inherit these tag ordinals; any backend using this layout must prove conformance independently."))
