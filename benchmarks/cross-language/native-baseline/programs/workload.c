#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    uint64_t n = argc > 1 ? strtoull(argv[1], NULL, 10) : 200000;
    uint64_t acc = 0;
    for (uint64_t i = 0; i <= n; ++i) acc += i * i;
    printf("%llu\n", (unsigned long long)acc);
    return 0;
}
