/*
 * H2 mechanical-only witness: caller-owned BE3 (stdin) -> Zig T5 (stdout).
 * Compiles as plain C11; the only external functions are Zig ABI v2.
 * No SENS semantic dispatch, no Rust imports, no domain name registry.
 *
 * stdout is ALWAYS raw T5, and remains empty on every rejection.
 * This intentionally accepts only the ordinary Zig T5 D1..D9 profile;
 * D10 coordinate transport and D11 remain outside this demonstrator.
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* One canonical mechanical Zig ABI v2 declaration source, shared with every C host. */
#include "zig_transport_v2.h"

#define WORD_CAP 512u
#define BE3_CAP (3u * WORD_CAP)
#define T5_CAP 4096u

static int reject(const char *reason) {
    fprintf(stderr, "H2_T5_DUMP_REJECT layer=transport category=%s\n", reason);
    return 2;
}

int main(void) {
    uint8_t words[BE3_CAP];
    uint8_t restored[BE3_CAP];
    uint8_t physical[T5_CAP];
    size_t used = 0;
    int c;

    if (sens_zig_codec_abi_version() != SENS_ZIG_TRANSPORT_ABI_VERSION)
        return reject("ABI_VERSION");
    while ((c = fgetc(stdin)) != EOF) {
        if (used == sizeof words)
            return reject("INPUT_TOO_LARGE");
        words[used++] = (uint8_t)c;
    }
    if (ferror(stdin))
        return reject("INPUT_READ");
    if (!used || used % 3u)
        return reject("MALFORMED_BE3_LENGTH");

    /* Zig, not this C program, validates width/payload/physical framing. */
    ptrdiff_t written = sens_zig_t5_encode_be3(
        words, used, physical, sizeof physical);
    if (written <= 0 || (size_t)written > sizeof physical)
        return reject("ZIG_ENCODE");
    if (sens_zig_t5_validate(physical, (size_t)written))
        return reject("ZIG_VALIDATE");
    ptrdiff_t decoded = sens_zig_t5_decode_be3(
        physical, (size_t)written, restored, sizeof restored);
    if (decoded < 0 || (size_t)decoded != used ||
        memcmp(words, restored, used) != 0)
        return reject("ZIG_EXACT_BE3_ROUNDTRIP");

    if (fwrite(physical, 1u, (size_t)written, stdout) != (size_t)written)
        return reject("OUTPUT_WRITE");
    if (fflush(stdout) != 0)
        return reject("OUTPUT_FLUSH");
    return 0;
}
