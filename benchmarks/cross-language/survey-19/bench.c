#include <stdio.h>
#include <stdlib.h>

static long long fib(long long n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

static long long sieve(long long n) {
    char *comp = (char *)calloc((size_t)n + 1, 1);
    for (long long i = 2; i * i <= n; i++) {
        if (!comp[i]) {
            for (long long j = i * i; j <= n; j += i) comp[j] = 1;
        }
    }
    long long count = 0;
    for (long long k = 2; k <= n; k++) if (!comp[k]) count++;
    free(comp);
    return count;
}

static long long collatz(long long n) {
    long long total = 0;
    for (long long i = 1; i <= n; i++) {
        long long x = i;
        while (x != 1) {
            x = (x % 2 == 0) ? x / 2 : 3 * x + 1;
            total++;
        }
    }
    return total;
}

int main(int argc, char **argv) {
    long long fibN   = argc > 1 ? atoll(argv[1]) : 35;
    long long sieveN = argc > 2 ? atoll(argv[2]) : 10000000;
    long long colN   = argc > 3 ? atoll(argv[3]) : 1000000;

    printf("fib(%lld) = %lld\n", fibN, fib(fibN));
    printf("sieve(%lld) = %lld\n", sieveN, sieve(sieveN));
    printf("collatz(%lld) = %lld\n", colN, collatz(colN));
    return 0;
}
