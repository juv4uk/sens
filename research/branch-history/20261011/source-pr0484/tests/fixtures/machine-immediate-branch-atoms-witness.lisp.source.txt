; #178 preparation — typed immediate/relative-control atom witness.
; All forms here were already admitted/encoded by #176 before these atoms
; existed. This file owns only composition evidence and bounded native probes.

(load "lib/core.lisp")
(load "lib/machine/block.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/atoms/x86-64.lisp")

(def machine-imm-branch-rows
  (lambda ()
    (list
      (list (quote imm32-min)
            (x86-imm32 -2147483648)
            (quote (imm32 -2147483648)))
      (list (quote imm32-max)
            (x86-imm32 2147483647)
            (quote (imm32 2147483647)))
      (list (quote imm32-overflow)
            (x86-imm32 2147483648)
            (quote (rejected machine-operand imm32 2147483648)))
      (list (quote uimm8-max)
            (x86-uimm8 255)
            (quote (uimm8 255)))
      (list (quote uimm8-overflow)
            (x86-uimm8 256)
            (quote (rejected machine-operand uimm8 256)))
      (list (quote rel32-min)
            (x86-rel32 -2147483648)
            (quote (rel32 -2147483648)))
      (list (quote rel32-overflow)
            (x86-rel32 -2147483649)
            (quote (rejected machine-operand rel32 -2147483649)))
      (list (quote add-imm)
            (x86-add-r64-imm32 (quote r8) -7)
            (quote (add-r64-imm32 r8 -7)))
      (list (quote shift)
            (x86-shl-r64-imm8 (quote rax) 3)
            (quote (shl-r64-imm8 rax 3)))
      (list (quote jnz-rel8)
            (x86-jnz-rel8 -12)
            (quote (jnz-rel8 -12)))
      (list (quote jle-rel8)
            (x86-jle-rel8 12)
            (quote (jle-rel8 12)))
      (list (quote jnz-rel32)
            (x86-jnz-rel32 -4096)
            (quote (jnz-rel32 -4096)))
      (list (quote jmp-rel32)
            (x86-jmp-rel32 11)
            (quote (jmp-rel32 11)))
      (list (quote call-rel32)
            (x86-call-rel32 1)
            (quote (call-rel32 1)))
      (list (quote test-imm)
            (x86-test-r64-imm32 (quote rax) 42)
            (quote (test-r64-imm32 rax 42)))
      (list (quote bt-imm)
            (x86-bt-r64-imm8 (quote rax) 3)
            (quote (bt-r64-imm8 rax 3)))
      (list (quote bts-imm)
            (x86-bts-r64-imm8 (quote rax) 5)
            (quote (bts-r64-imm8 rax 5)))
      (list (quote btr-imm)
            (x86-btr-r64-imm8 (quote rax) 5)
            (quote (btr-r64-imm8 rax 5)))
      (list (quote btc-imm)
            (x86-btc-r64-imm8 (quote rax) 5)
            (quote (btc-r64-imm8 rax 5)))
      (list (quote rol-imm)
            (x86-rol-r64-imm8 (quote rax) 1)
            (quote (rol-r64-imm8 rax 1)))
      (list (quote ror-imm)
            (x86-ror-r64-imm8 (quote rax) 1)
            (quote (ror-r64-imm8 rax 1)))
      (list (quote typed-shift-rejection)
            (x86-shl-r64-imm8 (quote rax) 256)
            (quote (rejected machine-operand uimm8 256)))
      (list (quote typed-branch-rejection)
            (x86-jmp-rel32 2147483648)
            (quote (rejected machine-operand rel32 2147483648))))))

(def machine-imm-branch-check
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote pass))
      ((atom rows) (structural-kind atom)
       (list (quote fail) (quote malformed-row-tail) rows))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (name (car row))
              (actual (second row))
              (expected (third row)))
         (cond
           ((equal? actual expected) (structural-relation same)
            (machine-imm-branch-check (cdr rows)))
           ((equal? actual expected) (structural-relation distinct)
            (list (quote fail) name expected actual))))))))

(def machine-native-add-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 10)
        (x86-add-r64-imm32 (quote rax) 32)
        (x86-ret))
      0)))

(def machine-native-shift
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 21)
        (x86-shl-r64-imm8 (quote rax) 1)
        (x86-ret))
      0)))

(def machine-native-jnz-rel8
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 2)
        (x86-mov-r64-imm64 (quote rcx) 3)
        (x86-cmp-r64-r64 (quote rax) (quote rcx))
        (x86-jnz-rel8 11)
        (x86-mov-r64-imm64 (quote rax) 111)
        (x86-ret)
        (x86-mov-r64-imm64 (quote rax) 222)
        (x86-ret))
      0)))

(def machine-native-jnz-rel32
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 2)
        (x86-mov-r64-imm64 (quote rcx) 3)
        (x86-cmp-r64-r64 (quote rax) (quote rcx))
        (x86-jnz-rel32 11)
        (x86-mov-r64-imm64 (quote rax) 111)
        (x86-ret)
        (x86-mov-r64-imm64 (quote rax) 222)
        (x86-ret))
      0)))

(def machine-native-jmp-rel32
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-jmp-rel32 11)
        (x86-mov-r64-imm64 (quote rax) 111)
        (x86-ret)
        (x86-mov-r64-imm64 (quote rax) 222)
        (x86-ret))
      0)))

(def machine-native-call-rel32
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-call-rel32 1)
        (x86-ret)
        (x86-mov-r64-imm64 (quote rax) 42)
        (x86-ret))
      0)))


(def machine-native-test-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 42)
        (x86-test-r64-imm32 (quote rax) 2)
        (x86-setnz-r8 (quote al))
        (x86-movzx-r64-r8 (quote rax) (quote al))
        (x86-ret))
      0)))

(def machine-native-bt-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 8)
        (x86-bt-r64-imm8 (quote rax) 3)
        (x86-setc-r8 (quote al))
        (x86-movzx-r64-r8 (quote rax) (quote al))
        (x86-ret))
      0)))

(def machine-native-bts-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 0)
        (x86-bts-r64-imm8 (quote rax) 5)
        (x86-ret))
      0)))

(def machine-native-btr-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 32)
        (x86-btr-r64-imm8 (quote rax) 5)
        (x86-ret))
      0)))

(def machine-native-btc-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 0)
        (x86-btc-r64-imm8 (quote rax) 5)
        (x86-ret))
      0)))

(def machine-native-rol-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 21)
        (x86-rol-r64-imm8 (quote rax) 1)
        (x86-ret))
      0)))

(def machine-native-ror-imm
  (lambda ()
    (x86-call-admitted-u64
      (list
        (x86-mov-r64-imm64 (quote rax) 84)
        (x86-ror-r64-imm8 (quote rax) 1)
        (x86-ret))
      0)))

(def machine-imm-branch-native-rows
  (lambda ()
    (list
      (list (quote add-imm) (machine-native-add-imm) 42)
      (list (quote shift) (machine-native-shift) 42)
      (list (quote jnz-rel8) (machine-native-jnz-rel8) 222)
      (list (quote jnz-rel32) (machine-native-jnz-rel32) 222)
      (list (quote jmp-rel32) (machine-native-jmp-rel32) 222)
      (list (quote call-rel32) (machine-native-call-rel32) 42)
      (list (quote test-imm) (machine-native-test-imm) 1)
      (list (quote bt-imm) (machine-native-bt-imm) 1)
      (list (quote bts-imm) (machine-native-bts-imm) 32)
      (list (quote btr-imm) (machine-native-btr-imm) 0)
      (list (quote btc-imm) (machine-native-btc-imm) 32)
      (list (quote rol-imm) (machine-native-rol-imm) 42)
      (list (quote ror-imm) (machine-native-ror-imm) 42))))

(def machine-imm-branch-witness
  (lambda ()
    (let ((form-state (machine-imm-branch-check (machine-imm-branch-rows))))
      (cond
        ((eq form-state (quote pass)) (identity-relation same)
         (let ((native-state
                 (machine-imm-branch-check
                   (machine-imm-branch-native-rows))))
           (cond
             ((eq native-state (quote pass)) (identity-relation same)
              (quote (machine-immediate-branch-atoms-witness (status pass))))
             ((eq native-state (quote pass)) (identity-relation distinct)
              (list
                (quote machine-immediate-branch-atoms-witness)
                (quote (status fail))
                (list (quote native) native-state))))))
        ((eq form-state (quote pass)) (identity-relation distinct)
         (list
           (quote machine-immediate-branch-atoms-witness)
           (quote (status fail))
           (list (quote forms) form-state)))))))

(machine-imm-branch-witness)
