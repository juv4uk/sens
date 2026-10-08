; Lisp-owned x86-64 pair representation contract for the first native proof slice.
;
; The host owns only raw memory allocation and the call boundary. Lisp-authored
; machine lowering owns these field offsets and therefore owns the loads/stores
; that interpret the arena as a pair cell.
;
; This is deliberately not a general heap or GC ABI yet. The cell exists only
; for one native-call-u64-raw invocation and must not escape that call.

(00001001 x86-pair-cell-bytes 16)
(00001001 x86-pair-car-offset 0)
(00001001 x86-pair-cdr-offset 8)

(00001001 x86-pair-layout
  (00000001
    (machine-pair-layout/1
      (target x86-64)
      (word-bits 64)
      (cell-bytes 16)
      (fields
        ((100 (offset-bytes 0) (width-bits 64))
         (011 (offset-bytes 8) (width-bits 64))))
      (arena-argument-register rdi)
      (allocation raw-host-arena)
      (lifetime native-call)
      (escape forbidden))))
