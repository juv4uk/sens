#ifndef SENS_ZIG_TRANSPORT_V2_H
#define SENS_ZIG_TRANSPORT_V2_H
/*
 * C declarations for EXISTING Zig transport ABI v2.
 * Implementation: research/zig-codecs/transport_abi.zig.
 * Mechanical bytes only: no SENS semantic registry, callable admission,
 * host owned Value types, or legacy identity translation.
 *
 * The caller owns source and destination buffers. BE3 encodes each exact
 * word as [width, payload_hi, payload_lo] (in-process, not .sens wire).
 * Current T5 ABI functions use the ordinary D1..D9 physical profile;
 * D10 coordinate transport and D11 executable admission are NOT enabled.
 */
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#if CHAR_BIT != 8
#error "SENS Zig transport ABI v2 requires eight-bit bytes"
#endif

#ifdef __cplusplus
extern "C" {
#endif

enum {
    SENS_ZIG_TRANSPORT_ABI_VERSION = 2,
    SENS_ZIG_TRANSPORT_OK = 0,
    SENS_ZIG_TRANSPORT_INVALID = -1,
    SENS_ZIG_TRANSPORT_CAPACITY = -2,
    SENS_ZIG_F3C_NO_SAVING = -3
};

uint32_t sens_zig_codec_abi_version(void);
/* Returns 0 for physically valid T5, -1 for invalid input. */
int sens_zig_t5_validate(const uint8_t *src, size_t len);
/* Returns output length in bytes; -1 invalid, -2 capacity insufficient. */
ptrdiff_t sens_zig_t5_encode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5_decode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
/* Exact-word BE3 -> canonical physical E1 RAW/REPEAT + CRC32, Zig-owned.
 * E1 is an explicit carrier, not .sens, and conveys no callable identity.
 * Returns physical byte count, -1 invalid/overlap, -2 small output.
 */
ptrdiff_t sens_zig_e1_encode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
/* F3C pack returns -3 if tiny framing does not save space, not an error. */
ptrdiff_t sens_zig_f3c_pack(const uint8_t *src, size_t len,
                             uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_f3c_unpack(const uint8_t *src, size_t len,
                               uint8_t *dst, size_t capacity);

#ifdef __cplusplus
}
#endif
#endif /* SENS_ZIG_TRANSPORT_V2_H */
