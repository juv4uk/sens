; #3989 — target-neutral machine capability axis.
;
; This file does NOT define language semantics and does NOT define an ISA.
; Current semantic meaning is exact-domain: exact bits + exact domain +
; ratified law (Contract 11.7). Human spellings and historical SID8 bytes are
; not machine-capability authority.
;
; Current axis:
;   exact DomainIdentity -> 0..N machine capabilities -> 0..N target witnesses
;
; The legacy SID8 axis is retained below only as an explicit compatibility
; projection for historical tests/evidence. New machine work must use
; machine-capabilities-for-domain.
;
; A capability name never mints a semantic identity. A target may honestly have
; no witness yet. Target-specific lowering remains under lib/machine/lowering/*.

; Current exact-domain machine-capability slice.
;
; The keys below are exact domain literals, not zero-padded bytes:
;   D5:01010 = PLUS
;   D3:101   = EQ
;   D3:110   = COND
;   D3:111   = CONS
;   D3:100   = CAR
;   D3:011   = CDR
(00001001 machine-capability-axis-v2
  (00000001
    ((01010
       ((integer-add bounded-u64)))
     (101
       ((identity-compare bounded-u64)))
     (110
       ((conditional-branch bounded-u64)))
     (111
       ((pair-field-store head bounded-u64)
        (pair-field-store tail bounded-u64)))
     (100
       ((pair-field-load head bounded-u64)))
     (011
       ((pair-field-load tail bounded-u64))))))

; Historical SID8 compatibility projection. It does not own current meaning.
(00001001 machine-capability-legacy-sid-axis-v1
  (00000001
    ((00001100
       ((integer-add bounded-u64)))
     (00000011
       ((identity-compare bounded-u64)))
     (00000111
       ((conditional-branch bounded-u64)))
     (00000100
       ((pair-field-store head bounded-u64)
        (pair-field-store tail bounded-u64)))
     (00000101
       ((pair-field-load head bounded-u64)))
     (00000110
       ((pair-field-load tail bounded-u64))))))

(00001001 machine-capability-target-witnesses-v2
  (00000001
    ((x86-64
       (integer-add bounded-u64
         (admitted-form add-r64-r64)
         (lowering x86-lower-add-u64-forms))
       (identity-compare bounded-u64
         (admitted-form cmp-r64-r64)
         (lowering x86-lower-eq-cond-u64-forms))
       (conditional-branch bounded-u64
         (admitted-form jnz-rel8)
         (lowering x86-lower-eq-cond-u64-forms))
       (pair-field-store head bounded-u64
         (admitted-form mov-mem-disp8-r64)
         (lowering x86-lower-bounded-pair-store-u64-forms))
       (pair-field-store tail bounded-u64
         (admitted-form mov-mem-disp8-r64)
         (lowering x86-lower-bounded-pair-store-u64-forms))
       (pair-field-load head bounded-u64
         (admitted-form mov-r64-mem-disp8)
         (lowering x86-lower-cons-car-u64-forms))
       (pair-field-load tail bounded-u64
         (admitted-form mov-r64-mem-disp8)
         (lowering x86-lower-cons-cdr-u64-forms))))))

(00001001 machine-target-witness-status-v1
  (00000001
    ((x86-64 witnessed)
     (arm64 absent)
     (risc-v absent)
     (fpga absent))))

(00001001 machine-capability-find-row
  (00001000 (key rows)
    (00000111
      ((00000010 rows) () ())
      ((00000010 rows) (1) ())
      ((00100010 key (00000101 (00000101 rows))) (00000101 rows))
      (t (machine-capability-find-row key (00000110 rows))))))

; Current lookup: exact domain identity only.
(00001001 machine-capabilities-for-domain
  (00001000 (identity)
    (10011100 ((row (machine-capability-find-row identity machine-capability-axis-v2)))
      (00000111
        ((00000010 row) () ())
        ((00000010 row) (1) ())
        (t (00000101 (00000110 row)))))))

; Compatibility lookup for historical evidence only.
(00001001 machine-capabilities-for-sid
  (00001000 (sid)
    (10011100 ((row (machine-capability-find-row sid machine-capability-legacy-sid-axis-v1)))
      (00000111
        ((00000010 row) () ())
        ((00000010 row) (1) ())
        (t (00000101 (00000110 row)))))))

(00001001 machine-target-witness-status
  (00001000 (target)
    (10011100 ((row (machine-capability-find-row target machine-target-witness-status-v1)))
      (00000111
        ((00000010 row) () (00000001 absent))
        ((00000010 row) (1) (00000001 absent))
        (t (00000101 (00000110 row)))))))
