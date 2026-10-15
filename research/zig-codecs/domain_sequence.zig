//! Zig mixed SENS domain ladder: exact width + bits, zero semantic authority.
//! Physical E1 can transport D1..D9; D10 is never silently truncated.
//! Every buffer belongs to the caller. No heap, libc, interpreter or registry.
const std = @import("std");
const ladder = @import("domain_ladder.zig");
const e1 = @import("transport/e1.zig");
const writer = @import("transport/e1_writer.zig");
const fields = @import("transport/fields.zig");

pub const Error = writer.Error || ladder.CoordinateError ||
    error{UnsupportedCarrierWidth};

pub fn fromTyped(comptime width: u8, word: ladder.DomainWord(width)) ladder.Coordinate {
    return word.coordinate();
}

/// Pure physical overlap check, safe from pointer-end addition overflow.
fn overlaps(left: []const u8, right: []const u8) bool {
    if (left.len == 0 or right.len == 0) return false;
    const a = @intFromPtr(left.ptr);
    const b = @intFromPtr(right.ptr);
    return if (a <= b) b - a < left.len else a - b < right.len;
}

/// Validates the complete mixed-width source before publishing output bytes.
pub fn encode(
    source: []const ladder.Coordinate,
    output: []u8,
    words: []e1.Word,
    steps: []writer.Step,
) Error!usize {
    if (source.len > e1.MAX_WORDS) return error.TooLarge;
    for (source) |coordinate| {
        _ = try ladder.Coordinate.init(coordinate.width, coordinate.bits);
        if (coordinate.width > 9) return error.UnsupportedCarrierWidth;
    }
    if (words.len < source.len or steps.len <= source.len)
        return error.BufferTooSmall;
    // Validate ALL caller memory boundaries before staging the first word.
    // The lower-level writer checks too, but previously checked too late.
    const src_bytes = std.mem.sliceAsBytes(source);
    const word_bytes = std.mem.sliceAsBytes(words);
    const step_bytes = std.mem.sliceAsBytes(steps);
    if (overlaps(src_bytes, word_bytes) or
        overlaps(src_bytes, step_bytes) or
        overlaps(src_bytes, output) or
        overlaps(word_bytes, step_bytes) or
        overlaps(word_bytes, output) or
        overlaps(step_bytes, output))
        return error.OverlappingBuffers;
    for (source, 0..) |coordinate, i|
        words[i] = .{ .width = coordinate.width, .bits = coordinate.bits };
    return writer.encode(words[0..source.len], output, steps);
}

/// CRC + canonical E1 byte replay before returning ANY exact coordinate.
/// The restored width is explicit; it never decides SENS executable identity.
pub fn decode(
    input: []const u8,
    out: []ladder.Coordinate,
    words: []e1.Word,
    steps: []writer.Step,
    replay: []u8,
) Error!usize {
    const count = try e1.inspect(input);
    if (out.len < count or words.len < count or steps.len <= count)
        return error.BufferTooSmall;
    // Canonical replay writes intermediate buffers before publishing out.
    // Never let any host-provided slice alias another writable region.
    const out_bytes = std.mem.sliceAsBytes(out);
    const word_bytes = std.mem.sliceAsBytes(words);
    const step_bytes = std.mem.sliceAsBytes(steps);
    if (overlaps(input, out_bytes) or
        overlaps(input, word_bytes) or
        overlaps(input, step_bytes) or
        overlaps(input, replay) or
        overlaps(out_bytes, word_bytes) or
        overlaps(out_bytes, step_bytes) or
        overlaps(out_bytes, replay) or
        overlaps(word_bytes, step_bytes) or
        overlaps(word_bytes, replay) or
        overlaps(step_bytes, replay))
        return error.OverlappingBuffers;
    _ = try writer.inspectCanonical(input, words[0..count], steps, replay);
    for (words[0..count]) |word|
        _ = try ladder.Coordinate.init(word.width, word.bits);
    for (words[0..count], 0..) |word, i|
        out[i] = .{ .width = word.width, .bits = word.bits };
    return count;
}

test "mixed typed D1 D2 D3 D8 D9 retain exact identity through canonical E1" {
    const source = [_]ladder.Coordinate{
        fromTyped(1, ladder.D1.init(1)),
        fromTyped(2, ladder.D2.init(1)),
        fromTyped(3, ladder.D3.init(0b001)),
        fromTyped(8, ladder.D8.init(0b10101000)),
        fromTyped(9, ladder.D9.init(0b010101000)),
    };
    try std.testing.expectEqual(source[3].bits, source[4].bits);
    try std.testing.expect(!source[3].same(source[4]));
    var bytes: [128]u8 = undefined;
    var tmp: [5]e1.Word = undefined;
    var plan: [6]writer.Step = undefined;
    const len = try encode(&source, &bytes, &tmp, &plan);
    var decoded: [5]ladder.Coordinate = undefined;
    var replay: [128]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 5),
        try decode(bytes[0..len], &decoded, &tmp, &plan, &replay));
    for (source, decoded) |left, right| try std.testing.expect(left.same(right));
    try std.testing.expect(!decoded[0].same(decoded[1]));
}

test "invalid bits, D10 and short caller buffers never write output" {
    const valid = fromTyped(9, ladder.D9.init(1));
    const bad = ladder.Coordinate{ .width = 2, .bits = 4 };
    const too_wide = fromTyped(10, ladder.D10.init(1));
    var bytes: [64]u8 = [_]u8{0xa5} ** 64;
    var tmp: [2]e1.Word = undefined;
    var plan: [3]writer.Step = undefined;
    try std.testing.expectError(error.PayloadOverflow,
        encode(&.{ valid, bad }, &bytes, &tmp, &plan));
    try std.testing.expectError(error.UnsupportedCarrierWidth,
        encode(&.{ valid, too_wide }, &bytes, &tmp, &plan));
    try std.testing.expectError(error.BufferTooSmall,
        encode(&.{valid}, &bytes, tmp[0..0], &plan));
    try std.testing.expectError(error.BufferTooSmall,
        encode(&.{valid}, &bytes, &tmp, plan[0..1]));
    for (bytes) |v| try std.testing.expectEqual(@as(u8, 0xa5), v);
}

test "noncanonical alias and CRC one-bit mutant never publish domain coordinates" {
    const source = [_]ladder.Coordinate{fromTyped(1, ladder.D1.init(1))};
    var bytes: [64]u8 = undefined;
    var tmp: [1]e1.Word = undefined;
    var steps: [2]writer.Step = undefined;
    const n = try encode(&source, &bytes, &tmp, &steps);
    var out: [1]ladder.Coordinate = .{.{ .width = 9, .bits = 256 }};
    var replay: [64]u8 = undefined;
    bytes[n - 1] ^= 1;
    try std.testing.expectError(error.IntegrityMismatch,
        decode(bytes[0..n], &out, &tmp, &steps, &replay));
    try std.testing.expectEqual(@as(u8, 9), out[0].width);
    const head = [_]u8{ 'S', '3', 1, 1, 1, 1, 1, 0x80 };
    var alias: [12]u8 = undefined;
    @memcpy(alias[0..8], &head);
    const crc = fields.crc32(&head);
    alias[8] = @intCast(crc >> 24);
    alias[9] = @intCast((crc >> 16) & 0xff);
    alias[10] = @intCast((crc >> 8) & 0xff);
    alias[11] = @intCast(crc & 0xff);
    try std.testing.expectError(error.NonCanonical,
        decode(&alias, &out, &tmp, &steps, &replay));
    try std.testing.expectEqual(@as(u16, 256), out[0].bits);
}

test "129 mixed D8 D9 values cross E1 block limit without width collapse" {
    var source: [129]ladder.Coordinate = undefined;
    for (&source, 0..) |*word, i|
        word.* = if (i % 2 == 0)
            fromTyped(8, ladder.D8.init(0b10101000))
        else
            fromTyped(9, ladder.D9.init(0b010101000));
    var physical: [1024]u8 = undefined;
    var tmp: [129]e1.Word = undefined;
    var steps: [130]writer.Step = undefined;
    const len = try encode(&source, &physical, &tmp, &steps);
    var out: [129]ladder.Coordinate = undefined;
    var replay: [1024]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 129),
        try decode(physical[0..len], &out, &tmp, &steps, &replay));
    for (source, out) |left, right| try std.testing.expect(left.same(right));
}

test "empty E1 is a valid physical envelope but not semantic admission" {
    var bytes: [16]u8 = undefined;
    var tmp: [1]e1.Word = undefined;
    var steps: [1]writer.Step = undefined;
    const len = try encode(&.{}, &bytes, &tmp, &steps);
    try std.testing.expectEqualSlices(u8,
        &.{ 'S', '3', 1, 0, 0xc7, 0xca, 0x15, 0xd8 }, bytes[0..len]);
    var out: [1]ladder.Coordinate = undefined;
    var replay: [16]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 0),
        try decode(bytes[0..len], &out, &tmp, &steps, &replay));
}

test "E1 maximum 4096 words preserves D8 D9 widths and 4097 fails without publishing" {
    // Same opaque payload, different contemporary domains: exact width survives
    // the largest permitted E1 coordinate stream. This is transport, not callability.
    var source: [e1.MAX_WORDS + 1]ladder.Coordinate = undefined;
    for (&source, 0..) |*coordinate, i| {
        coordinate.* = if (i % 2 == 0)
            fromTyped(8, ladder.D8.init(0b00000001))
        else
            fromTyped(9, ladder.D9.init(0b000000001));
    }
    try std.testing.expectEqual(source[0].bits, source[1].bits);
    try std.testing.expect(!source[0].same(source[1]));

    var physical: [8192]u8 = [_]u8{0xa5} ** 8192;
    var temp: [e1.MAX_WORDS]e1.Word = undefined;
    var steps: [e1.MAX_WORDS + 1]writer.Step = undefined;
    // 4097 is outside the admitted physical count; never touch caller output.
    try std.testing.expectError(error.TooLarge,
        encode(&source, &physical, &temp, &steps));
    for (physical) |byte| try std.testing.expectEqual(@as(u8, 0xa5), byte);

    const size = try encode(source[0..e1.MAX_WORDS], &physical, &temp, &steps);
    try std.testing.expect(size > 0 and size < physical.len);
    const exact_bytes = physical;
    try std.testing.expectError(error.BufferTooSmall,
        encode(source[0..e1.MAX_WORDS], physical[0 .. size - 1], &temp, &steps));
    try std.testing.expectEqualSlices(u8, &exact_bytes, &physical);

    var restored: [e1.MAX_WORDS]ladder.Coordinate = undefined;
    var replay: [8192]u8 = undefined;
    try std.testing.expectEqual(@as(usize, e1.MAX_WORDS),
        try decode(physical[0..size], &restored, &temp, &steps, &replay));
    for (source[0..e1.MAX_WORDS], restored) |expected, actual|
        try std.testing.expect(expected.same(actual));
    const previous = restored;
    try std.testing.expectError(error.BufferTooSmall,
        decode(physical[0..size], restored[0 .. e1.MAX_WORDS - 1],
            &temp, &steps, &replay));
    for (previous, restored) |expected, actual|
        try std.testing.expect(expected.same(actual));
}


test "E1 coordinate adapter rejects all host aliasing before publishing any bytes" {
    const source = [_]ladder.Coordinate{fromTyped(1, ladder.D1.init(1))};
    var plan: [2]writer.Step = undefined;

    // Regression: former code staged words and clobbered this output BEFORE
    // writer.encode finally returned OverlappingBuffers.
    var shared: [8]e1.Word = undefined;
    const shared_bytes = std.mem.sliceAsBytes(shared[0..]);
    @memset(shared_bytes, 0xa5);
    try std.testing.expectError(error.OverlappingBuffers,
        encode(&source, shared_bytes, shared[0..1], &plan));
    for (shared_bytes) |byte|
        try std.testing.expectEqual(@as(u8, 0xa5), byte);

    var mutable_source = source;
    const source_bytes = std.mem.sliceAsBytes(mutable_source[0..]);
    var temp: [1]e1.Word = undefined;
    try std.testing.expectError(error.OverlappingBuffers,
        encode(&mutable_source, source_bytes, &temp, &plan));
    try std.testing.expect(mutable_source[0].same(source[0]));

    var frame: [64]u8 = undefined;
    const len = try encode(&source, &frame, &temp, &plan);
    var words: [1]e1.Word = undefined;
    var steps: [2]writer.Step = undefined;
    var replay: [64]u8 = undefined;

    // Frame and coordinate output share backing storage: neither byte of
    // the original CRC-checked physical frame may be overwritten.
    var shared_coords: [4]ladder.Coordinate = undefined;
    const coordinate_bytes = std.mem.sliceAsBytes(shared_coords[0..]);
    try std.testing.expect(coordinate_bytes.len >= len);
    @memcpy(coordinate_bytes[0..len], frame[0..len]);
    try std.testing.expectError(error.OverlappingBuffers,
        decode(coordinate_bytes[0..len], shared_coords[0..1],
            &words, &steps, &replay));
    try std.testing.expectEqualSlices(u8, frame[0..len], coordinate_bytes[0..len]);

    @memset(coordinate_bytes, 0xa5);
    try std.testing.expectError(error.OverlappingBuffers,
        decode(frame[0..len], shared_coords[0..1],
            &words, &steps, coordinate_bytes));
    for (coordinate_bytes) |byte|
        try std.testing.expectEqual(@as(u8, 0xa5), byte);

    // Nonaliased host buffers still preserve exact width and payload.
    var result: [1]ladder.Coordinate = undefined;
    try std.testing.expectEqual(@as(usize, 1),
        try decode(frame[0..len], &result, &words, &steps, &replay));
    try std.testing.expect(source[0].same(result[0]));
}
