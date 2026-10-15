//! A freestanding physical transport boundary: Zig 0.16.
//! All buffers/lengths explicit; no OS or libc, no semantic domain assignment.
//! The F3C rank tables also consume stack: an object build is not MCU stack proof.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const fields = @import("transport/fields.zig");

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

/// Inverse physical T5 ingress for a Rust-free C/MCU host. All storage is
/// caller-owned: no heap, no semantic lookup, no D10 callable admission.
/// Returns exact BE3 byte count, -1 on malformed/aliased input, -2 if small.
pub export fn sens_zig_free_t5_decode_be3(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
) i32 {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    const written = t5.decodeTripletsInto(
        dst[0..@as(usize, capacity)], src[0..@as(usize, len)],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(written); // Bounded by T5 physical max and exact BE3.
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
    // CRC is a physical receipt, never permission to mutate source bytes.
    // The host owns both ranges; reject a result pointer inside the input.
    if (overlaps(@intFromPtr(src), @as(usize, len),
        @intFromPtr(output), @sizeOf(u32))) return -1;
    output.* = fields.crc32(src[0..@as(usize, len)]);
    return 0;
}


test "freestanding CRC32 rejects aliased result without changing any physical bit" {
    // This input is NOT a numerical SENS value: its bytes are opaque carrier
    // data, and the output u32 is merely a CRC receipt owned by the host.
    var backing: [3]u32 = .{ 0x11223344, 0x55667788, 0xa5a5a5a5 };
    const raw = std.mem.sliceAsBytes(backing[0..]);
    const expected = fields.crc32(raw[0..8]);

    // Adjacent output range is legal, including within one allocation.
    try std.testing.expectEqual(@as(i32, 0),
        sens_zig_free_crc32(raw.ptr, 8, &backing[2]));
    try std.testing.expectEqual(expected, backing[2]);

    const before = backing;
    // Complete overlap: output overwrites the first four input bytes.
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_crc32(raw.ptr, 8, &backing[0]));
    for (backing, before) |got, want| try std.testing.expectEqual(want, got);

    // Partial overlap in the opposite direction: the input begins at the
    // last byte of the output's u32 and continues into the next word.
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_crc32(raw[3..].ptr, 2, &backing[0]));
    for (backing, before) |got, want| try std.testing.expectEqual(want, got);

    // A source size outside the physical bound cannot touch the receipt.
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_crc32(
        raw.ptr, @intCast(t5.MAX_PHYSICAL_BYTES + 1), &backing[2]));
    for (backing, before) |got, want| try std.testing.expectEqual(want, got);
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

test "freestanding Zig T5 ingress exact BE3 bits and no-write negatives" {
    const exact = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };
    const wire = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    var decoded: [18]u8 = .{0xa5} ** 18;
    try std.testing.expectEqual(@as(i32, exact.len),
        sens_zig_free_t5_decode_be3(&wire, wire.len, &decoded, decoded.len));
    try std.testing.expectEqualSlices(u8, &exact, decoded[0..exact.len]);
    try std.testing.expectEqual(@as(u8, 0xa5), decoded[exact.len]);

    // Invalid physical input and insufficient destination cannot write bytes.
    var short: [14]u8 = .{0x79} ** 14;
    try std.testing.expectEqual(@as(i32, -2),
        sens_zig_free_t5_decode_be3(&wire, wire.len, &short, short.len));
    try std.testing.expectEqualSlices(u8, &([_]u8{0x79} ** 14), &short);
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_t5_decode_be3(&.{0xf3}, 1, &decoded, decoded.len));
    try std.testing.expectEqualSlices(u8, &exact, decoded[0..exact.len]);

    // The caller can use one allocation with adjacent, non-overlapping spans.
    var shared: [32]u8 = .{0xa5} ** 32;
    @memcpy(shared[0..wire.len], &wire);
    try std.testing.expectEqual(@as(i32, exact.len),
        sens_zig_free_t5_decode_be3(&shared, wire.len,
            shared[wire.len..].ptr, exact.len));
    try std.testing.expectEqualSlices(u8, &wire, shared[0..wire.len]);
    try std.testing.expectEqualSlices(u8, &exact,
        shared[wire.len .. wire.len + exact.len]);

    // Full and two shifted aliases must reject BEFORE touching any bytes.
    @memset(&shared, 0xa5);
    @memcpy(shared[0..wire.len], &wire);
    const before_full = shared;
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_t5_decode_be3(&shared, wire.len, &shared, shared.len));
    try std.testing.expectEqualSlices(u8, &before_full, &shared);
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_t5_decode_be3(&shared, wire.len,
            shared[2..].ptr, exact.len));
    try std.testing.expectEqualSlices(u8, &before_full, &shared);

    @memset(&shared, 0xa5);
    @memcpy(shared[3 .. 3 + wire.len], &wire);
    const before_reverse = shared;
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_t5_decode_be3(shared[3..].ptr, wire.len,
            &shared, exact.len));
    try std.testing.expectEqualSlices(u8, &before_reverse, &shared);

    // Identical payload is not identical domain: physical D8 != D9.
    var d8_wire: [4]u8 = undefined;
    var d9_wire: [4]u8 = undefined;
    const d8 = [_]u8{ 8, 0, 0xa8 };
    const d9 = [_]u8{ 9, 0, 0xa8 };
    const n8 = sens_zig_free_t5_encode_be3(&d8, d8.len, &d8_wire, d8_wire.len);
    const n9 = sens_zig_free_t5_encode_be3(&d9, d9.len, &d9_wire, d9_wire.len);
    try std.testing.expectEqual(@as(i32, 2), n8);
    try std.testing.expectEqual(@as(i32, 2), n9);
    try std.testing.expect(!std.mem.eql(u8, d8_wire[0..2], d9_wire[0..2]));
    var recovered: [3]u8 = undefined;
    try std.testing.expectEqual(@as(i32, 3),
        sens_zig_free_t5_decode_be3(&d9_wire, @intCast(n9), &recovered, recovered.len));
    try std.testing.expectEqualSlices(u8, &d9, &recovered);
    var forbidden: [4]u8 = .{0xa5} ** 4;
    try std.testing.expectEqual(@as(i32, -1),
        sens_zig_free_t5_encode_be3(&.{ 10, 0, 1 }, 3, &forbidden, forbidden.len));
    try std.testing.expectEqualSlices(u8, &([_]u8{0xa5} ** 4), &forbidden);
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
    // Both spans must be large enough; test real overlap, not tiny scratch.
    var shared: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    try std.testing.expectEqual(@as(i32, -1), sens_zig_free_f3c_pack(
        &.{ 0x63, 0x89, 0x06, 0xa1 }, 4,
        &shared, shared.len, &shared, shared.len));
    try std.testing.expectEqualSlices(u8, &([_]u8{0xa5} ** 32), &dst);
}

/// Source-level physical memory components, NOT full stack usage.
/// FixedBufferAllocator scratch is caller-owned; suffix counts are immutable
/// data. Nested calls, spills, compiler helpers and other local arrays remain
/// unmeasured and must be assessed on actual hardware.
pub const F3C_SCRATCH_BYTES: usize = f3c.ABI_SCRATCH_BYTES;
pub const F3C_RANK_TABLE_BYTES: usize = 0;
pub const F3C_SUFFIX_ROM_BYTES: usize = f3c.SUFFIX_ROM_BYTES;

test "F3C scratch and ROM component audit, not a firmware stack guarantee" {
    try std.testing.expectEqual(@as(usize, 8192), F3C_SCRATCH_BYTES);
    try std.testing.expectEqual(@as(usize, 0), F3C_RANK_TABLE_BYTES);
    try std.testing.expectEqual(@as(usize, 4000), F3C_SUFFIX_ROM_BYTES);
    std.debug.print(
        "F3C_MEMORY_COMPONENTS scratch_bytes={d} rank_table_stack_bytes={d} suffix_rom_bytes={d} total_stack_bound=NOT_MEASURED\n",
        .{ F3C_SCRATCH_BYTES, F3C_RANK_TABLE_BYTES, F3C_SUFFIX_ROM_BYTES },
    );
}
