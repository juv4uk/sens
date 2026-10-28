/*
 * ENERGY-02 / T03 frozen corpus: genuinely construct and parse key=value rows,
 * retain duplicate keys, lexicographically sort, hash newline-joined keys.
 *
 * Build: cc -std=c11 -O2 -Wall -Wextra -Werror t03_parse.c -lcrypto -o t03_parse
 * Inputs: TASK_ID=T03-parsing-text TASK_LINES=50 (verify) or 5000 (measure).
 * Output: one lower-case SHA-256 hex digest + newline, no hidden timing.
 * This is a standalone physical workload, NOT a SENS semantic oracle.
 */
#include <errno.h>
#include <openssl/evp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_lines(size_t *count) {
    const char *id = getenv("TASK_ID");
    const char *s = getenv("TASK_LINES");
    if (!id || strcmp(id, "T03-parsing-text") || !s || !*s || *s == '-') {
        return -1;
    }
    for (const char *p = s; *p; ++p) {
        if (*p < '0' || *p > '9') return -1;
    }
    errno = 0;
    char *end = NULL;
    unsigned long long value = strtoull(s, &end, 10);
    if (errno || !end || *end || value < 1 || value > 1000000ULL) return -1;
    *count = (size_t)value;
    return *count == 0 ? -1 : 0;
}

static int compare_keys(const void *a, const void *b) {
    const char *const *ka = a;
    const char *const *kb = b;
    return strcmp(*ka, *kb);
}

int main(void) {
    size_t count = 0;
    if (parse_lines(&count)) {
        fputs("T03_INPUT_INVALID: require TASK_ID=T03-parsing-text and TASK_LINES=1..1000000\n", stderr);
        return 2;
    }

    char **keys = calloc(count, sizeof(*keys));
    if (!keys) {
        fputs("T03_ALLOCATION_FAILED\n", stderr);
        return 3;
    }

    int exit_code = 3;
    EVP_MD_CTX *ctx = NULL;
    for (size_t i = 0; i < count; ++i) {
        /* The frozen reference constructs 'k{(i*7919)%1000}=v{i}' rows. */
        char row[64];
        int length = snprintf(row, sizeof(row), "k%zu=v%zu", (i * 7919u) % 1000u, i);
        if (length < 0 || (size_t)length >= sizeof(row)) goto cleanup;
        char *allocated = malloc((size_t)length + 1);
        if (!allocated) goto cleanup;
        memcpy(allocated, row, (size_t)length + 1);

        /* Parse a REAL row at the first '='; do not hash a generated key
         * before parsing, even if a competitor currently takes that shortcut. */
        char *equals = strchr(allocated, '=');
        if (!equals || equals == allocated || !equals[1]) {
            free(allocated);
            goto cleanup;
        }
        *equals = '\0';
        keys[i] = allocated;
    }
    qsort(keys, count, sizeof(*keys), compare_keys);

    ctx = EVP_MD_CTX_new();
    if (!ctx || EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) goto cleanup;
    for (size_t i = 0; i < count; ++i) {
        if (i > 0 && EVP_DigestUpdate(ctx, "\n", 1) != 1) goto cleanup;
        if (EVP_DigestUpdate(ctx, keys[i], strlen(keys[i])) != 1) goto cleanup;
    }
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int digest_len = 0;
    if (EVP_DigestFinal_ex(ctx, digest, &digest_len) != 1 || digest_len != 32) goto cleanup;
    for (unsigned int i = 0; i < digest_len; ++i) printf("%02x", digest[i]);
    putchar('\n');
    exit_code = 0;

cleanup:
    if (exit_code != 0) fputs("T03_EXECUTION_FAILED\n", stderr);
    EVP_MD_CTX_free(ctx);
    for (size_t i = 0; i < count; ++i) free(keys[i]);
    free(keys);
    return exit_code;
}
