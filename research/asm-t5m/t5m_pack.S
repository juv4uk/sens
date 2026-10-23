/* T5M (ДЕФОЛТНИЙ) pack/unpack — x86-64 SysV, без libc.
   5 трітів (0/1, роздільник 2) → 1 байт; 3^5 = 243 < 256.
   value = value*3 + trit, перший тріт — старший. Дзеркалить lib/core4.lisp
   (трітів-у-байті 5) і scripts/sens_t5_t5m_codec.py (encode_words/decode_bytes).
   pack і unpack розгорнуто на 5 кроків; ділення на 3 — магічним множенням.
   Це механізм транспорту, не семантика SENS. */

.text

/* uint64_t sens_t5m_pack(const uint8_t *trits, size_t n, uint8_t *out)  (n кратне 5) */
.globl sens_t5m_pack
.type sens_t5m_pack,@function
sens_t5m_pack:
    xor %rax,%rax
    xor %rcx,%rcx
.Lp_group:
    cmp %rsi,%rcx
    jae .Lp_done
    movzbl (%rdi,%rcx),%r8d
    movzbl 1(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 2(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 3(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 4(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    mov %r8b,(%rdx,%rax)
    inc %rax
    add $5,%rcx
    jmp .Lp_group
.Lp_done:
    ret
.size sens_t5m_pack,.-sens_t5m_pack

/* void sens_t5m_unpack(const uint8_t *bytes, size_t n_bytes, uint8_t *trits) */
.globl sens_t5m_unpack
.type sens_t5m_unpack,@function
sens_t5m_unpack:
    push %rbx
    push %r12
    push %r13
    mov %rdx,%rbx
    mov $0xAAAAAAAB,%r12d
    xor %rcx,%rcx
.Lu_group:
    cmp %rsi,%rcx
    jae .Lu_done
    movzbl (%rdi,%rcx),%r8d
    lea (%rcx,%rcx,4),%r9
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,4(%rbx,%r9)
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,3(%rbx,%r9)
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,2(%rbx,%r9)
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,1(%rbx,%r9)
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,0(%rbx,%r9)
    inc %rcx
    jmp .Lu_group
.Lu_done:
    pop %r13
    pop %r12
    pop %rbx
    ret
.size sens_t5m_unpack,.-sens_t5m_unpack

.section .note.GNU-stack,"",@progbits
