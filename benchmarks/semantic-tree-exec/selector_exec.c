/* #1988: root + suffix execution cost harness (research, not production).
 *
 * The proven selector family of #1975: root 101 = CAR, 110 = CDR; a suffix bit 0 adds CAR, 1 adds CDR;
 * the operations are stored outer -> inner and applied inner -> outer, so word 1011 = CAR(CDR(x)) = CADR.
 *
 * Strategies (the candidates of #1988):
 *   A  flat lookup: one precomputed row per descendant word (the row-per-name registry); build cost is
 *      PREPARATION and is counted in the setup phase, never hidden
 *   B  root + suffix, interpreted on every call (decode the bits, apply, no state kept)
 *   C  root + suffix with a decoded-path cache (direct-mapped): miss = decode + store, hit = reuse
 *   D  hybrid: flat rows for suffix length <= 2, interpreter above
 *
 * Usage:  selector_exec <A|B|C|D> <k> <calls> <repeat|random> <mode>
 *   mode  setup   build everything, make no calls            (the "ready" baseline)
 *         full    setup + all calls                           (full - setup = the calls)
 *         check   parity of every word up to length k against an independent c[ad]+r oracle, no timing
 *         count   full run with the mechanical counters, printed as one TSV line (built with -DCOUNT)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int32_t car, cdr; } Node;                 /* value >= 0: node index; value < 0: leaf -(id+1) */
typedef struct { uint8_t root; uint8_t k; uint32_t suffix; } Word;  /* root 0 = CAR, 1 = CDR; suffix has k bits, MSB = outermost */

#ifdef COUNT
static struct { uint64_t bits, gens, edges, lookups, hits, misses, allocs, alloc_bytes; } C;
#define CNT(f, n) (C.f += (n))
#else
#define CNT(f, n) ((void)0)
#endif

static Node *nodes;
static int32_t root_value;
static size_t n_nodes;

static int32_t build(int levels, uint32_t *next_leaf)
{
    if (levels == 0) return -(int32_t)(++*next_leaf);
    size_t me = n_nodes++;
    int32_t a = build(levels - 1, next_leaf);
    int32_t b = build(levels - 1, next_leaf);
    nodes[me].car = a;
    nodes[me].cdr = b;
    return (int32_t)me;
}

static inline int32_t step(int32_t v, int op)
{
    CNT(gens, 1);
    CNT(edges, 1);
    if (v < 0) { fprintf(stderr, "domain error\n"); exit(2); }
    return op ? nodes[v].cdr : nodes[v].car;
}

/* ---- B: interpreter ---------------------------------------------------- */
static int32_t exec_b(const Word *w, int32_t x)
{
    CNT(bits, 3 + w->k);
    for (int i = 0; i < w->k; i++)                          /* suffix, innermost (last bit) first */
        x = step(x, (w->suffix >> i) & 1);
    return step(x, w->root);
}

/* ---- A: flat rows ------------------------------------------------------ */
typedef struct { uint8_t len; uint8_t ops[24]; } Row;       /* ops in application order (inner -> outer) */
static Row *flat;
static int flat_kmax;
static size_t flat_rows;

static inline size_t flat_index(const Word *w) { return ((size_t)w->root << (flat_kmax + 1)) + ((size_t)1u << w->k) + w->suffix; }

static void build_flat(int kmax)
{
    flat_kmax = kmax;
    size_t per_root = (size_t)1 << (kmax + 1);
    flat = calloc(2 * per_root, sizeof(Row));
    CNT(allocs, 1);
    CNT(alloc_bytes, 2 * per_root * sizeof(Row));
    for (int r = 0; r < 2; r++)
        for (int k = 0; k <= kmax; k++)
            for (uint32_t s = 0; s < (1u << k); s++) {
                Word w = { (uint8_t)r, (uint8_t)k, s };
                Row *row = &flat[flat_index(&w)];
                int n = 0;
                for (int i = 0; i < k; i++) row->ops[n++] = (s >> i) & 1;
                row->ops[n++] = (uint8_t)r;
                row->len = (uint8_t)n;
                flat_rows++;
            }
}

static int32_t exec_a(const Word *w, int32_t x)
{
    CNT(lookups, 1);
    const Row *row = &flat[flat_index(w)];
    for (int i = 0; i < row->len; i++) x = step(x, row->ops[i]);
    return x;
}

/* ---- C: decoded-path cache (direct mapped) ----------------------------- */
#define CACHE_SLOTS 1024
typedef struct { int valid; Word w; Row row; } Slot;
static Slot cache[CACHE_SLOTS];

static inline unsigned slot_of(const Word *w)
{
    uint32_t h = (uint32_t)w->suffix * 2654435761u ^ ((uint32_t)w->k << 7) ^ ((uint32_t)w->root << 13);
    return (h >> 8) & (CACHE_SLOTS - 1);
}

static int32_t exec_c(const Word *w, int32_t x)
{
    Slot *s = &cache[slot_of(w)];
    if (s->valid && s->w.root == w->root && s->w.k == w->k && s->w.suffix == w->suffix) {
        CNT(hits, 1);
    } else {
        CNT(misses, 1);
        CNT(bits, 3 + w->k);
        s->valid = 1;
        s->w = *w;
        int n = 0;
        for (int i = 0; i < w->k; i++) s->row.ops[n++] = (w->suffix >> i) & 1;
        s->row.ops[n++] = w->root;
        s->row.len = (uint8_t)n;
    }
    for (int i = 0; i < s->row.len; i++) x = step(x, s->row.ops[i]);
    return x;
}

/* ---- D: hybrid ---------------------------------------------------------- */
static int32_t exec_d(const Word *w, int32_t x) { return w->k <= 2 ? exec_a(w, x) : exec_b(w, x); }

static int32_t run(char strategy, const Word *w, int32_t x)
{
    switch (strategy) {
    case 'A': return exec_a(w, x);
    case 'B': return exec_b(w, x);
    case 'C': return exec_c(w, x);
    default:  return exec_d(w, x);
    }
}

/* ---- the independent oracle: the classical name c L1 ... Lk r ----------- */
static int32_t oracle(const Word *w, int32_t x)
{
    char name[40];
    int n = 0;
    name[n++] = w->root ? 'd' : 'a';                         /* L1 = the root */
    for (int i = w->k - 1; i >= 0; i--) name[n++] = ((w->suffix >> i) & 1) ? 'd' : 'a';   /* L2.. outer -> inner */
    for (int i = n - 1; i >= 0; i--) x = name[i] == 'd' ? nodes[x].cdr : nodes[x].car;     /* last letter first */
    return x;
}

static uint64_t rng_state = 88172645463325252ull;
static uint64_t rng(void) { rng_state ^= rng_state << 13; rng_state ^= rng_state >> 7; rng_state ^= rng_state << 17; return rng_state; }

int main(int argc, char **argv)
{
    if (argc < 6) { fprintf(stderr, "usage: selector_exec <A|B|C|D> <k> <calls> <repeat|random> <setup|full|check|count>\n"); return 1; }
    char strategy = argv[1][0];
    int k = atoi(argv[2]);
    long calls = atol(argv[3]);
    int repeat = strcmp(argv[4], "repeat") == 0;
    const char *mode = argv[5];
    if (k < 0 || k > 16) return 1;

    /* the tree: a full binary tree of k+1 levels, every leaf has its own id (an "address" tree: any wrong path is visible) */
    int levels = k + 1;
    size_t internal = ((size_t)1 << levels) - 1;
    nodes = malloc(internal * sizeof(Node));
    CNT(allocs, 1);
    CNT(alloc_bytes, internal * sizeof(Node));
    uint32_t leaf = 0;
    root_value = build(levels, &leaf);

    if (strategy == 'A' || strategy == 'D') build_flat(strategy == 'D' ? 2 : k);

    Word fixed = { (uint8_t)(rng() & 1), (uint8_t)k, k ? (uint32_t)(rng() & ((1u << k) - 1)) : 0 };

    if (strcmp(mode, "check") == 0) {
        long checked = 0, bad = 0;
        for (int r = 0; r < 2; r++)
            for (int kk = 0; kk <= k; kk++)
                for (uint32_t s = 0; s < (1u << kk); s++) {
                    Word w = { (uint8_t)r, (uint8_t)kk, s };
                    if (strategy == 'A' && kk > flat_kmax) continue;
                    checked++;
                    if (run(strategy, &w, root_value) != oracle(&w, root_value)) bad++;
                }
        printf("parity\t%c\tk<=%d\twords=%ld\tmismatches=%ld\n", strategy, k, checked, bad);
        return bad != 0;
    }

    int32_t sum = 0;
    if (strcmp(mode, "setup") != 0) {
        for (long i = 0; i < calls; i++) {
            Word w = fixed;
            if (!repeat) { w.root = (uint8_t)(rng() & 1); w.suffix = k ? (uint32_t)(rng() & ((1u << k) - 1)) : 0; }
            sum += run(strategy, &w, root_value);
        }
    }
    if (strcmp(mode, "count") == 0) {
#ifdef COUNT
        printf("counters\t%c\t%d\t%s\tcalls=%ld\tbits=%llu\tgens=%llu\tedges=%llu\tlookups=%llu\thits=%llu\tmisses=%llu\tallocs=%llu\talloc_bytes=%llu\n",
               strategy, k, argv[4], calls, (unsigned long long)C.bits, (unsigned long long)C.gens, (unsigned long long)C.edges,
               (unsigned long long)C.lookups, (unsigned long long)C.hits, (unsigned long long)C.misses,
               (unsigned long long)C.allocs, (unsigned long long)C.alloc_bytes);
#else
        fprintf(stderr, "build with -DCOUNT for the count mode\n");
        return 1;
#endif
    }
    printf("sum\t%d\n", sum);                               /* keeps the calls alive and gives a cross-strategy checksum */
    return 0;
}
