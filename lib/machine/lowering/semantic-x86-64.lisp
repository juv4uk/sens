; Українська проєкція зниження семантики СЕНС до x86-64.
; Значення мови належить чинному контракту та ратифікованим законам доменів.
; Набір інструкцій і кодування належать lib/machine/isa та lib/machine/encoding.
; Цей файл визначає лише реалізацію вже наявної семантичної тотожності.
;
; Зниження повертає структуровані машинні форми. Фізичні байти створює
; окремий закритий шар допуску; прямого обхідного інтерфейсу тут немає.

; First executable semantic-lowering witness.
; Semantic identity 00001100 already exists before this file is loaded. This
; routine does not define addition; it chooses one bounded u64 realization.
; It returns structured machine forms only. Admission owns the path from those
; forms to executable bytes.
;
; RAX carries the result per SysV x86-64. RCX is caller-saved, so the proof
; routine does not violate the host ABI by clobbering a callee-saved register.
(визначити машина-знизити-додавання-беззнакових-64-до-форм
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є add-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

; #4001 bounded exact-D5 DIFFERENCE/TIMES witnesses. These routines only
; describe machine forms. Selection is guarded below by exact D5 evaluation,
; so SUB/IMUL are used only when inputs and the exact result all fit u64.
(визначити машина-знизити-віднімання-беззнакових-64-до-форм
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є sub-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

(визначити машина-знизити-множення-беззнакових-64-до-форм
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є imul-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

; #4017 first exact-D5 QUOTIENT machine witness.
; This intentionally proves only x/x = 1 for positive signed-i64 operands.
; The narrow relation guarantees exact divisibility without borrowing a
; spelling, historical SID8 remainder helper, or truncating rational semantics.
(визначити машина-знизити-частку-знакових-64-до-форм
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є cqo))
      (список (як-є idiv-r64) (як-є rcx))
      (список (як-є ret)))))

; #196 bounded conditional-growth witness for existing EQ + COND semantics.
; This routine does not define equality or conditional evaluation. It chooses
; one fixed-width u64 realization whose only purpose is to establish the
; machine-effect lower bound demanded by a two-arm runtime decision.
;
; JNZ +11 skips exactly one MOV r64,imm64 (10 bytes) plus one RET (1 byte),
; landing at the ELSE arm. This is deliberately not a general label resolver,
; branch assembler, or compiler policy. It returns structured forms only;
; closed admission remains the sole path to bytes.
(визначити машина-знизити-рівність-та-умову-64
  (функція (лівий-операнд правий-операнд значення-якщо-так значення-якщо-ні)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд)
      (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є jnz-rel8) 11)
      (список (як-є mov-r64-imm64) (як-є rax) значення-якщо-так)
      (список (як-є ret))
      (список (як-є mov-r64-imm64) (як-є rax) значення-якщо-ні)
      (список (як-є ret)))))

; #196 conditional+structural composition helper. Each branch constructs one
; bounded pair in the same native-call arena and returns its CAR. The caller
; selects distinct caller-saved extended GPRs so #207's widened MOV imm64
; admission is exercised by semantic composition rather than by an ISA-only
; witness. RAX remains the guest ABI result register.
(визначити машина-знизити-обмежений-вибір-першого-пари-64
  (функція (лівий-операнд правий-операнд лівий-регістр правий-регістр)
    (список
      (список (як-є mov-r64-imm64) лівий-регістр лівий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-перше-зсув
        лівий-регістр)
      (список (як-є mov-r64-imm64) правий-регістр правий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-решта-зсув
        правий-регістр)
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-пара-перше-зсув)
      (список (як-є ret)))))

; Third bounded #196 slice: compose runtime COND/EQ choice with structural
; CAR(CONS ...) branch bodies. This remains deliberately finite: JNZ +33 skips
; exactly one six-form CAR(CONS) arm (10+4+10+4+4+1 bytes with base RDI), and
; each arm returns directly. No label resolver, register allocator, GC, or
; general recursive expression lowering is claimed here.
(визначити машина-знизити-рівність-умову-та-пару-64
  (функція (лівий-операнд правий-операнд перше-якщо-так решта-якщо-так перше-якщо-ні решта-якщо-ні)
    (приєднати
      (список
        (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
        (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд)
        (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
        (список (як-є jnz-rel8) 33))
      (приєднати
        (машина-знизити-обмежений-вибір-першого-пари-64
          перше-якщо-так решта-якщо-так (як-є r8) (як-є r9))
        (машина-знизити-обмежений-вибір-першого-пари-64
          перше-якщо-ні решта-якщо-ні (як-є r10) (як-є r11))))))

; Bounded structural witness for semantic identities 00000100/00000101/00000110.
; The host contributes only a raw writable arena pointer in RDI. Lisp owns
; the fact that one admitted pair cell has head at x86-пара-перше-зсув and
; tail at x86-пара-решта-зсув. These routines produce structured STORE/LOAD
; forms; admission and the encoder produce physical bytes only afterwards.
;
; This is deliberately not a claim that arbitrary first-class pair values may
; already escape native code: pair-x86-64.lisp fixes lifetime=native-call and
; escape=forbidden for this proof slice.
(визначити машина-знизити-запис-пари-64
  (функція (лівий-операнд правий-операнд)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-перше-зсув
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) правий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-решта-зсув
        (як-є rax)))))

; Historical internal name retained as an explicit forwarding closure.
; Do not place the bare function designator in value position: the strict
; source path must make callability explicit and preserve structured forms.
(визначити машина-знизити-інструкції-запису-пари-64
  (функція (лівий-операнд правий-операнд)
    (машина-знизити-запис-пари-64 лівий-операнд правий-операнд)))

; Append only the finite structured machine-form lists using current D3
; primitives. Do not route this boundary through Core4's deferred legacy
; reverse-onto/COND implementation: tests and authority remain language-owned.
(визначити машина-приєднати-форми
  (функція (форми хвіст)
    (за-умовою
      ((атом? форми) хвіст)
      (так (сполучити (перше форми) (машина-приєднати-форми (решта форми) хвіст))))))

; The bounded native pair witness has a fixed six-instruction shape. Build it
; directly rather than routing through generic append/reverse: those Core4 list
; traversals currently consume graded relation answers as COND control and must
; keep failing closed until their predicate adapter is migrated. This narrow
; witness should not depend on an unfinished generic traversal path.
(визначити знизити-складену-пару-до-машинних-форм
  (функція (лівий-операнд правий-операнд)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-перше-зсув
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) правий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-решта-зсув
        (як-є rax))
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-пара-перше-зсув)
      (список (як-є ret)))))

(визначити x86-lower-cons-car-u64-forms знизити-складену-пару-до-машинних-форм)

(визначити машина-знизити-решту-пари-64
  (функція (лівий-операнд правий-операнд)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-перше-зсув
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) правий-операнд)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-пара-решта-зсув
        (як-є rax))
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-пара-решта-зсув)
      (список (як-є ret)))))

; Bounded semantic entry for the Vertical Day CAR witness.
; Canonical CAR/CDR own pair validity and therefore fail with the language's
; existing Type outcome before any machine request exists. Only after that
; language-owned gate succeeds do the extracted u64 fields become structured
; machine forms, pass closed admission, and enter the semantics-blind host.
; No pair predicate or tag rule is duplicated in this machine layer.
(визначити машина-викликати-семантичне-перше-64
  (функція (значення-пари)
    (викликати-допущену-машинну-програму
      (знизити-складену-пару-до-машинних-форм
        (перше значення-пари)
        (решта значення-пари))
      x86-пара-байти-комірки)))


; #3989/#4001 current exact-domain D5 arithmetic entry.
; Exact D5 semantic identity chooses the operation. The machine fast path then
; applies a deliberately conservative numeric guard that cannot change exact
; language meaning:
;   PLUS/TIMES: both exact-integer inputs in u32 => result is guaranteed u64;
;   DIFFERENCE: both exact-integer inputs in u64 and left >= right.
; Anything outside those proved rectangles fails closed to the exact Lisp/Q
; fallback. Historical SID8 values and human spellings never participate.
(визначити машина-поточний-д5-допустимі-входи-32?
  (функція (лівий-операнд правий-операнд)
    (за-умовою
      ((машина-допуск-точне-ціле? лівий-операнд)
       (за-умовою
         ((машина-допуск-ціле-у-включних-межах?
            лівий-операнд 0 4294967295)
          (за-умовою
            ((машина-допуск-точне-ціле? правий-операнд)
             (машина-допуск-ціле-у-включних-межах?
               правий-операнд 0 4294967295))
            (так (як-є ()))))
         (так (як-є ()))))
      (так (як-є ())))))

(визначити машина-поточний-д5-безпечна-різниця-64?
  (функція (лівий-операнд правий-операнд)
    (за-умовою
      ((машина-допуск-точне-ціле? лівий-операнд)
       (за-умовою
         ((машина-допуск-ціле-у-включних-межах?
            лівий-операнд 0 18446744073709551615)
          (за-умовою
            ((машина-допуск-точне-ціле? правий-операнд)
             (за-умовою
               ((машина-допуск-ціле-у-включних-межах?
                  правий-операнд 0 18446744073709551615)
                ; Inclusive order is derived from admitted D5 LESSP + D4 NOT.
                ; Exact D1 controls stay distinct from numeric 0/1 and host truth.
                (за-умовою
                  ((хибне? (менше? лівий-операнд правий-операнд)) так)
                  (так (як-є ()))))
               (так (як-є ()))))
            (так (як-є ()))))
         (так (як-є ()))))
      (так (як-є ())))))

; #4068 width-safe machine key helper. Width and packed bits are separate
; mechanism scalars derived from Rust DomainIdentity; source leading zeros are never
; consulted.
(визначити машинний-ключ-поточного-домену?
  (функція (ширина-домену біти-домену очікувана-ширина очікувані-біти)
    (за-умовою
      ((тотожне? ширина-домену очікувана-ширина)
       (тотожне? біти-домену очікувані-біти))
      (так (як-є ())))))

(визначити машина-знизити-поточну-двомісну-дію-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 10)
       (за-умовою
         ((машина-поточний-д5-допустимі-входи-32? лівий-операнд правий-операнд)
          (машина-знизити-додавання-беззнакових-64-до-форм лівий-операнд правий-операнд))
         (так (як-є exact-d5-fallback-required))))
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 11)
       (за-умовою
         ((машина-поточний-д5-безпечна-різниця-64? лівий-операнд правий-операнд)
          (машина-знизити-віднімання-беззнакових-64-до-форм лівий-операнд правий-операнд))
         (так (як-є exact-d5-fallback-required))))
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 22)
       (за-умовою
         ((машина-поточний-д5-допустимі-входи-32? лівий-операнд правий-операнд)
          (машина-знизити-множення-беззнакових-64-до-форм лівий-операнд правий-операнд))
         (так (як-є exact-d5-fallback-required))))
      (так
       (як-є unsupported-current-domain-binary-u64)))))

(визначити машина-кодувати-поточну-двомісну-дію-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    ((функція (машинні-форми)
       (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-binary-u64))
         (як-є unsupported-current-domain-binary-u64))
        ((тотожне? машинні-форми (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        (так
         (машина-кодувати-допущену-програму машинні-форми))))
      (машина-знизити-поточну-двомісну-дію-64
                    ширина-домену біти-домену лівий-операнд правий-операнд))))

; #4063 exact D6 ADD1/SUB1 bounded fast paths.
; Language meaning is already admitted as LOWER_DOMAIN_COMPOSITION over exact
; D5 PLUS/DIFFERENCE with exact integer 1. This machine slice reuses the same
; admitted ADD/SUB forms and adds no arithmetic meaning of its own.
(визначити машина-поточний-д6-безпечний-наступник-64?
  (функція (значення)
    (за-умовою
      ((машина-допуск-точне-ціле? значення)
       (машина-допуск-ціле-у-включних-межах?
         значення 0 18446744073709551614))
      (так (як-є ())))))

(визначити машина-поточний-д6-безпечний-попередник-64?
  (функція (значення)
    (за-умовою
      ((машина-допуск-точне-ціле? значення)
       (машина-допуск-ціле-у-включних-межах?
         значення 1 18446744073709551615))
      (так (як-є ())))))

(визначити машина-знизити-поточну-одномісну-дію-д6
  (функція (ширина-домену біти-домену значення)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 6 14)
       (за-умовою
         ((машина-поточний-д6-безпечний-наступник-64? значення)
          (машина-знизити-додавання-беззнакових-64-до-форм значення 1))
         (так (як-є exact-d6-fallback-required))))
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 6 15)
       (за-умовою
         ((машина-поточний-д6-безпечний-попередник-64? значення)
          (машина-знизити-віднімання-беззнакових-64-до-форм значення 1))
         (так (як-є exact-d6-fallback-required))))
      (так
       (як-є unsupported-current-domain-d6-unary-u64)))))

(визначити машина-кодувати-поточну-одномісну-дію-д6
  (функція (ширина-домену біти-домену значення)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-d6-unary-u64))
         (як-є unsupported-current-domain-d6-unary-u64))
        ((тотожне? машинні-форми (як-є exact-d6-fallback-required))
         (як-є exact-d6-fallback-required))
        (так
         (машина-кодувати-допущену-програму машинні-форми)))) (машина-знизити-поточну-одномісну-дію-д6
                    ширина-домену біти-домену значення))))

; #4017 exact D5:10111 QUOTIENT bounded dispatcher.
; Only equal positive exact integers inside signed i64 enter IDIV. This is a
; proof slice, not a claim of general integer division. All non-equal,
; rational, zero, negative or out-of-range cases remain exact Lisp/Q fallback.
(визначити машина-поточний-д5-безпечна-ціла-частка?
  (функція (лівий-операнд правий-операнд)
    (за-умовою
      ((машина-допуск-точне-ціле? лівий-операнд)
       (за-умовою
         ((машина-допуск-ціле-у-включних-межах?
            лівий-операнд 1 9223372036854775807)
          (за-умовою
            ((машина-допуск-точне-ціле? правий-операнд)
             (за-умовою
               ((машина-допуск-ціле-у-включних-межах?
                  правий-операнд 1 9223372036854775807)
                (тотожне? лівий-операнд правий-операнд))
               (так (як-є ()))))
            (так (як-є ()))))
         (так (як-є ()))))
      (так (як-є ())))))

(визначити машина-знизити-поточну-цілу-частку-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 23)
       (за-умовою
         ((машина-поточний-д5-безпечна-ціла-частка? лівий-операнд правий-операнд)
          (машина-знизити-частку-знакових-64-до-форм лівий-операнд правий-операнд))
         (так (як-є exact-d5-fallback-required))))
      (так (як-є unsupported-current-domain-quotient-i64)))))

(визначити машина-кодувати-поточну-цілу-частку-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-quotient-i64))
         (як-є unsupported-current-domain-quotient-i64))
        ((тотожне? машинні-форми (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        (так
         (машина-кодувати-допущену-програму машинні-форми)))) (машина-знизити-поточну-цілу-частку-64
                    ширина-домену біти-домену лівий-операнд правий-операнд))))

; #4018 exact D5 order-predicate machine proof.
; These forms intentionally produce only an INTERNAL machine bit in RAX.
; No native-call wrapper exposes that 0/1 as a language predicate. The
; language-visible result boundary remains the existing D5 -> D1
; canonicalization in Rust.
(визначити машина-поточний-д5-безпечний-порядок-63?
  (функція (лівий-операнд правий-операнд)
    (за-умовою
      ((машина-допуск-точне-ціле? лівий-операнд)
       (за-умовою
         ((машина-допуск-ціле-у-включних-межах?
            лівий-операнд 0 9223372036854775807)
          (за-умовою
            ((машина-допуск-точне-ціле? правий-операнд)
             (машина-допуск-ціле-у-включних-межах?
               правий-операнд 0 9223372036854775807))
            (так (як-є ()))))
         (так (як-є ()))))
      (так (як-є ())))))

(визначити машина-знизити-порівняння-порядку-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    (за-умовою
      ((машина-поточний-д5-безпечний-порядок-63? лівий-операнд правий-операнд)
       (за-умовою
         ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 26)
          (список
            (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
            (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд)
            (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
            (список (як-є setl-r8) (як-є al))
            (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
            (список (як-є ret))))
         ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 27)
          (список
            (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд)
            (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд)
            (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
            (список (як-є setg-r8) (як-є al))
            (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
            (список (як-є ret))))
         (так
          (як-є unsupported-current-domain-order-i64))))
      (так
       (як-є exact-d5-fallback-required)))))

(визначити машина-кодувати-поточний-біт-порядку
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-order-i64))
         (як-є unsupported-current-domain-order-i64))
        ((тотожне? машинні-форми (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        (так
         (машина-кодувати-допущену-програму машинні-форми)))) (машина-знизити-порівняння-порядку-64 ширина-домену біти-домену лівий-операнд правий-операнд))))

; #4064/#4068 exact D5:01000 ZEROP bounded machine proof.
; Full ZEROP semantics include the historical epsilon policy for rational
; carriers. Native CMP-to-zero is therefore admitted only for exact
; nonnegative u64 integers. The emitted 0/1 remains INTERNAL machine data;
; language-visible result remains exact D1.
(визначити машина-поточний-д5-безпечна-перевірка-нуля?
  (функція (значення)
    (за-умовою
      ((машина-допуск-точне-ціле? значення)
       (машина-допуск-ціле-у-включних-межах?
         значення 0 18446744073709551615))
      (так (як-є ())))))

(визначити машина-знизити-перевірку-нуля-64
  (функція (значення)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) значення)
      (список (як-є mov-r64-imm64) (як-є rcx) 0)
      (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є sete-r8) (як-є al))
      (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
      (список (як-є ret)))))

(визначити машина-знизити-поточну-перевірку-нуля-64
  (функція (ширина-домену біти-домену значення)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 5 8)
       (за-умовою
         ((машина-поточний-д5-безпечна-перевірка-нуля? значення)
          (машина-знизити-перевірку-нуля-64 значення))
         (так (як-є exact-d5-fallback-required))))
      (так
       (як-є unsupported-current-domain-zerop-u64)))))

(визначити машина-кодувати-поточний-біт-нуля
  (функція (ширина-домену біти-домену значення)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-zerop-u64))
         (як-є unsupported-current-domain-zerop-u64))
        ((тотожне? машинні-форми (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        (так
         (машина-кодувати-допущену-програму машинні-форми)))) (машина-знизити-поточну-перевірку-нуля-64 ширина-домену біти-домену значення))))

; #3996 exact-domain structural D3 dispatcher.
; These are bounded native-call witnesses only. They do not claim a general
; allocator, escaping pair ABI, GC, or arbitrary first-class native pair value.
(визначити машина-знизити-поточну-структурну-дію-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 3 7)
       (машина-знизити-запис-пари-64 лівий-операнд правий-операнд))
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 3 4)
       (знизити-складену-пару-до-машинних-форм лівий-операнд правий-операнд))
      ((машинний-ключ-поточного-домену? ширина-домену біти-домену 3 3)
       (машина-знизити-решту-пари-64 лівий-операнд правий-операнд))
      (так
       (як-є unsupported-current-domain-structural-u64)))))

(визначити машина-кодувати-поточну-структурну-дію-64
  (функція (ширина-домену біти-домену лівий-операнд правий-операнд)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-structural-u64))
         (як-є unsupported-current-domain-structural-u64))
        (так
         (машина-кодувати-допущену-програму-або-відхилити машинні-форми)))) (машина-знизити-поточну-структурну-дію-64
                    ширина-домену біти-домену лівий-операнд правий-операнд))))

; #4000 exact-domain bounded composition for current D3 EQ + COND.
; This route intentionally does not expose an independent numeric-boolean EQ
; machine API. The equality decision stays internal to the already-witnessed
; two-arm composition; the language boundary remains exact D1/EMPTY according
; to current D3 law.
(визначити машина-знизити-поточну-рівність-та-умову-64
  (функція
    (ширина-тотожності біти-тотожності ширина-умови біти-умови лівий-операнд правий-операнд значення-якщо-так значення-якщо-ні)
    (за-умовою
      ((машинний-ключ-поточного-домену? ширина-тотожності біти-тотожності 3 5)
       (за-умовою
         ((машинний-ключ-поточного-домену? ширина-умови біти-умови 3 6)
          (машина-знизити-рівність-та-умову-64
            лівий-операнд правий-операнд значення-якщо-так значення-якщо-ні))
         (так
          (як-є unsupported-current-domain-eq-cond-u64))))
      (так
       (як-є unsupported-current-domain-eq-cond-u64)))))

(визначити машина-кодувати-поточну-рівність-та-умову-64
  (функція
    (ширина-тотожності біти-тотожності ширина-умови біти-умови лівий-операнд правий-операнд значення-якщо-так значення-якщо-ні)
    ((функція (машинні-форми) (за-умовою
        ((тотожне? машинні-форми (як-є unsupported-current-domain-eq-cond-u64))
         (як-є unsupported-current-domain-eq-cond-u64))
        (так
         (машина-кодувати-допущену-програму-або-відхилити машинні-форми)))) (машина-знизити-поточну-рівність-та-умову-64
              ширина-тотожності біти-тотожності ширина-умови біти-умови
              лівий-операнд правий-операнд значення-якщо-так значення-якщо-ні))))


; Збережене ім'я механічного виконавця — лише сумісна прив'язка.
; Семантична тотожність функцій і ратифіковані координати незмінні.
(визначити x86-current-domain-key? машинний-ключ-поточного-домену?)

; Історичні машинні назви збережено тільки як сумісні посилання.
; Основні визначення та їхні виклики написані українською.
(визначити x86-lower-add-u64-forms машина-знизити-додавання-беззнакових-64-до-форм)
(визначити x86-lower-difference-u64-forms машина-знизити-віднімання-беззнакових-64-до-форм)
(визначити x86-lower-times-u64-forms машина-знизити-множення-беззнакових-64-до-форм)
(визначити x86-lower-bounded-car-cons-u64-arm-forms машина-знизити-обмежений-вибір-першого-пари-64)
(визначити x86-machine-append-forms машина-приєднати-форми)

; Зовнішні історичні назви пов'язані з тими самими українськими функціями.
(визначити x86-lower-quotient-i64-equal-forms машина-знизити-частку-знакових-64-до-форм)
(визначити x86-lower-eq-cond-u64-forms машина-знизити-рівність-та-умову-64)
(визначити x86-lower-eq-cond-car-cons-u64-forms машина-знизити-рівність-умову-та-пару-64)
(визначити x86-lower-bounded-pair-store-u64-forms машина-знизити-запис-пари-64)
(визначити x86-lower-bounded-pair-store-u64-instructions машина-знизити-інструкції-запису-пари-64)
(визначити x86-lower-cons-cdr-u64-forms машина-знизити-решту-пари-64)
(визначити x86-call-semantic-car-u64 машина-викликати-семантичне-перше-64)
(визначити x86-current-d5-u32-inputs? машина-поточний-д5-допустимі-входи-32?)
(визначити x86-current-d5-difference-u64-safe? машина-поточний-д5-безпечна-різниця-64?)
(визначити x86-lower-current-binary-u64-forms машина-знизити-поточну-двомісну-дію-64)
(визначити x86-encode-current-binary-u64 машина-кодувати-поточну-двомісну-дію-64)
(визначити x86-current-d6-add1-u64-safe? машина-поточний-д6-безпечний-наступник-64?)
(визначити x86-current-d6-sub1-u64-safe? машина-поточний-д6-безпечний-попередник-64?)
(визначити x86-lower-current-d6-unary-u64-forms машина-знизити-поточну-одномісну-дію-д6)
(визначити x86-encode-current-d6-unary-u64 машина-кодувати-поточну-одномісну-дію-д6)
(визначити x86-current-d5-quotient-i64-equal-safe? машина-поточний-д5-безпечна-ціла-частка?)
(визначити x86-lower-current-quotient-i64-forms машина-знизити-поточну-цілу-частку-64)
(визначити x86-encode-current-quotient-i64 машина-кодувати-поточну-цілу-частку-64)
(визначити x86-current-d5-order-i63-safe? машина-поточний-д5-безпечний-порядок-63?)
(визначити x86-lower-order-i64-forms машина-знизити-порівняння-порядку-64)
(визначити x86-encode-current-order-bit машина-кодувати-поточний-біт-порядку)
(визначити x86-current-d5-zerop-u64-safe? машина-поточний-д5-безпечна-перевірка-нуля?)
(визначити x86-lower-zerop-u64-forms машина-знизити-перевірку-нуля-64)
(визначити x86-lower-current-zerop-u64-forms машина-знизити-поточну-перевірку-нуля-64)
(визначити x86-encode-current-zerop-bit машина-кодувати-поточний-біт-нуля)
(визначити x86-lower-current-structural-u64-forms машина-знизити-поточну-структурну-дію-64)
(визначити x86-encode-current-structural-u64 машина-кодувати-поточну-структурну-дію-64)
(визначити x86-lower-current-eq-cond-u64-forms машина-знизити-поточну-рівність-та-умову-64)
(визначити x86-encode-current-eq-cond-u64 машина-кодувати-поточну-рівність-та-умову-64)
