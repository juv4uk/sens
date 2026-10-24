//! Zig 0.16: фізична перевірка T5M, без мовного оракула SENS.
//! Виконувати zig test окремо від zig run бенчмарка.
const std = @import("std");
const codec = @import("research/zig-codecs/t5m.zig");
const benchmark = @import("bench_t5m.zig");
const physical: []const u8 = @embedFile("benchmarks/lists.sens");

test "physical T5M fixture is canonical and malformed bytes fail closed" {
    const allocator = std.testing.allocator;
    var decoded = try codec.decode(allocator, physical);
    defer decoded.deinit(allocator);
    const words = try allocator.alloc(codec.Word, decoded.words.len);
    defer allocator.free(words);
    for (decoded.words, 0..) |word, i| {
        words[i] = .{ .width = word.width, .bits = word.bits };
    }
    const replay = try codec.encode(allocator, words);
    defer allocator.free(replay);
    try std.testing.expectEqualSlices(u8, physical, replay);

    // Fail-closed negative controls match the active T5M codec error categories.
    // These test transport mechanics only; they are not SENS D1 false values.
    try std.testing.expectError(error.EmptyProgram, codec.decode(allocator, &.{}));
    try std.testing.expectError(error.InvalidPhysicalByte, codec.decode(allocator, &.{243}));
    try std.testing.expectError(error.InvalidTail, codec.decode(allocator, &.{242}));
}

test "T5M benchmark alternates decode and encode order across paired samples" {
    const expected = [_][2]benchmark.Operation{
        .{ .decode, .encode },
        .{ .encode, .decode },
        .{ .decode, .encode },
        .{ .encode, .decode },
    };
    for (expected, 0..) |pair, sample| {
        const actual = benchmark.orderForSample(sample);
        try std.testing.expectEqual(pair[0], actual[0]);
        try std.testing.expectEqual(pair[1], actual[1]);
    }
}

test "T5M benchmark observer sees full single-word payload before release" {
    const allocator = std.testing.allocator;
    const Spy = struct {
        var encoded_first: u8 = 0;
        var decoded_first: u8 = 0;

        fn encoded(bytes: []const u8) void {
            std.debug.assert(bytes.len == 1);
            encoded_first = bytes[0];
        }

        fn decoded(words: []const codec.DecodedWord, bit_storage: []const u8) void {
            std.debug.assert(words.len == 1 and bit_storage.len == 1);
            decoded_first = bit_storage[0];
        }
    };
    const cases = [_]struct { bits: []const u8, physical_byte: u8 }{
        .{ .bits = "0", .physical_byte = 80 },
        .{ .bits = "1", .physical_byte = 161 },
    };
    for (cases) |case| {
        Spy.encoded_first = 0xff;
        Spy.decoded_first = 0xff;
        const words = [_]codec.Word{.{ .width = 1, .bits = case.bits }};
        const encoded_count = try benchmark.encodeOnce(allocator, &words, Spy.encoded);
        try std.testing.expectEqual(@as(usize, 1), encoded_count);
        try std.testing.expectEqual(case.physical_byte, Spy.encoded_first);

        const physical_word = [_]u8{case.physical_byte};
        const decoded_count = try benchmark.decodeOnce(allocator, &physical_word, Spy.decoded);
        try std.testing.expectEqual(@as(usize, 1), decoded_count);
        try std.testing.expectEqual(case.bits[0], Spy.decoded_first);
    }
}
