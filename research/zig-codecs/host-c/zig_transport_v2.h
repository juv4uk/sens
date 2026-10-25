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
 * The canonical BE3 executable-reader adapter uses D1..D9. A separate raw
 * T5M exact-word record adapter preserves any positive width without semantic
 * admission. A legacy T5 coordinate validator is limited to D1..D10; its
 * success NEVER admits execution, changes SENS semantics, or permits D11.
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
/* Raw MSB-first fields: repeated [width:u8][value:u64 big-endian].
 * Returns exact output byte length; capacity=0 queries length, -1 invalid,
 * -2 insufficient capacity. This is an in-process ABI, not .sens wire data.
 */
ptrdiff_t sens_zig_bitpack_fields(const uint8_t *src, size_t byte_len,
                                  uint8_t *dst, size_t capacity);
/* Ordinary D1..D9 T5: physical success only, never semantic admission. */
int sens_zig_t5_validate(const uint8_t *src, size_t len);
/* Explicit D1..D10 COORDINATE-ONLY physical validation (0 or -1).
 * D10 is NOT callable, and the ordinary T5 decode/encode route remains <=D9.
 * No allocator, host struct, or width inference crosses this ABI boundary.
 */
int sens_zig_t5_validate_coordinates(const uint8_t *src, size_t len);
/* Returns output length in bytes; -1 invalid, -2 capacity insufficient. */
int sens_zig_t5m_validate(const uint8_t *src, size_t len);
ptrdiff_t sens_zig_t5m_encode_be3(const uint8_t *src, size_t byte_len,
                                  uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5m_decode_be3(const uint8_t *src, size_t byte_len,
                                  uint8_t *dst, size_t capacity);
/* Exact T5M records: u32 big-endian width + ASCII '0'/'1' payload bytes.
 * In-process only; preserves exact widths and grants no SENS callability.
 * Returns output length, -1 invalid/overlap, -2 capacity insufficient.
 */
ptrdiff_t sens_zig_t5m_encode_words(const uint8_t *src, size_t byte_len,
                                    uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5m_decode_words(const uint8_t *src, size_t byte_len,
                                    uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5_encode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5_decode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
/* Точні слова без семантичного допуску: повтор [width:u32 big-endian][width байтів 0/1].
 * В обох напрямках зберігаються фізична ширина й біти. Ширина не є доменною
 * identity: належність до D1–24+ та викличність визначає SENS.
 * Повертає довжину результату; -1 некоректно/перетин, -2 замалий буфер.
 */
ptrdiff_t sens_zig_t5m_encode_words(const uint8_t *src, size_t byte_len,
                                    uint8_t *dst, size_t capacity);
ptrdiff_t sens_zig_t5m_decode_words(const uint8_t *src, size_t byte_len,
                                    uint8_t *dst, size_t capacity);
/* Exact-word BE3 -> canonical physical E1 RAW/REPEAT + CRC32, Zig-owned.
 * E1 is an explicit carrier, not .sens, and conveys no callable identity.
 * Returns physical byte count, -1 invalid/overlap, -2 small output.
 */
ptrdiff_t sens_zig_e1_encode_be3(const uint8_t *src, size_t byte_len,
                                 uint8_t *dst, size_t capacity);
/* Strict, canonical E1 S3/v1 -> exact BE3 words (physical data only).
 * On invalid CRC, noncanonical replay, alias or insufficient capacity,
 * no output bytes are modified. This implementation caps E1 to 64 KiB
 * per call; such a transport limit grants no semantic identity.
 */
ptrdiff_t sens_zig_e1_decode_be3(const uint8_t *src, size_t byte_len,
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
