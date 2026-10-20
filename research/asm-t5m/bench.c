/* Спільний бенчмарк T5M (дефолтний): асемблер проти Zig, C і (опційно) Rust.
   Збірка без Rust:  zig cc -O2 bench.c t5m_pack.o t5m_ref.o -o bench
   Збірка з Rust:    zig cc -O2 -DHAVE_RUST bench.c t5m_pack.o t5m_ref.o rust_t5m_ref.o -o bench
   Усі реалізації роблять те саме: 5 трітів → 1 байт (3^5=243<256), value = value*3 + trit. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

extern uint64_t sens_t5m_pack(const uint8_t *trits, size_t n, uint8_t *out);
extern void sens_t5m_unpack(const uint8_t *bytes, size_t n_groups, uint8_t *trits);
extern size_t zig_t5m_pack(const uint8_t *trits, size_t n, uint8_t *out);
extern void zig_t5m_unpack(const uint8_t *bytes, size_t n_groups, uint8_t *trits);
#ifdef HAVE_RUST
extern size_t rust_t5m_pack(const uint8_t *trits, size_t n, uint8_t *out);
extern void rust_t5m_unpack(const uint8_t *bytes, size_t n_groups, uint8_t *trits);
#endif

static size_t c_pack(const uint8_t *trits, size_t n, uint8_t *out) {
    size_t o = 0;
    for (size_t i = 0; i < n; i += 5) {
        uint32_t v = 0;
        for (size_t j = 0; j < 5; j++) v = v * 3 + trits[i + j];
        out[o] = (uint8_t)v;
        o += 1;
    }
    return o;
}

static void c_unpack(const uint8_t *bytes, size_t n_groups, uint8_t *trits) {
    for (size_t g = 0; g < n_groups; g++) {
        uint32_t v = (uint32_t)bytes[g];
        for (size_t j = 5; j-- > 0;) {
            trits[g * 5 + j] = (uint8_t)(v % 3);
            v /= 3;
        }
    }
}

static double now_s(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(void) {
    const size_t n = 5 * 200000; /* кратне 5 */
    const size_t groups = n / 5;
    uint8_t *trits = malloc(n), *pkbuf = malloc(groups), *unp = malloc(n);
    uint8_t *p1 = malloc(groups), *p2 = malloc(groups), *p3 = malloc(groups);
#ifdef HAVE_RUST
    uint8_t *p4 = malloc(groups);
#endif
    if (!trits || !pkbuf || !unp || !p1 || !p2 || !p3) return 2;

    uint64_t seed = 1;
    for (size_t i = 0; i < n; i++) {
        seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
        trits[i] = (uint8_t)((seed >> 33) % 3);
    }

    uint64_t ab = sens_t5m_pack(trits, n, p1);
    size_t zb = zig_t5m_pack(trits, n, p2);
    size_t cb = c_pack(trits, n, p3);
    printf("груп=%zu asm_байт=%llu zig_байт=%zu c_байт=%zu | pack збіг: asm/zig=%d asm/c=%d\n",
           groups, (unsigned long long)ab, zb, cb,
           memcmp(p1, p2, groups) == 0, memcmp(p1, p3, groups) == 0);
#ifdef HAVE_RUST
    size_t rb = rust_t5m_pack(trits, n, p4);
    printf("rust_байт=%zu | pack збіг: asm/rust=%d\n", rb, memcmp(p1, p4, groups) == 0);
#endif

    sens_t5m_unpack(p1, groups, unp);
    int ok_asm = memcmp(unp, trits, n) == 0;
    zig_t5m_unpack(p2, groups, unp);
    int ok_zig = memcmp(unp, trits, n) == 0;
    c_unpack(p3, groups, unp);
    int ok_c = memcmp(unp, trits, n) == 0;
    printf("unpack==трити: asm=%d zig=%d c=%d", ok_asm, ok_zig, ok_c);
#ifdef HAVE_RUST
    rust_t5m_unpack(p4, groups, unp);
    printf(" rust=%d", memcmp(unp, trits, n) == 0);
#endif
    printf("\n");

    const int reps = 200;
    double t, asm_pack, zig_pack, c_pack_t, asm_unp, zig_unp, c_unp;
#ifdef HAVE_RUST
    double rust_pack, rust_unp;
#endif

    t = now_s(); for (int r = 0; r < reps; r++) sens_t5m_pack(trits, n, pkbuf); asm_pack = (now_s() - t) / reps;
    t = now_s(); for (int r = 0; r < reps; r++) zig_t5m_pack(trits, n, pkbuf); zig_pack = (now_s() - t) / reps;
    t = now_s(); for (int r = 0; r < reps; r++) c_pack(trits, n, pkbuf);      c_pack_t = (now_s() - t) / reps;
#ifdef HAVE_RUST
    t = now_s(); for (int r = 0; r < reps; r++) rust_t5m_pack(trits, n, pkbuf); rust_pack = (now_s() - t) / reps;
#endif

    t = now_s(); for (int r = 0; r < reps; r++) sens_t5m_unpack(p1, groups, unp); asm_unp = (now_s() - t) / reps;
    t = now_s(); for (int r = 0; r < reps; r++) zig_t5m_unpack(p2, groups, unp);  zig_unp = (now_s() - t) / reps;
    t = now_s(); for (int r = 0; r < reps; r++) c_unpack(p3, groups, unp);        c_unp = (now_s() - t) / reps;
#ifdef HAVE_RUST
    t = now_s(); for (int r = 0; r < reps; r++) rust_t5m_unpack(p4, groups, unp); rust_unp = (now_s() - t) / reps;
#endif

    const double nf = (double)n;
    printf("\n%-12s %10s %14s\n", "реалізація", "мкс", "M трит/с");
    printf("%-12s %10.1f %14.1f\n", "pack asm",   asm_pack * 1e6,  nf / asm_pack / 1e6);
    printf("%-12s %10.1f %14.1f\n", "pack zig",   zig_pack * 1e6,  nf / zig_pack / 1e6);
    printf("%-12s %10.1f %14.1f\n", "pack c",     c_pack_t * 1e6,  nf / c_pack_t / 1e6);
#ifdef HAVE_RUST
    printf("%-12s %10.1f %14.1f\n", "pack rust",  rust_pack * 1e6, nf / rust_pack / 1e6);
#endif
    printf("%-12s %10.1f %14.1f\n", "unpack asm", asm_unp * 1e6,   nf / asm_unp / 1e6);
    printf("%-12s %10.1f %14.1f\n", "unpack zig", zig_unp * 1e6,   nf / zig_unp / 1e6);
    printf("%-12s %10.1f %14.1f\n", "unpack c",   c_unp * 1e6,     nf / c_unp / 1e6);
#ifdef HAVE_RUST
    printf("%-12s %10.1f %14.1f\n", "unpack rust", rust_unp * 1e6, nf / rust_unp / 1e6);
#endif
    return 0;
}
