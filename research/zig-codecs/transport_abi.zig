//! Stable caller-owned transport ABI v1; no allocator crosses Zig↔Rust.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
pub const Word = extern struct { width: u8, bits: u16 };
/// ABI v2: the preferred boundary uses explicit [width, payload-MSB, payload-LSB]
/// per word, NOT a C struct with host-dependent padding/alignment/endianness.
/// This triplet stream is an in-process FFI representation, NEVER .sens wire.
pub export fn sens_zig_codec_abi_version() u32 { return 2; }

pub export fn sens_zig_t5_validate(src: [*]const u8, len: usize) c_int {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    // Heapless physical scan only: no host allocator or SENS semantic dispatch.
    t5.validatePhysical(src[0..len]) catch return -1;
    return 0;
}
/// Explicit and alignment-independent ABI v2 for exact-width T5 words.
/// Each word occupies exactly three bytes: [width, payload high, payload low].
/// -1 invalid input; -2 output too small. No implicit semantic domain mapping.
pub export fn sens_zig_t5_encode_be3(
    src: [*]const u8, byte_len: usize, dst: [*]u8, capacity: usize,
) isize {
    if (byte_len == 0 or byte_len % 3 != 0) return -1;
    const count = byte_len / 3;
    if (count > t5.MAX_PHYSICAL_BYTES * 5) return -1;
    // The complete v2 path is caller-owned and allocation-free.
    const written = t5.encodeTripletsInto(dst[0..capacity], src[0..byte_len])
        catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
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
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    const written = (f3c.encodeInto(src[0..len], dst[0..cap], &scratch)
        catch |err| return if (err == error.BufferTooSmall) -2 else -1) orelse return -3;
    return @intCast(written);
}
pub export fn sens_zig_f3c_unpack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len < 2 or len >= f3c.MAX_TINY_T5_BYTES) return -1;
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    const written = f3c.decodeInto(src[0..len], dst[0..cap], &scratch)
        catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
}
test "no-allocation-crossing Zig C ABI roundtrip and caller bounds" {
    try std.testing.expectEqual(@as(u32, 2), sens_zig_codec_abi_version());
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

test "ABI v2 big endian triplets reject Rust layout and preserve exact word widths" {
    // D2:10, D3:001, D2:00, D3:000, D2:01 from the known carrier.
    const input = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };
    var buf: [32]u8 = undefined;
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_t5_encode_be3(&input, input.len, &buf, buf.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, buf[0..4]);
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_encode_be3(&input, input.len, &buf, 3));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&input, input.len - 1, &buf, buf.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&.{ 0, 0, 1 }, 3, &buf, buf.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&.{ 2, 0, 4 }, 3, &buf, buf.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&.{ 9, 2, 0 }, 3, &buf, buf.len));

    // Equal numeric payload, DIFFERENT exact widths: D1:1 is not D2:01.
    const one = [_]u8{ 1, 0, 1 };
    const two = [_]u8{ 2, 0, 1 };
    var left: [4]u8 = undefined;
    var right: [4]u8 = undefined;
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_encode_be3(&one, one.len, &left, left.len));
    try std.testing.expectEqual(@as(isize, 1),
        sens_zig_t5_encode_be3(&two, two.len, &right, right.len));
    try std.testing.expectEqual(@as(u8, 0xa1), left[0]);
    try std.testing.expectEqual(@as(u8, 0x35), right[0]);
}
