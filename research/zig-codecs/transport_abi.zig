//! Single caller-owned transport ABI v2; no padded host structs or heap crossing.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const e1 = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");
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

/// E1 v1 physical egress through the SAME host-neutral ABI v2.
/// Source is caller-owned BE3 (width, payload MSB, payload LSB), not a Rust
/// struct or an executable SENS identity. No allocator crosses the corridor.
/// Positive return: E1 byte count; -1: invalid/overlap; -2: small output.
/// E1 uses its already-defined RAW/REPEAT DP, framing, and CRC in Zig.
pub export fn sens_zig_e1_encode_be3(
    src: [*]const u8, byte_len: usize, dst: [*]u8, capacity: usize,
) isize {
    if (byte_len == 0 or byte_len % 3 != 0) return -1;
    const count = byte_len / 3;
    if (count > e1.MAX_WORDS) return -1;

    // Fail closed before writes; a shared host allocation is not an excuse
    // to corrupt unread width/payload source triplets.
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity)))
        return -1;

    // Zig-local bounded scratch: never expose compiler-specific Step/Word
    // struct layout across FFI and never allocate from a host allocator.
    var words: [e1.MAX_WORDS]e1.Word = undefined;
    var scratch: [e1.MAX_WORDS + 1]e1_writer.Step = undefined;
    for (0..count) |i| {
        const at = i * 3;
        const width = src[at];
        const bits = (@as(u16, src[at + 1]) << 8) | @as(u16, src[at + 2]);
        if (width == 0 or width > 9) return -1;
        if (bits >= (@as(u16, 1) << @as(u4, @intCast(width)))) return -1;
        words[i] = .{ .width = width, .bits = bits };
    }
    const size = e1_writer.encode(words[0..count], dst[0..capacity], scratch[0 .. count + 1])
        catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(size);
}

test "E1 ABI v2 Zig exact RAW witness, rejected alias, bad widths and capacity" {
    const input = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 1 };
    const expected = [_]u8{ 0x53, 0x33, 1, 3, 0, 3, 0x23, 0x20,
        0x8a, 0x36, 0x20, 0x5d, 0x52 };
    var physical: [64]u8 = .{0x5c} ** 64;
    try std.testing.expectEqual(@as(isize, expected.len),
        sens_zig_e1_encode_be3(&input, input.len, &physical, physical.len));
    try std.testing.expectEqualSlices(u8, &expected, physical[0..expected.len]);

    var too_small: [8]u8 = .{0x6d} ** 8;
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_e1_encode_be3(&input, input.len, &too_small, too_small.len));
    for (too_small) |byte| try std.testing.expectEqual(@as(u8, 0x6d), byte);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_e1_encode_be3(&.{ 10, 0, 0 }, 3, &physical, physical.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_e1_encode_be3(&.{ 2, 0, 4 }, 3, &physical, physical.len));
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_e1_encode_be3(&input, input.len - 1, &physical, physical.len));

    var shared: [64]u8 = .{0x3a} ** 64;
    @memcpy(shared[0..input.len], &input);
    const before = shared;
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_e1_encode_be3(&shared, input.len, &shared, shared.len));
    try std.testing.expectEqualSlices(u8, &before, &shared);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_e1_encode_be3(shared[0..].ptr, input.len,
            shared[input.len - 2 ..].ptr, shared.len - input.len + 2));
    try std.testing.expectEqualSlices(u8, &before, &shared);
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

test "ABI v2 T5 decode rejects partial overlap and accepts adjacent buffers" {
    // Caller-owned buffers may share one allocation. Every rejected alias
    // must leave both the T5 source and destination byte-for-byte unchanged.
    // A merely adjacent destination is safe and must remain accepted.
    const carrier = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const expected = [_]u8{ 2, 0, 2, 3, 0, 1, 2, 0, 0, 3, 0, 0, 2, 0, 1 };

    // Destination starts two bytes inside the T5 source.
    var forward: [32]u8 = .{0x6e} ** 32;
    @memcpy(forward[0..carrier.len], carrier[0..]);
    const forward_original = forward;
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_decode_be3(forward[0..].ptr, carrier.len,
            forward[2..].ptr, forward.len - 2));
    try std.testing.expectEqualSlices(u8, forward_original[0..], forward[0..]);

    // Source starts inside the 15-byte BE3 destination (the opposite order).
    var reverse: [32]u8 = .{0x6e} ** 32;
    @memcpy(reverse[13 .. 13 + carrier.len], carrier[0..]);
    const reverse_original = reverse;
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_t5_decode_be3(reverse[13..].ptr, carrier.len,
            reverse[0..].ptr, reverse.len));
    try std.testing.expectEqualSlices(u8, reverse_original[0..], reverse[0..]);

    // The exact end of source is NOT an overlap; preserve exact domain widths.
    var adjacent: [32]u8 = .{0x6e} ** 32;
    @memcpy(adjacent[0..carrier.len], carrier[0..]);
    try std.testing.expectEqual(@as(isize, expected.len),
        sens_zig_t5_decode_be3(adjacent[0..].ptr, carrier.len,
            adjacent[carrier.len..].ptr, adjacent.len - carrier.len));
    try std.testing.expectEqualSlices(u8, carrier[0..], adjacent[0..carrier.len]);
    try std.testing.expectEqualSlices(u8, expected[0..],
        adjacent[carrier.len .. carrier.len + expected.len]);
    try std.testing.expectEqual(@as(u8, 0x6e), adjacent[carrier.len + expected.len]);
}

test "ABI v2 F3C return codes remain mechanical and never clobber" {
    // Both Rust and Rust-free C hosts call these exact Zig ABI v2 exports.
    // A transport error is NOT a SENS D1:NO or semantic rejection.
    const t5_quote = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const f3_quote = [_]u8{ 0xf3, 0x40, 0x60 };
    const untouched = [_]u8{0x75} ** 32;
    var output: [32]u8 = untouched;

    // Refuse publication on insufficient capacity, malformed input, or
    // a valid ordinary T5 carrier that does not produce an F3C saving.
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_f3c_pack(&t5_quote, t5_quote.len, &output, 2));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_f3c_pack(&.{0xff}, 1, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -3),
        sens_zig_f3c_pack(&.{0x64}, 1, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);

    try std.testing.expectEqual(@as(isize, 3),
        sens_zig_f3c_pack(&t5_quote, t5_quote.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &f3_quote, output[0..f3_quote.len]);
    try std.testing.expectEqual(@as(u8, 0x75), output[f3_quote.len]);

    // Ingress is also fail-closed: insufficient output or a corrupt marker
    // must not mutate caller-owned bytes, including a trailing sentinel.
    output = untouched;
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_f3c_unpack(&f3_quote, f3_quote.len, &output, 3));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -1),
        sens_zig_f3c_unpack(&.{ 0xf4, 0x40, 0x60 }, 3, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_f3c_unpack(&f3_quote, f3_quote.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &t5_quote, output[0..t5_quote.len]);
    try std.testing.expectEqual(@as(u8, 0x75), output[t5_quote.len]);

    // Legitimate in-place operations remain supported: scratch is internal to
    // Zig; no Rust/C allocator, struct layout, or SENS truth value crosses.
    var shared: [32]u8 = untouched;
    @memcpy(shared[0..t5_quote.len], &t5_quote);
    try std.testing.expectEqual(@as(isize, 3),
        sens_zig_f3c_pack(shared[0..].ptr, t5_quote.len,
            shared[0..].ptr, shared.len));
    try std.testing.expectEqualSlices(u8, &f3_quote, shared[0..f3_quote.len]);
    try std.testing.expectEqual(@as(isize, 4),
        sens_zig_f3c_unpack(shared[0..].ptr, f3_quote.len,
            shared[0..].ptr, shared.len));
    try std.testing.expectEqualSlices(u8, &t5_quote, shared[0..t5_quote.len]);
}
