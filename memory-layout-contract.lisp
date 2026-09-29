; memory-layout-contract.lisp — historical/mechanism NaN-box layout design
; Історичний/механічний дизайн layout; НЕ семантична онтологія SENS.
; Historischer/mechanischer Layout-Entwurf; KEINE SENS-Semantik.
;
; This records a proposed 64-bit IEEE 754 NaN-boxing representation.
; Tag widths and ordinals are implementation evidence only: they do not define
; SENS value identity, payload domains, or canonical language semantics.
; The lower 32-bit shape was designed to align with the fpga-lisp VALUE WORD;
; independent runtimes may represent the same language values differently.

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
          (string . 6)    ; New: extended-payload + payload = 48-bit pointer to heap
          (rational . 7)  ; New: extended-payload + payload = 48-bit pointer to heap
          (closure . 8)   ; New: extended-payload + payload = 48-bit pointer to heap
          (tcp-conn . 9))) ; New: host resource handle

 (heap-representation .
  ((string . "null-terminated UTF-8 byte array")
   (rational . "two consecutive 64-bit pointers (numerator, denominator) to BigInt blocks")
   (closure . "two consecutive 64-bit pointers (environment, compiled-code-pointer)")))

 (notes . "Mechanism/history evidence only. Current SENS semantics must not inherit these tag ordinals; any backend using this layout must prove conformance independently."))
