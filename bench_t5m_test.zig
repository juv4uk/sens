//! Власні Zig-тести фізичного T5M-коридору: байти, ширини й відмови.
//! Жодного оцінювання SENS-виразів або логічних законів.
//! Запуск: zig test -O ReleaseFast -lc bench_t5m_test.zig
const std = @import("std");
const codec = @import("research/zig-codecs/t5m.zig");
const benchmark = @import("bench_t5m.zig");
const physical: []const u8 = @embedFile("benchmarks/lists.sens");

test "t5m real physical corpus is byte-exact after decode encode" {
    const allocator = std.testing.allocator;
    var decoded = try codec.decode(allocator, physical);
    defer decoded.deinit(allocator);
    try std.testing.expect(decoded.words.len > 0);

    const words = try allocator.alloc(codec.Word, decoded.words.len);
    defer allocator.free(words);
    for (decoded.words, 0..) |word, i| {
        words[i] = .{ .width = word.width, .bits = word.bits };
    }
    const encoded = try codec.encode(allocator, words);
    defer allocator.free(encoded);
    try std.testing.expectEqualSlices(u8, physical, encoded);
}

test "t5m transport retains exact widths and leading zeros" {
    const allocator = std.testing.allocator;
    const words = [_]codec.Word{
        .{ .width = 1, .bits = "0" },
        .{ .width = 9, .bits = "000000001" },
        .{ .width = 12, .bits = "000000000010" },
    };
    const encoded = try codec.encode(allocator, &words);
    defer allocator.free(encoded);
    var decoded = try codec.decode(allocator, encoded);
    defer decoded.deinit(allocator);

    try std.testing.expect(decoded.words.len == words.len);
    for (words, decoded.words) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqualSlices(u8, expected.bits, actual.bits);
    }
}

test "t5m rejects malformed physical bytes and invalid padding" {
    const allocator = std.testing.allocator;
    try std.testing.expectError(error.EmptyProgram, codec.decode(allocator, &[_]u8{}));
    try std.testing.expectError(error.InvalidPhysicalByte, codec.decode(allocator, &[_]u8{243}));
    try std.testing.expectError(error.InvalidTail, codec.decode(allocator, &[_]u8{242}));
}

test "t5m rejects non-binary source words" {
    const allocator = std.testing.allocator;
    const invalid = [_]codec.Word{.{ .width = 3, .bits = "012" }};
    try std.testing.expectError(error.InvalidBinaryDigit, codec.encode(allocator, &invalid));
    try std.testing.expectError(error.EmptyProgram, codec.encode(allocator, &[_]codec.Word{}));
}

test "t5m benchmark alternates corridor operations outside semantics" {
    const first = benchmark.orderForSample(0);
    const second = benchmark.orderForSample(1);
    try std.testing.expectEqual(benchmark.Operation.decode, first[0]);
    try std.testing.expectEqual(benchmark.Operation.encode, first[1]);
    try std.testing.expectEqual(benchmark.Operation.encode, second[0]);
    try std.testing.expectEqual(benchmark.Operation.decode, second[1]);
}
