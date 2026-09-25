; #815 — target-neutral machine capability axis.
;
; This file does NOT define language semantics and does NOT define an ISA.
; Semantic meaning stays in lib/surface/semantic-registry.lisp + Lisp laws.
; Capability names below are ordinary data used to describe bounded physical
; requirements of already-existing semantic identities.
;
; Axis:
;   semantic SID -> 0..N machine capabilities -> 0..N target witnesses
;
; A capability name never mints a semantic SID. A target may honestly have no
; witness yet. Target-specific lowering remains under lib/machine/lowering/*.

(00001001 machine-capability-axis-v1
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

(00001001 machine-capability-target-witnesses-v1
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
      ((00000010 rows) ())
      ((equal? key (00000101 (00000101 rows))) (00000101 rows))
      (t (machine-capability-find-row key (00000110 rows))))))

(00001001 machine-capabilities-for-sid
  (00001000 (sid)
    (let ((row (machine-capability-find-row sid machine-capability-axis-v1)))
      (00000111
        ((00000010 row) ())
        (t (00000101 (00000110 row)))))))

(00001001 machine-target-witness-status
  (00001000 (target)
    (let ((row (machine-capability-find-row target machine-target-witness-status-v1)))
      (00000111
        ((00000010 row) (00000001 absent))
        (t (00000101 (00000110 row)))))))
