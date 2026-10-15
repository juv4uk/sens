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

/* Rust-free second client of the SAME Zig E1 physical export.
 * This confirms ABI layout, canonical framing and negative error contracts
 * without treating Zig transport as SENS execution or mathematical truth.
 */
static int witness_zig_e1_encode_be3(void) {
    static const uint8_t source[] = {2, 0, 2, 3, 0, 1, 2, 0, 1};
    static const uint8_t golden[] = {
        0x53, 0x33, 1, 3, 0, 3, 0x23, 0x20,
        0x8a, 0x36, 0x20, 0x5d, 0x52
    };
    static const uint8_t invalid_width[] = {10, 0, 0};
    static const uint8_t invalid_bits[] = {2, 0, 4};
    uint8_t output[64] = {0};
    uint8_t too_small[8];
    uint8_t unchanged[8];
    uint8_t aliased[32] = {0};
    memset(too_small, 0x72, sizeof too_small);
    memset(unchanged, 0x72, sizeof unchanged);

    if (!check_number("e1-canonical-size",
            sens_zig_e1_encode_be3(source, sizeof source, output, sizeof output),
            (ptrdiff_t)sizeof golden)) return 0;
    if (!check_bytes("e1-canonical-raw-crc", output, golden, sizeof golden)) return 0;
    uint8_t restored[32];
    memset(restored, 0x37, sizeof restored);
    if (!check_number("e1-decode-be3-size",
            sens_zig_e1_decode_be3(golden, sizeof golden,
                                   restored, sizeof restored),
            (ptrdiff_t)sizeof source)) return 0;
    if (!check_bytes("e1-decode-be3-golden",
                     restored, source, sizeof source)) return 0;
    if (!check_number("e1-decode-untouched-suffix",
            restored[sizeof source], 0x37)) return 0;

    uint8_t damaged[sizeof golden];
    memcpy(damaged, golden, sizeof golden);
    damaged[sizeof damaged - 1] ^= 1;  /* CRC negative */
    memset(restored, 0x37, sizeof restored);
    if (!check_number("e1-crc-invalid-reject",
            sens_zig_e1_decode_be3(damaged, sizeof damaged,
                                   restored, sizeof restored), -1)) return 0;
    if (!check_number("e1-crc-negative-keeps-output",
            restored[0], 0x37)) return 0;
    if (!check_number("e1-decode-short-output",
            sens_zig_e1_decode_be3(golden, sizeof golden,
                                   restored, sizeof source - 1), -2)) return 0;
    if (!check_number("e1-decode-short-keeps-output",
            restored[0], 0x37)) return 0;
    uint8_t aliased_decode[64] = {0};
    memcpy(aliased_decode, golden, sizeof golden);
    if (!check_number("e1-decode-overlap-reject",
            sens_zig_e1_decode_be3(aliased_decode, sizeof golden,
                                   aliased_decode + 2, sizeof aliased_decode - 2), -1)) return 0;
    if (!check_bytes("e1-decode-reject-keeps-input",
                     aliased_decode, golden, sizeof golden)) return 0;
    if (!check_number("e1-small-output",
            sens_zig_e1_encode_be3(source, sizeof source,
                                   too_small, sizeof too_small), -2)) return 0;
    if (!check_bytes("e1-small-output-unchanged",
                     too_small, unchanged, sizeof too_small)) return 0;
    if (!check_number("e1-truncated-triplet",
            sens_zig_e1_encode_be3(source, sizeof source - 1,
                                   output, sizeof output), -1)) return 0;
    if (!check_number("e1-no-d10-admission",
            sens_zig_e1_encode_be3(invalid_width, sizeof invalid_width,
                                   output, sizeof output), -1)) return 0;
    if (!check_number("e1-invalid-bits",
            sens_zig_e1_encode_be3(invalid_bits, sizeof invalid_bits,
                                   output, sizeof output), -1)) return 0;
    memcpy(aliased, source, sizeof source);
    if (!check_number("e1-source-output-alias",
            sens_zig_e1_encode_be3(aliased, sizeof source,
                                   aliased, sizeof aliased), -1)) return 0;
    if (!check_bytes("e1-rejected-alias-keeps-input",
                     aliased, source, sizeof source)) return 0;
    return 1;
}

/* Rust-free E1 ABI memory-boundary witness: byte ownership only.
 * Adjacent caller-owned slices are legal; full/shifted alias and a corrupted
 * CRC must not alter any destination byte. No SENS semantic verdict here.
 */
static int witness_zig_e1_decode_buffer_boundaries(void) {
    static const uint8_t golden[] = {
        0x53, 0x33, 1, 3, 0, 3, 0x23, 0x20,
        0x8a, 0x36, 0x20, 0x5d, 0x52
    };
    static const uint8_t exact_be3[] = {2, 0, 2, 3, 0, 1, 2, 0, 1};
    uint8_t shared[64];
    uint8_t snapshot[sizeof shared];
    uint8_t corrupt[sizeof golden];
    uint8_t decoded[32];
    uint8_t sentinel[sizeof decoded];

    /* Two nonoverlapping slices of the same allocation may cross Zig. */
    memset(shared, 0x6c, sizeof shared);
    memcpy(shared, golden, sizeof golden);
    if (!check_number("e1-decode-adjacent-slices",
            sens_zig_e1_decode_be3(shared, sizeof golden,
                                   shared + sizeof golden,
                                   sizeof shared - sizeof golden),
            (ptrdiff_t)sizeof exact_be3)) return 0;
    if (!check_bytes("e1-decode-adjacent-exact-be3",
                     shared + sizeof golden, exact_be3, sizeof exact_be3)) return 0;

    memset(shared, 0x6c, sizeof shared);
    memcpy(shared, golden, sizeof golden);
    memcpy(snapshot, shared, sizeof shared);
    if (!check_number("e1-decode-full-alias-rejected",
            sens_zig_e1_decode_be3(shared, sizeof golden,
                                   shared, sizeof shared), -1)) return 0;
    if (!check_bytes("e1-decode-full-alias-all-bytes-unchanged",
                     shared, snapshot, sizeof shared)) return 0;

    /* Two overlap orientations: Zig must reject BEFORE touching memory. */
    memset(shared, 0x6c, sizeof shared);
    memcpy(shared, golden, sizeof golden);
    memcpy(snapshot, shared, sizeof shared);
    if (!check_number("e1-decode-forward-overlap-rejected",
            sens_zig_e1_decode_be3(shared, sizeof golden,
                                   shared + 5, sizeof shared - 5), -1)) return 0;
    if (!check_bytes("e1-decode-forward-overlap-all-bytes-unchanged",
                     shared, snapshot, sizeof shared)) return 0;

    memset(shared, 0x6c, sizeof shared);
    memcpy(shared + 5, golden, sizeof golden);
    memcpy(snapshot, shared, sizeof shared);
    if (!check_number("e1-decode-reverse-overlap-rejected",
            sens_zig_e1_decode_be3(shared + 5, sizeof golden,
                                   shared, sizeof shared), -1)) return 0;
    if (!check_bytes("e1-decode-reverse-overlap-all-bytes-unchanged",
                     shared, snapshot, sizeof shared)) return 0;

    memcpy(corrupt, golden, sizeof golden);
    corrupt[sizeof corrupt - 1] ^= 1u;
    memset(decoded, 0x49, sizeof decoded);
    memset(sentinel, 0x49, sizeof sentinel);
    if (!check_number("e1-decode-crc-bit-mutant-rejected",
            sens_zig_e1_decode_be3(corrupt, sizeof corrupt,
                                   decoded, sizeof decoded), -1)) return 0;
    if (!check_bytes("e1-decode-crc-bit-mutant-no-output-mutation",
                     decoded, sentinel, sizeof decoded)) return 0;
    return 1;
}

/*
 * F3C pack must reject physically invalid T5 before any framing write.
 * Same sterile contract as Rust zig_transport::encode_f3 (validate then pack).
 * No SENS semantic admission — only mechanical byte ownership.
 */
static int witness_zig_f3c_invalid_t5_reject(void) {
    static const uint8_t bad_byte[] = {243};
    static const uint8_t oversize[17] = {0};
    uint8_t out[32];
    uint8_t sentinel[32];

    memset(out, 0x3c, sizeof out);
    memset(sentinel, 0x3c, sizeof sentinel);

    /* Invalid physical byte: validate rejects, pack must return -1 and leave out. */
    if (!check_number("f3c-validate-byte243",
            sens_zig_t5_validate(bad_byte, sizeof bad_byte), -1)) return 0;
    if (!check_number("f3c-pack-rejects-byte243",
            sens_zig_f3c_pack(bad_byte, sizeof bad_byte, out, sizeof out), -1)) return 0;
    if (!check_bytes("f3c-pack-byte243-out-unchanged", out, sentinel, sizeof out)) return 0;

    /* Empty source is invalid for F3C pack. */
    memset(out, 0x3c, sizeof out);
    if (!check_number("f3c-pack-rejects-empty",
            sens_zig_f3c_pack(bad_byte, 0, out, sizeof out), -1)) return 0;
    if (!check_bytes("f3c-pack-empty-out-unchanged", out, sentinel, sizeof out)) return 0;

    /* Oversize beyond MAX_TINY_T5_BYTES: reject without write. */
    memset(out, 0x3c, sizeof out);
    if (!check_number("f3c-pack-rejects-oversize",
            sens_zig_f3c_pack(oversize, sizeof oversize, out, sizeof out), -1)) return 0;
    if (!check_bytes("f3c-pack-oversize-out-unchanged", out, sentinel, sizeof out)) return 0;

    return 1;
}


/* Negative controls for Zig F3C ingress from an independent C host.
 * Every rejection must leave the *whole* caller-owned destination unchanged.
 * A successful recovery must then pass the very same Zig T5 physical validator
 * used by Rust, without inferring any SENS callable or semantic identity.
 */
static int witness_zig_f3c_decode_fail_closed(void) {
    static const uint8_t golden_f3c[] = {0xf3, 0x40, 0x60};
    static const uint8_t golden_t5[] = {0x63, 0x89, 0x06, 0xa1};
    static const uint8_t invalid_marker[] = {0xf4, 0x40, 0x60};
    static const uint8_t invalid_short[] = {0xf3};
    static const uint8_t invalid_program[] = {0xf3, 0x00};
    const struct {
        const char *id;
        const uint8_t *bytes;
        size_t length;
    } negatives[] = {
        {"f3c-unpack-wrong-marker", invalid_marker, sizeof invalid_marker},
        {"f3c-unpack-truncated", invalid_short, sizeof invalid_short},
        {"f3c-unpack-invalid-program", invalid_program, sizeof invalid_program},
    };
    uint8_t output[32];
    uint8_t sentinel[sizeof output];
    memset(sentinel, 0xa6, sizeof sentinel);
    for (size_t i = 0; i < sizeof negatives / sizeof negatives[0]; ++i) {
        memcpy(output, sentinel, sizeof output);
        if (!check_number(negatives[i].id,
                sens_zig_f3c_unpack(negatives[i].bytes, negatives[i].length,
                                    output, sizeof output), -1)) return 0;
        if (!check_bytes(negatives[i].id, output, sentinel, sizeof output)) return 0;
    }
    memcpy(output, sentinel, sizeof output);
    if (!check_number("f3c-unpack-small-output",
            sens_zig_f3c_unpack(golden_f3c, sizeof golden_f3c,
                                output, sizeof golden_t5 - 1), -2)) return 0;
    if (!check_bytes("f3c-unpack-small-output-unchanged", output,
                     sentinel, sizeof output)) return 0;
    if (!check_number("f3c-unpack-recovered-length",
            sens_zig_f3c_unpack(golden_f3c, sizeof golden_f3c,
                                output, sizeof output), sizeof golden_t5)) return 0;
    if (!check_bytes("f3c-unpack-recovered-exact-t5", output,
                     golden_t5, sizeof golden_t5)) return 0;
    if (!check_bytes("f3c-unpack-untouched-suffix", output + sizeof golden_t5,
                     sentinel + sizeof golden_t5,
                     sizeof output - sizeof golden_t5)) return 0;
    if (!check_number("f3c-unpack-recovered-zig-t5-validation",
            sens_zig_t5_validate(output, sizeof golden_t5), 0)) return 0;
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
    if (!witness_zig_e1_encode_be3()) return 1;
    if (!witness_zig_e1_decode_buffer_boundaries()) return 1;
    if (!witness_zig_f3c_invalid_t5_reject()) return 1;
    if (!witness_zig_f3c_decode_fail_closed()) return 1;
    puts("SENS_C_CORRIDOR_PASS abi=2 host=C rust_linked=false transport=T5+F3C+E1 exact_width=true semantic_verdict=NOT_TESTED");
    return 0;
}
