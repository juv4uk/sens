/*
 * Rust-free host-side witness for the existing Zig transport ABI v2.
 * This file has no SENS semantic interpreter and must never grant callability.
 * Build/run: bash research/zig-codecs/host-c/verify.sh
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* The sole declaration source for the existing mechanical Zig ABI v2. */
#include "zig_transport_v2.h"

static int check_number(const char *id, ptrdiff_t actual, ptrdiff_t expected) {
    if (actual == expected) return 1;
    fprintf(stderr, "SENS_C_CORRIDOR_FAIL test_id=%s layer=transport expected=%td actual=%td\n",
            id, expected, actual);
    return 0;
}

static int check_bytes(const char *id, const uint8_t *actual,
                       const uint8_t *expected, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        if (actual[i] != expected[i]) {
            fprintf(stderr,
                    "SENS_C_CORRIDOR_FAIL test_id=%s layer=transport first_diff=%zu expected=%02x actual=%02x\n",
                    id, i, (unsigned)expected[i], (unsigned)actual[i]);
            return 0;
        }
    }
    return 1;
}

/* Independently exercise Zig-owned ingress in a Rust-free caller.
 * The decoded BE3 triples are physical data, not a SENS semantic verdict.
 */
static int witness_zig_decode_be3(void) {
    static const uint8_t golden_t5[] = {0x63, 0x89, 0x06, 0xa1};
    static const uint8_t golden_be3[] = {
        2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1
    };
    static const uint8_t w1[] = {1, 0, 1};
    static const uint8_t w2[] = {2, 0, 1};
    static const uint8_t w9[] = {9, 0, 1};
    static const uint8_t invalid_byte[] = {243};
    static const uint8_t overwide_word[] = {0, 0};
    static const uint8_t invalid_tail[] = {0xf2};
    uint8_t decoded[32] = {0};
    uint8_t reencoded[32] = {0};
    uint8_t sentinel[32];
    uint8_t too_small[14];
    uint8_t alias[32] = {0};
    uint8_t d1_be3[3] = {0};
    uint8_t d2_be3[3] = {0};
    uint8_t d9_be3[3] = {0};
    uint8_t d9_t5[4] = {0};

    if (!check_number("be3-ingress-golden-size",
            sens_zig_t5_decode_be3(golden_t5, sizeof golden_t5, decoded, sizeof decoded),
            (ptrdiff_t)sizeof golden_be3)) return 0;
    if (!check_bytes("be3-ingress-golden", decoded, golden_be3, sizeof golden_be3)) return 0;
    if (!check_number("be3-reencode-size",
            sens_zig_t5_encode_be3(decoded, sizeof golden_be3, reencoded, sizeof reencoded),
            (ptrdiff_t)sizeof golden_t5)) return 0;
    if (!check_bytes("be3-reencode-carrier", reencoded, golden_t5, sizeof golden_t5)) return 0;

    /* Mechanical rejection must never overwrite caller-owned output. */
    memset(decoded, 0x5a, sizeof decoded);
    memset(sentinel, 0x5a, sizeof sentinel);
    if (!check_number("be3-reject-byte243",
            sens_zig_t5_decode_be3(invalid_byte, sizeof invalid_byte, decoded, sizeof decoded),
            -1)) return 0;
    if (!check_bytes("be3-reject-byte243-unchanged", decoded, sentinel, sizeof decoded)) return 0;
    if (!check_number("be3-reject-overwidth-d10",
            sens_zig_t5_decode_be3(overwide_word, sizeof overwide_word, decoded, sizeof decoded),
            -1)) return 0;
    if (!check_bytes("be3-reject-overwidth-unchanged", decoded, sentinel, sizeof decoded)) return 0;
    if (!check_number("be3-reject-invalid-tail",
            sens_zig_t5_decode_be3(invalid_tail, sizeof invalid_tail, decoded, sizeof decoded),
            -1)) return 0;
    if (!check_bytes("be3-reject-tail-unchanged", decoded, sentinel, sizeof decoded)) return 0;

    memset(too_small, 0x5a, sizeof too_small);
    if (!check_number("be3-reject-capacity",
            sens_zig_t5_decode_be3(golden_t5, sizeof golden_t5, too_small, sizeof too_small),
            -2)) return 0;
    if (!check_bytes("be3-reject-capacity-unchanged", too_small, sentinel, sizeof too_small)) return 0;

    memcpy(alias, golden_t5, sizeof golden_t5);
    if (!check_number("be3-reject-alias",
            sens_zig_t5_decode_be3(alias, sizeof golden_t5, alias, sizeof alias), -1)) return 0;
    if (!check_bytes("be3-reject-alias-unchanged", alias, golden_t5, sizeof golden_t5)) return 0;

    if (!check_number("be3-d1-width",
            sens_zig_t5_decode_be3((const uint8_t[]){0xa1}, 1, d1_be3, sizeof d1_be3), 3)) return 0;
    if (!check_number("be3-d2-width",
            sens_zig_t5_decode_be3((const uint8_t[]){0x35}, 1, d2_be3, sizeof d2_be3), 3)) return 0;
    if (!check_bytes("be3-d1-leading-bit", d1_be3, w1, sizeof w1)) return 0;
    if (!check_bytes("be3-d2-leading-zero", d2_be3, w2, sizeof w2)) return 0;

    /* W9:000000001 remains nine bits rather than shrinking to W1. */
    if (!check_number("be3-w9-encode-size",
            sens_zig_t5_encode_be3(w9, sizeof w9, d9_t5, sizeof d9_t5), 2)) return 0;
    if (!check_number("be3-w9-decode-size",
            sens_zig_t5_decode_be3(d9_t5, 2, d9_be3, sizeof d9_be3), 3)) return 0;
    if (!check_bytes("be3-w9-leading-zeros", d9_be3, w9, sizeof w9)) return 0;
    return 1;
}

int main(void) {
    /* BE3 is a caller-owned in-process ABI. It is NOT the .sens wire. */
    static const uint8_t words[] = {
        2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1
    };
    static const uint8_t known_t5[] = {0x63, 0x89, 0x06, 0xa1};
    static const uint8_t known_f3c[] = {0xf3, 0x40, 0x60};
    static const uint8_t d1[] = {1, 0, 1};
    static const uint8_t d2[] = {2, 0, 1};
    static const uint8_t width_zero[] = {0, 0, 0};
    static const uint8_t width_ten[] = {10, 0, 1};
    static const uint8_t overwidth[] = {2, 0, 4};
    static const uint8_t bad_physical[] = {243};
    uint8_t t5[32] = {0};
    uint8_t f3c[32] = {0};
    uint8_t unpacked[32] = {0};
    uint8_t small[4] = {0xa5, 0xa5, 0xa5, 0xa5};
    uint8_t d1_t5[4] = {0};
    uint8_t d2_t5[4] = {0};
    const uint8_t unchanged[4] = {0xa5, 0xa5, 0xa5, 0xa5};

    if (!check_number("abi-v2", sens_zig_codec_abi_version(), 2)) return 1;
    if (!check_number("known-t5-size",
            sens_zig_t5_encode_be3(words, sizeof words, t5, sizeof t5), 4)) return 1;
    if (!check_bytes("known-t5-bytes", t5, known_t5, sizeof known_t5)) return 1;
    if (!check_number("validate-canonical-t5",
            sens_zig_t5_validate(t5, sizeof known_t5), 0)) return 1;
    if (!check_number("reject-out-of-range-byte",
            sens_zig_t5_validate(bad_physical, sizeof bad_physical), -1)) return 1;

    if (!check_number("small-buffer",
            sens_zig_t5_encode_be3(words, sizeof words, small, 3), -2)) return 1;
    if (!check_bytes("small-buffer-unchanged", small, unchanged, sizeof small)) return 1;
    if (!check_number("reject-truncated-triplet",
            sens_zig_t5_encode_be3(words, sizeof words - 1, t5, sizeof t5), -1)) return 1;
    if (!check_number("reject-width-zero",
            sens_zig_t5_encode_be3(width_zero, sizeof width_zero, t5, sizeof t5), -1)) return 1;
    if (!check_number("reject-width-ten-ordinary-profile",
            sens_zig_t5_encode_be3(width_ten, sizeof width_ten, t5, sizeof t5), -1)) return 1;
    if (!check_number("reject-payload-overwidth",
            sens_zig_t5_encode_be3(overwidth, sizeof overwidth, t5, sizeof t5), -1)) return 1;

    if (!check_number("d1-single-word",
            sens_zig_t5_encode_be3(d1, sizeof d1, d1_t5, sizeof d1_t5), 1)) return 1;
    if (!check_number("d2-single-word",
            sens_zig_t5_encode_be3(d2, sizeof d2, d2_t5, sizeof d2_t5), 1)) return 1;
    if (!check_number("d1-width-kept", d1_t5[0], 0xa1)) return 1;
    if (!check_number("d2-width-kept", d2_t5[0], 0x35)) return 1;
    if (!check_number("different-domain-carriers", d1_t5[0] != d2_t5[0], 1)) return 1;

    if (!check_number("f3c-pack-size",
            sens_zig_f3c_pack(known_t5, sizeof known_t5, f3c, sizeof f3c), 3)) return 1;
    if (!check_bytes("f3c-golden", f3c, known_f3c, sizeof known_f3c)) return 1;
    if (!check_number("f3c-unpack-small-buffer",
            sens_zig_f3c_unpack(f3c, sizeof known_f3c, unpacked, 3), -2)) return 1;
    if (!check_number("f3c-unpack-size",
            sens_zig_f3c_unpack(f3c, sizeof known_f3c, unpacked, sizeof unpacked), 4)) return 1;
    if (!check_bytes("f3c-recovered-t5", unpacked, known_t5, sizeof known_t5)) return 1;

    if (!witness_zig_decode_be3()) return 1;
    puts("SENS_C_CORRIDOR_PASS abi=2 host=C rust_linked=false transport=T5+F3C exact_width=true semantic_verdict=NOT_TESTED");
    return 0;
}
