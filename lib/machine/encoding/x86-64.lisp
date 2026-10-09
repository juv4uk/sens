(00001001 x86-reg-code
  (00001000 (register)
    (00000111
      ((00000011 register (00000001 rax)) 0)
      ((00000011 register (00000001 al)) 0)
      ((00000011 register (00000001 rcx)) 1)
      ((00000011 register (00000001 cl)) 1)
      ((00000011 register (00000001 rdx)) 2)
      ((00000011 register (00000001 dl)) 2)
      ((00000011 register (00000001 rbx)) 3)
      ((00000011 register (00000001 bl)) 3)
      ((00000011 register (00000001 rsp)) 4)
      ((00000011 register (00000001 spl)) 4)
      ((00000011 register (00000001 rbp)) 5)
      ((00000011 register (00000001 bpl)) 5)
      ((00000011 register (00000001 rsi)) 6)
      ((00000011 register (00000001 sil)) 6)
      ((00000011 register (00000001 rdi)) 7)
      ((00000011 register (00000001 dil)) 7)
      ((00000011 register (00000001 r8)) 8)
      ((00000011 register (00000001 r8b)) 8)
      ((00000011 register (00000001 r9)) 9)
      ((00000011 register (00000001 r9b)) 9)
      ((00000011 register (00000001 r10)) #d10)
      ((00000011 register (00000001 r10b)) #d10)
      ((00000011 register (00000001 r11)) #d11)
      ((00000011 register (00000001 r11b)) #d11)
      ((00000011 register (00000001 r12)) 12)
      ((00000011 register (00000001 r12b)) 12)
      ((00000011 register (00000001 r13)) 13)
      ((00000011 register (00000001 r13b)) 13)
      ((00000011 register (00000001 r14)) 14)
      ((00000011 register (00000001 r14b)) 14)
      ((00000011 register (00000001 r15)) 15)
      ((00000011 register (00000001 r15b)) 15)
      ((00000010 (00000001 ())) (00000001 ())))))

(00001001 x86-xmm-reg-code
  (00001000 (register)
    (00000111
      ((00000011 register (00000001 xmm0)) 0)
      ((00000011 register (00000001 xmm1)) 1)
      ((00000011 register (00000001 xmm2)) 2)
      ((00000011 register (00000001 xmm3)) 3)
      ((00000011 register (00000001 xmm4)) 4)
      ((00000011 register (00000001 xmm5)) 5)
      ((00000011 register (00000001 xmm6)) 6)
      ((00000011 register (00000001 xmm7)) 7)
      ((00000011 register (00000001 xmm8)) 8)
      ((00000011 register (00000001 xmm9)) 9)
      ((00000011 register (00000001 xmm10)) #d10)
      ((00000011 register (00000001 xmm11)) #d11)
      ((00000011 register (00000001 xmm12)) 12)
      ((00000011 register (00000001 xmm13)) 13)
      ((00000011 register (00000001 xmm14)) 14)
      ((00000011 register (00000001 xmm15)) 15)
      ((00000010 (00000001 ())) (00000001 ())))))

(00001001 x86-low3
  (00001000 (code)
    (00010011 code 8)))

(00001001 x86-high1
  (00001000 (code)
    (00010100 code 8)))

(00001001 x86-encode-rex
  (00001000 (w r x b)
    (00001100 64 (00001100 (00001110 w 8) (00001100 (00001110 r 4) (00001100 (00001110 x 2) b))))))

(00001001 x86-encode-modrm
  (00001000 (mode reg rm)
    (00001100 (00001110 mode 64) (00001100 (00001110 reg 8) rm))))

; #4104 — explicit representation boundary for an exact 3-bit machine field.
; Canonical BinaryNumber remains the source identity (#b...).  The shared
; legacy byte packer below still consumes mechanical Number fields, so project
; only the closed u3 domain 0..7 here.  This is intentionally not a general
; BinaryNumber -> legacy Number coercion.
(00001001 x86-project-bin3-to-mechanism-u3
  (00001000 (value)
    (00000111
      ((00011010 value #b1)    #d0)
      ((00011010 value #b10)   #d1)
      ((00011010 value #b11)   #d2)
      ((00011010 value #b100)  #d3)
      ((00011010 value #b101)  #d4)
      ((00011010 value #b110)  #d5)
      ((00011010 value #b111)  #d6)
      ((00011010 value #b1000) #d7)
      (1 (00000001 ())))))


(00001001 x86-encode-sib
  (00001000 (scale index base)
    (00001100 (00001110 scale 64) (00001100 (00001110 index 8) base))))

(00001001 x86-u32-bytes
  (00001000 (value)
    (00100111
      (00010011 value 256)
      (00010011 (00010100 value 256) 256)
      (00010011 (00010100 value 65536) 256)
      (00010011 (00010100 value 16777216) 256))))

(00001001 x86-u64-bytes
  (00001000 (value)
    (00100111
      (00010011 value 256)
      (00010011 (00010100 value 256) 256)
      (00010011 (00010100 value 65536) 256)
      (00010011 (00010100 value 16777216) 256)
      (00010011 (00010100 value 4294967296) 256)
      (00010011 (00010100 value 1099511627776) 256)
      (00010011 (00010100 value 281474976710656) 256)
      (00010011 (00010100 value 72057594037927936) 256))))

(00001001 x86-encode-ret
  (00001000 ()
    (00100111 195)))

(00001001 x86-encode-mov-eax-imm32
  (00001000 (immediate)
    (00000100 184 (x86-u32-bytes immediate))))

(00001001 x86-encode-mov-r64-imm64
  (00001000 (register immediate)
    (10011100 ((code (x86-reg-code register)))
      (00000100
        (x86-encode-rex 1 0 0 (x86-high1 code))
        (00000100
          (00001100 184 (x86-low3 code))
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
(00001001 x86-disp8-byte
  (00001000 (displacement)
    (00010011 (00001100 displacement 256) 256)))

; MOV r64, [base + disp8], opcode 8B /r.
; ModR/M mode 01 always carries one displacement byte. RSP/R12 bases use the
; required no-index SIB byte instead of silently emitting an invalid address.
(00001001 x86-encode-mov-r64-mem-disp8
  (00001000 (destination base displacement)
    (10011100 ((dst (x86-reg-code destination)))
      (10011100 ((base-code (x86-reg-code base)))
        (10011100 ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (10011100 ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (00000111
              ((00000011 (x86-low3 base-code) 4)
                (00100111
                  rex
                  139
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((00000010 (00000001 ()))
                (00100111 rex 139 modrm (x86-disp8-byte displacement))))))))))

; MOV [base + disp8], r64, opcode 89 /r.
(00001001 x86-encode-mov-mem-disp8-r64
  (00001000 (base displacement source)
    (10011100 ((base-code (x86-reg-code base)))
      (10011100 ((src (x86-reg-code source)))
        (10011100 ((rex (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 base-code))))
          (10011100 ((modrm (x86-encode-modrm 1 (x86-low3 src) (x86-low3 base-code))))
            (00000111
              ((00000011 (x86-low3 base-code) 4)
                (00100111
                  rex
                  137
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((00000010 (00000001 ()))
                (00100111 rex 137 modrm (x86-disp8-byte displacement))))))))))

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
(00001001 x86-encode-lea-r64-mem-disp8
  (00001000 (destination base displacement)
    (10011100 ((dst (x86-reg-code destination)))
      (10011100 ((base-code (x86-reg-code base)))
        (10011100 ((rex (x86-encode-rex 1 (x86-high1 dst) 0 (x86-high1 base-code))))
          (10011100 ((modrm (x86-encode-modrm 1 (x86-low3 dst) (x86-low3 base-code))))
            (00000111
              ((00000011 (x86-low3 base-code) 4)
                (00100111
                  rex
                  141
                  modrm
                  (x86-encode-sib 0 4 4)
                  (x86-disp8-byte displacement)))
              ((00000010 (00000001 ()))
                (00100111 rex 141 modrm (x86-disp8-byte displacement))))))))))

; Group-1 ALU r/m64, r64 (mod=3 register/register), opcode base+1: ADD 0x01,
; OR 0x09, AND 0x21, SUB 0x29, XOR 0x31, CMP 0x39 (Intel SDM, confirmed
; against #175's pinned XED evidence: lib/machine/xed/vendor/base/xed-isa.txt
; PATTERN lines for each ICLASS's `MOD[0b11] MOD=3 REG[rrr] RM[nnn]` form).
; All six share one shape; only the opcode byte differs.
(00001001 x86-encode-alu-r64-r64
  (00001000 (opcode destination source)
    (10011100 ((dst (x86-reg-code destination)))
      (10011100 ((src (x86-reg-code source)))
        (00100111
          (x86-encode-rex 1 (x86-high1 src) 0 (x86-high1 dst))
          opcode
          (x86-encode-modrm 3 (x86-low3 src) (x86-low3 dst)))))))

(00001001 x86-encode-add-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 1 destination source)))

(00001001 x86-encode-or-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 9 destination source)))

(00001001 x86-encode-and-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 33 destination source)))

(00001001 x86-encode-sub-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 41 destination source)))

(00001001 x86-encode-xor-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 49 destination source)))

(00001001 x86-encode-cmp-r64-r64
  (00001000 (destination source)
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
(00001001 x86-encode-mov-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 137 destination source)))

; Two's-complement little-endian bytes for a sign-extended imm32 value
; already known to be in [-2147483648,2147483647]. Same wrap-before-split
; discipline #199 proved for disp8 (x86-disp8-byte) -- `mod` in this Lisp
; does not wrap negative operands, so adding 2^32 before reducing mod 2^32
; is exact for the whole imm32 domain.
(00001001 x86-imm32-bytes
  (00001000 (immediate)
    (x86-u32-bytes (00010011 (00001100 immediate 4294967296) 4294967296))))

; ALU r/m64, imm32 (mod=3, sign-extended to 64 bits): opcode 0x81, ModRM reg
; field selects the operation (ADD=0, OR=1, AND=4, SUB=5, XOR=6, CMP=7,
; matching the same fixed group-1 numbering the register/register family's
; own opcodes already encode), rm field is the destination register -- per
; #175's pinned XED evidence (`PATTERN : 0x81 MOD[0b11] MOD=3 REG[rrr]
; RM[nnn] SIMMz()`). Lets a comparison/arithmetic-against-a-constant (the
; #196 COND base-case shape: compare a variable to a literal) skip loading
; the constant into a scratch register first.
(00001001 x86-encode-alu-r64-imm32
  (00001000 (opcode-extension destination immediate)
    (10011100 ((dst (x86-reg-code destination)))
      (00000100
        (x86-encode-rex 1 0 0 (x86-high1 dst))
        (00000100
          129
          (00000100
            (x86-encode-modrm 3 opcode-extension (x86-low3 dst))
            (x86-imm32-bytes immediate)))))))

(00001001 x86-encode-add-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 0 destination immediate)))

(00001001 x86-encode-or-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 1 destination immediate)))

(00001001 x86-encode-and-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 4 destination immediate)))

(00001001 x86-encode-sub-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 5 destination immediate)))

(00001001 x86-encode-xor-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 6 destination immediate)))

(00001001 x86-encode-cmp-r64-imm32
  (00001000 (destination immediate)
    (x86-encode-alu-r64-imm32 7 destination immediate)))

; TEST r/m64, r64 (opcode 0x85 /r, mod=3 register/register): destination AND
; source, result discarded, flags set only -- per #175's pinned XED evidence
; (`PATTERN : 0x85 MOD[0b11] MOD=3 REG[rrr] RM[nnn]`). Same REX.W+opcode+
; ModRM shape used by the group-1 ALU family, so it reuses x86-encode-alu-r64-r64
; directly rather than duplicating the REX/ModRM arithmetic.
(00001001 x86-encode-test-r64-r64
  (00001000 (destination source)
    (x86-encode-alu-r64-r64 133 destination source)))

; PUSH r64 (opcode 0x50+rd, ICLASS PUSH: `0b0101_0 SRM[rrr] ... DF64()`) and
; POP r64 (opcode 0x58+rd, ICLASS POP: `0b0101_1 SRM[rrr] ... DF64()`), per
; #175's pinned XED evidence. Both default to 64-bit operand size in long
; mode (`DF64()`), so no REX.W is emitted; only REX.B is needed, and only
; for r8-r15.
(00001001 x86-encode-push-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00000111
        ((00000011 (x86-high1 code) 1)
          (00100111 (x86-encode-rex 0 0 0 1) (00001100 80 (x86-low3 code))))
        ((00000010 (00000001 ()))
          (00100111 (00001100 80 (x86-low3 code))))))))

(00001001 x86-encode-pop-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00000111
        ((00000011 (x86-high1 code) 1)
          (00100111 (x86-encode-rex 0 0 0 1) (00001100 88 (x86-low3 code))))
        ((00000010 (00000001 ()))
          (00100111 (00001100 88 (x86-low3 code))))))))

; INC r64 / DEC r64: group-5 opcode 0xFF, /reg extension (not a register
; operand) selects the operation -- INC is /0, DEC is /1 -- per #175's
; pinned XED evidence (`PATTERN : 0xFF MOD[0b11] MOD=3 REG[0b000] RM[nnn]`
; / `REG[0b001]`). Unlike PUSH/POP, this form always needs REX.W: the
; legacy single-byte 0x40+r/0x48+r INC/DEC opcodes exist in the same pinned
; evidence tagged `not64` -- those byte values became REX prefixes in
; 64-bit mode, so encoding INC/DEC in long mode always goes through this
; ModRM group-5 path, never the legacy one.
(00001001 x86-encode-inc-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 0 (x86-low3 code))))))

(00001001 x86-encode-dec-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        255
        (x86-encode-modrm 3 1 (x86-low3 code))))))

; NOT r64 / NEG r64: group-3 opcode 0xF7, /reg extension (not a register
; operand) selects the operation -- NOT is /2, NEG is /3 -- per #175's
; pinned XED evidence (`PATTERN : 0xF7 MOD[0b11] MOD=3 REG[0b010] RM[nnn]`
; / `REG[0b011]`). This matches INC/DEC's group-5 shape: always REX.W,
; REX.B only for r8-r15.
(00001001 x86-encode-not-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        247
        (x86-encode-modrm 3 2 (x86-low3 code))))))

(00001001 x86-encode-neg-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00100111
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
(00001001 x86-encode-shift-r64-imm8
  (00001000 (opcode-extension register count)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        193
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        count))))

(00001001 x86-encode-shl-r64-imm8
  (00001000 (register count)
    (x86-encode-shift-r64-imm8 4 register count)))

(00001001 x86-encode-shr-r64-imm8
  (00001000 (register count)
    (x86-encode-shift-r64-imm8 5 register count)))

(00001001 x86-encode-sar-r64-imm8
  (00001000 (register count)
    (x86-encode-shift-r64-imm8 7 register count)))

; Jcc rel8: opcode 0x70+cc followed by a signed 8-bit relative displacement
; (from the address of the *next* instruction). No REX prefix -- this is a
; control-transfer, not a GPR operation. The 16 condition codes and their
; opcode offsets are fixed by Intel's encoding and confirmed against #175's
; pinned XED evidence (`PATTERN : 0x7<cc> mode64 ... BRDISP8()` for each
; ICLASS in order: JO,JNO,JB,JNB,JZ,JNZ,JBE,JNBE,JS,JNS,JP,JNP,JL,JNL,JLE,
; JNLE). Reuses x86-disp8-byte for the same two's-complement byte
; conversion #199 already proved correct for MOV's disp8 slot.
(00001001 x86-encode-jcc-rel8
  (00001000 (condition-code displacement)
    (00100111
      (00001100 112 condition-code)
      (x86-disp8-byte displacement))))

(00001001 x86-encode-jo-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 0 displacement)))
(00001001 x86-encode-jno-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 1 displacement)))
(00001001 x86-encode-jb-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 2 displacement)))
(00001001 x86-encode-jnb-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 3 displacement)))
(00001001 x86-encode-jz-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 4 displacement)))
(00001001 x86-encode-jnz-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 5 displacement)))
(00001001 x86-encode-jbe-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 6 displacement)))
(00001001 x86-encode-jnbe-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 7 displacement)))
(00001001 x86-encode-js-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 8 displacement)))
(00001001 x86-encode-jns-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 9 displacement)))
(00001001 x86-encode-jp-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 #d10 displacement)))
(00001001 x86-encode-jnp-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 #d11 displacement)))
(00001001 x86-encode-jl-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 12 displacement)))
(00001001 x86-encode-jnl-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 13 displacement)))
(00001001 x86-encode-jle-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 14 displacement)))
(00001001 x86-encode-jnle-rel8 (00001000 (displacement) (x86-encode-jcc-rel8 15 displacement)))

; JMP rel8: opcode 0xEB followed by a signed 8-bit relative displacement,
; confirmed against #175's pinned XED evidence
; (`PATTERN : 0xEB mode64 norex2_prefix FORCE64() BRDISP8()`). Unlike Jcc,
; JMP is unconditional -- no condition-code byte, no ModRM, no REX -- but
; reuses the same x86-disp8-byte two's-complement conversion.
(00001001 x86-encode-jmp-rel8
  (00001000 (displacement)
    (00100111
      235
      (x86-disp8-byte displacement))))

; Two's-complement little-endian bytes for a rel32 value already known to be
; in [-2147483648,2147483647]. Same wrap-before-split fix #199 proved for
; disp8 (x86-disp8-byte) and this file's own x86-u64-bytes lack for
; mov-r64-imm64 (#220's truth-sentinel audit documented this being an
; existing, out-of-scope gap) -- `mod` in this Lisp does not wrap negative operands, so
; adding 2^32 before reducing mod 2^32 is exact for the whole rel32 domain.
(00001001 x86-rel32-bytes
  (00001000 (displacement)
    (x86-u32-bytes (00010011 (00001100 displacement 4294967296) 4294967296))))

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
(00001001 x86-encode-call-rel32
  (00001000 (displacement)
    (00000100 232 (x86-rel32-bytes displacement))))

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
(00001001 x86-encode-jcc-rel32
  (00001000 (condition-code displacement)
    (00000100
      15
      (00000100
        (00001100 128 condition-code)
        (x86-rel32-bytes displacement)))))

(00001001 x86-encode-jo-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 0 displacement)))
(00001001 x86-encode-jno-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 1 displacement)))
(00001001 x86-encode-jb-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 2 displacement)))
(00001001 x86-encode-jnb-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 3 displacement)))
(00001001 x86-encode-jz-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 4 displacement)))
(00001001 x86-encode-jnz-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 5 displacement)))
(00001001 x86-encode-jbe-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 6 displacement)))
(00001001 x86-encode-jnbe-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 7 displacement)))
(00001001 x86-encode-js-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 8 displacement)))
(00001001 x86-encode-jns-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 9 displacement)))
(00001001 x86-encode-jp-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 #d10 displacement)))
(00001001 x86-encode-jnp-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 #d11 displacement)))
(00001001 x86-encode-jl-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 12 displacement)))
(00001001 x86-encode-jnl-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 13 displacement)))
(00001001 x86-encode-jle-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 14 displacement)))
(00001001 x86-encode-jnle-rel32 (00001000 (displacement) (x86-encode-jcc-rel32 15 displacement)))

; JMP rel32: opcode 0xE9 followed by a signed 32-bit relative displacement,
; confirmed against #175's pinned XED evidence (`PATTERN : 0xE9 mode64
; norex2_prefix FORCE64() BRDISP32()`). Matches JMP rel8's own
; unconditional, no-ModRM, no-REX shape -- only the opcode byte and
; displacement width differ.
(00001001 x86-encode-jmp-rel32
  (00001000 (displacement)
    (00000100 233 (x86-rel32-bytes displacement))))

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
(00001001 x86-encode-group5-indirect-r64
  (00001000 (opcode-extension register)
    (10011100 ((code (x86-reg-code register)))
      (00000111
        ((00000011 (x86-high1 code) 1)
          (00100111
            (x86-encode-rex 0 0 0 1)
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))
        ((00000010 (00000001 ()))
          (00100111
            255
            (x86-encode-modrm 3 opcode-extension (x86-low3 code))))))))

(00001001 x86-encode-call-r64
  (00001000 (register)
    (x86-encode-group5-indirect-r64 2 register)))

(00001001 x86-encode-jmp-r64
  (00001000 (register)
    (x86-encode-group5-indirect-r64 4 register)))

; SETcc r8: opcode 0x0F 0x90+cc, ModRM mod=3, reg=0, rm=low3(code).
; In 64-bit mode:
; - codes 0..3 (al, cl, dl, bl) require no REX prefix.
; - codes 4..7 (spl, bpl, sil, dil) require REX prefix (0x40) to distinguish
;   them from legacy high bytes (ah, ch, dh, bh).
; - codes 8..15 (r8b..r15b) require REX.B=1 prefix (0x41).
(00001001 x86-encode-setcc-r8
  (00001000 (condition-code register)
    (10011100 ((code (x86-reg-code register)))
      ; Exact-D1 predicate selects REX; structural default is the
      ; explicit D1 true witness, never legacy (query expected result).
      (00000111
        ((00011011 code 3)
         (00100111
           (x86-encode-rex 0 0 0 (x86-high1 code))
           15
           (00001100 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))
        ((00000010 (00000001 ()))
         (00100111
           15
           (00001100 144 condition-code)
           (x86-encode-modrm 3 0 (x86-low3 code))))))))

(00001001 x86-encode-seto-r8 (00001000 (register) (x86-encode-setcc-r8 0 register)))
(00001001 x86-encode-setno-r8 (00001000 (register) (x86-encode-setcc-r8 1 register)))
(00001001 x86-encode-setb-r8 (00001000 (register) (x86-encode-setcc-r8 2 register)))
(00001001 x86-encode-setc-r8 (00001000 (register) (x86-encode-setcc-r8 2 register)))
(00001001 x86-encode-setnb-r8 (00001000 (register) (x86-encode-setcc-r8 3 register)))
(00001001 x86-encode-setnc-r8 (00001000 (register) (x86-encode-setcc-r8 3 register)))
(00001001 x86-encode-setae-r8 (00001000 (register) (x86-encode-setcc-r8 3 register)))
(00001001 x86-encode-setz-r8 (00001000 (register) (x86-encode-setcc-r8 4 register)))
(00001001 x86-encode-sete-r8 (00001000 (register) (x86-encode-setcc-r8 4 register)))
(00001001 x86-encode-setnz-r8 (00001000 (register) (x86-encode-setcc-r8 5 register)))
(00001001 x86-encode-setne-r8 (00001000 (register) (x86-encode-setcc-r8 5 register)))
(00001001 x86-encode-setbe-r8 (00001000 (register) (x86-encode-setcc-r8 6 register)))
(00001001 x86-encode-setna-r8 (00001000 (register) (x86-encode-setcc-r8 6 register)))
(00001001 x86-encode-setnbe-r8 (00001000 (register) (x86-encode-setcc-r8 7 register)))
(00001001 x86-encode-seta-r8 (00001000 (register) (x86-encode-setcc-r8 7 register)))
(00001001 x86-encode-sets-r8 (00001000 (register) (x86-encode-setcc-r8 8 register)))
(00001001 x86-encode-setns-r8 (00001000 (register) (x86-encode-setcc-r8 9 register)))
(00001001 x86-encode-setp-r8 (00001000 (register) (x86-encode-setcc-r8 #d10 register)))
(00001001 x86-encode-setpe-r8 (00001000 (register) (x86-encode-setcc-r8 #d10 register)))
(00001001 x86-encode-setnp-r8 (00001000 (register) (x86-encode-setcc-r8 #d11 register)))
(00001001 x86-encode-setpo-r8 (00001000 (register) (x86-encode-setcc-r8 #d11 register)))
(00001001 x86-encode-setl-r8 (00001000 (register) (x86-encode-setcc-r8 12 register)))
(00001001 x86-encode-setnge-r8 (00001000 (register) (x86-encode-setcc-r8 12 register)))
(00001001 x86-encode-setnl-r8 (00001000 (register) (x86-encode-setcc-r8 13 register)))
(00001001 x86-encode-setge-r8 (00001000 (register) (x86-encode-setcc-r8 13 register)))
(00001001 x86-encode-setle-r8 (00001000 (register) (x86-encode-setcc-r8 14 register)))
(00001001 x86-encode-setng-r8 (00001000 (register) (x86-encode-setcc-r8 14 register)))
(00001001 x86-encode-setnle-r8 (00001000 (register) (x86-encode-setcc-r8 15 register)))
(00001001 x86-encode-setg-r8 (00001000 (register) (x86-encode-setcc-r8 15 register)))

; MOVZX r64, r8: opcode 0x0F 0xB6, ModRM mod=3, reg=dest, rm=src.
; REX.W=1 extends the 8-bit source into the full 64-bit destination register.
(00001001 x86-encode-movzx-r64-r8
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        182
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; IMUL r64, r64: two-operand signed multiply, opcode 0x0F 0xAF.
; Destination receives the low 64 bits of the signed product.
(00001001 x86-encode-imul-r64-r64
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        175
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; CQO: Convert Quadword to Octword (sign-extend RAX into RDX:RAX).
; Opcode 0x48 0x99. Prepares dividend for 64-bit IDIV.
(00001001 x86-encode-cqo
  (00001000 ()
    (00100111 72 153)))

; IDIV r64: signed division of RDX:RAX by r64 operand.
; Group 3 opcode 0xF7 /7, ModRM mod=3, reg=7, rm=src.
; Quotient is stored in RAX, remainder in RDX.
(00001001 x86-encode-idiv-r64
  (00001000 (source)
    (10011100 ((src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 src-code))
        247
        (x86-encode-modrm 3 7 (x86-low3 src-code))))))

; CMOVcc r64, r64: conditional move, opcode 0x0F 0x40+cc.
; Moves source to destination if condition code is satisfied.
(00001001 x86-encode-cmovcc-r64-r64
  (00001000 (condition-code destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        (00001100 64 condition-code)
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

(00001001 x86-encode-cmovo-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 0 dest src)))
(00001001 x86-encode-cmovno-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 1 dest src)))
(00001001 x86-encode-cmovb-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(00001001 x86-encode-cmovc-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 2 dest src)))
(00001001 x86-encode-cmovnb-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(00001001 x86-encode-cmovnc-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(00001001 x86-encode-cmovae-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 3 dest src)))
(00001001 x86-encode-cmovz-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(00001001 x86-encode-cmove-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 4 dest src)))
(00001001 x86-encode-cmovnz-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(00001001 x86-encode-cmovne-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 5 dest src)))
(00001001 x86-encode-cmovbe-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(00001001 x86-encode-cmovna-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 6 dest src)))
(00001001 x86-encode-cmovnbe-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(00001001 x86-encode-cmova-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 7 dest src)))
(00001001 x86-encode-cmovs-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 8 dest src)))
(00001001 x86-encode-cmovns-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 9 dest src)))
(00001001 x86-encode-cmovp-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 #d10 dest src)))
(00001001 x86-encode-cmovpe-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 #d10 dest src)))
(00001001 x86-encode-cmovnp-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 #d11 dest src)))
(00001001 x86-encode-cmovpo-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 #d11 dest src)))
(00001001 x86-encode-cmovl-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(00001001 x86-encode-cmovnge-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 12 dest src)))
(00001001 x86-encode-cmovnl-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(00001001 x86-encode-cmovge-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 13 dest src)))
(00001001 x86-encode-cmovle-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(00001001 x86-encode-cmovng-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 14 dest src)))
(00001001 x86-encode-cmovnle-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))
(00001001 x86-encode-cmovg-r64-r64 (00001000 (dest src) (x86-encode-cmovcc-r64-r64 15 dest src)))

; NOP: opcode 0x90.
(00001001 x86-encode-nop
  (00001000 ()
    (00100111 144)))

; TEST r/m64, imm32: Group 3 opcode 0xF7 /0 id, ModRM mod=3, reg=0, rm=dest.
(00001001 x86-encode-test-r64-imm32
  (00001000 (destination immediate)
    (10011100 ((code (x86-reg-code destination)))
      (00101001
        (00100111
          (x86-encode-rex 1 0 0 (x86-high1 code))
          247
          (x86-encode-modrm 3 0 (x86-low3 code)))
        (x86-imm32-bytes immediate)))))

; BT r/m64, r64: opcode 0x0F 0xA3 /r. ModRM reg=index, rm=base.
; Sets Carry Flag (CF) to the value of the bit at the given index.
(00001001 x86-encode-bt-r64-r64
  (00001000 (base index)
    (10011100 ((base-code (x86-reg-code base))
          (index-code (x86-reg-code index)))
      (00100111
        (x86-encode-rex 1 (x86-high1 index-code) 0 (x86-high1 base-code))
        15
        163
        (x86-encode-modrm 3 (x86-low3 index-code) (x86-low3 base-code))))))

; Group 8 bit operations with imm8: opcode 0x0F 0xBA /reg ib.
(00001001 x86-encode-group8-r64-imm8
  (00001000 (opcode-extension register bit-index)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        186
        (x86-encode-modrm 3 opcode-extension (x86-low3 code))
        bit-index))))

(00001001 x86-encode-bt-r64-imm8
  (00001000 (register bit-index)
    (x86-encode-group8-r64-imm8 4 register bit-index)))

(00001001 x86-encode-bts-r64-imm8
  (00001000 (register bit-index)
    (x86-encode-group8-r64-imm8 5 register bit-index)))

(00001001 x86-encode-btr-r64-imm8
  (00001000 (register bit-index)
    (x86-encode-group8-r64-imm8 6 register bit-index)))

(00001001 x86-encode-btc-r64-imm8
  (00001000 (register bit-index)
    (x86-encode-group8-r64-imm8 7 register bit-index)))

; MOVSX r64, r/m8: opcode 0x0F 0xBE /r. Sign-extend 8-bit to 64-bit.
(00001001 x86-encode-movsx-r64-r8
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        190
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; MOVSXD r64, r/m32: opcode 0x63 /r. Sign-extend 32-bit to 64-bit.
(00001001 x86-encode-movsxd-r64-r32
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        99
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; POPCNT r64, r/m64: opcode 0xF3 0x0F 0xB8 /r. Count set bits (population count).
(00001001 x86-encode-popcnt-r64-r64
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        184
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; TZCNT r64, r/m64: opcode 0xF3 0x0F 0xBC /r. Count trailing zeros.
(00001001 x86-encode-tzcnt-r64-r64
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        243
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSF r64, r/m64: opcode 0x0F 0xBC /r. Bit Scan Forward (first set bit).
(00001001 x86-encode-bsf-r64-r64
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        188
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSR r64, r/m64: opcode 0x0F 0xBD /r. Bit Scan Reverse (last set bit).
(00001001 x86-encode-bsr-r64-r64
  (00001000 (destination source)
    (10011100 ((dest-code (x86-reg-code destination))
          (src-code (x86-reg-code source)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dest-code) 0 (x86-high1 src-code))
        15
        189
        (x86-encode-modrm 3 (x86-low3 dest-code) (x86-low3 src-code))))))

; BSWAP r64: opcode 0x0F (0xC8 + rd). Byte Swap (reverse byte order).
(00001001 x86-encode-bswap-r64
  (00001000 (register)
    (10011100 ((code (x86-reg-code register)))
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        15
        (00001100 200 (x86-low3 code))))))

; ROL / ROR r64, imm8: group-2 opcode 0xC1, /0 for ROL, /1 for ROR.
(00001001 x86-encode-rol-r64-imm8
  (00001000 (register count)
    (x86-encode-shift-r64-imm8 0 register count)))

(00001001 x86-encode-ror-r64-imm8
  (00001000 (register count)
    (x86-encode-shift-r64-imm8 1 register count)))

; XCHG r64, r64: opcode 0x87 /r. Exchange register values.
(00001001 x86-encode-xchg-r64-r64
  (00001000 (dst src)
    (10011100 ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (00100111
        (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
        135
        (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CLD: opcode 0xFC (252). Clear direction flag (DF=0).
(00001001 x86-encode-cld
  (00001000 ()
    (00100111 252)))

; STD: opcode 0xFD (253). Set direction flag (DF=1).
(00001001 x86-encode-std
  (00001000 ()
    (00100111 253)))

; STOSQ: opcode 0x48 0xAB (72 171). Store RAX to [RDI], increment RDI by 8.
(00001001 x86-encode-stosq
  (00001000 ()
    (00100111 (x86-encode-rex 1 0 0 0) 171)))

; REP STOSQ: opcode 0xF3 0x48 0xAB. Fill RCX qwords at [RDI] with RAX.
(00001001 x86-encode-rep-stosq
  (00001000 ()
    (00100111 243 (x86-encode-rex 1 0 0 0) 171)))

; STOSB: opcode 0xAA (170). Store AL to [RDI], increment RDI by 1.
(00001001 x86-encode-stosb
  (00001000 ()
    (00100111 170)))

; REP STOSB: opcode 0xF3 0xAA. Fill RCX bytes at [RDI] with AL.
(00001001 x86-encode-rep-stosb
  (00001000 ()
    (00100111 243 170)))

; MOVSQ: opcode 0x48 0xA5 (72 165). Move qword from [RSI] to [RDI].
(00001001 x86-encode-movsq
  (00001000 ()
    (00100111 (x86-encode-rex 1 0 0 0) 165)))

; REP MOVSQ: opcode 0xF3 0x48 0xA5. Copy RCX qwords from [RSI] to [RDI].
(00001001 x86-encode-rep-movsq
  (00001000 ()
    (00100111 243 (x86-encode-rex 1 0 0 0) 165)))

; MOVSB: opcode 0xA4 (164). Move byte from [RSI] to [RDI].
(00001001 x86-encode-movsb
  (00001000 ()
    (00100111 164)))

; REP MOVSB: opcode 0xF3 0xA4. Copy RCX bytes from [RSI] to [RDI].
(00001001 x86-encode-rep-movsb
  (00001000 ()
    (00100111 243 164)))

(00001001 x86-encode-sse2-f2-xmm-xmm
  (00001000 (opcode-byte dst src)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (00000111
        ((10011010 (00000011 (x86-high1 dst-code) 0) (00000011 (x86-high1 src-code) 0))
         (00100111 242 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((00000010 (00000001 ()))
         (00100111 242 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

(00001001 x86-encode-sse2-66-xmm-xmm
  (00001000 (opcode-byte dst src)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (00000111
        ((10011010 (00000011 (x86-high1 dst-code) 0) (00000011 (x86-high1 src-code) 0))
         (00100111 102 15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((00000010 (00000001 ()))
         (00100111 102 (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
               15 opcode-byte (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AES-NI register-source форми з pinned #175 XED evidence мають спільну
; будову: mandatory 0x66, optional REX.R/REX.B для XMM8-XMM15, далі
; 0F 38 або 0F 3A, opcode і ModR/M з mode=3. Цей helper описує лише
; машинне кодування; значення AES-операцій тут не визначається.
(00001001 x86-encode-sse-66-map-xmm-xmm
  (00001000 (map-byte opcode-byte dst src)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (00000111
        ((10011010 (00000011 (x86-high1 dst-code) 0) (00000011 (x86-high1 src-code) 0))
         (00100111
           102
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))
        ((00000010 (00000001 ()))
         (00100111
           102
           (x86-encode-rex 0 (x86-high1 dst-code) 0 (x86-high1 src-code))
           15
           map-byte
           opcode-byte
           (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))))

; AESENC xmm, xmm: 66 0F 38 DC /r.
(00001001 x86-encode-aesenc-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 220 dst src)))

; AESENCLAST xmm, xmm: 66 0F 38 DD /r.
(00001001 x86-encode-aesenclast-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 221 dst src)))

; AESDEC xmm, xmm: 66 0F 38 DE /r.
(00001001 x86-encode-aesdec-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 222 dst src)))

; AESDECLAST xmm, xmm: 66 0F 38 DF /r.
(00001001 x86-encode-aesdeclast-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 223 dst src)))

; AESIMC xmm, xmm: 66 0F 38 DB /r.
(00001001 x86-encode-aesimc-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse-66-map-xmm-xmm 56 219 dst src)))

; AESKEYGENASSIST xmm, xmm, imm8: 66 0F 3A DF /r ib.
; Межа imm8 перевіряється admission-шаром до матеріалізації байтів.
(00001001 x86-encode-aeskeygenassist-xmm-xmm-imm8
  (00001000 (dst src immediate)
    (00101001
      (x86-encode-sse-66-map-xmm-xmm 58 223 dst src)
      (00100111 immediate))))

; AES-NI memory-source bounded base+disp8 використовує ту саму x86
; адресацію, що вже доведена для MOV/LEA: ModR/M mode=01, SIB для rsp/r12,
; REX.R для xmm8-xmm15 і REX.B для r8-r15. Ширину пам'яті визначає сама
; інструкція AES, тому цей helper не створює окремої семантики пам'яті.
(00001001 x86-encode-sse-66-map-xmm-mem-disp8
  (00001000 (map-byte opcode-byte dst base displacement)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (base-code (x86-reg-code base)))
      (10011100 ((modrm
              (x86-encode-modrm
                1
                (x86-low3 dst-code)
                (x86-low3 base-code)))
            (disp-byte (x86-disp8-byte displacement)))
        (10011100 ((address-tail
                (00000111
                  ((00000011 (x86-low3 base-code) 4)
                   (00100111 modrm (x86-encode-sib 0 4 4) disp-byte))
                  ((00000010 (00000001 ()))
                   (00100111 modrm disp-byte)))))
          (00000111
            ((10011010
               (00000011 (x86-high1 dst-code) 0)
               (00000011 (x86-high1 base-code) 0))
             (00101001
               (00100111 102 15 map-byte opcode-byte)
               address-tail))
            ((00000010 (00000001 ()))
             (00101001
               (00100111
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

(00001001 x86-encode-aesenc-xmm-mem-disp8
  (00001000 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 220 dst base displacement)))

(00001001 x86-encode-aesenclast-xmm-mem-disp8
  (00001000 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 221 dst base displacement)))

(00001001 x86-encode-aesdec-xmm-mem-disp8
  (00001000 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 222 dst base displacement)))

(00001001 x86-encode-aesdeclast-xmm-mem-disp8
  (00001000 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 223 dst base displacement)))

(00001001 x86-encode-aesimc-xmm-mem-disp8
  (00001000 (dst base displacement)
    (x86-encode-sse-66-map-xmm-mem-disp8
      56 219 dst base displacement)))

(00001001 x86-encode-aeskeygenassist-xmm-mem-disp8-imm8
  (00001000 (dst base displacement immediate)
    (00101001
      (x86-encode-sse-66-map-xmm-mem-disp8
        58 223 dst base displacement)
      (00100111 immediate))))

; PCLMULQDQ xmm, xmm, imm8: 66 0F 3A 44 /r ib.
; Pinned #175 XED evidence exposes exactly register-source and memory-source
; forms. The immediate selects the source 64-bit lanes; that ISA meaning is
; not redefined here -- this layer only materializes the admitted bytes.
(00001001 x86-encode-pclmulqdq-xmm-xmm-imm8
  (00001000 (dst src immediate)
    (00101001
      (x86-encode-sse-66-map-xmm-xmm #d58 #d68 dst src)
      (00100111 immediate))))

; Bounded memory projection: base+disp8 reuses the already witnessed
; ModR/M/SIB/REX mechanism. This is not a claim of general x86 addressing.
(00001001 x86-encode-pclmulqdq-xmm-mem-disp8-imm8
  (00001000 (dst base displacement immediate)
    (00101001
      (x86-encode-sse-66-map-xmm-mem-disp8
        #d58 #d68 dst base displacement)
      (00100111 immediate))))

; MOVSD xmm, xmm: opcode 0xF2 0x0F 0x10 /r
(00001001 x86-encode-movsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 16 dst src)))

; SQRTSD xmm, xmm: opcode 0xF2 0x0F 0x51 /r
(00001001 x86-encode-sqrtsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 81 dst src)))

; ADDSD xmm, xmm: opcode 0xF2 0x0F 0x58 /r
(00001001 x86-encode-addsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 88 dst src)))

; MULSD xmm, xmm: opcode 0xF2 0x0F 0x59 /r
(00001001 x86-encode-mulsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 89 dst src)))

; SUBSD xmm, xmm: opcode 0xF2 0x0F 0x5C /r
(00001001 x86-encode-subsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 92 dst src)))

; MINSD xmm, xmm: opcode 0xF2 0x0F 0x5D /r
(00001001 x86-encode-minsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 93 dst src)))

; DIVSD xmm, xmm: opcode 0xF2 0x0F 0x5E /r
(00001001 x86-encode-divsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 94 dst src)))

; MAXSD xmm, xmm: opcode 0xF2 0x0F 0x5F /r
(00001001 x86-encode-maxsd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-f2-xmm-xmm 95 dst src)))

; UCOMISD xmm, xmm: opcode 0x66 0x0F 0x2E /r
(00001001 x86-encode-ucomisd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-66-xmm-xmm 46 dst src)))

; XORPD xmm, xmm: opcode 0x66 0x0F 0x57 /r
(00001001 x86-encode-xorpd-xmm-xmm
  (00001000 (dst src)
    (x86-encode-sse2-66-xmm-xmm 87 dst src)))

; CVTSI2SD xmm, r64: opcode 0xF2 REX.W 0x0F 0x2A /r
(00001001 x86-encode-cvtsi2sd-xmm-r64
  (00001000 (dst src)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (00100111 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 42 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; CVTTSD2SI r64, xmm: opcode 0xF2 REX.W 0x0F 0x2C /r
(00001001 x86-encode-cvttsd2si-r64-xmm
  (00001000 (dst src)
    (10011100 ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (00100111 242 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 44 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ xmm, r64: opcode 0x66 REX.W 0x0F 0x6E /r
(00001001 x86-encode-movq-xmm-r64
  (00001000 (dst src)
    (10011100 ((dst-code (x86-xmm-reg-code dst))
          (src-code (x86-reg-code src)))
      (00100111 102 (x86-encode-rex 1 (x86-high1 dst-code) 0 (x86-high1 src-code))
            15 #d110 (x86-encode-modrm 3 (x86-low3 dst-code) (x86-low3 src-code))))))

; MOVQ r64, xmm: opcode 0x66 REX.W 0x0F 0x7E /r
(00001001 x86-encode-movq-r64-xmm
  (00001000 (dst src)
    (10011100 ((dst-code (x86-reg-code dst))
          (src-code (x86-xmm-reg-code src)))
      (00100111 102 (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 126 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

; RDRAND/RDSEED r64 — positive control for #2372 generator-first machine grammar.
; Both descend from one XED-proven shape: REX.W + 0F C7 /digit, MOD=3, RM=GPRv.
; The shared helper is the encoding law; mnemonic wrappers are derived projections.
(00001001 x86-encode-0f-c7-group-r64
  (00001000 (opcode-extension register)
    (10011100 ((code (x86-reg-code register))
          (mechanism-extension
            (x86-project-bin3-to-mechanism-u3 opcode-extension)))
      ; Emitted instruction bytes are the legacy/mechanical byte carrier.
      ; Keep the opcode-extension input canonical (#b...) above, but do not
      ; leak BinaryNumber into the byte list: equal? intentionally keeps
      ; canonical BinaryNumber distinct from legacy/mechanical Number.
      (00100111
        (x86-encode-rex 1 0 0 (x86-high1 code))
        #d15
        #d199
        (x86-encode-modrm 3 mechanism-extension (x86-low3 code))))))

(00001001 x86-encode-rdrand-r64
  (00001000 (register)
    (x86-encode-0f-c7-group-r64 #b110 register)))

(00001001 x86-encode-rdseed-r64
  (00001000 (register)
    (x86-encode-0f-c7-group-r64 #b111 register)))

; RDTSC: opcode 0x0F 0x31
(00001001 x86-encode-rdtsc
  (00001000 ()
    (00100111 15 49)))

; CMPXCHG r64, r64: opcode REX.W 0x0F 0xB1 /r
(00001001 x86-encode-cmpxchg-r64-r64
  (00001000 (dst src)
    (10011100 ((dst-code (x86-reg-code dst))
          (src-code (x86-reg-code src)))
      (00100111 (x86-encode-rex 1 (x86-high1 src-code) 0 (x86-high1 dst-code))
            15 177 (x86-encode-modrm 3 (x86-low3 src-code) (x86-low3 dst-code))))))

(00001001 x86-encode-program
  (00001000 (instructions)
    (00000111
      ; ATOM is the exact D1 predicate. Within the atom branch, EQ is safe
      ; and distinguishes the empty-list terminator from any invalid atom.
      ; Invalid non-NIL atoms fail closed through CAR; admitted pairs recurse.
      ((00000010 instructions)
       (00000111
         ((00000011 instructions (00000001 ()))
          (00000001 ()))
         ((00000011 0 0)
          (00000101 instructions))))
      ((00000011 0 0)
       (00101001
         (00000101 instructions)
         (x86-encode-program (00000110 instructions)))))))

; #2372 reusable VEX3 XMM register law.
; byte1 = C4; byte2 = ~R ~X ~B m-mmmm; byte3 = W ~vvvv L pp.
; These are machine bytes in the exact Number carrier already used by the
; x86 encoder, so the instruction-set witness compares identity, not print.
(00001001 x86-vex3-byte2
  (00001000 (mmmmm r x b)
    (00001100
      (00001110 (00001101 1 r) 128)
      (00001100
        (00001110 (00001101 1 x) 64)
        (00001100
          (00001110 (00001101 1 b) 32)
          mmmmm)))))

(00001001 x86-vex3-byte3
  (00001000 (w vvvv l pp)
    (00001100
      (00001110 w 128)
      (00001100
        (00001110 (00001101 15 vvvv) 8)
        (00001100
          (00001110 l 4)
          pp)))))

(00001001 x86-encode-vex3-xmm-xmm-xmm
  (00001000 (mmmmm w l pp opcode dst src1 src2)
    (10011100
      ((dst-code (x86-xmm-reg-code dst))
       (src1-code (x86-xmm-reg-code src1))
       (src2-code (x86-xmm-reg-code src2)))
      (00100111
        196
        (x86-vex3-byte2
          mmmmm
          (x86-high1 dst-code)
          0
          (x86-high1 src2-code))
        (x86-vex3-byte3 w src1-code l pp)
        opcode
        (x86-encode-modrm
          3
          (x86-low3 dst-code)
          (x86-low3 src2-code))))))

; VANDNPS xmm,xmm,xmm: VEX.128.0F.WIG 55 /r.
(00001001 x86-encode-vandnps-xmm-xmm-xmm
  (00001000 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 0 85 dst src1 src2)))

; VANDNPD xmm,xmm,xmm: VEX.128.66.0F.WIG 55 /r.
(00001001 x86-encode-vandnpd-xmm-xmm-xmm
  (00001000 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 1 85 dst src1 src2)))

; VADDPD xmm,xmm,xmm: VEX.128.66.0F.WIG 58 /r.
(00001001 x86-encode-vaddpd-xmm-xmm-xmm
  (00001000 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 1 88 dst src1 src2)))

; VADDPS xmm,xmm,xmm: VEX.128.0F.WIG 58 /r.
(00001001 x86-encode-vaddps-xmm-xmm-xmm
  (00001000 (dst src1 src2)
    (x86-encode-vex3-xmm-xmm-xmm
      1 0 0 0 88 dst src1 src2)))

