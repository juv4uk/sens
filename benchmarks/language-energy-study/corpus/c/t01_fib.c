/* ENERGY-02 / T01: independent C workload, not a SENS semantic oracle.
 * Contract: exactly the same naive Fibonacci(n) recursion as Python/JS T01.
 * Input from frozen corpus: TASK_ID=T01-symbolic-recursion, TASK_N=12 (verify)
 * or TASK_N=24 (measure). Exactly one decimal stdout line on success.
 * Failure: nonzero exit, diagnostic on stderr only; no fake result.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint64_t fibonacci(unsigned n) {
    if (n < 2U) return n;
    return fibonacci(n - 1U) + fibonacci(n - 2U);
}

int main(void) {
    const char *task = getenv("TASK_ID");
    const char *raw = getenv("TASK_N");
    if (task == NULL || strcmp(task, "T01-symbolic-recursion") != 0 ||
        raw == NULL || *raw == '\0' || *raw == '-' || *raw == '+') {
        fputs("T01_INPUT_INVALID: require TASK_ID and unsigned TASK_N\n", stderr);
        return 2;
    }
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(raw, &end, 10);
    /* Fail closed against pathological exponential work. The frozen task
     * requests only 12 (verify) or 24 (measure). */
    if (errno != 0 || end == raw || *end != '\0' || value > 32UL) {
        fputs("T01_INPUT_INVALID: TASK_N must be an integer 0..32\n", stderr);
        return 2;
    }
    printf("%" PRIu64 "\n", fibonacci((unsigned)value));
    return 0;
}
