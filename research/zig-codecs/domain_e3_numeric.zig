//! Narrow, independent E3 physical numeric-run carrier for one wide word.
//! Mirrors the ratified E3 v3 single-word NUMERIC_RUN profile, not new wire.
//! D24/D48/D96/D192 identities remain exact, distinct typed bit containers.
//! Neither mathematical meaning nor SENS execution is established here.
//! No libc, heap, host byte order, callbacks or semantic registry.
const std = @import("std");
const ladder = @import("domain_ladder.zig");
const numeric_domains = @import("numeric_domains.zig");
const fields = @import("transport/fields.zig");

pub const Error = error{ BufferTooSmall, WrongLength, WrongProfile, IntegrityMismatch };

const prefix = [_]u8{ 'S', '3', 3, 1, 2, 1 };
// v3 | one word | NUMERIC_RUN | one block word | explicit numeric rung.
// Only one-word numeric-run is handled; this is NOT the full E3 decoder.
fn levelFor(comptime width: u16) u8 {
    // The single physical width profile is defined in numeric_domains.zig.
    // E3 transports its ordinal; Zig does not independently assign domain IDs.
    inline for (numeric_domains.WIDE_WIDTHS, 0..) |known_width, index| {
        if (width == known_width) return @intCast(index);
    }
    @compileError("E3 numeric carrier expects a declared wide transport width");
}

fn frameBytes(comptime width: u16) usize {
    return prefix.len + 1 + ladder.WideDomainWord(width).byte_len + 4;
}

/// Caller owns the output; preflight its length before changing any byte.
/// Exactly one canonical E3 NUMERIC_RUN word is emitted, MSB-first, CRC32/BE.
pub fn encodeOne(
    comptime width: u16,
    value: ladder.WideDomainWord(width),
    output: []u8,
) Error!usize {
    const size = frameBytes(width);
    if (output.len < size) return error.BufferTooSmall;
    const body = value.writeBytes();
    @memcpy(output[0..prefix.len], &prefix);
    output[prefix.len] = levelFor(width);
    @memcpy(output[prefix.len + 1 .. size - 4], &body);
    const crc = fields.crc32(output[0 .. size - 4]);
    output[size - 4] = @intCast(crc >> 24);
    output[size - 3] = @intCast((crc >> 16) & 0xff);
    output[size - 2] = @intCast((crc >> 8) & 0xff);
    output[size - 1] = @intCast(crc & 0xff);
    return size;
}

/// Typed restoration of this one physical profile only: no fallback,
// descriptor guessing, numeric coercion, or E3 grammar interpretation.
pub fn decodeOne(
    comptime width: u16,
    frame: []const u8,
) Error!ladder.WideDomainWord(width) {
    const size = frameBytes(width);
    if (frame.len != size) return error.WrongLength;
    if (!std.mem.eql(u8, frame[0..prefix.len], &prefix) or
        frame[prefix.len] != levelFor(width)) return error.WrongProfile;
    const crc = fields.crc32(frame[0 .. size - 4]);
    const expected = (@as(u32, frame[size - 4]) << 24) |
        (@as(u32, frame[size - 3]) << 16) |
        (@as(u32, frame[size - 2]) << 8) |
        @as(u32, frame[size - 1]);
    if (crc != expected) return error.IntegrityMismatch;
    return ladder.WideDomainWord(width).fromBytes(
        frame[prefix.len + 1 .. size - 4],
    ) catch return error.WrongLength;
}

// Independent negative witness: a correctly recomputed CRC cannot authorize
// an unknown physical numeric-run descriptor. All-zero bytes retain the
// declared wide width; the codec must not infer SENS arithmetic or callability.
