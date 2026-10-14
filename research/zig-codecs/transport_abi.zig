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
