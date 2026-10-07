; #3989 — target-neutral machine capability axis.
;
; This file does NOT define language semantics and does NOT define an ISA.
; Current semantic meaning is exact-domain: exact bits + exact domain +
; ratified law (Contract 11.8). Human spellings and historical SID8 bytes are
; not machine-capability authority.
;
; Current axis:
;   exact DomainIdentity -> 0..N machine capabilities -> 0..N target witnesses
;
; Historical SID8 machine-capability projections are no longer live code.
; Provenance remains in git history; current machine work uses
; machine-capabilities-for-domain exclusively.
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
       ((integer-add bounded-u32-inputs u64-result)))
     (01011
       ((integer-subtract bounded-u64 no-underflow)))
     (10110
       ((integer-multiply bounded-u32-inputs u64-result)))
     (10111
       ((integer-quotient bounded-positive-i64 equal-operands-only)))
     (11010
       ((integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary)))
     (11011
       ((integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary)))
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

(00001001 machine-capability-target-witnesses-v2
  (00000001
    ((x86-64
       (integer-add bounded-u32-inputs u64-result
         (admitted-form add-r64-r64)
         (lowering x86-lower-add-u64-forms))
       (integer-subtract bounded-u64 no-underflow
         (admitted-form sub-r64-r64)
         (lowering x86-lower-difference-u64-forms))
       (integer-multiply bounded-u32-inputs u64-result
         (admitted-form imul-r64-r64)
         (lowering x86-lower-times-u64-forms))
       (integer-quotient bounded-positive-i64 equal-operands-only
         (admitted-form cqo)
         (admitted-form idiv-r64)
         (lowering x86-lower-quotient-i64-equal-forms))
       (integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form setl-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-order-i64-forms))
       (integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form setg-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-order-i64-forms))
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

(00001001 machine-target-witness-status
  (00001000 (target)
    (10011100 ((row (machine-capability-find-row target machine-target-witness-status-v1)))
      (00000111
        ((00000010 row) () (00000001 absent))
        ((00000010 row) (1) (00000001 absent))
        (t (00000101 (00000110 row)))))))
