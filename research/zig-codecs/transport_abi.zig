//! Stable caller-owned transport ABI v1; no allocator crosses Zig↔Rust.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
pub const Word = extern struct { width: u8, bits: u16 };
pub export fn sens_zig_codec_abi_version() u32 { return 1; }

pub export fn sens_zig_t5_validate(src: [*]const u8, len: usize) c_int {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    const a = std.heap.c_allocator;
    const words = t5.decode(a, src[0..len]) catch return -1;
    defer a.free(words);
    return 0;
}
pub export fn sens_zig_t5_encode(src: [*]const Word, count: usize, dst: [*]u8, cap: usize) isize {
    if (count == 0 or count > t5.MAX_PHYSICAL_BYTES * 5) return -1;
    const a = std.heap.c_allocator;
    const typed = a.alloc(t5.Word, count) catch return -1;
    defer a.free(typed);
    for (src[0..count], 0..) |w, i| typed[i] = .{ .width = w.width, .bits = w.bits };
    const physical = t5.encode(a, typed) catch return -1;
    defer a.free(physical);
    if (physical.len > cap) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}
/// F3C: -3 means no saving, NOT an invalid T5 program.
pub export fn sens_zig_f3c_pack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len == 0 or len > f3c.MAX_TINY_T5_BYTES) return -1;
    const a = std.heap.c_allocator;
    const physical = (f3c.encode(a, src[0..len]) catch return -1) orelse return -3;
    defer a.free(physical);
    if (physical.len > cap) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}
pub export fn sens_zig_f3c_unpack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len < 2 or len >= f3c.MAX_TINY_T5_BYTES) return -1;
    const a = std.heap.c_allocator;
    const physical = f3c.decode(a, src[0..len]) catch return -1;
    defer a.free(physical);
    if (physical.len > cap) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}
/// Opaque physical-file boundary: host passes only bytes, never Rust Word/
/// enum/ExprKind layout or host truthiness. Transport-only canonical repack.
/// The existing typed v1 ABI symbol is retained for independent legacy clients,
/// but the feature-gated Rust CLI must call THIS byte-oriented function.
/// -1 = malformed physical T5; -2 = caller buffer too small. Neither means
/// SENS D1:NO or any semantic verdict; Zig does not parse executable D2.
/// The bytes are buffered before writing, so in-place src==dst is permitted.
pub export fn sens_zig_t5_repack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    const a = std.heap.c_allocator;
    const words = t5.decode(a, src[0..len]) catch return -1;
    defer a.free(words);
    const physical = t5.encode(a, words) catch return -1;
    defer a.free(physical);
    if (physical.len != len or !std.mem.eql(u8, physical, src[0..len])) return -1;
    if (physical.len > cap) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}

test "opaque T5 ABI: preserve physical domain-width collision and separate grammar" {
    var out: [8]u8 = undefined;
    // D1:1 and D2:01 are different exact words; neither is a host boolean.
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_repack(&.{0xa1}, 1, &out, out.len));
    try std.testing.expectEqual(@as(u8, 0xa1), out[0]);
    // A lone D2 CLOSE is TRANSPORT-VALID but syntax-invalid SENS:
    // Zig must preserve it and must not claim an evaluator or semantic PASS.
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_repack(&.{0x35}, 1, &out, out.len));
    try std.testing.expectEqual(@as(u8, 0x35), out[0]);
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_repack(&.{0xa1}, 1, &out, 0));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_repack(&.{0xf3}, 1, &out, out.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_repack(&.{}, 0, &out, out.len));
    // No hidden host buffer alias restriction; output cannot taint source.
    var in_place = [_]u8{0xa1};
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_repack(&in_place, in_place.len, &in_place, in_place.len));
    try std.testing.expectEqual(@as(u8, 0xa1), in_place[0]);
}

/// SENS-supplied exact payload bits + width schedule -> Zig T5 bytes.
/// Both inputs are opaque physical data, not a Rust enum, SID8 or truth value.
/// The width schedule is a declared mechanical boundary, NOT callability.
/// -1 bad mechanical input, -2 output capacity; neither is SENS D1:NO.
/// `exact_bit_len` is meaningful bits, NOT rounded physical byte length.
pub export fn sens_zig_t5_encode_dense(
    bits: [*]const u8,
    exact_bit_len: usize,
    widths: [*]const u8,
    word_count: usize,
    dst: [*]u8,
    cap: usize,
) isize {
    if (word_count == 0 or word_count > t5.MAX_PHYSICAL_BYTES * 5)
        return -1;
    if (exact_bit_len == 0 or exact_bit_len > t5.MAX_PHYSICAL_BYTES * 5)
        return -1;
    if (word_count > exact_bit_len) return -1;
    const packed_len = (exact_bit_len + 7) / 8;
    const payload = bits[0..packed_len];
    if (exact_bit_len % 8 != 0) {
        const unused: u3 = @intCast(8 - exact_bit_len % 8);
        const tail_mask: u8 = (@as(u8, 1) << unused) - 1;
        if ((payload[payload.len - 1] & tail_mask) != 0) return -1;
    }

    const schedule = widths[0..word_count];
    var remaining = exact_bit_len;
    for (schedule) |width| {
        if (width == 0 or width > 9 or width > remaining) return -1;
        remaining -= width;
    }
    if (remaining != 0) return -1;

    const a = std.heap.c_allocator;
    const words = a.alloc(t5.Word, word_count) catch return -1;
    defer a.free(words);
    var pos: usize = 0;
    for (schedule, 0..) |width, index| {
        var word_bits: u16 = 0;
        for (0..@as(usize, width)) |_| {
            const bit: u16 = @intCast(
                (payload[pos / 8] >> @as(u3, @intCast(7 - pos % 8))) & 1
            );
            word_bits = (word_bits << 1) | bit;
            pos += 1;
        }
        words[index] = .{ .width = width, .bits = word_bits };
    }
    const encoded = t5.encode(a, words) catch return -1;
    defer a.free(encoded);
    if (encoded.len > cap) return -2;
    @memcpy(dst[0..encoded.len], encoded);
    return @intCast(encoded.len);
}

test "opaque dense SENS words become Zig-owned T5 bytes with exact widths" {
    var out: [16]u8 = undefined;
    // 10 | 001 | 00 | 000 | 01 = 100010000001, 12 meaningful bits.
    const widths = [_]u8{ 2, 3, 2, 3, 2 };
    const input = [_]u8{ 0x88, 0x10 };
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_t5_encode_dense(&input, 12, &widths, widths.len, &out, out.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, out[0..4]);
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_encode_dense(&input, 12, &widths, widths.len, &out, 3));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_dense(&.{ 0x88, 0x11 }, 12, &widths, widths.len, &out, out.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_dense(&input, 11, &widths, widths.len, &out, out.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_dense(&input, 12, &.{ 2, 3, 2, 4, 2 }, 5, &out, out.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_dense(&input, 12, &.{ 2, 3, 0, 5, 2 }, 5, &out, out.len));

    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_encode_dense(&.{0x80}, 1, &.{1}, 1, &out, out.len));
    try std.testing.expectEqual(@as(u8, 0xa1), out[0]);
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_encode_dense(&.{0x40}, 2, &.{2}, 1, &out, out.len));
    try std.testing.expectEqual(@as(u8, 0x35), out[0]);
}

test "no-allocation-crossing Zig C ABI roundtrip and caller bounds" {
    try std.testing.expectEqual(@as(u32, 1), sens_zig_codec_abi_version());
    const words = [_]Word{
        .{ .width = 2, .bits = 2 }, .{ .width = 3, .bits = 1 },
        .{ .width = 2, .bits = 0 }, .{ .width = 3, .bits = 0 },
        .{ .width = 2, .bits = 1 },
    };
    var buf: [32]u8 = undefined;
    try std.testing.expectEqual(@as(isize, -2), sens_zig_t5_encode(&words, words.len, &buf, 3));
    try std.testing.expectEqual(@as(isize, 4), sens_zig_t5_encode(&words, words.len, &buf, buf.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, buf[0..4]);
    try std.testing.expectEqual(@as(c_int, 0), sens_zig_t5_validate(&buf, 4));
    try std.testing.expectEqual(@as(isize, 3), sens_zig_f3c_pack(&buf, 4, &buf, buf.len));
    try std.testing.expectEqualSlices(u8, &.{ 0xf3, 0x40, 0x60 }, buf[0..3]);
    try std.testing.expectEqual(@as(isize, -2), sens_zig_f3c_unpack(&buf, 3, &buf, 3));
    try std.testing.expectEqual(@as(isize, 4), sens_zig_f3c_unpack(&buf, 3, &buf, buf.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, buf[0..4]);
    try std.testing.expectEqual(@as(c_int, -1), sens_zig_t5_validate(&.{0xf3}, 1));
}
