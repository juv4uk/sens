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
