/* Intel Skylake x86-64 SysV: rdi=a, rsi=b, rdx=n; xmm0=result.
   SSE2 is sequential; AVX2/FMA uses four vector accumulators. */
.text
.p2align 4
.globl sens_dot_scalar
.type sens_dot_scalar,@function
sens_dot_scalar:
    xorpd %xmm0,%xmm0
    xor %eax,%eax
    test %rdx,%rdx
    je .Lscalar_done
.Lscalar_loop:
    movsd (%rdi,%rax,8),%xmm1
    mulsd (%rsi,%rax,8),%xmm1
    addsd %xmm1,%xmm0
    inc %rax
    cmp %rdx,%rax
    jb .Lscalar_loop
.Lscalar_done:
    ret
.size sens_dot_scalar,.-sens_dot_scalar

.p2align 5
.globl sens_dot_avx2
.type sens_dot_avx2,@function
sens_dot_avx2:
    vxorpd %ymm0,%ymm0,%ymm0
    vxorpd %ymm1,%ymm1,%ymm1
    vxorpd %ymm2,%ymm2,%ymm2
    vxorpd %ymm3,%ymm3,%ymm3
    xor %eax,%eax
    mov %rdx,%rcx
    and $-16,%rcx
    jz .Lavx_reduce
.Lavx_loop:
    vmovupd (%rdi,%rax,8),%ymm4
    vfmadd231pd (%rsi,%rax,8),%ymm4,%ymm0
    vmovupd 32(%rdi,%rax,8),%ymm4
    vfmadd231pd 32(%rsi,%rax,8),%ymm4,%ymm1
    vmovupd 64(%rdi,%rax,8),%ymm4
    vfmadd231pd 64(%rsi,%rax,8),%ymm4,%ymm2
    vmovupd 96(%rdi,%rax,8),%ymm4
    vfmadd231pd 96(%rsi,%rax,8),%ymm4,%ymm3
    add $16,%rax
    cmp %rcx,%rax
    jb .Lavx_loop
.Lavx_reduce:
    vaddpd %ymm1,%ymm0,%ymm0
    vaddpd %ymm3,%ymm2,%ymm2
    vaddpd %ymm2,%ymm0,%ymm0
    vextractf128 $1,%ymm0,%xmm1
    vaddpd %xmm1,%xmm0,%xmm0
    vhaddpd %xmm0,%xmm0,%xmm0
    cmp %rdx,%rax
    jae .Lavx_done
.Lavx_tail:
    vmovsd (%rdi,%rax,8),%xmm1
    vfmadd231sd (%rsi,%rax,8),%xmm1,%xmm0
    inc %rax
    cmp %rdx,%rax
    jb .Lavx_tail
.Lavx_done:
    vzeroupper
    ret
.size sens_dot_avx2,.-sens_dot_avx2

/* Точні знакові D24 механізми без плаваючої коми. Обидва аргументи
 * уже допущені SENS і розширені зі знакових 24 до i64.
 * Результат ADD/SUB/IMUL вміщується у знакові 48 бітів.
 * Вибір D24 або D48 залишається за доменним законом SENS. */
.p2align 4
.globl sens_i24_add_exact
.type sens_i24_add_exact,@function
sens_i24_add_exact:
    mov %rdi,%rax
    add %rsi,%rax
    ret
.size sens_i24_add_exact,.-sens_i24_add_exact

.p2align 4
.globl sens_i24_sub_exact
.type sens_i24_sub_exact,@function
sens_i24_sub_exact:
    mov %rdi,%rax
    sub %rsi,%rax
    ret
.size sens_i24_sub_exact,.-sens_i24_sub_exact

.p2align 4
.globl sens_i24_mul_exact
.type sens_i24_mul_exact,@function
sens_i24_mul_exact:
    mov %rdi,%rax
    imul %rsi,%rax
    ret
.size sens_i24_mul_exact,.-sens_i24_mul_exact

/* D48 signed multiplication, exact RDX:RAX (128 bits).
 * SysV RDI=left, RSI=right, RDX=high_out pointer, RAX=low.
 * The caller selects D48/D96 using ratified domain law. */
.p2align 4
.globl sens_i48_mul_exact
.type sens_i48_mul_exact,@function
sens_i48_mul_exact:
    mov %rdx,%rcx
    mov %rdi,%rax
    imul %rsi
    mov %rdx,(%rcx)
    ret
.size sens_i48_mul_exact,.-sens_i48_mul_exact

/* Точне двослівне D96 ADD/SUB, System V:
 * RDI=a_low RSI=a_high, RDX=b_low RCX=b_high, R8=out_high.
 * RAX=out_low, ADC/SBB переносить біт між половинами. */
.p2align 4
.globl sens_i96_add_exact
.type sens_i96_add_exact,@function
sens_i96_add_exact:
    mov %rdi,%rax
    add %rdx,%rax
    mov %rsi,%r10
    adc %rcx,%r10
    mov %r10,(%r8)
    ret
.size sens_i96_add_exact,.-sens_i96_add_exact

.p2align 4
.globl sens_i96_sub_exact
.type sens_i96_sub_exact,@function
sens_i96_sub_exact:
    mov %rdi,%rax
    sub %rdx,%rax
    mov %rsi,%r10
    sbb %rcx,%r10
    mov %r10,(%r8)
    ret
.size sens_i96_sub_exact,.-sens_i96_sub_exact

.section .note.GNU-stack,"",@progbits
