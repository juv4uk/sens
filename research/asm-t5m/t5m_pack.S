/* T5M-3 pack/unpack — x86-64 SysV, самодостатній, без libc. ОПТИМІЗОВАНО.
   Дзеркалить research/zig-codecs/t5m3.zig і lib/core4.lisp т5м-у-байти/т5м-з-байтів.
   15 тритів (0/1, роздільник 2) → 3 байти little-endian; value = value*3 + trit.
   pack: внутрішній цикл розгорнуто на 15 кроків (без гілок).
   unpack: ділення на 3 через магічне множення (x*0xAAAAAAAB)>>33, без div. */

.text

/* uint64_t sens_t5m_pack(const uint8_t *trits, size_t n, uint8_t *out) */
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
    movzbl 5(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 6(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 7(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 8(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 9(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 10(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 11(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 12(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 13(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    movzbl 14(%rdi,%rcx),%r10d
    lea (%r8,%r8,2),%r8
    add %r10,%r8
    mov %r8b,(%rdx,%rax)
    mov %r8d,%r10d
    shr $8,%r10d
    mov %r10b,1(%rdx,%rax)
    shr $16,%r8d
    mov %r8b,2(%rdx,%rax)
    add $3,%rax
    add $15,%rcx
    jmp .Lp_group
.Lp_done:
    ret
.size sens_t5m_pack,.-sens_t5m_pack

/* void sens_t5m_unpack(const uint8_t *bytes, size_t n_groups, uint8_t *trits) */
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
    lea (%rcx,%rcx,2),%r9
    movzbl (%rdi,%r9),%r8d
    movzbl 1(%rdi,%r9),%r11d
    shl $8,%r11d
    or %r11d,%r8d
    movzbl 2(%rdi,%r9),%r11d
    shl $16,%r11d
    or %r11d,%r8d
    imul $15,%rcx,%r9
    add $14,%r9
    mov $14,%r10
.Lu_inner:
    mov %r8d,%eax
    imul %r12,%rax
    shr $33,%rax
    lea (%rax,%rax,2),%r13d
    mov %r8d,%edx
    sub %r13d,%edx
    mov %eax,%r8d
    mov %dl,(%rbx,%r9)
    dec %r9
    dec %r10
    jns .Lu_inner
    inc %rcx
    jmp .Lu_group
.Lu_done:
    pop %r13
    pop %r12
    pop %rbx
    ret
.size sens_t5m_unpack,.-sens_t5m_unpack

.section .note.GNU-stack,"",@progbits
