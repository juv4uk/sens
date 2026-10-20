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
.section .note.GNU-stack,"",@progbits
