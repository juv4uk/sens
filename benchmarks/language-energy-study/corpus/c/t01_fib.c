/* T01 naive Fibonacci — C implementation for the ENERGY-02 corpus. */
#include <stdio.h>
#include <stdlib.h>

static unsigned long long fib(int k) { return k < 2 ? (unsigned long long)k : fib(k-1) + fib(k-2); }

int main(void) {
    const char *n_env = getenv("TASK_N");
    if (!n_env) { fprintf(stderr, "TASK_N required\n"); return 2; }
    printf("%llu\n", fib(atoi(n_env)));
    return 0;
}
