/* Frozen ENERGY-02 T09, independent C11 mechanism; never a SENS semantic oracle.
 * Exact unsigned 64-bit LCG and popcount sum, zero external dependencies.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int decimal_u64(const char *text, uint64_t *value) {
    if (!text || !*text || (*text < '0' || *text > '9')) return 0;
    if (strlen(text) > 1 && *text == '0') return 0;  /* canonical digits */
    for (const char *p = text; *p; ++p) {
        if (*p < '0' || *p > '9') return 0;
    }
    errno = 0;
    char *end = NULL;
    unsigned long long parsed = strtoull(text, &end, 10);
    if (errno == ERANGE || !end || *end) return 0;
    *value = (uint64_t)parsed;
    return (unsigned long long)*value == parsed;
}

int main(void) {
    const char *task = getenv("TASK_ID");
    uint64_t n = 0, seed = 0;
    if (!task || strcmp(task, "T09-bit-operations") != 0 ||
        !decimal_u64(getenv("TASK_N"), &n) ||
        !decimal_u64(getenv("TASK_SEED"), &seed) ||
        !((n == UINT64_C(2000) && seed == UINT64_C(3)) ||
          (n == UINT64_C(1000000) && seed == UINT64_C(999)))) {
        fputs("INVALID_TASK_INPUT: only frozen T09 VERIFY or MEASURE inputs admitted\n", stderr);
        return 2;
    }

    uint64_t x = seed;
    uint64_t total = 0;
    for (uint64_t i = 0; i < n; ++i) {
        /* uint64_t arithmetic is modulo 2^64 as required by the frozen LCG. */
        x = x * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        uint64_t word = x;
        while (word != 0) {
            word &= word - UINT64_C(1);
            ++total;
        }
    }
    printf("%" PRIu64 "\n", total);
    return 0;
}
