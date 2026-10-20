/* T5M word-level кодек — x86-64 SysV. 5 трітів/байт (3^5=243<256).
   encode: слова (bits u16, widths u8) -> T5M байти
   decode: T5M байти -> слова (bits u16, widths u8)
   Роздільник-трит 2 між словами; доповнення трітом 2 до кратного 5.
   Викликає sens_t5m_pack/unpack з t5m_pack.S. Це транспорт, не семантика. */
.text

.globl sens_t5m_encode
.type sens_t5m_encode,@function
/* uint64_t sens_t5m_encode(const uint16_t *bits, const uint8_t *widths, size_t n,
                            uint8_t *scratch, uint8_t *out)  -> rax = байти */
sens_t5m_encode:
    push %rbx
    push %r12
    push %r13
    push %r14
    push %r15
    mov %rcx,%r14            /* scratch */
    mov %r8,%r15             /* out */
    xor %r9,%r9              /* at (індекс трита) */
    xor %r10,%r10            /* i (індекс слова) */
.Lenc_word:
    cmp %rdx,%r10
    jae .Lenc_pad
    test %r10,%r10
    jz .Lenc_nosep
    movb $2,(%r14,%r9)       /* роздільник між словами */
    inc %r9
.Lenc_nosep:
    movzbl (%rsi,%r10),%r11d /* width */
    movzwl (%rdi,%r10,2),%ebx/* bits */
.Lenc_bit:
    test %r11,%r11
    jz .Lenc_next
    dec %r11
    mov %rbx,%r12
    mov %r11,%rcx
    shr %cl,%r12
    and $1,%r12d
    mov %r12b,(%r14,%r9)     /* біт як трит (MSB-first) */
    inc %r9
    jmp .Lenc_bit
.Lenc_next:
    inc %r10
    jmp .Lenc_word
.Lenc_pad:
    mov %r9,%rax
    xor %edx,%edx
    mov $5,%ecx
    div %ecx                 /* edx = at % 5 */
    test %edx,%edx
    jz .Lenc_pack
    movb $2,(%r14,%r9)
    inc %r9
    jmp .Lenc_pad
.Lenc_pack:
    mov %r14,%rdi            /* scratch */
    mov %r9,%rsi             /* довжина тритів */
    mov %r15,%rdx            /* out */
    call sens_t5m_pack
    pop %r15
    pop %r14
    pop %r13
    pop %r12
    pop %rbx
    ret
.size sens_t5m_encode,.-sens_t5m_encode

.globl sens_t5m_decode
.type sens_t5m_decode,@function
/* uint64_t sens_t5m_decode(const uint8_t *bytes, size_t nbytes, uint8_t *scratch,
                            uint16_t *out_bits, uint8_t *out_widths) -> rax = слова */
sens_t5m_decode:
    push %rbx
    push %r12
    push %r13
    push %r14
    push %r15
    mov %rsi,%r12            /* nbytes */
    mov %rdx,%r14            /* scratch */
    mov %rcx,%r15            /* out_bits */
    mov %r8,%rbx             /* out_widths */
    call sens_t5m_unpack     /* (bytes=rdi, nbytes=rsi, scratch=rdx) — незмінні */
    imul $5,%r12,%r13        /* усього тритів */
    xor %r9,%r9              /* індекс трита */
    xor %r10,%r10            /* індекс слова */
    xor %r11,%r11            /* поточне значення */
    xor %rcx,%rcx            /* поточна ширина */
.Ldec_loop:
    cmp %r13,%r9
    jae .Ldec_end
    movzbl (%r14,%r9),%eax
    inc %r9
    cmp $2,%eax
    je .Ldec_sep
    lea (%r11,%r11),%r11
    add %rax,%r11            /* value = value*2 + bit */
    inc %rcx
    jmp .Ldec_loop
.Ldec_sep:
    test %rcx,%rcx
    jz .Ldec_loop            /* провідний/кінцевий роздільник */
    mov %r11w,(%r15,%r10,2)
    mov %cl,(%rbx,%r10)
    inc %r10
    xor %r11,%r11
    xor %rcx,%rcx
    jmp .Ldec_loop
.Ldec_end:
    test %rcx,%rcx
    jz .Ldec_done
    mov %r11w,(%r15,%r10,2)
    mov %cl,(%rbx,%r10)
    inc %r10
.Ldec_done:
    mov %r10,%rax
    pop %r15
    pop %r14
    pop %r13
    pop %r12
    pop %rbx
    ret
.size sens_t5m_decode,.-sens_t5m_decode

.section .note.GNU-stack,"",@progbits
