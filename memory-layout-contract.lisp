; memory-layout-contract.lisp — historical/mechanism NaN-boxing layout design
; Історичний/механічний дизайн layout; НЕ семантична онтологія SENS.
; Historischer/mechanischer Layout-Entwurf; KEINE SENS-Semantik.
;
; This records a historical/mechanism 64-bit IEEE 754 NaN-boxing representation.
; Tag widths and ordinals are implementation evidence only: they do NOT define
; SENS value identity, payload domains, or canonical language semantics.
; The lower 32-bit shape was designed to align with the fpga-lisp VALUE WORD;
; independent runtimes may represent the same language values differently.
;
; STATUS: mechanism-private / historical-transition — NOT current language semantic authority.
; Current SENS semantics: binary-only (Control2, Function8, Text7, Predicate1).
; This layout is mechanism evidence only; tag ordinals MUST NOT be inherited as semantics.
;
; See: #1774 slice D (layout demotion), #1696 (no canonical Symbol), #1713 (Predicate1),
; #1700 (Text7/UPC-7), #1709 (semantic witnesses own canonical identities).

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

 (tags . ((fixnum . 0)        ; host/mechanism — exact integer representation
          (cons . 1)          ; host/mechanism — pair structure (Control2 is canonical)
          (symbol . 2)        ; OBSOLETE — conflicts with binary-only ontology (#1696)
          (nil . 3)           ; host/mechanism — empty list (Control2 `01` canonical)
          (true . 4)          ; OBSOLETE — conflicts with binary-only predicate=1/0 (#1713)
          (primitive . 5)     ; host/mechanism — primitive function entry
          (string . 6)        ; OBSOLETE — UTF-8 string conflicts with Text7 (#1700)
          (rational . 7)      ; host/mechanism — two 64-bit pointers
          (closure . 8)       ; host/mechanism — env + code pointer
          (tcp-conn . 9)))    ; host/resource — OS handle, not language value

 (heap-representation .
  ((string . "null-terminated UTF-8 byte array")
   (rational . "two consecutive 64-bit pointers (numerator, denominator) to BigInt blocks")
   (closure . "two consecutive 64-bit pointers (environment, compiled-code-pointer)")))

 (notes . "Mechanism/history evidence only. Current SENS semantics MUST NOT inherit these tag ordinals; any backend using this layout must prove conformance independently. Obsolete tags (symbol, true, string) conflict with binary-only ontology and are retained only as historical mechanism evidence."))
