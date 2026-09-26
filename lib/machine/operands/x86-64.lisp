; #177 — typed x86-64 machine operands as Lisp-owned data.
;
; This layer owns operand *shape*, not instruction admission and not encoding.
; Register knowledge is intentionally reused from x86-reg-code in the existing
; Lisp encoder so this file cannot become a second GPR table. A well-typed
; operand may still participate in an instruction form that #176 admission
; rejects; type success is not capability/admission success.

(00001001 x86-machine-operand-rejection
  (00001000 (expected actual)
    (list (00000001 rejected) (00000001 machine-operand) expected actual)))

(00001001 x86-machine-rejected?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000001 ()))
      ((00000011 (00000101 value) (00000001 rejected)) t)
      (t (00000001 ())))))

(00001001 x86-gpr8-name?
  (00001000 (name)
    (00000111
      ((symbol? name)
       (member?
         name
         (00000001
           (al cl dl bl spl bpl sil dil
               r8b r9b r10b r11b r12b r13b r14b r15b))))
      (t (00000001 ())))))

(00001001 x86-gpr64-name?
  (00001000 (name)
    (00000111
      ((symbol? name)
       (and
         (not? (00000011 (x86-reg-code name) (00000001 ())))
         (not? (x86-gpr8-name? name))))
      (t (00000001 ())))))

(00001001 x86-gpr8?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 gpr8))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (x86-gpr8-name? (second operand)))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-gpr8
  (00001000 (name)
    (00000111
      ((x86-gpr8-name? name) (list (00000001 gpr8) name))
      (t (x86-machine-operand-rejection (00000001 gpr8) name)))))

(00001001 x86-as-gpr8
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr8? operand) operand)
      (t (x86-gpr8 operand)))))

(00001001 x86-gpr8-value
  (00001000 (operand)
    (second operand)))

(00001001 x86-gpr64?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 gpr64))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (x86-gpr64-name? (second operand)))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-gpr64
  (00001000 (name)
    (00000111
      ((x86-gpr64-name? name) (list (00000001 gpr64) name))
      (t (x86-machine-operand-rejection (00000001 gpr64) name)))))

(00001001 x86-as-gpr64
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr64? operand) operand)
      (t (x86-gpr64 operand)))))

(00001001 x86-gpr64-value
  (00001000 (operand)
    (second operand)))

; A gpr32 operand is a 32-bit view of the same physical general-purpose
; register named by its canonical 64-bit base name. The encoder already owns
; the physical register-code mapping and the instruction form owns width, so
; this typed view deliberately does not introduce a second eax/ecx/... code
; table merely to say "lower 32 bits of rax/rcx/...".
(00001001 x86-gpr32-name?
  (00001000 (name)
    (x86-gpr64-name? name)))

(00001001 x86-gpr32?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 gpr32))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (x86-gpr32-name? (second operand)))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-gpr32
  (00001000 (name)
    (00000111
      ((x86-gpr32-name? name) (list (00000001 gpr32) name))
      (t (x86-machine-operand-rejection (00000001 gpr32) name)))))

(00001001 x86-as-gpr32
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr32? operand) operand)
      (t (x86-gpr32 operand)))))

(00001001 x86-gpr32-value
  (00001000 (operand)
    (second operand)))

; XMM is a separate register class even though encoding uses the same 4-bit
; ModR/M namespace width. Validity is projected from x86-xmm-reg-code so this
; typed layer does not become a second XMM number table.
(00001001 x86-xmm-name?
  (00001000 (name)
    (00000111
      ((symbol? name)
       (00000111
         ((equal? (x86-xmm-reg-code name) (00000001 ()))
          (structural-relation same)
          (00000001 ()))
         ((equal? (x86-xmm-reg-code name) (00000001 ()))
          (structural-relation distinct)
          t)))
      (t (00000001 ())))))

(00001001 x86-xmm?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 xmm))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (x86-xmm-name? (second operand)))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-xmm
  (00001000 (name)
    (00000111
      ((x86-xmm-name? name) (list (00000001 xmm) name))
      (t (x86-machine-operand-rejection (00000001 xmm) name)))))

(00001001 x86-as-xmm
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-xmm? operand) operand)
      (t (x86-xmm operand)))))

(00001001 x86-xmm-value
  (00001000 (operand)
    (second operand)))

; Exact integer recognition stays in Lisp and does not require a new host
; `number?`/`integer?` primitive. Canonical serialization is already a language
; contract: exact integers print as optional '-' followed only by decimal
; digits; exact non-integral rationals contain '/', and inexact values retain a
; decimal marker. symbol? is checked first so a symbol created with numeric text
; cannot impersonate a number.
(00001001 x86-decimal-digit?
  (00001000 (character)
    (member? character
             (00000001 ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(00001001 x86-decimal-digits?
  (00001000 (text)
    (00000111
      ((string-empty? text) t)
      ((x86-decimal-digit? (string-first text))
       (x86-decimal-digits? (string-rest text)))
      (t (00000001 ())))))

(00001001 x86-exact-integer?
  (00001000 (value)
    (00000111
      ((not? (00000010 value)) (00000001 ()))
      ((symbol? value) (00000001 ()))
      (t
       (let ((text (write-to-string value)))
         (00000111
           ((string-empty? text) (00000001 ()))
           ((00000011 (string-first text) "-")
            (00000111
              ((string-empty? (string-rest text)) (00000001 ()))
              (t (x86-decimal-digits? (string-rest text)))))
           (t (x86-decimal-digits? text))))))))

(00001001 x86-operand-in-inclusive-range?
  (00001000 (value lower upper)
    ; Exact-Q comparisons answer 1 (так) / 0 (ні), and 0 is truthy -- so a
    ; bare `and` over comparison results accepted every operand, overflowing
    ; u64-imm/disp8 slots. E1 (#216): explicit expected-result domains,
    ; reduced to a t/() structural predicate so it is safe as a cond query.
    (00000111
      ((>= value lower) 1
        (00000111
          ((<= value upper) 1 t)
          ((<= value upper) 0 (00000001 ()))))
      ((>= value lower) 0 (00000001 ())))))

(00001001 x86-u64-imm?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 u64-imm))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (let ((value (second operand)))
            (00000111
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value 0 18446744073709551615))
              (t (00000001 ())))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-u64-imm
  (00001000 (value)
    (00000111
      ((x86-exact-integer? value)
       (00000111
         ((x86-operand-in-inclusive-range? value 0 18446744073709551615)
          (list (00000001 u64-imm) value))
         (t (x86-machine-operand-rejection (00000001 u64-imm) value))))
      (t (x86-machine-operand-rejection (00000001 u64-imm) value)))))

(00001001 x86-as-u64-imm
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-u64-imm? operand) operand)
      (t (x86-u64-imm operand)))))

(00001001 x86-u64-imm-value
  (00001000 (operand)
    (second operand)))

(00001001 x86-disp8?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 disp8))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((equal? (00000110 (00000110 operand)) (00000001 ()))
          (let ((value (second operand)))
            (00000111
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value -128 127))
              (t (00000001 ())))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-disp8
  (00001000 (value)
    (00000111
      ((x86-exact-integer? value)
       (00000111
         ((x86-operand-in-inclusive-range? value -128 127)
          (list (00000001 disp8) value))
         (t (x86-machine-operand-rejection (00000001 disp8) value))))
      (t (x86-machine-operand-rejection (00000001 disp8) value)))))

(00001001 x86-as-disp8
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-disp8? operand) operand)
      (t (x86-disp8 operand)))))

(00001001 x86-disp8-value
  (00001000 (operand)
    (second operand)))

(00001001 x86-mem64-disp8?
  (00001000 (operand)
    (00000111
      ((00000010 operand) (00000001 ()))
      ((00000011 (00000101 operand) (00000001 mem64-disp8))
       (00000111
         ((00000010 (00000110 operand)) (00000001 ()))
         ((00000010 (00000110 (00000110 operand))) (00000001 ()))
         ((equal? (00000110 (00000110 (00000110 operand))) (00000001 ()))
          (and (x86-gpr64? (second operand))
               (x86-disp8? (third operand))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-mem64-disp8
  (00001000 (base displacement)
    (let ((typed-base (x86-as-gpr64 base)))
      (00000111
        ((x86-machine-rejected? typed-base) typed-base)
        (t
         (let ((typed-displacement (x86-as-disp8 displacement)))
           (00000111
             ((x86-machine-rejected? typed-displacement) typed-displacement)
             (t
              (list (00000001 mem64-disp8)
                    typed-base
                    typed-displacement)))))))))

(00001001 x86-as-mem64-disp8
  (00001000 (operand)
    (00000111
      ((x86-machine-rejected? operand) operand)
      ((x86-mem64-disp8? operand) operand)
      (t (x86-machine-operand-rejection (00000001 mem64-disp8) operand)))))

(00001001 x86-mem64-disp8-base
  (00001000 (operand)
    (x86-gpr64-value (second operand))))

(00001001 x86-mem64-disp8-displacement
  (00001000 (operand)
    (x86-disp8-value (third operand))))
