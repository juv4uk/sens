/* Спільний драйвер: C, ASM SSE2, ASM AVX2/FMA, Fortran і Rust.
 * Вхідний масив змінюється перед кожним добутком, щоб не вилучити роботу. */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

enum { N = 65536, ROUNDS = 2048 };

#if defined(SENS_ASM_SCALAR) && defined(SENS_ASM_AVX2)
#error "Only one assembler kernel can be enabled"
#endif
#if defined(SENS_ASM_SCALAR)
extern double sens_dot_scalar(const double *, const double *, size_t);
#elif defined(SENS_ASM_AVX2)
extern double sens_dot_avx2(const double *, const double *, size_t);
#elif defined(SENS_ZIG)
extern double sens_dot_zig(const double *, const double *, size_t);
#endif


int main(void) {
    double *a = malloc(sizeof(double) * N);
    double *b = malloc(sizeof(double) * N);
    if (!a || !b) {
        free(a);
        free(b);
        return 2;
    }
    for (int i = 0; i < N; i++) {
        a[i] = (double)(i % 97 + 1) * 0.001;
        b[i] = (double)(i % 89 + 1) * 0.002;
    }
    double total = 0.0;
    for (int round = 0; round < ROUNDS; round++) {
        a[round % N] += 1.0e-9;
        double dot = 0.0;
#if defined(SENS_ASM_SCALAR)
        dot = sens_dot_scalar(a, b, N);
#elif defined(SENS_ASM_AVX2)
        dot = sens_dot_avx2(a, b, N);
#elif defined(SENS_ZIG)
        dot = sens_dot_zig(a, b, N);
#else
        for (int i = 0; i < N; i++) {
            dot += a[i] * b[i];
        }
#endif
        total += dot;
    }
    printf("%.16e\n", total);
    free(a);
    free(b);
    return 0;
}
