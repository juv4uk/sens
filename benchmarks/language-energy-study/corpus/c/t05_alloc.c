/*
 * ENERGY-02 / T05: C implementation of the frozen allocation/GC workload.
 * Standalone process, no SENS semantic authority.
 *
 * Required environment: TASK_ID=T05-allocation-gc, TASK_N, TASK_K.
 * Contract: create and discard N short-lived arrays of K integers initialized
 * with 0..K-1; stdout is the exact sum of their lengths (one line).
 *
 * The volatile address publication makes malloc's returned pointer observable
 * to the abstract machine, preventing an optimizer from proving all allocations
 * dead merely because the final output is N*K. Volatile element writes also
 * preserve the specified initialization in optimized builds. This does NOT
 * guarantee equal allocator/GC costs across C, Python, or JavaScript.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *volatile published_allocation;

static int read_positive_size(const char *key, size_t limit, size_t *out) {
    const char *text = getenv(key);
    if (text == NULL || *text == '\0') return 0;
    for (const char *p = text; *p != '\0'; ++p) {
        if (*p < '0' || *p > '9') return 0;
    }
    errno = 0;
    char *end = NULL;
    uintmax_t parsed = strtoumax(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || parsed == 0 || parsed > limit) {
        return 0;
    }
    *out = (size_t)parsed;
    return 1;
}

int main(void) {
    const char *task = getenv("TASK_ID");
    size_t n, k;
    if (task == NULL || strcmp(task, "T05-allocation-gc") != 0 ||
        !read_positive_size("TASK_N", 1000000, &n) ||
        !read_positive_size("TASK_K", 4096, &k) ||
        k > SIZE_MAX / sizeof(uint32_t) || n > UINT64_MAX / k ||
        n > 50000000 / k) {
        fputs("T05_INVALID_INPUT: TASK_ID, TASK_N, TASK_K, or physical work limit\n", stderr);
        return 2;
    }

    uint64_t total = 0;
    for (size_t i = 0; i < n; ++i) {
        uint32_t *allocation = malloc(k * sizeof(*allocation));
        if (allocation == NULL) {
            fputs("T05_ALLOCATION_FAILED\n", stderr);
            return 3;
        }
        /* Volatile element writes keep the specified initialization in -O2
         * builds; publishing the address separately keeps the allocation
         * itself observable until it is freed. */
        volatile uint32_t *items = allocation;
        published_allocation = allocation;
        for (size_t j = 0; j < k; ++j) items[j] = (uint32_t)j;
        total += (uint64_t)k;
        free(allocation);
        published_allocation = NULL;
    }
    printf("%" PRIu64 "\n", total);
    return 0;
}
