/* Векторний контроль компілятора C проти ручного ASM на Skylake.
 * Чотири незалежні AVX2/FMA накопичувачі, той самий порядок редукції.
 * Це ідіоматичні intrinsics C, а не виклик ASM SENS.
 * Не використовуємо глобальний -ffast-math: лише явні FMA.
 */
#include <stddef.h>
#include <immintrin.h>

__attribute__((target("avx2,fma"), noinline))
double sens_dot_c_avx2(const double *a, const double *b, size_t n) {
    __m256d s0 = _mm256_setzero_pd();
    __m256d s1 = _mm256_setzero_pd();
    __m256d s2 = _mm256_setzero_pd();
    __m256d s3 = _mm256_setzero_pd();
    size_t i = 0;
    for (; n - i >= 16; i += 16) {
        s0 = _mm256_fmadd_pd(_mm256_loadu_pd(a + i), _mm256_loadu_pd(b + i), s0);
        s1 = _mm256_fmadd_pd(_mm256_loadu_pd(a + i + 4), _mm256_loadu_pd(b + i + 4), s1);
        s2 = _mm256_fmadd_pd(_mm256_loadu_pd(a + i + 8), _mm256_loadu_pd(b + i + 8), s2);
        s3 = _mm256_fmadd_pd(_mm256_loadu_pd(a + i + 12), _mm256_loadu_pd(b + i + 12), s3);
    }
    const __m256d accum = _mm256_add_pd(_mm256_add_pd(s0, s1), _mm256_add_pd(s2, s3));
    const __m128d lo = _mm256_castpd256_pd128(accum);
    const __m128d hi = _mm256_extractf128_pd(accum, 1);
    const __m128d lanes = _mm_add_pd(lo, hi);
    __m128d result = _mm_hadd_pd(lanes, lanes);
    for (; i < n; ++i) {
        result = _mm_fmadd_sd(_mm_load_sd(a + i), _mm_load_sd(b + i), result);
    }
    return _mm_cvtsd_f64(result);
}
