/* T09 bit operations — C implementation for the ENERGY-02 corpus.
 *
 * Reads TASK_N and TASK_SEED from the environment (parity_check.py --run) and
 * prints exactly one line: the total popcount.
 *
 * The LCG is bit-identical to the reference on purpose: parity means both
 * languages perform the SAME work on the SAME inputs, so any difference in
 * measured time or memory cannot be blamed on a different workload.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(void) {
    const char *n_env = getenv("TASK_N");
    const char *seed_env = getenv("TASK_SEED");
    if (!n_env || !seed_env) { fprintf(stderr, "TASK_N and TASK_SEED required\n"); return 2; }
    uint64_t n = strtoull(n_env, NULL, 10);
    uint64_t x = strtoull(seed_env, NULL, 10);
    uint64_t total = 0;
    for (uint64_t i = 0; i < n; i++) {
        x = x * 6364136223846793005ULL + 1442695040888963407ULL;
        total += (uint64_t)__builtin_popcountll(x);
    }
    printf("%llu\n", (unsigned long long)total);
    return 0;
}
