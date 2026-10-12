#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint64_t tree(uint32_t depth, uint64_t seed) {
    if (depth == 0) return seed;
    uint64_t left = tree(depth - 1, seed * 3 + 1);
    uint64_t right = tree(depth - 1, seed * 3 + 2);
    return left ^ (right + depth);
}

int main(int argc, char **argv) {
    uint32_t depth = argc > 1 ? (uint32_t)strtoul(argv[1], NULL, 10) : 18;
    printf("%llu\n", (unsigned long long)tree(depth, 1));
    return 0;
}
