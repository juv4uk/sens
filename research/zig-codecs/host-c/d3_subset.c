/* A Rust-free, deliberately SMALL independent SENS executor witness.
 * The only ingress for executable words is Zig ABI v2 T5 -> BE3.
 * This is a conformance implementation, never SENS semantic authority.
 * Supported closed forms: D1 predicate/atom data, D3 EMPTY, QUOTE, ATOM,
 * EQ (atom operands), CAR (quoted nonempty list), and two-field COND.
 * Unsupported calls and malformed D2 fail; D11 has no physical admission.
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* One Zig mechanical ABI v2 contract shared with the corridor smoke host. */
#include "zig_transport_v2.h"

#define MAX_WORDS 512
#define MAX_CHILDREN 16
#define MAX_BYTES 4096

typedef struct { uint8_t width; uint16_t bits; } Word;
typedef struct Node {
    int list, count;
    Word atom;
    struct Node *items[MAX_CHILDREN];
} Node;
typedef struct {
    Node pool[MAX_WORDS];
    size_t used, pos, len;
    Word words[MAX_WORDS];
    const char *error;
} Machine;
typedef struct { int kind; Word atom; const Node *list; } Value;
/* Value.kind: 0 atom, 1 nonempty list datum, 2 structural EMPTY. */
static const char *failure;
static Value v_atom(Word a) { Value v = {0, a, NULL}; return v; }
static Value v_empty(void) { Value v = {2, {3, 0}, NULL}; return v; }
static Value v_list(const Node *a) { Value v = {1, {0, 0}, a}; return v; }
static Value quoted(const Node *n) {
    if (n->list) return n->count ? v_list(n) : v_empty();
    if (n->atom.width == 3 && n->atom.bits == 0) return v_empty();
    return v_atom(n->atom);
}
static int is(Word w, unsigned width, unsigned bits) {
    return w.width == width && w.bits == bits;
}
static Node *node(Machine *m) {
    if (m->used >= MAX_WORDS) { m->error = "RESOURCE_LIMIT"; return NULL; }
    Node *n = &m->pool[m->used++];
    memset(n, 0, sizeof(*n));
    return n;
}
static Node *parse(Machine *m, unsigned depth) {
    if (depth > 32 || m->pos >= m->len) { m->error = "MALFORMED_D2"; return NULL; }
    Word w = m->words[m->pos++];
    Node *n = node(m);
    if (!n) return NULL;
    if (!is(w, 2, 2)) {
        if (w.width == 2) { m->error = "MALFORMED_D2"; return NULL; }
        n->atom = w;
        return n;
    }
    n->list = 1;
    int expect_value = 1;
    for (;;) {
        if (m->pos >= m->len) { m->error = "MALFORMED_D2"; return NULL; }
        w = m->words[m->pos];
        if (is(w, 2, 1)) {
            if (expect_value && n->count) { m->error = "MALFORMED_D2"; return NULL; }
            ++m->pos;
            return n;
        }
        if (!expect_value) {
            if (!is(w, 2, 0)) { m->error = "MALFORMED_D2"; return NULL; }
            ++m->pos;
            expect_value = 1;
            continue;
        }
        if (n->count >= MAX_CHILDREN || is(w, 2, 0) || is(w, 2, 3)) {
            m->error = "UNSUPPORTED_D2_FORM"; return NULL;
        }
        Node *child = parse(m, depth + 1);
        if (!child) return NULL;
        n->items[n->count++] = child;
        expect_value = 0;
    }
}
static int ev(const Node *n, Value *out, unsigned depth) {
    if (depth > 32) { failure = "RESOURCE_LIMIT"; return 0; }
    if (!n->list) { *out = quoted(n); return 1; }
    if (n->count == 0) { *out = v_empty(); return 1; }
    const Node *h = n->items[0];
    if (h->list || h->atom.width != 3) { failure = "NONCALLABLE_HEAD"; return 0; }
    const Word op = h->atom;
    if (is(op, 3, 1)) { /* QUOTE: inert data; no recursive evaluation. */
        if (n->count != 2) { failure = "ARITY"; return 0; }
        *out = quoted(n->items[1]); return 1;
    }
    if (is(op, 3, 2)) { /* ATOM: actual pair => D1 NO, atom/empty => YES. */
        Value v;
        if (n->count != 2) { failure = "ARITY"; return 0; }
        if (!ev(n->items[1], &v, depth + 1)) return 0;
        *out = v_atom((Word){1, (uint16_t)(v.kind != 1)}); return 1;
    }
    if (is(op, 3, 5)) { /* EQ: only admissible atoms, never host pointer equality. */
        Value a, b;
        if (n->count != 3) { failure = "ARITY"; return 0; }
        if (!ev(n->items[1], &a, depth + 1) || !ev(n->items[2], &b, depth + 1)) return 0;
        if (a.kind == 1 || b.kind == 1) { *out = v_empty(); return 1; }
        *out = v_atom((Word){1, (uint16_t)(a.kind == b.kind && a.atom.width == b.atom.width && a.atom.bits == b.atom.bits)});
        return 1;
    }
    if (is(op, 3, 4)) { /* CAR: only a nonempty pair datum. */
        Value v;
        if (n->count != 2) { failure = "ARITY"; return 0; }
        if (!ev(n->items[1], &v, depth + 1)) return 0;
        if (v.kind != 1 || !v.list->count) { failure = "DOMAIN_ERROR"; return 0; }
        *out = quoted(v.list->items[0]); return 1;
    }
    if (is(op, 3, 6)) { /* COND: each clause strictly (test expression). */
        for (int i = 1; i < n->count; ++i) {
            const Node *clause = n->items[i];
            Value test;
            if (!clause->list || clause->count != 2) { failure = "COND_SHAPE"; return 0; }
            if (!ev(clause->items[0], &test, depth + 1)) return 0;
            if (test.kind == 2 || (test.kind == 0 && is(test.atom, 1, 0))) continue;
            if (test.kind != 0 || !is(test.atom, 1, 1)) { failure = "NON_D1_CONTROL"; return 0; }
            return ev(clause->items[1], out, depth + 1);
        }
        *out = v_empty(); return 1;
    }
    failure = "UNSUPPORTED_D3_CALL";
    return 0;
}
static int source(const char *path, uint8_t *be3, size_t *length) {
    FILE *f = fopen(path, "rb");
    if (!f) { failure = "SOURCE_OPEN"; return 0; }
    size_t count = 0;
    int c, in_word = 0;
    unsigned width = 0, value = 0;
    while ((c = fgetc(f)) != EOF) {
        if (c == '0' || c == '1') {
            in_word = 1;
            if (++width > 9) { failure = "WORD_WIDTH"; break; }
            value = (value << 1) | (unsigned)(c - '0');
        } else if (c == ' ' || c == '\n' || c == '\r' || c == '\t') {
            if (in_word) {
                if (count >= MAX_WORDS) { failure = "RESOURCE_LIMIT"; break; }
                be3[3 * count] = (uint8_t)width;
                be3[3 * count + 1] = (uint8_t)(value >> 8);
                be3[3 * count + 2] = (uint8_t)value;
                ++count; in_word = 0; width = value = 0;
            }
        } else { failure = "NON_BINARY_SOURCE"; break; }
    }
    if (!failure && in_word && count >= MAX_WORDS) failure = "RESOURCE_LIMIT";
    if (!failure && in_word) {
        be3[3 * count] = (uint8_t)width;
        be3[3 * count + 1] = (uint8_t)(value >> 8);
        be3[3 * count + 2] = (uint8_t)value;
        ++count;
    }
    if (!failure && !count) failure = "EMPTY_SOURCE";
    if (ferror(f) && !failure) failure = "SOURCE_READ";
    fclose(f);
    *length = 3 * count;
    return !failure;
}
static int execute(const char *path, const char *expected) {
    uint8_t be3[3 * MAX_WORDS], restored[3 * MAX_WORDS], physical[MAX_BYTES];
    size_t count = 0;
    Machine m = {0};
    Value got;
    failure = NULL;
    if (!source(path, be3, &count)) goto fail;
    ptrdiff_t size = sens_zig_t5_encode_be3(be3, count, physical, sizeof physical);
    if (size <= 0 || sens_zig_t5_validate(physical, (size_t)size) != 0) {
        failure = "ZIG_PHYSICAL_REJECT"; goto fail;
    }
    /* Physical T5 receipt from the actual Zig encoder, never a verdict. */
    printf("C_D3_SUBSET_T5 source=%s bytes=%td hex=", path, size);
    for (ptrdiff_t i = 0; i < size; ++i) printf("%02x", (unsigned)physical[i]);
    putchar('\n');
    ptrdiff_t decoded = sens_zig_t5_decode_be3(physical, (size_t)size, restored, sizeof restored);
    if (decoded < 0 || (size_t)decoded != count || memcmp(be3, restored, count)) {
        failure = "ZIG_BE3_MISMATCH"; goto fail;
    }
    m.len = count / 3;
    for (size_t i = 0; i < m.len; ++i) {
        m.words[i] = (Word){restored[3 * i], (uint16_t)((unsigned)restored[3 * i + 1] << 8 | restored[3 * i + 2])};
        if (m.words[i].width == 0 || m.words[i].width > 9 || m.words[i].bits >= (1u << m.words[i].width)) {
            failure = "WIDTH_MISMATCH"; goto fail;
        }
    }
    Node *root = parse(&m, 0);
    if (!root) { failure = m.error; goto fail; }
    if (m.pos != m.len) { failure = "EXTRA_TOP_LEVEL"; goto fail; }
    if (!ev(root, &got, 0)) goto fail;
    if (strcmp(expected, "YES") || got.kind != 0 || !is(got.atom, 1, 1)) {
        failure = "UNEXPECTED_VERDICT"; goto fail;
    }
    printf("C_D3_SUBSET_PASS source=%s physical_bytes=%td exact_be3_bytes=%zu result=D1:1\n", path, size, count);
    return 1;
fail:
    if (failure && strcmp(expected, "NONCALLABLE_HEAD") == 0 && strcmp(failure, expected) == 0) {
        printf("C_D3_SUBSET_NEGATIVE_PASS source=%s category=%s\n", path, failure);
        return 1;
    }
    fprintf(stderr, "C_D3_SUBSET_FAIL source=%s expected=%s actual=%s layer=%s\n",
            path, expected, failure ? failure : "UNKNOWN", (!failure || strncmp(failure, "ZIG_", 4)) ? "eval" : "transport");
    return 0;
}
static int one_bit_pair(const char *positive, const char *mutant) {
    uint8_t a[3 * MAX_WORDS], b[3 * MAX_WORDS];
    size_t alen = 0, blen = 0, changes = 0;
    failure = NULL;
    if (!source(positive, a, &alen)) return 0;
    failure = NULL;
    if (!source(mutant, b, &blen) || alen != blen) return 0;
    for (size_t i = 0; i < alen; i += 3) {
        if (a[i] != b[i]) return 0; /* width MUST stay exact */
        unsigned diff = ((unsigned)(a[i + 1] ^ b[i + 1]) << 8)
                      | (unsigned)(a[i + 2] ^ b[i + 2]);
        while (diff) { changes += diff & 1u; diff >>= 1; }
    }
    if (changes != 1) {
        fprintf(stderr, "C_D3_SUBSET_FAIL layer=source expected=one-bit actual=%zu\n", changes);
        return 0;
    }
    printf("C_D3_SUBSET_MUTATION_PASS source=%s mutant=%s exact_changed_bits=1\n", positive, mutant);
    return 1;
}
int main(int argc, char **argv) {
    static const char *const cases[][2] = {
        {"tests/semantic/retired-d3-cond-law.bits", "YES"},
        {"tests/semantic/retired-d3-cond-mutant.bits", "NONCALLABLE_HEAD"},
        {"tests/semantic/retired-d3-eq-law.bits", "YES"},
        {"tests/semantic/retired-d3-eq-mutant.bits", "NONCALLABLE_HEAD"},
        {"tests/semantic/retired-quote-inert-d3-law.bits", "YES"},
        {"tests/semantic/retired-quote-inert-d3-mutant.bits", "NONCALLABLE_HEAD"}
    };
    if (argc != 1) { fprintf(stderr, "usage: %s (run from repository root)\n", argv[0]); return 2; }
    if (sens_zig_codec_abi_version() != 2) {
        fputs("C_D3_SUBSET_FAIL layer=transport category=BAD_ABI_VERSION\n", stderr); return 2;
    }
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
        if (!execute(cases[i][0], cases[i][1])) return 1;
    }
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i += 2) {
        if (!one_bit_pair(cases[i][0], cases[i + 1][0])) return 1;
    }
    puts("C_D3_SUBSET_SOURCE_WITNESS_PASS tests=6 host=C rust_linked=false semantic_scope=D1+D2+D3 cross_host_parity=NOT_VERIFIED");
    return 0;
}
