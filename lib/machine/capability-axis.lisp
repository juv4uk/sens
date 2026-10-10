; #3989/#4068 — target-neutral machine capability axis.
;
; This file does NOT define language semantics and does NOT define an ISA.
; Current semantic meaning is exact-domain: exact bits + exact domain +
; ratified law (Contract 11.8). Human spellings and historical SID8 bytes are
; not machine-capability authority.
;
; LIVE MACHINE KEY:
;   (domain-width, packed-bits)
;
; Atomic mechanism keys are compared by D3 EQ -> exact D1 PredicateBit;
; historical structural EQUAL is not used to compare width/packed-bit scalars.
; Width is explicit mechanism data derived from Rust DomainIdentity::width().
; Packed bits are derived from DomainIdentity::packed_bits(). This remains
; width-safe even while ordinary Lisp source cannot preserve W1-W7 leading
; zero width (#3946).
;
; Examples:
;   D5:01010 PLUS  -> (5, 10)
;   D4:1010 LOOKUP -> (4, 10)
; Same packed payload, different key. No spelling or quoted bit string enters.
;
; A capability name never mints a semantic identity. Target-specific lowering
; remains under lib/machine/lowering/*.

(00001001 machine-capability-axis-v3
  (00000001
    ((5 8
       ((integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary)))
     (5 10
       ((integer-add bounded-u32-inputs u64-result)))
     (5 11
       ((integer-subtract bounded-u64 no-underflow)))
     (5 22
       ((integer-multiply bounded-u32-inputs u64-result)))
     (5 23
       ((integer-quotient bounded-positive-i64 equal-operands-only)))
     (5 26
       ((integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary)))
     (5 27
       ((integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary)))
     (6 14
       ((integer-increment bounded-u64 no-overflow)))
     (6 15
       ((integer-decrement bounded-u64 no-underflow)))
     (3 5
       ((identity-compare bounded-u64)))
     (3 6
       ((conditional-branch bounded-u64)))
     (3 7
       ((pair-field-store head bounded-u64)
        (pair-field-store tail bounded-u64)))
     (3 4
       ((pair-field-load head bounded-u64)))
     (3 3
       ((pair-field-load tail bounded-u64))))))

(00001001 machine-capability-target-witnesses-v2
  (00000001
    ((x86-64
       (integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary
         (admitted-form cmp-r64-r64)
         (admitted-form sete-r8)
         (admitted-form movzx-r64-r8)
         (lowering x86-lower-zerop-u64-forms))
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
       (integer-increment bounded-u64 no-overflow
         (admitted-form add-r64-r64)
         (lowering x86-lower-add-u64-forms))
       (integer-decrement bounded-u64 no-underflow
         (admitted-form sub-r64-r64)
         (lowering x86-lower-difference-u64-forms))
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

; Migration: canonical D3 ATOM produces only D1 1/0. Empty rows return
; structural (), not PredicateBit 0. Every default COND test is exact D1:1
; from ATOM(QUOTE ()), never host T, data equality, or implicit truthiness.
(00001001 machine-capability-find-domain-row
  (00001000 (width bits rows)
    (00000111
      ((00000010 rows) (00000001 ()))
      ((00000011 width (00000101 (00000101 rows)))
       (00000111
         ((00000011 bits (00000101 (00000110 (00000101 rows))))
          (00000101 rows))
         ((00000010 (00000001 ()))
          (machine-capability-find-domain-row
            width bits (00000110 rows)))))
      ((00000010 (00000001 ()))
       (machine-capability-find-domain-row
         width bits (00000110 rows))))))

; Current lookup: explicit width + packed-bits mechanism key only.
(00001001 machine-capabilities-for-domain
  (00001000 (width bits)
    (10011100
      ((row
         (machine-capability-find-domain-row
           width bits machine-capability-axis-v3)))
      (00000111
        ((00000010 row) (00000001 ()))
        ((00000010 (00000001 ()))
         (00000101 (00000110 (00000110 row))))))))

(00001001 machine-capability-find-row
  (00001000 (key rows)
    (00000111
      ((00000010 rows) (00000001 ()))
      ((00000011 key (00000101 (00000101 rows))) (00000101 rows))
      ((00000010 (00000001 ())) (machine-capability-find-row key (00000110 rows))))))

(00001001 machine-target-witness-status
  (00001000 (target)
    (10011100 ((row (machine-capability-find-row target machine-target-witness-status-v1)))
      (00000111
        ((00000010 row) (00000001 absent))
        ((00000010 (00000001 ())) (00000101 (00000110 row)))))))
