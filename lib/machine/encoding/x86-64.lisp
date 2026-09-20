(def x86-reg-code
  (lambda (register)
    (cond
      ((eq register (quote rax)) 0)
      ((eq register (quote al)) 0)
      ((eq register (quote rcx)) 1)
      ((eq register (quote cl)) 1)
      ((eq register (quote rdx)) 2)
      ((eq register (quote dl)) 2)
      ((eq register (quote rbx)) 3)
      ((eq register (quote bl)) 3)
      ((eq register (quote rsp)) 4)
      ((eq register (quote spl)) 4)
      ((eq register (quote rbp)) 5)
      ((eq register (quote bpl)) 5)
      ((eq register (quote rsi)) 6)
      ((eq register (quote sil)) 6)
      ((eq register (quote rdi)) 7)
      ((eq register (quote dil)) 7)
      ((eq register (quote r8)) 8)
      ((eq register (quote r8b)) 8)
      ((eq register (quote r9)) 9)
      ((eq register (quote r9b)) 9)
      ((eq register (quote r10)) 10)
      ((eq register (quote r10b)) 10)
      ((eq register (quote r11)) 11)
      ((eq register (quote r11b)) 11)
      ((eq register (quote r12)) 12)
      ((eq register (quote r12b)) 12)
      ((eq register (quote r13)) 13)
      ((eq register (quote r13b)) 13)
      ((eq register (quote r14)) 14)
      ((eq register (quote r14b)) 14)
      ((eq register (quote r15)) 15)
      ((eq register (quote r15b)) 15)
      (t (quote ())))))

(def x86-xmm-reg-code
  (lambda (register)
    (cond
      ((eq register (quote xmm0)) 0)
      ((eq register (quote xmm1)) 1)
      ((eq register (quote xmm2)) 2)
      ((eq register (quote xmm3)) 3)
      ((eq register (quote xmm4)) 4)
      ((eq register (quote xmm5)) 5)
      ((eq register (quote xmm6)) 6)
      ((eq register (quote xmm7)) 7)
      ((eq register (quote xmm8)) 8)
      ((eq register (quote xmm9)) 9)
      ((eq register (quote xmm10)) 10)
      ((eq register (quote xmm11)) 11)
      ((eq register (quote xmm12)) 12)
      ((eq register (quote xmm13)) 13)
      ((eq register (quote xmm14)) 14)
      ((eq register (quote xmm15)) 15)
      (t (quote ())))))

(def x86-low3
  (lambda (code)
    (mod code 8)))

(def x86-high1
  (lambda (code)
    (quotient code 8)))

(def x86-encode-rex
  (lambda (w r x b)
    (+ 64 (+ (* w 8) (+ (* r 4) (+ (* x 2) b))))))

(def x86-encode-modrm
  (lambda (mode reg rm)
    (+ (* mode 64) (+ (* reg 8) rm))))

(def x86-encode-sib
  (lambda (scale index base)
    (+ (* scale 64) (+ (* index 8) base))))

(def x86-u32-bytes
  (lambda (value)
    (list
      (mod value 256)
      (mod (quotient value 256) 256)
      (mod (quotient value 65536) 256)
      (mod (quotient value 16777216) 256))))

(def x86-u64-bytes
  (lambda (value)
    (list
      (mod value 256)
      (mod (quotient value 256) 256)
      (mod (quotient value 65536) 256)
      (mod (quotient value 16777216) 256)
      (mod (quotient value 4294967296) 256)
      (mod (quotient value 1099511627776) 256)
      (mod (quotient value 281474976710656) 256)
      (mod (quotient value 72057594037927936) 256))))

(def x86-encode-ret
  (lambda ()
    (list 195)))

(def x86-encode-mov-eax-imm32
  (lambda (immediate)
    (cons 184 (x86-u32-bytes immediate))))

(def x86-encode-mov-r64-imm64
  (lambda (register immediate)
    (let ((code (x86-reg-code register)))
      (cons
        (x86-encode-rex 1 0 0 (x86-high1 code))
        (cons
          (+ 184 (x86-low3 code))
          (x86-u64-bytes immediate))))))

; Two's-complement byte for a disp8 value already known to be in [-128,127].
; `mod` in this Lisp does not wrap negative operands (`(mod -1 256)` is -1,
; not 255), so a plain `(mod displacement 256)` silently produced an
; out-of-range byte for any negative displacement -- caught fail-closed at
; the host boundary (`native-call-u64-raw` rejects non-0..255 bytes), but it
; meant negative disp8 could never actually be encoded despite the encoder
; otherwise already supporting arbitrary GPR bases/destinations, SIB for
; rsp/r12, REX.B for an extended base (r8-r15), and REX.R for an extended
; load-destination/store-source register. Adding 256 before reducing mod
; 256 is exact for the whole disp8 domain (verified by round-trip below,
; independently cross-checked against objdump across the full 16x16 base x
; data-register matrix).
(def x86-disp8-byte
  (lambda (displacement)
    (mod (+ displacement 256) 256)))

; MOV r64, [base + disp8], opcode 8B /r.
; ModR/M mode 01 always carries one displacement byte. RSP/R12 bases use the
; required no-index SIB byte instead of silently emitting an invalid address.
(def x86-encode-mov-r64-mem-disp8
  (lambda (destination base displacement)
    (let ((dst (x86-reg-code destination)))
      (let ((base-code (x86-reg-code base)))
        (let ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (cond
              ((eq (x86-low3 base-code) 4)
                (list
                  rex
                  139
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              (t
                (list rex 139 modrm (x86-disp8-byte displacement))))))))))

; MOV [base + disp8], r64, opcode 89 /r.
(def x86-encode-mov-mem-disp8-r64
  (lambda (base displacement source)
    (let ((base-code (x86-reg-code base)))
      (let ((src (x86-reg-code source)))
        (let ((rex (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 src) (x86-low3 base-code))))
            (cond
              ((eq (x86-low3 base-code) 4)
                (list
                  rex
                  137
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              (t
                (list rex 137 modrm (x86-disp8-byte displacement))))))))))

; LEA r64, [base + disp8], opcode 0x8D /r -- per #175's pinned XED evidence
; (`PATTERN : 0x8D MOD[mm] MOD!=3 REG[rrr] RM[nnn] MODRM() REMOVE_SEGMENT()`,
; `OPERANDS : REG0=GPRv_R():w AGEN:r`). AGEN means the operand is an address
; computed from the ModRM/SIB/displacement, never an actual memory read --
; the identical addressing shape #199's mov-r64-mem-disp8 already encodes,
; only the opcode byte differs and no memory access happens. This is the
; first form the encoder admits that computes an address without touching
; any flags, needed once pointer/offset arithmetic (e.g. advancing a
; bump-pointer arena, or computing a struct field's address) must not
; disturb a CMP result still pending in a nearby branch.
(def x86-encode-lea-r64-mem-disp8
  (lambda (destination base displacement)
    (let ((dst (x86-reg-code destination)))
      (let ((base-code (x86-reg-code base)))
        (let ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (let ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (cond
              ((eq (x86-low3 base-code) 4)
                (list
                  rex
                  141
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              (t
                (list rex 141 modrm (x86-disp8-byte displacement))))))))))

; Group-1 ALU r/m64, r64 (mod=3 register/register), opcode base+1: ADD 0x01,
; OR 0x09, AND 0x21, SUB 0x29, XOR 0x31, CMP 0x39 (Intel SDM, confirmed
; against #175's pinned XED evidence: lib/machine/xed/vendor/base/xed-isa.txt
; PATTERN lines for each ICLASS's `MOD[0b11] MOD=3 REG[rrr] RM[nnn]` form).
; All six share one shape; only the opcode byte differs.
(def x86-encode-alu-r64-r64
  (lambda (opcode destination source)
    (let ((dst (x86-reg-code destination)))
      (let ((src (x86-reg-code source)))
        (list
          (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 dst))
          opcode
          (x86-encode-modrm 3 (x86-low3 src) (x86-low3 dst)))))))

(def x86-encode-add-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 1 destination source)))

(def x86-encode-or-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 9 destination source)))

(def x86-encode-and-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 33 destination source)))

(def x86-encode-sub-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 41 destination source)))

(def x86-encode-xor-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 49 destination source)))

(def x86-encode-cmp-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 57 destination source)))

; MOV r/m64, r64 (opcode 0x89 /r, mod=3 register/register): copies source
; into destination with no flags touched -- per #175's pinned XED evidence
; (`PATTERN : 0x89 MOD[0b11] MOD=3 REG[rrr] RM[nnn]`, `OPERANDS : REG0=
; GPRv_B():w REG1=GPRv_R():r`, i.e. the reg field is the source being read
; and the rm field is the destination being written, the identical
; source/destination assignment the group-1 ALU family already uses). Same
; REX.W+opcode+ModRM shape, so it reuses x86-encode-alu-r64-r64 directly.
; This is the most elementary data-movement form still missing until now:
; every other admitted form can only load an immediate or a memory operand
; into a register, never copy register-to-register.
(def x86-encode-mov-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 137 destination source)))

; Two's-complement little-endian bytes for a sign-extended imm32 value
; already known to be in [-2147483648,2147483647]. Same wrap-before-split
; discipline #199 proved for disp8 (x86-disp8-byte) -- `mod` in this Lisp
; does not wrap negative operands, so adding 2^32 before reducing mod 2^32
; is exact for the whole imm32 domain.
(def x86-imm32-bytes
  (lambda (immediate)
    (x86-u32-bytes (mod (+ immediate 4294967296) 4294967296))))

; ALU r/m64, imm32 (mod=3, sign-extended to 64 bits): opcode 0x81, ModRM reg
; field selects the operation (ADD=0, OR=1, AND=4, SUB=5, XOR=6, CMP=7,
; matching the same fixed group-1 numbering the register/register family's
; own opcodes already encode), rm field is the destination register -- per
; #175's pinned XED evidence (`PATTERN : 0x81 MOD[0b11] MOD=3 REG[rrr]
; RM[nnn] SIMMz()`). Lets a comparison/arithmetic-against-a-constant (the
; #196 COND base-case shape: compare a variable to a literal) skip loading
; the constant into a scratch register first.
(def x86-encode-alu-r64-imm32
  (lambda (opcode-extension destination immediate)
    (let ((dst (x86-reg-code destination)))
      (cons
        (x86-encode-rex 1 0 0 (x86-high1 dst))
        (cons
          129
          (cons
            (x86-encode-modrm 3 opcode-extension (x86-low3 dst))
            (x86-imm32-bytes immediate)))))))

(def x86-encode-add-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 0 destination immediate)))

(def x86-encode-or-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 1 destination immediate)))

(def x86-encode-and-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 4 destination immediate)))

(def x86-encode-sub-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 5 destination immediate)))

(def x86-encode-xor-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 6 destination immediate)))

(def x86-encode-cmp-r64-imm32
  (lambda (destination immediate)
    (x86-encode-alu-r64-imm32 7 destination immediate)))

; TEST r/m64, r64 (opcode 0x85 /r, mod=3 register/register): destination AND
; source, result discarded, flags set only -- per #175's pinned XED evidence
; (`PATTERN : 0x85 MOD[0b11] MOD=3 REG[rrr] RM[nnn]`). Same REX.W+opcode+
; ModRM shape used by the group-1 ALU family, so it reuses x86-encode-alu-r64-r64
; directly rather than duplicating the REX/ModRM arithmetic.
(def x86-encode-test-r64-r64
  (lambda (destination source)
    (x86-encode-alu-r64-r64 133 destination source)))

; PUSH r64 (opcode 0x50+rd, ICLASS PUSH: `0b0101_0 SRM[rrr] ... DF64()`) and
; POP r64 (opcode 0x58+rd, ICLASS POP: `0b0101_1 SRM[rrr] ... DF64()`), per
; #175's pinned XED evidence. Both default to 64-bit operand size in long
; mode (`DF64()`), so no REX.W is emitted; only REX.B is needed, and only
; for r8-r15.
(def x86-encode-push-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (cond
        ((eq (x86-high1 code) 1)
          (list (x86-encode-rex 0 0 0 1) (+ 80 (x86-low3 code))))
        (t
          (list (+ 80 (x86-low3 code))))))))

(def x86-encode-pop-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (cond
        ((eq (x86-high1 code) 1)
          (list (x86-encode-rex 0 0 0 1) (+ 88 (x86-low3 code))))
        (t
          (list (+ 88 (x86-low3 code))))))))

; INC r64 / DEC r64: group-5 opcode 0xFF, /reg extension (not a register
; operand) selects the operation -- INC is /0, DEC is /1 -- per #175's
; pinned XED evidence (`PATTERN : 0xFF MOD[0b11] MOD=3 REG[0b000] RM[nnn]`
; / `REG[0b001]`). Unlike PUSH/POP, this form always needs REX.W: the
; legacy single-byte 0x40+r/0x48+r INC/DEC opcodes exist in the same pinned
; evidence tagged `not64` -- those byte values became REX prefixes in
; 64-bit mode, so encoding INC/DEC in long mode always goes through this
; ModRM group-5 path, never the legacy one.
(def x86-encode-inc-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 0 (x86-low3 code))))))

(def x86-encode-dec-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 1 (x86-low3 code))))))

; NOT r64 / NEG r64: group-3 opcode 0xF7, /reg extension (not a register
; operand) selects the operation -- NOT is /2, NEG is /3 -- per #175's
; pinned XED evidence (`PATTERN : 0xF7 MOD[0b11] MOD=3 REG[0b010] RM[nnn]`
; / `REG[0b011]`). This matches INC/DEC's group-5 shape: always REX.W,
; REX.B only for r8-r15.
(def x86-encode-not-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        247
        (x86-encode-modrm 3 2 (x86-low3 code))))))

(def x86-encode-neg-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        247
        (x86-encode-modrm 3 3 (x86-low3 code))))))

; SHL/SHR/SAR r64, imm8: group-2 opcode 0xC1, /reg extension selects the
; operation -- SHL is /4, SHR is /5, SAR is /7 (/6 duplicates SHL under an
; undocumented encoding and is intentionally not admitted) -- per #175's pinned XED
; evidence (`PATTERN : 0xC1 MOD[0b11] MOD=3 REG[0b100] RM[nnn] UIMM8()`
; for SHL, `REG[0b101]` for SHR, `REG[0b111]` for SAR). Unlike disp8/
; rel8/rel32/imm32, UIMM8 is an *unsigned* byte in [0,255], so no
; two's-complement wrap-before-split is needed -- the admitted count
; becomes the raw trailing byte directly.
(def x86-encode-shift-r64-imm8
  (lambda (opcode-extension register count)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        193
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        count))))

(def x86-encode-shl-r64-imm8
  (lambda (register count)
    (x86-encode-shift-r64-imm8 4 register count)))

(def x86-encode-shr-r64-imm8
  (lambda (register count)
    (x86-encode-shift-r64-imm8 5 register count)))

(def x86-encode-sar-r64-imm8
  (lambda (register count)
    (x86-encode-shift-r64-imm8 7 register count)))

; Jcc rel8: opcode 0x70+cc followed by a signed 8-bit relative displacement
; (from the address of the *next* instruction). No REX prefix -- this is a
; control-transfer, not a GPR operation. The 16 condition codes and their
; opcode offsets are fixed by Intel's encoding and confirmed against #175's
; pinned XED evidence (`PATTERN : 0x7<cc> mode64 ... BRDISP8()` for each
; ICLASS in order: JO,JNO,JB,JNB,JZ,JNZ,JBE,JNBE,JS,JNS,JP,JNP,JL,JNL,JLE,
; JNLE). Reuses x86-disp8-byte for the same two's-complement byte
; conversion #199 already proved correct for MOV's disp8 slot.
(def x86-encode-jcc-rel8
  (lambda (condition-code displacement)
    (list
      (+ 112 condition-code)
      (x86-disp8-byte displacement))))

(def x86-encode-jo-rel8 (lambda (displacement) (x86-encode-jcc-rel8 0 displacement)))
(def x86-encode-jno-rel8 (lambda (displacement) (x86-encode-jcc-rel8 1 displacement)))
(def x86-encode-jb-rel8 (lambda (displacement) (x86-encode-jcc-rel8 2 displacement)))
(def x86-encode-jnb-rel8 (lambda (displacement) (x86-encode-jcc-rel8 3 displacement)))
(def x86-encode-jz-rel8 (lambda (displacement) (x86-encode-jcc-rel8 4 displacement)))
(def x86-encode-jnz-rel8 (lambda (displacement) (x86-encode-jcc-rel8 5 displacement)))
(def x86-encode-jbe-rel8 (lambda (displacement) (x86-encode-jcc-rel8 6 displacement)))
(def x86-encode-jnbe-rel8 (lambda (displacement) (x86-encode-jcc-rel8 7 displacement)))
(def x86-encode-js-rel8 (lambda (displacement) (x86-encode-jcc-rel8 8 displacement)))
(def x86-encode-jns-rel8 (lambda (displacement) (x86-encode-jcc-rel8 9 displacement)))
(def x86-encode-jp-rel8 (lambda (displacement) (x86-encode-jcc-rel8 10 displacement)))
(def x86-encode-jnp-rel8 (lambda (displacement) (x86-encode-jcc-rel8 11 displacement)))
(def x86-encode-jl-rel8 (lambda (displacement) (x86-encode-jcc-rel8 12 displacement)))
(def x86-encode-jnl-rel8 (lambda (displacement) (x86-encode-jcc-rel8 13 displacement)))
(def x86-encode-jle-rel8 (lambda (displacement) (x86-encode-jcc-rel8 14 displacement)))
(def x86-encode-jnle-rel8 (lambda (displacement) (x86-encode-jcc-rel8 15 displacement)))

; JMP rel8: opcode 0xEB followed by a signed 8-bit relative displacement,
; confirmed against #175's pinned XED evidence
; (`PATTERN : 0xEB mode64 norex2_prefix FORCE64() BRDISP8()`). Unlike Jcc,
; JMP is unconditional -- no condition-code byte, no ModRM, no REX -- but
; reuses the same x86-disp8-byte two's-complement conversion.
(def x86-encode-jmp-rel8
  (lambda (displacement)
    (list
      235
      (x86-disp8-byte displacement))))

; Two's-complement little-endian bytes for a rel32 value already known to be
; in [-2147483648,2147483647]. Same wrap-before-split fix #199 proved for
; disp8 (x86-disp8-byte) and this file's own x86-u64-bytes lack for
; mov-r64-imm64 (#220's truth-sentinel audit documented this being an
; existing, out-of-scope gap) -- `mod` in this Lisp does not wrap negative operands, so
; adding 2^32 before reducing mod 2^32 is exact for the whole rel32 domain.
(def x86-rel32-bytes
  (lambda (displacement)
    (x86-u32-bytes (mod (+ displacement 4294967296) 4294967296))))

; CALL rel32: opcode 0xE8 followed by a signed 32-bit relative displacement
; (from the address of the *next* instruction), confirmed against #175's
; pinned XED evidence (`PATTERN : 0xE8 mode64 norex2_prefix BRDISP32()
; DF64() FORCE64()`). No REX, no ModRM -- like JMP rel8/Jcc rel8, this is a
; control-transfer, not a GPR operation. Unlike JMP, CALL also pushes the
; return address (XED_REG_STACKPUSH) -- on real hardware this is the actual
; RSP-based machine stack, so a CALL executed through native-call-u64-raw
; pushes/pops for real; nothing in the arena model needs to know about it,
; the same "guest ABI is Lisp's, host mechanism is the CPU's" split #204
; already established for the Windows/Linux execution adapters.
(def x86-encode-call-rel32
  (lambda (displacement)
    (cons 232 (x86-rel32-bytes displacement))))

; Jcc rel32: opcode 0x0F, then 0x80+cc, then a signed 32-bit relative
; displacement -- the conditional counterpart to JMP rel32, needed for the
; same reason: #196's own growth-v0 witnesses lean on CMP+Jcc far more than
; unconditional JMP (an arena-bounds check is inherently a Jcc), and their
; hand-derived disp8 offsets (e.g. "JNZ +11", "JNZ +33") will not survive
; much further composition. Confirmed against #175's pinned XED evidence
; (`PATTERN : 0x0F 0x8<cc> mode64 norex2_prefix FORCE64() BRANCH_HINT()
; BRDISP32()` for each ICLASS in the identical order the rel8 family
; already uses: JO,JNO,JB,JNB,JZ,JNZ,JBE,JNBE,JS,JNS,JP,JNP,JL,JNL,JLE,
; JNLE) -- reuses that same condition-code-to-opcode-offset mapping, just
; with a 2-byte opcode and a 4-byte displacement instead of 1+1.
(def x86-encode-jcc-rel32
  (lambda (condition-code displacement)
    (cons
      15
      (cons
        (+ 128 condition-code)
        (x86-rel32-bytes displacement)))))

(def x86-encode-jo-rel32 (lambda (displacement) (x86-encode-jcc-rel32 0 displacement)))
(def x86-encode-jno-rel32 (lambda (displacement) (x86-encode-jcc-rel32 1 displacement)))
(def x86-encode-jb-rel32 (lambda (displacement) (x86-encode-jcc-rel32 2 displacement)))
(def x86-encode-jnb-rel32 (lambda (displacement) (x86-encode-jcc-rel32 3 displacement)))
(def x86-encode-jz-rel32 (lambda (displacement) (x86-encode-jcc-rel32 4 displacement)))
(def x86-encode-jnz-rel32 (lambda (displacement) (x86-encode-jcc-rel32 5 displacement)))
(def x86-encode-jbe-rel32 (lambda (displacement) (x86-encode-jcc-rel32 6 displacement)))
(def x86-encode-jnbe-rel32 (lambda (displacement) (x86-encode-jcc-rel32 7 displacement)))
(def x86-encode-js-rel32 (lambda (displacement) (x86-encode-jcc-rel32 8 displacement)))
(def x86-encode-jns-rel32 (lambda (displacement) (x86-encode-jcc-rel32 9 displacement)))
(def x86-encode-jp-rel32 (lambda (displacement) (x86-encode-jcc-rel32 10 displacement)))
(def x86-encode-jnp-rel32 (lambda (displacement) (x86-encode-jcc-rel32 11 displacement)))
(def x86-encode-jl-rel32 (lambda (displacement) (x86-encode-jcc-rel32 12 displacement)))
(def x86-encode-jnl-rel32 (lambda (displacement) (x86-encode-jcc-rel32 13 displacement)))
(def x86-encode-jle-rel32 (lambda (displacement) (x86-encode-jcc-rel32 14 displacement)))
(def x86-encode-jnle-rel32 (lambda (displacement) (x86-encode-jcc-rel32 15 displacement)))

; JMP rel32: opcode 0xE9 followed by a signed 32-bit relative displacement,
; confirmed against #175's pinned XED evidence (`PATTERN : 0xE9 mode64
; norex2_prefix FORCE64() BRDISP32()`). Matches JMP rel8's own
; unconditional, no-ModRM, no-REX shape -- only the opcode byte and
; displacement width differ.
(def x86-encode-jmp-rel32
  (lambda (displacement)
    (cons 233 (x86-rel32-bytes displacement))))

; CALL r64 / JMP r64 (indirect through a register): group-5 opcode 0xFF,
; /reg extension selects the operation -- CALL is /2, JMP is /4 -- per
; #175's pinned XED evidence (`PATTERN : 0xFF MOD[0b11] MOD=3 REG[0b010]
; RM[nnn] DF64() ...` for CALL, `REG[0b100]` for JMP). Both are `DF64()`
; (default 64-bit operand size in long mode), matching PUSH/POP's own
; default-64-bit shape, so no REX.W is emitted -- only REX.B, and only for
; r8-r15. Unlike CALL rel32,
; the target here is whatever absolute address the admitted register holds
; at runtime, not a displacement fixed at encode time; CALL still pushes a
; real return address via XED_REG_STACKPUSH, onto the same real machine
; stack #204 already established. This is the first indirect (register-
; target) control transfer the encoder admits: the destination is
; genuinely a runtime value, not something knowable from the bytes alone.
(def x86-encode-group5-indirect-r64
  (lambda (opcode-extension register)
    (let ((code (x86-reg-code register)))
      (cond
        ((eq (x86-high1 code) 1)
          (list
            (x86-encode-rex 0 0 0 1)
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))
        (t
          (list
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))))))

(def x86-encode-call-r64
  (lambda (register)
    (x86-encode-group5-indirect-r64 2 register)))

(def x86-encode-jmp-r64
  (lambda (register)
    (x86-encode-group5-indirect-r64 4 register)))

; SETcc r8: opcode 0x0F 0x90+cc, ModRM mod=3, reg=0, rm=low3(code).
; In 64-bit mode:
; - codes 0..3 (al, cl, dl, bl) require no REX prefix.
; - codes 4..7 (spl, bpl, sil, dil) require REX prefix (0x40) to distinguish
;   them from legacy high bytes (ah, ch, dh, bh).
; - codes 8..15 (r8b..r15b) require REX.B=1 prefix (0x41).
(def x86-encode-setcc-r8
  (lambda (condition-code register)
    (let ((code (x86-reg-code register)))
      ; two-part `((> code 3) REX ...)` mis-branched once exact-Q made
      ; false comparisons answer 0 (which is truthy): REX was emitted for
      ; every register. E1 (#216): explicit expected-result domains.
      (cond
        ((> code 3) 1
         (list
           (x86-encode-rex 0 0 0 (x86-high1 code))
           15
           (+ 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))
        ((> code 3) 0
         (list
           15
           (+ 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))))))

(def x86-encode-seto-r8 (lambda (register) (x86-encode-setcc-r8 0 register)))
(def x86-encode-setno-r8 (lambda (register) (x86-encode-setcc-r8 1 register)))
(def x86-encode-setb-r8 (lambda (register) (x86-encode-setcc-r8 2 register)))
(def x86-encode-setc-r8 (lambda (register) (x86-encode-setcc-r8 2 register)))
(def x86-encode-setnb-r8 (lambda (register) (x86-encode-setcc-r8 3 register)))
(def x86-encode-setnc-r8 (lambda (register) (x86-encode-setcc-r8 3 register)))
(def x86-encode-setae-r8 (lambda (register) (x86-encode-setcc-r8 3 register)))
(def x86-encode-setz-r8 (lambda (register) (x86-encode-setcc-r8 4 register)))
(def x86-encode-sete-r8 (lambda (register) (x86-encode-setcc-r8 4 register)))
(def x86-encode-setnz-r8 (lambda (register) (x86-encode-setcc-r8 5 register)))
(def x86-encode-setne-r8 (lambda (register) (x86-encode-setcc-r8 5 register)))
(def x86-encode-setbe-r8 (lambda (register) (x86-encode-setcc-r8 6 register)))
(def x86-encode-setna-r8 (lambda (register) (x86-encode-setcc-r8 6 register)))
(def x86-encode-setnbe-r8 (lambda (register) (x86-encode-setcc-r8 7 register)))
(def x86-encode-seta-r8 (lambda (register) (x86-encode-setcc-r8 7 register)))
(def x86-encode-sets-r8 (lambda (register) (x86-encode-setcc-r8 8 register)))
(def x86-encode-setns-r8 (lambda (register) (x86-encode-setcc-r8 9 register)))
(def x86-encode-setp-r8 (lambda (register) (x86-encode-setcc-r8 10 register)))
(def x86-encode-setpe-r8 (lambda (register) (x86-encode-setcc-r8 10 register)))
(def x86-encode-setnp-r8 (lambda (register) (x86-encode-setcc-r8 11 register)))
(def x86-encode-setpo-r8 (lambda (register) (x86-encode-setcc-r8 11 register)))
(def x86-encode-setl-r8 (lambda (register) (x86-encode-setcc-r8 12 register)))
(def x86-encode-setnge-r8 (lambda (register) (x86-encode-setcc-r8 12 register)))
(def x86-encode-setnl-r8 (lambda (register) (x86-encode-setcc-r8 13 register)))
(def x86-encode-setge-r8 (lambda (register) (x86-encode-setcc-r8 13 register)))
(def x86-encode-setle-r8 (lambda (register) (x86-encode-setcc-r8 14 register)))
(def x86-encode-setng-r8 (lambda (register) (x86-encode-setcc-r8 14 register)))
(def x86-encode-setnle-r8 (lambda (register) (x86-encode-setcc-r8 15 register)))
(def x86-encode-setg-r8 (lambda (register) (x86-encode-setcc-r8 15 register)))

; MOVZX r64, r8: opcode 0x0F 0xB6, ModRM mod=3, reg=dest, rm=src.
; REX.W=1 extends the 8-bit source into the full 64-bit destination register.
(def x86-encode-movzx-r64-r8
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        182
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; IMUL r64, r64: two-operand signed multiply, opcode 0x0F 0xAF.
; Destination receives the low 64 bits of the signed product.
(def x86-encode-imul-r64-r64
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        175
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; CQO: Convert Quadword to Octword (sign-extend RAX into RDX:RAX).
; Opcode 0x48 0x99. Prepares dividend for 64-bit IDIV.
(def x86-encode-cqo
  (lambda ()
    (list 72 153)))

; IDIV r64: signed division of RDX:RAX by r64 operand.
; Group 3 opcode 0xF7 /7, ModRM mod=3, reg=7, rm=src.
; Quotient is stored in RAX, remainder in RDX.
(def x86-encode-idiv-r64
  (lambda (source)
    (let ((src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 src-code))
        247
        (x86-encode-modrm 3 7 (x86-low3 src-code))))))

; CMOVcc r64, r64: conditional move, opcode 0x0F 0x40+cc.
; Moves source to destination if condition code is satisfied.
(def x86-encode-cmovcc-r64-r64
  (lambda (condition-code destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        (+ 64 condition-code)
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

(def x86-encode-cmovo-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 0 dest src)))
(def x86-encode-cmovno-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 1 dest src)))
(def x86-encode-cmovb-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(def x86-encode-cmovc-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(def x86-encode-cmovnb-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(def x86-encode-cmovnc-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(def x86-encode-cmovae-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(def x86-encode-cmovz-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(def x86-encode-cmove-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(def x86-encode-cmovnz-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(def x86-encode-cmovne-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(def x86-encode-cmovbe-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(def x86-encode-cmovna-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(def x86-encode-cmovnbe-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(def x86-encode-cmova-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(def x86-encode-cmovs-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 8 dest src)))
(def x86-encode-cmovns-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 9 dest src)))
(def x86-encode-cmovp-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 10 dest src)))
(def x86-encode-cmovpe-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 10 dest src)))
(def x86-encode-cmovnp-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 11 dest src)))
(def x86-encode-cmovpo-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 11 dest src)))
(def x86-encode-cmovl-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(def x86-encode-cmovnge-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(def x86-encode-cmovnl-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(def x86-encode-cmovge-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(def x86-encode-cmovle-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(def x86-encode-cmovng-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(def x86-encode-cmovnle-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))
(def x86-encode-cmovg-r64-r64 (lambda (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))

; NOP: opcode 0x90.
(def x86-encode-nop
  (lambda ()
    (list 144)))

; TEST r/m64, imm32: Group 3 opcode 0xF7 /0 id, ModRM mod=3, reg=0, rm=dest.
(def x86-encode-test-r64-imm32
  (lambda (destination immediate)
    (let ((code (x86-reg-code destination)))
      (append
        (list
          (x86-encode-rex 1 0 0 (x86-high1 code))
          247
          (x86-encode-modrm 3 0 (x86-low3 code)))
        (x86-imm32-bytes immediate)))))

; BT r/m64, r64: opcode 0x0F 0xA3 /r. ModRM reg=index, rm=base.
; Sets Carry Flag (CF) to the value of the bit at the given index.
(def x86-encode-bt-r64-r64
  (lambda (base index)
    (let ((base-code (x86-reg-code base))
          (index-code (x86-reg-code index)))
      (list
        (x86-encode-rex 1 (x86-high1 index-code) 0 (x86-high1 base-code))
        15
        163
        (x86-encode-modrm 3 (x86-low3 index-code) (x86-low3 base-code))))))

; Group 8 bit operations with imm8: opcode 0x0F 0xBA /reg ib.
(def x86-encode-group8-r64-imm8
  (lambda (opcode-extension register bit-index)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        186
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        bit-index))))

(def x86-encode-bt-r64-imm8
  (lambda (register bit-index)
    (x86-encode-group8-r64-imm8 4 register bit-index)))

(def x86-encode-bts-r64-imm8
  (lambda (register bit-index)
    (x86-encode-group8-r64-imm8 5 register bit-index)))

(def x86-encode-btr-r64-imm8
  (lambda (register bit-index)
    (x86-encode-group8-r64-imm8 6 register bit-index)))

(def x86-encode-btc-r64-imm8
  (lambda (register bit-index)
    (x86-encode-group8-r64-imm8 7 register bit-index)))

; MOVSX r64, r/m8: opcode 0x0F 0xBE /r. Sign-extend 8-bit to 64-bit.
(def x86-encode-movsx-r64-r8
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        190
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; MOVSXD r64, r/m32: opcode 0x63 /r. Sign-extend 32-bit to 64-bit.
(def x86-encode-movsxd-r64-r32
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        99
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; POPCNT r64, r/m64: opcode 0xF3 0x0F 0xB8 /r. Count set bits (population count).
(def x86-encode-popcnt-r64-r64
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        184
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; TZCNT r64, r/m64: opcode 0xF3 0x0F 0xBC /r. Count trailing zeros.
(def x86-encode-tzcnt-r64-r64
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSF r64, r/m64: opcode 0x0F 0xBC /r. Bit Scan Forward (first set bit).
(def x86-encode-bsf-r64-r64
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSR r64, r/m64: opcode 0x0F 0xBD /r. Bit Scan Reverse (last set bit).
(def x86-encode-bsr-r64-r64
  (lambda (destination source)
    (let ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (list
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        189
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSWAP r64: opcode 0x0F (0xC8 + rd). Byte Swap (reverse byte order).
(def x86-encode-bswap-r64
  (lambda (register)
    (let ((code (x86-reg-code register)))
      (list
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        (+ 200 (x86-low3 code))))))

; ROL / ROR r64, imm8: group-2 opcode 0xC1, /0 for ROL, /1 for ROR.
(def x86-encode-rol-r64-imm8
  (lambda (register count)
    (x86-encode-shift-r64-imm8 0 register count)))

(def x86-encode-ror-r64-imm8
  (lambda (register count)
    (x86-encode-shift-r64-imm8 1 register count)))

; XCHG r64, r64: opcode 0x87 /r. Exchange register values.
(def x86-encode-xchg-r64-r64
  (lambda (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (list
        (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
        135
        (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CLD: opcode 0xFC (252). Clear direction flag (DF=0).
(def x86-encode-cld
  (lambda ()
    (list 252)))

; STD: opcode 0xFD (253). Set direction flag (DF=1).
(def x86-encode-std
  (lambda ()
    (list 253)))

; STOSQ: opcode 0x48 0xAB (72 171). Store RAX to [RDI], increment RDI by 8.
(def x86-encode-stosq
  (lambda ()
    (list (x86-encode-rex 1 0 0 0) 171)))

; REP STOSQ: opcode 0xF3 0x48 0xAB. Fill RCX qwords at [RDI] with RAX.
(def x86-encode-rep-stosq
  (lambda ()
    (list 243 (x86-encode-rex 1 0 0 0) 171)))

; STOSB: opcode 0xAA (170). Store AL to [RDI], increment RDI by 1.
(def x86-encode-stosb
  (lambda ()
    (list 170)))

; REP STOSB: opcode 0xF3 0xAA. Fill RCX bytes at [RDI] with AL.
(def x86-encode-rep-stosb
  (lambda ()
    (list 243 170)))

; MOVSQ: opcode 0x48 0xA5 (72 165). Move qword from [RSI] to [RDI].
(def x86-encode-movsq
  (lambda ()
    (list (x86-encode-rex 1 0 0 0) 165)))

; REP MOVSQ: opcode 0xF3 0x48 0xA5. Copy RCX qwords from [RSI] to [RDI].
(def x86-encode-rep-movsq
  (lambda ()
    (list 243 (x86-encode-rex 1 0 0 0) 165)))

; MOVSB: opcode 0xA4 (164). Move byte from [RSI] to [RDI].
(def x86-encode-movsb
  (lambda ()
    (list 164)))

; REP MOVSB: opcode 0xF3 0xA4. Copy RCX bytes from [RSI] to [RDI].
(def x86-encode-rep-movsb
  (lambda ()
    (list 243 164)))

(def x86-encode-sse2-f2-xmm-xmm
  (lambda (opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (cond
        ((and (eq (x86-high1 dst-code) 0) (eq (x86-high1 src-code) 0))
         (list 242 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        (t
         (list 242 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

(def x86-encode-sse2-66-xmm-xmm
  (lambda (opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (cond
        ((and (eq (x86-high1 dst-code) 0) (eq (x86-high1 src-code) 0))
         (list 102 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        (t
         (list 102 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AES-NI register-source форми з pinned #175 XED evidence мають спільну
; будову: mandatory 0x66, optional REX.R/REX.B для XMM8-XMM15, далі
; 0F 38 або 0F 3A, opcode і ModR/M з mode=3. Цей helper описує лише
; машинне кодування; значення AES-операцій тут не визначається.
(def x86-encode-sse-66-map-xmm-xmm
  (lambda (map-byte opcode-byte dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (cond
        ((and (eq (x86-high1 dst-code) 0) (eq (x86-high1 src-code) 0))
         (list
           102
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        (t
         (list
           102
           (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AESENC xmm, xmm: 66 0F 38 DC /r.
(def x86-encode-aesenc-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 220 dst src)))

; AESENCLAST xmm, xmm: 66 0F 38 DD /r.
(def x86-encode-aesenclast-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 221 dst src)))

; AESDEC xmm, xmm: 66 0F 38 DE /r.
(def x86-encode-aesdec-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 222 dst src)))

; AESDECLAST xmm, xmm: 66 0F 38 DF /r.
(def x86-encode-aesdeclast-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 223 dst src)))

; AESIMC xmm, xmm: 66 0F 38 DB /r.
(def x86-encode-aesimc-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 219 dst src)))

; AESKEYGENASSIST xmm, xmm, imm8: 66 0F 3A DF /r ib.
; Межа imm8 перевіряється admission-шаром до матеріалізації байтів.
(def x86-encode-aeskeygenassist-xmm-xmm-imm8
  (lambda (dst src immediate)
    (append
      (x86-encode-sse-66-map-xmm-xmm 58 223 dst src)
      (list immediate))))

; AES-NI memory-source bounded base+disp8 використовує ту саму x86
; адресацію, що вже доведена для MOV/LEA: ModR/M mode=01, SIB для rsp/r12,
; REX.R для xmm8-xmm15 і REX.B для r8-r15. Ширину пам'яті визначає сама
; інструкція AES, тому цей helper не створює окремої семантики пам'яті.
(def x86-encode-sse-66-map-xmm-mem-disp8
  (lambda (map-byte opcode-byte dst base displacement)
    (let ((dst-code (x86-xmm-reg-code dst))
          (base-code (x86-reg-code base)))
      (let ((modrm
              (x86-encode-modrm
                1
                (x86-low3 dst-code)
                (x86-low3 base-code)))
            (disp-byte (x86-disp8-byte displacement)))
        (let ((address-tail
                (cond
                  ((eq (x86-low3 base-code) 4)
                   (list modrm (x86-encode-sib 0 4 4) disp-byte))
                  (t
                   (list modrm disp-byte)))))
          (cond
            ((and
               (eq (x86-high1 dst-code) 0)
               (eq (x86-high1 base-code) 0))
             (append
               (list 102 15 map-byte opcode-byte)
               address-tail))
            (t
             (append
               (list
                 102
                 (x86-encode-rex
                   0
                   (x86-high1 dst-code)
                   0
                   (x86-high1 base-code))
                 15
                 map-byte
                 opcode-byte)
               address-tail))))))))

(def x86-encode-aesenc-xmm-mem-disp8
  (lambda (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 220 dst base displacement)))

(def x86-encode-aesenclast-xmm-mem-disp8
  (lambda (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 221 dst base displacement)))

(def x86-encode-aesdec-xmm-mem-disp8
  (lambda (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 222 dst base displacement)))

(def x86-encode-aesdeclast-xmm-mem-disp8
  (lambda (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 223 dst base displacement)))

(def x86-encode-aesimc-xmm-mem-disp8
  (lambda (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 219 dst base displacement)))

(def x86-encode-aeskeygenassist-xmm-mem-disp8-imm8
  (lambda (dst base displacement immediate)
    (append
      (x86-encode-sse-66-map-xmm-mem-disp8
        58 223 dst base displacement)
      (list immediate))))

; MOVSD xmm, xmm: opcode 0xF2 0x0F 0x10 /r
(def x86-encode-movsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 16 dst src)))

; SQRTSD xmm, xmm: opcode 0xF2 0x0F 0x51 /r
(def x86-encode-sqrtsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 81 dst src)))

; ADDSD xmm, xmm: opcode 0xF2 0x0F 0x58 /r
(def x86-encode-addsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 88 dst src)))

; MULSD xmm, xmm: opcode 0xF2 0x0F 0x59 /r
(def x86-encode-mulsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 89 dst src)))

; SUBSD xmm, xmm: opcode 0xF2 0x0F 0x5C /r
(def x86-encode-subsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 92 dst src)))

; MINSD xmm, xmm: opcode 0xF2 0x0F 0x5D /r
(def x86-encode-minsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 93 dst src)))

; DIVSD xmm, xmm: opcode 0xF2 0x0F 0x5E /r
(def x86-encode-divsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 94 dst src)))

; MAXSD xmm, xmm: opcode 0xF2 0x0F 0x5F /r
(def x86-encode-maxsd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-f2-xmm-xmm 95 dst src)))

; UCOMISD xmm, xmm: opcode 0x66 0x0F 0x2E /r
(def x86-encode-ucomisd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-66-xmm-xmm 46 dst src)))

; XORPD xmm, xmm: opcode 0x66 0x0F 0x57 /r
(def x86-encode-xorpd-xmm-xmm
  (lambda (dst src)
    (x86-encode-sse2-66-xmm-xmm 87 dst src)))

; CVTSI2SD xmm, r64: opcode 0xF2 REX.W 0x0F 0x2A /r
(def x86-encode-cvtsi2sd-xmm-r64
  (lambda (dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (list 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 42 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CVTTSD2SI r64, xmm: opcode 0xF2 REX.W 0x0F 0x2C /r
(def x86-encode-cvttsd2si-r64-xmm
  (lambda (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (list 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 44 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ xmm, r64: opcode 0x66 REX.W 0x0F 0x6E /r
(def x86-encode-movq-xmm-r64
  (lambda (dst src)
    (let ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (list 102 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 110 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ r64, xmm: opcode 0x66 REX.W 0x0F 0x7E /r
(def x86-encode-movq-r64-xmm
  (lambda (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (list 102 (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 126 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

; RDTSC: opcode 0x0F 0x31
(def x86-encode-rdtsc
  (lambda ()
    (list 15 49)))

; CMPXCHG r64, r64: opcode REX.W 0x0F 0xB1 /r
(def x86-encode-cmpxchg-r64-r64
  (lambda (dst src)
    (let ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (list (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 177 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

(def x86-encode-program
  (lambda (instructions)
    (cond
      ((atom instructions) (quote ()))
      (t
        (append
          (car instructions)
          (x86-encode-program (cdr instructions)))))))
