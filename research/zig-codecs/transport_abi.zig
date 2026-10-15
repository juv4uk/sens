//! Single caller-owned transport ABI v2; no padded host structs or heap crossing.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
// ABI v2 uses caller-owned byte triplets; no padded host structs cross the boundary.
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

/// Symmetric ABI v2 ingress: canonical T5 bytes -> caller-owned BE3 words.
/// Only physical width+payload crosses; Zig never assigns semantic identity.
/// Positive return is exact BE3 byte count; -1 invalid; -2 insufficient output.
/// An error never changes destination bytes. No allocator crosses this ABI.
pub export fn sens_zig_t5_decode_be3(
    src: [*]const u8, byte_len: usize, dst: [*]u8, capacity: usize,
) isize {
    if (byte_len == 0 or byte_len > t5.MAX_PHYSICAL_BYTES) return -1;
    const written = t5.decodeTripletsInto(dst[0..capacity], src[0..byte_len])
        catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
}

test "ABI v2 Zig is the mechanical T5 ingress and egress without code registry" {
    const be3 = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };
    var carrier: [16]u8 = undefined;
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_t5_encode_be3(&be3, be3.len, &carrier, carrier.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, carrier[0..4]);

    var decoded: [18]u8 = .{0x75} ** 18;
    try std.testing.expectEqual(@as(isize, be3.len),
        sens_zig_t5_decode_be3(&carrier, 4, &decoded, decoded.len));
    try std.testing.expectEqualSlices(u8, &be3, decoded[0..be3.len]);
    try std.testing.expectEqual(@as(u8, 0x75), decoded[be3.len]);

    var short: [14]u8 = .{0x42} ** 14;
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_decode_be3(&carrier, 4, &short, short.len));
    for (short) |b| try std.testing.expectEqual(@as(u8, 0x42), b);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_decode_be3(&.{0xf3}, 1, &decoded, decoded.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_decode_be3(&.{ 0, 0 }, 2, &decoded, decoded.len));

    // The output is not written through an overlapping Rust/C host buffer.
    var same: [32]u8 = .{0x77} ** 32;
    @memcpy(same[0..4], carrier[0..4]);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_decode_be3(&same, 4, &same, same.len));
    try std.testing.expectEqualSlices(u8, carrier[0..4], same[0..4]);
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
    const words_be3 = [_]u8{
        2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1,
    };
    var buf: [32]u8 = undefined;
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_encode_be3(&words_be3, words_be3.len, &buf, 3));
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_t5_encode_be3(&words_be3, words_be3.len, &buf, buf.len));
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

test "ABI v2 T5 encode rejects whole and partial alias without writes" {
    // An FFI caller may reuse one allocation. Either overlap is an invalid
    // physical transport request; failure must leave ALL caller bytes intact.
    const source_be3 = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };
    var storage: [32]u8 = .{0x5a} ** 32;
    @memcpy(storage[0..source_be3.len], &source_be3);
    const original = storage;

    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&storage, source_be3.len, &storage, storage.len));
    try std.testing.expectEqualSlices(u8, &original, &storage);

    // Source occupies [0..15), destination [13..17): only two bytes overlap.
    // Do not depend on identical pointers to detect this mutation.
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&storage, source_be3.len,
            storage[13..].ptr, storage.len - 13));
    try std.testing.expectEqualSlices(u8, &original, &storage);

    var output: [4]u8 = .{0x79} ** 4;
    const unchanged = [_]u8{0x79} ** 4;
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_t5_encode_be3(&source_be3, source_be3.len, &output, 3));
    try std.testing.expectEqualSlices(u8, &unchanged, &output);

    // Ordinary T5 rejects an otherwise representable D10 coordinate;
    // a physical width is not a callable SENS function.
    const d10 = [_]u8{ 10, 0, 0 };
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_encode_be3(&d10, d10.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &unchanged, &output);

    // Positive control: an independent buffer accepts the SAME source.
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_t5_encode_be3(&source_be3, source_be3.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &.{ 0x63, 0x89, 0x06, 0xa1 }, &output);
}
