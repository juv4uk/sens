/* #2209 - D3/D4 dispatch mechanism benchmark.
 *
 * Same pair-tree and same six ratified selector operations are executed through:
 *   flat   : already-ready u8 identity -> one 256-slot row lookup
 *   prefix : already-ready exact D3/D4 word -> root + suffix generator
 *   direct : operation already specialized -> direct CAR/CDR chain
 *
 * The flat lane is intentionally favorable. It models the old 8-bit flat-slot
 * mechanism, not the exact historical Function8 allocation: historical rows do
 * not symmetrically cover all four D4 selectors.
 *
 * Usage:
 *   d34_dispatch <flat|prefix|direct> <repeat-d3|random-d3|repeat-d4|random-d4|mixed>
 *                <calls> <setup|full|check|count>
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int32_t car, cdr; } Node;
typedef struct {
    uint8_t op;
    uint8_t flat_id;
    uint8_t width;
    uint8_t bits;
} Call;

typedef struct { uint8_t len; uint8_t ops[2]; } Row;

#ifdef COUNT
static struct {
    uint64_t steps, lookups, bits, gens, dispatches, root_selections;
} C;
#define CNT(field, n) (C.field += (n))
#else
#define CNT(field, n) ((void)0)
#endif

static Node nodes[3];
static Row flat_table[256];

static const Call OPS[6] = {
    {0, 0, 3, 0b101},
    {1, 1, 3, 0b110},
    {2, 2, 4, 0b1010},
    {3, 3, 4, 0b1011},
    {4, 4, 4, 0b1100},
    {5, 5, 4, 0b1101},
};

static uint64_t rng_state = 0x9e3779b97f4a7c15ULL;
static uint64_t rng64(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}

static void build_tree(void) {
    nodes[0].car = 1;
    nodes[0].cdr = 2;
    nodes[1].car = -1;
    nodes[1].cdr = -2;
    nodes[2].car = -3;
    nodes[2].cdr = -4;
}

static inline int32_t step(int32_t value, uint8_t op) {
    CNT(steps, 1);
    if (value < 0) {
        fprintf(stderr, "selector domain error\n");
        exit(2);
    }
    return op ? nodes[value].cdr : nodes[value].car;
}

static void build_flat(void) {
    memset(flat_table, 0, sizeof(flat_table));
    flat_table[0] = (Row){1, {0, 0}};
    flat_table[1] = (Row){1, {1, 0}};
    flat_table[2] = (Row){2, {0, 0}};
    flat_table[3] = (Row){2, {1, 0}};
    flat_table[4] = (Row){2, {0, 1}};
    flat_table[5] = (Row){2, {1, 1}};
}

static int32_t exec_flat(const Call *call, int32_t value) {
    CNT(dispatches, 1);
    CNT(lookups, 1);
    const Row *row = &flat_table[call->flat_id];
    for (uint8_t i = 0; i < row->len; i++)
        value = step(value, row->ops[i]);
    return value;
}

static int32_t exec_prefix(const Call *call, int32_t value) {
    CNT(dispatches, 1);
    CNT(bits, call->width);
    CNT(root_selections, 1);

    if (call->width == 3) {
        if (call->bits == 0b101) return step(value, 0);
        if (call->bits == 0b110) return step(value, 1);
        fprintf(stderr, "bad D3 selector word\n");
        exit(3);
    }

    if (call->width == 4) {
        const uint8_t root = call->bits >> 1;
        const uint8_t suffix = call->bits & 1;
        if (root != 0b101 && root != 0b110) {
            fprintf(stderr, "bad D4 selector root\n");
            exit(3);
        }
        CNT(gens, 1);
        value = step(value, suffix);
        return step(value, root == 0b110);
    }

    fprintf(stderr, "unsupported selector width\n");
    exit(3);
}

static int32_t exec_direct(const Call *call, int32_t value) {
    CNT(dispatches, 1);
    switch (call->op) {
    case 0: return step(value, 0);
    case 1: return step(value, 1);
    case 2: return step(step(value, 0), 0);
    case 3: return step(step(value, 1), 0);
    case 4: return step(step(value, 0), 1);
    case 5: return step(step(value, 1), 1);
    default: fprintf(stderr, "bad direct op\n"); exit(4);
    }
}

static int32_t execute(const char *strategy, const Call *call, int32_t value) {
    if (strcmp(strategy, "flat") == 0) return exec_flat(call, value);
    if (strcmp(strategy, "prefix") == 0) return exec_prefix(call, value);
    if (strcmp(strategy, "direct") == 0) return exec_direct(call, value);
    fprintf(stderr, "unknown strategy\n");
    exit(5);
}

static uint8_t choose_op(const char *workload) {
    if (strcmp(workload, "repeat-d3") == 0) return 0;
    if (strcmp(workload, "random-d3") == 0) return (uint8_t)(rng64() & 1);
    if (strcmp(workload, "repeat-d4") == 0) return 3;
    if (strcmp(workload, "random-d4") == 0) return (uint8_t)(2 + (rng64() & 3));
    if (strcmp(workload, "mixed") == 0) return (uint8_t)(rng64() % 6);
    fprintf(stderr, "unknown workload\n");
    exit(6);
}

static Call *prepare_calls(const char *workload, long calls) {
    Call *out = malloc((size_t)calls * sizeof(Call));
    if (!out) exit(7);
    rng_state = 0x9e3779b97f4a7c15ULL;
    for (long i = 0; i < calls; i++)
        out[i] = OPS[choose_op(workload)];
    return out;
}

static int check_parity(const char *strategy) {
    int bad = 0;
    for (int i = 0; i < 6; i++) {
        int32_t expected = exec_direct(&OPS[i], 0);
        int32_t got = execute(strategy, &OPS[i], 0);
        if (got != expected) bad++;
    }
    printf("parity\t%s\tselectors=6\tmismatches=%d\n", strategy, bad);
    return bad;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: d34_dispatch <flat|prefix|direct> <workload> <calls> <setup|full|check|count>\n");
        return 1;
    }

    const char *strategy = argv[1];
    const char *workload = argv[2];
    const long calls = atol(argv[3]);
    const char *mode = argv[4];
    if (calls <= 0) return 1;

    build_tree();
    if (strcmp(strategy, "flat") == 0) build_flat();

    if (strcmp(mode, "check") == 0)
        return check_parity(strategy) != 0;

    Call *prepared = prepare_calls(workload, calls);
    int64_t checksum = 0;

    if (strcmp(mode, "setup") != 0) {
        for (long i = 0; i < calls; i++)
            checksum += execute(strategy, &prepared[i], 0);
    }

    if (strcmp(mode, "count") == 0) {
#ifdef COUNT
        const uint64_t prepared_bytes =
            strcmp(strategy, "flat") == 0 ? (uint64_t)sizeof(flat_table) : 0;
        printf("counters\t%s\t%s\tcalls=%ld\tsteps=%llu\tlookups=%llu\tbits=%llu\tgens=%llu\tdispatches=%llu\troot_selections=%llu\tprepared_bytes=%llu\n",
               strategy, workload, calls,
               (unsigned long long)C.steps,
               (unsigned long long)C.lookups,
               (unsigned long long)C.bits,
               (unsigned long long)C.gens,
               (unsigned long long)C.dispatches,
               (unsigned long long)C.root_selections,
               (unsigned long long)prepared_bytes);
#else
        fprintf(stderr, "count mode requires -DCOUNT\n");
        free(prepared);
        return 1;
#endif
    }

    printf("checksum\t%lld\n", (long long)checksum);
    free(prepared);
    return 0;
}
