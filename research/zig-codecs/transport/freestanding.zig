//! A freestanding physical transport boundary: Zig 0.16.
//! All buffers/lengths explicit; no OS or libc, no semantic domain assignment.
//! The F3C rank tables also consume stack: an object build is not MCU stack proof.
const std = @import("std");
const t5 = @import("../t5/t5.zig");
const f3c = @import("../f3c/f3c.zig");
const fields = @import("fields.zig");

/// 0 = physically valid; positive = bytes written; -1 = invalid input;
/// -2 = caller buffer too small; -3 = F3C cannot save space.
pub export fn sens_zig_free_t5_validate(src: [*]const u8, len: u32) i32 {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    t5.validatePhysical(src[0..@as(usize, len)]) catch return -1;
    return 0;
}

pub export fn sens_zig_free_t5_encode_be3(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
) i32 {
    if (len == 0 or len % 3 != 0) return -1;
    const count = t5.encodeTripletsInto(
        dst[0..@as(usize, capacity)], src[0..@as(usize, len)],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(count); // Physical output <= 4 MiB.
}

fn overlaps(a_ptr: usize, a_len: usize, b_ptr: usize, b_len: usize) bool {
    if (a_len == 0 or b_len == 0) return false;
    return if (a_ptr <= b_ptr) b_ptr - a_ptr < a_len
        else a_ptr - b_ptr < b_len;
}

fn scratchValid(src: []const u8, dst: []u8, arena: []u8) bool {
    if (arena.len < f3c.ABI_SCRATCH_BYTES) return false;
    const work = arena[0..f3c.ABI_SCRATCH_BYTES];
    return !overlaps(@intFromPtr(src.ptr), src.len, @intFromPtr(work.ptr), work.len) and
        !overlaps(@intFromPtr(dst.ptr), dst.len, @intFromPtr(work.ptr), work.len);
}

/// Explicit carrier pack. F3C stages output before writing, supporting
/// in-place input/output. Scratch must not overlap either logical buffer.
pub export fn sens_zig_free_f3c_pack(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
    scratch: [*]u8, scratch_capacity: u32,
) i32 {
    if (len == 0 or len > f3c.MAX_TINY_T5_BYTES) return -1;
    const input = src[0..@as(usize, len)];
    const output = dst[0..@as(usize, capacity)];
    const work = scratch[0..@as(usize, scratch_capacity)];
    if (work.len < f3c.ABI_SCRATCH_BYTES) return -2;
    if (!scratchValid(input, output, work)) return -1;
    const count = (f3c.encodeInto(
        input, output, work[0..f3c.ABI_SCRATCH_BYTES],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1) orelse return -3;
    return @intCast(count);
}

/// Strict F3C decode; malformed .senc never falls back to .sens T5.
pub export fn sens_zig_free_f3c_unpack(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
    scratch: [*]u8, scratch_capacity: u32,
) i32 {
    if (len < 2 or len >= f3c.MAX_TINY_T5_BYTES) return -1;
    const input = src[0..@as(usize, len)];
    const output = dst[0..@as(usize, capacity)];
    const work = scratch[0..@as(usize, scratch_capacity)];
    if (work.len < f3c.ABI_SCRATCH_BYTES) return -2;
    if (!scratchValid(input, output, work)) return -1;
    const count = f3c.decodeInto(
        input, output, work[0..f3c.ABI_SCRATCH_BYTES],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(count);
}

/// CRC32 detects physical corruption, never authenticates program meaning.
pub export fn sens_zig_free_crc32(
    src: [*]const u8, len: u32, output: *u32,
) i32 {
    if (len > t5.MAX_PHYSICAL_BYTES) return -1;
    output.* = fields.crc32(src[0..@as(usize, len)]);
    return 0;
}

test "freestanding T5 F3C CRC golden and exact 8-bit word" {
    const raw = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };
    var buffer: [32]u8 = undefined;
    try std.testing.expectEqual(@as(i32, 4),
        sens_zig_free_t5_encode_be3(&raw, raw.len, &buffer, buffer.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, buffer[0..4]);
    try std.testing.expectEqual(@as(i32, 0), sens_zig_free_t5_validate(&buffer, 4));
    var crc: u32 = 0;
    try std.testing.expectEqual(@as(i32, 0), sens_zig_free_crc32("123456789", 9, &crc));
    try std.testing.expectEqual(@as(u32, 0xcbf43926), crc);
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    try std.testing.expectEqual(@as(i32, 3), sens_zig_free_f3c_pack(
        &buffer, 4, &buffer, buffer.len, &scratch, scratch.len));
    try std.testing.expectEqualSlices(u8, &.{ 0xf3, 0x40, 0x60 }, buffer[0..3]);
    try std.testing.expectEqual(@as(i32, 4), sens_zig_free_f3c_unpack(
        &buffer, 3, &buffer, buffer.len, &scratch, scratch.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, buffer[0..4]);
    const eight = [_]u8{ 8, 0, 0xa8 };
    try std.testing.expect(sens_zig_free_t5_encode_be3(
        &eight, eight.len, &buffer, buffer.len) > 0);
}

test "freestanding fail closed: invalid, capacity, scratch, overlap, no saving" {
    var dst: [32]u8 = [_]u8{0xa5} ** 32;
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_t5_validate(&.{0xf3}, 1));
    try std.testing.expectEqual(@as(i32, -2), sens_zig_free_t5_encode_be3(
        &.{ 1, 0, 1 }, 3, &dst, 0));
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_t5_encode_be3(
        &.{ 2, 0, 4 }, 3, &dst, dst.len));
    try std.testing.expectEqual(@as(i32, -2), sens_zig_free_f3c_unpack(
        &.{ 0xf3, 0x40, 0x60 }, 3, &dst, dst.len, &scratch, scratch.len - 1));
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_f3c_unpack(
        &.{ 0xf4, 0x40, 0x60 }, 3, &dst, dst.len, &scratch, scratch.len));
    try std.testing.expectEqual(@as(i32, -3), sens_zig_free_f3c_pack(
        &.{0x64}, 1, &dst, dst.len, &scratch, scratch.len));
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_f3c_pack(
        &.{ 0x63, 0x89, 0x06, 0xa1 }, 4, &dst, dst.len, &dst, dst.len));
    try std.testing.expectEqualSlices(u8, &([_]u8{0xa5} ** 32), &dst);
}
