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

test "E3 single numeric-run D24 and D48 independently pinned Rust wire vectors" {
    // Fixed bytes from current frame3_domain.rs independently-pinned cases.
    // They are evidence of physical parity, not SENS arithmetic.
    const d24 = ladder.WideDomainWord(24).init(1);
    const d48 = ladder.WideDomainWord(48).init(1);
    const gold24 = [_]u8{ 0x53, 0x33, 0x03, 0x01, 0x02, 0x01, 0x00,
        0x00, 0x00, 0x01, 0x89, 0x42, 0x1d, 0x50 };
    const gold48 = [_]u8{ 0x53, 0x33, 0x03, 0x01, 0x02, 0x01, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x9d, 0x8f, 0xe7, 0xcc };
    var buffer: [64]u8 = undefined;
    const len24 = try encodeOne(24, d24, &buffer);
    try std.testing.expectEqualSlices(u8, &gold24, buffer[0..len24]);
    try std.testing.expectEqual(d24.bits, (try decodeOne(24, &gold24)).bits);
    const len48 = try encodeOne(48, d48, &buffer);
    try std.testing.expectEqualSlices(u8, &gold48, buffer[0..len48]);
    try std.testing.expectEqual(d48.bits, (try decodeOne(48, &gold48)).bits);
    try std.testing.expect(@TypeOf(d24) != @TypeOf(d48));
    try std.testing.expectError(error.WrongLength, decodeOne(48, &gold24));
    try std.testing.expectError(error.WrongLength, decodeOne(24, &gold48));
}

test "E3 single-source numeric width order and CRC-correct profile mutant" {
    // Numeric rung order is imported from the shared physical profile, not
    // independently declared by the E3 codec. CRC integrity alone never
    // authorizes reinterpreting the same payload as another domain.
    inline for (numeric_domains.WIDE_WIDTHS, 0..) |width, ordinal| {
        const Domain = ladder.WideDomainWord(width);
        const value = Domain.init(1);
        var frame: [frameBytes(width)]u8 = undefined;
        const len = try encodeOne(width, value, &frame);
        try std.testing.expectEqual(@as(u8, @intCast(ordinal)), frame[prefix.len]);
        try std.testing.expectEqual(value.bits, (try decodeOne(width, frame[0..len])).bits);

        var wrong = frame;
        wrong[prefix.len] = @intCast((ordinal + 1) % numeric_domains.WIDE_WIDTHS.len);
        const crc = fields.crc32(wrong[0 .. len - 4]);
        wrong[len - 4] = @intCast(crc >> 24);
        wrong[len - 3] = @intCast((crc >> 16) & 0xff);
        wrong[len - 2] = @intCast((crc >> 8) & 0xff);
        wrong[len - 1] = @intCast(crc & 0xff);
        try std.testing.expectError(error.WrongProfile,
            decodeOne(width, wrong[0..len]));
    }
}

test "E3 wide numeric bit positions remain exact across all declared rungs" {
    var checked: usize = 0;
    inline for (numeric_domains.WIDE_WIDTHS) |width| {
        const D = ladder.WideDomainWord(width);
        var frame: [frameBytes(width)]u8 = undefined;
        for (0..@as(usize, width)) |bit_index| {
            var bytes = [_]u8{0} ** D.byte_len;
            bytes[bit_index / 8] |= @as(u8, 1) <<
                @as(u3, @intCast(7 - bit_index % 8));
            const source = try D.fromBytes(&bytes);
            const length = try encodeOne(width, source, &frame);
            try std.testing.expectEqual(@as(usize, frameBytes(width)), length);
            try std.testing.expectEqualSlices(u8, &bytes,
                frame[prefix.len + 1 .. length - 4]);
            const restored = try decodeOne(width, frame[0..length]);
            try std.testing.expectEqual(source.bits, restored.bits);
            checked += 1;
        }
    }
    try std.testing.expectEqual(@as(usize, 360), checked);
}

test "E3 one-word profile refuses mutation and never writes into a small buffer" {
    const D = ladder.WideDomainWord(24);
    const original = D.init(1);
    var full: [frameBytes(24)]u8 = undefined;
    const size = try encodeOne(24, original, &full);
    var short: [frameBytes(24) - 1]u8 = [_]u8{0xa5} ** (frameBytes(24) - 1);
    try std.testing.expectError(error.BufferTooSmall,
        encodeOne(24, original, &short));
    try std.testing.expectEqualSlices(u8,
        &([_]u8{0xa5} ** (frameBytes(24) - 1)), &short);
    try std.testing.expectError(error.WrongLength, decodeOne(24, full[0 .. size - 1]));
    var long: [frameBytes(24) + 1]u8 = undefined;
    @memcpy(long[0..size], full[0..size]);
    long[size] = 0;
    try std.testing.expectError(error.WrongLength, decodeOne(24, &long));

    var damaged = full;
    damaged[8] ^= 1;
    try std.testing.expectError(error.IntegrityMismatch, decodeOne(24, &damaged));
    damaged = full;
    damaged[2] = 2;
    try std.testing.expectError(error.WrongProfile, decodeOne(24, &damaged));
    damaged = full;
    damaged[6] = 1;
    const crc = fields.crc32(damaged[0 .. size - 4]);
    damaged[size - 4] = @intCast(crc >> 24);
    damaged[size - 3] = @intCast((crc >> 16) & 0xff);
    damaged[size - 2] = @intCast((crc >> 8) & 0xff);
    damaged[size - 1] = @intCast(crc & 0xff);
    try std.testing.expectError(error.WrongProfile, decodeOne(24, &damaged));
}
