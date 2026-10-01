/* #2209: 8-bit flat-slot dispatch vs ratified D3/D4 prefix dispatch on the same selector AST (research, not production).
 *
 * The six selectors of the ratified D3/D4 foundation, on one address tree:
 *   D3  101 CAR   110 CDR
 *   D4  1010 CAAR  1011 CADR  1100 CDAR  1101 CDDR        (word = root 101/110 + one suffix bit; suffix 0 = inner CAR, 1 = inner CDR;
 *                                                          the inner operation is applied first)
 * Lanes:
 *   F  u8-flat-ready      identity = an 8-bit slot; ONE flat row lookup, then execute the row's recipe (a deliberately favourable
 *                         mechanical baseline: no human-name lookup, rows prepared before the calls)
 *   P  d3d4-prefix-ready  identity = an exact-width word (width 3 or 4); the recipe is derived from the prefix law, NO descendant row
 *   D  direct-specialized compile-time CAR/CDR chains: a lower bound (a fixed loop for one selector; a minimal switch when mixed)
 *   N  null               the call loop only (draw a selector), to be subtracted
 * Usage: d34_dispatch <F|P|D|N> <selector 0..5 | mixed> <calls> <setup|full|check|count>
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int32_t car, cdr; } Node;
#ifdef COUNT
static struct { uint64_t lookups, bits, gens; } C;
#define CNT(f, n) (C.f += (n))
#else
#define CNT(f, n) ((void)0)
#endif

static Node nodes[64];
static size_t n_nodes;
static int32_t root_value;
static inline int32_t rootv(void) { return *(volatile int32_t *)&root_value; }   /* an opaque read: the compiler cannot hoist the chain out of the loop */

static int32_t build(int levels, uint32_t *leaf)
{
    if (levels == 0) return -(int32_t)(++*leaf);
    size_t me = n_nodes++;
    int32_t a = build(levels - 1, leaf), b = build(levels - 1, leaf);
    nodes[me].car = a;
    nodes[me].cdr = b;
    return (int32_t)me;
}

static inline int32_t op(int32_t v, int cdr)
{
    CNT(gens, 1);
    if (v < 0) { fprintf(stderr, "domain error\n"); exit(2); }
    return cdr ? nodes[v].cdr : nodes[v].car;
}

/* the six selectors: index, name, word (bits, width), the 8-bit slot of the flat lane */
typedef struct { const char *name; uint8_t bits, width, slot; } Sel;
static const Sel SEL[6] = {
    {"CAR", 0x5, 3, 0x05}, {"CDR", 0x6, 3, 0x06},
    {"CAAR", 0xA, 4, 0x20}, {"CADR", 0xB, 4, 0x21}, {"CDAR", 0xC, 4, 0x22}, {"CDDR", 0xD, 4, 0x23},
};

/* ---- F: flat rows ------------------------------------------------------- */
typedef struct { uint8_t len; uint8_t ops[2]; } Row;      /* ops in application order (inner first) */
static Row flat[256];

static void build_flat(void)
{
    for (int i = 0; i < 6; i++) {
        Row *r = &flat[SEL[i].slot];
        if (SEL[i].width == 3) { r->len = 1; r->ops[0] = (SEL[i].bits >> 1) & 1; }
        else { r->len = 2; r->ops[0] = SEL[i].bits & 1; r->ops[1] = (SEL[i].bits >> 2) & 1; }
    }
}

static inline int32_t exec_flat(uint8_t slot, int32_t x)
{
    CNT(lookups, 1);
    const Row *r = &flat[slot];
    for (int i = 0; i < r->len; i++) x = op(x, r->ops[i]);
    return x;
}

/* ---- P: prefix law ------------------------------------------------------ */
static inline int32_t exec_prefix(uint8_t bits, uint8_t width, int32_t x)
{
    CNT(bits, width);
    if (width == 4) x = op(x, bits & 1);                  /* suffix: the inner operation, applied first */
    return op(x, (bits >> (width == 4 ? 2 : 1)) & 1);     /* root 101 = CAR, 110 = CDR: the middle bit decides */
}

/* ---- D: direct chains --------------------------------------------------- */
static inline int32_t d_car(int32_t x) { return op(x, 0); }
static inline int32_t d_cdr(int32_t x) { return op(x, 1); }
static inline int32_t d_caar(int32_t x) { return d_car(d_car(x)); }
static inline int32_t d_cadr(int32_t x) { return d_car(d_cdr(x)); }
static inline int32_t d_cdar(int32_t x) { return d_cdr(d_car(x)); }
static inline int32_t d_cddr(int32_t x) { return d_cdr(d_cdr(x)); }

static inline int32_t exec_direct(int s, int32_t x)
{
    switch (s) {
    case 0: return d_car(x);
    case 1: return d_cdr(x);
    case 2: return d_caar(x);
    case 3: return d_cadr(x);
    case 4: return d_cdar(x);
    default: return d_cddr(x);
    }
}

/* ---- the independent oracle: the classical name ------------------------- */
static int32_t oracle(int s, int32_t x)
{
    static const char *names[6] = {"ar", "dr", "aar", "adr", "dar", "ddr"};
    const char *n = names[s];
    for (int i = (int)strlen(n) - 1; i >= 0; i--) {
        if (n[i] == 'r') continue;
        x = n[i] == 'd' ? nodes[x].cdr : nodes[x].car;
    }
    return x;
}

static uint64_t rng_state = 88172645463325252ull;
static uint64_t rng(void) { rng_state ^= rng_state << 13; rng_state ^= rng_state >> 7; rng_state ^= rng_state << 17; return rng_state; }

static inline int32_t run(char lane, int s, int32_t x)
{
    switch (lane) {
    case 'F': return exec_flat(SEL[s].slot, x);
    case 'P': return exec_prefix(SEL[s].bits, SEL[s].width, x);
    default:  return exec_direct(s, x);
    }
}

int main(int argc, char **argv)
{
    if (argc < 5) { fprintf(stderr, "usage: d34_dispatch <F|P|D|N> <0..5|mixed> <calls> <setup|full|check|count>\n"); return 1; }
    char lane = argv[1][0];
    int mixed = strcmp(argv[2], "mixed") == 0;
    int fixed = mixed ? 0 : atoi(argv[2]);
    long calls = atol(argv[3]);
    const char *mode = argv[4];

    uint32_t leaf = 0;
    root_value = build(3, &leaf);                         /* a full tree of 3 levels: every selector is defined, every leaf has an address */
    build_flat();

    if (strcmp(mode, "check") == 0) {
        long bad = 0;
        for (char l = 'F'; l != 'Q'; l = (l == 'F') ? 'P' : 'Q') {
            for (int s = 0; s < 6; s++) bad += run(l, s, root_value) != oracle(s, root_value);
        }
        for (int s = 0; s < 6; s++) bad += run('D', s, root_value) != oracle(s, root_value);
        printf("parity\tselectors=6\tlanes=F,P,D\tmismatches=%ld\n", bad);
        return bad != 0;
    }

    int32_t sum = 0;
    if (strcmp(mode, "setup") != 0) {
        if (lane == 'D' && !mixed) {
            switch (fixed) {                              /* one specialised loop per selector: no dispatch at all */
            case 0: for (long i = 0; i < calls; i++) sum += d_car(rootv()); break;
            case 1: for (long i = 0; i < calls; i++) sum += d_cdr(rootv()); break;
            case 2: for (long i = 0; i < calls; i++) sum += d_caar(rootv()); break;
            case 3: for (long i = 0; i < calls; i++) sum += d_cadr(rootv()); break;
            case 4: for (long i = 0; i < calls; i++) sum += d_cdar(rootv()); break;
            default: for (long i = 0; i < calls; i++) sum += d_cddr(rootv()); break;
            }
        } else {
            for (long i = 0; i < calls; i++) {
                int s = mixed ? (int)(rng() % 6) : fixed;
                if (lane == 'N') sum += s;
                else sum += run(lane, s, rootv());
            }
        }
    }
    if (strcmp(mode, "count") == 0) {
#ifdef COUNT
        printf("counters\t%c\t%s\tcalls=%ld\tlookups=%llu\tbits=%llu\tgens=%llu\n", lane, argv[2], calls,
               (unsigned long long)C.lookups, (unsigned long long)C.bits, (unsigned long long)C.gens);
#else
        fprintf(stderr, "build with -DCOUNT\n");
        return 1;
#endif
    }
    printf("sum\t%d\n", sum);
    return 0;
}
