/* ENERGY-02 / T04-sorting: independent physical C11 implementation.
 *
 * Frozen functional unit: produce N unsigned 64-bit LCG words, numerically
 * sort them, then SHA-256 the comma-separated decimal representation.
 * Identical to parity_check.py::ref_T04 and corpus/javascript/t04_sort.mjs.
 *
 * OpenSSL EVP is a byte-hash mechanism, not a SENS semantic oracle.
 * Compile: cc -std=c11 -O2 -Wall -Wextra -Werror t04_sort.c -lcrypto -o t04_sort
 *
 * Verification and measurement sizes are distinct, declared in manifest.json.
 * No timing, RAPL, or energy values are fabricated by this program.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>

#define MAX_WORDS UINT64_C(1000000)
#define LCG_MUL UINT64_C(6364136223846793005)
#define LCG_ADD UINT64_C(1442695040888963407)

static int parse_u64(const char *raw, uint64_t *out) {
    if (raw == NULL || *raw == '\0') return 0;
    for (const unsigned char *p = (const unsigned char *)raw; *p; ++p) {
        if (*p < '0' || *p > '9') return 0;
    }
    errno = 0;
    char *end = NULL;
    unsigned long long value = strtoull(raw, &end, 10);
    if (errno == ERANGE || end == raw || *end != '\0') return 0;
    if (value > UINT64_MAX) return 0;
    *out = (uint64_t)value;
    return 1;
}

static int compare_u64(const void *a, const void *b) {
    const uint64_t x = *(const uint64_t *)a;
    const uint64_t y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

int main(void) {
    const char *task = getenv("TASK_ID");
    uint64_t n, seed;
    if (task == NULL || strcmp(task, "T04-sorting") != 0 ||
        !parse_u64(getenv("TASK_N"), &n) ||
        !parse_u64(getenv("TASK_SEED"), &seed) ||
        n == 0 || n > MAX_WORDS) {
        fputs("T04_INPUT_INVALID: expected TASK_ID=T04-sorting, "
              "1<=TASK_N<=1000000, unsigned decimal TASK_SEED\n", stderr);
        return 2;
    }
    if (n > SIZE_MAX / sizeof(uint64_t)) {
        fputs("T04_INPUT_INVALID: allocation overflow\n", stderr);
        return 2;
    }
    uint64_t *values = malloc((size_t)n * sizeof(*values));
    if (values == NULL) {
        fputs("T04_RESOURCE_UNAVAILABLE: allocation failed\n", stderr);
        return 3;
    }

    uint64_t x = seed;
    for (uint64_t i = 0; i < n; ++i) {
        /* uint64_t multiplication is defined modulo 2^64. */
        x = x * LCG_MUL + LCG_ADD;
        values[i] = x;
    }
    qsort(values, (size_t)n, sizeof(*values), compare_u64);

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int digest_len = 0;
    int valid = (ctx != NULL && EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) == 1);
    for (uint64_t i = 0; valid && i < n; ++i) {
        char word[32]; /* 20 digits for uint64_t + terminating NUL. */
        int size = snprintf(word, sizeof(word), "%" PRIu64, values[i]);
        if (size < 1 || (size_t)size >= sizeof(word)) {
            valid = 0;
            break;
        }
        if (i && EVP_DigestUpdate(ctx, ",", 1) != 1) valid = 0;
        if (valid && EVP_DigestUpdate(ctx, word, (size_t)size) != 1) valid = 0;
    }
    if (valid) valid = (EVP_DigestFinal_ex(ctx, digest, &digest_len) == 1);
    EVP_MD_CTX_free(ctx);
    free(values);
    if (!valid || digest_len != 32) {
        fputs("T04_HASH_FAILURE\n", stderr);
        return 3;
    }

    for (unsigned int i = 0; i < digest_len; ++i) printf("%02x", digest[i]);
    putchar('\n');
    return 0;
}
