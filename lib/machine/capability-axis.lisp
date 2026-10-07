; #4068 — target-neutral width-safe machine capability axis.
;
; This file does NOT define language semantics and does NOT define an ISA.
; Current semantic meaning is exact-domain: exact bits + exact domain +
; ratified law (Contract 11.8). Human spellings and historical SID8 bytes are
; not machine-capability authority.
;
; IMPORTANT: ordinary Lisp source does not preserve leading-zero width for
; W1-W7 (#3946). Therefore live machine dispatch never uses a bare bit-looking
; token as an identity key. It carries the two scalar fields obtained from the
; real DomainIdentity:
;
;   domain-width + packed-bits -> capabilities
;
; Examples:
;   D5:01010 PLUS  -> (5, 10)
;   D4:1010 LOOKUP -> (4, 10)
;
; Those keys cannot collide even though the ordinary Lisp reader would collapse
; the source spellings 01010 and 1010 to the same numeric value.

; Row schema:
;   (domain-width packed-bits ((capability ...)*))
(00001001 machine-capability-axis-v3
  (00000001
    ((5 10
       ((integer-add bounded-u32-inputs u64-result)))              ; D5:01010 PLUS
     (5 11
       ((integer-subtract bounded-u64 no-underflow)))              ; D5:01011 DIFFERENCE
     (5 22
       ((integer-multiply bounded-u32-inputs u64-result)))         ; D5:10110 TIMES
     (5 23
       ((integer-quotient bounded-positive-i64 equal-operands-only))) ; D5:10111 QUOTIENT
     (5 26
       ((integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary))) ; D5:11010 LESSP
     (5 27
       ((integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary))) ; D5:11011 GREATERP
     (3 5
       ((identity-compare bounded-u64)))                            ; D3:101 EQ
     (3 6
       ((conditional-branch bounded-u64)))                         ; D3:110 COND
     (3 7
       ((pair-field-store head bounded-u64)
        (pair-field-store tail bounded-u64)))                      ; D3:111 CONS
     (3 4
       ((pair-field-load head bounded-u64)))                       ; D3:100 CAR
     (3 3
       ((pair-field-load tail bounded-u64))))))                    ; D3:011 CDR

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

(00001001 machine-domain-capability-find-row
  (00001000 (width packed-bits rows)
    (00000111
      ((00000010 rows) () ())
      ((00000010 rows) (1) ())
      ((00100010 width (00000101 (00000101 rows)))
       (00000111
         ((00100010 packed-bits (00000101 (00000110 (00000101 rows))))
          (00000101 rows))
         (t
          (machine-domain-capability-find-row
            width packed-bits (00000110 rows)))))
      (t
       (machine-domain-capability-find-row
         width packed-bits (00000110 rows))))))

; Current lookup: width-safe exact domain identity transport.
(00001001 machine-capabilities-for-domain
  (00001000 (width packed-bits)
    (10011100 ((row
                  (machine-domain-capability-find-row
                    width packed-bits machine-capability-axis-v3)))
      (00000111
        ((00000010 row) () ())
        ((00000010 row) (1) ())
        (t
         (00000101 (00000110 (00000110 row))))))))

(00001001 machine-capability-find-row
  (00001000 (key rows)
    (00000111
      ((00000010 rows) () ())
      ((00000010 rows) (1) ())
      ((00100010 key (00000101 (00000101 rows))) (00000101 rows))
      (t (machine-capability-find-row key (00000110 rows))))))

(00001001 machine-target-witness-status
  (00001000 (target)
    (10011100 ((row (machine-capability-find-row target machine-target-witness-status-v1)))
      (00000111
        ((00000010 row) () (00000001 absent))
        ((00000010 row) (1) (00000001 absent))
        (t (00000101 (00000110 row)))))))
