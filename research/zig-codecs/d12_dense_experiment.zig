//! Драбина кодеків · рівень 1: щільний фізичний D12-run (дослідний).
//! Рівно 12 сирих бітів на слово, MSB-first; два слова займають три байти.
//! Кількість слів задає викликач явно. Це payload, НЕ самовизначальний кадр.
//! Код не вгадує домен, знак, дріб, float або виконуваність SENS.
//! Немає auto-detect/fallback до T5M, T5M3, F3C чи інших форматів.

const std = @import("std");

pub const WIDTH: usize = 12;
pub const Error = error{
    EmptyRun,
    InvalidWord,
    OutputTooSmall,
    InvalidLength,
    NonCanonicalTail,
    TooLarge,
};

/// Кількість байтів payload; у непарного останнє півбайта — нульове.
pub fn packedLen(word_count: usize) Error!usize {
    if (word_count == 0) return Error.EmptyRun;
    const pairs = std.math.mul(usize, word_count / 2, 3) catch return Error.TooLarge;
    return std.math.add(usize, pairs, if (word_count % 2 == 0) @as(usize, 0) else 2) catch
        return Error.TooLarge;
}

/// Транспортує непрозорі 12-бітні слова без втрати старших нулів.
/// За помилки жоден байт output не змінюється.
pub fn encode(words: []const u16, output: []u8) Error!usize {
    const n = try packedLen(words.len);
    for (words) |word| {
        if (word > 0x0fff) return Error.InvalidWord;
    }
    if (output.len < n) return Error.OutputTooSmall;
    @memset(output[0..n], 0);

    for (words, 0..) |word, i| {
        const base = (i / 2) * 3;
        if (i % 2 == 0) {
            output[base] = @intCast(word >> 4);
            output[base + 1] = @intCast((word & 0x000f) << 4);
        } else {
            output[base + 1] |= @intCast(word >> 8);
            output[base + 2] = @intCast(word & 0x00ff);
        }
    }
    return n;
}

/// Відновлює рівно word_count слів. Невірна довжина чи padding — відмова.
/// За помилки жодне слово output не змінюється.
pub fn decode(data: []const u8, word_count: usize, output: []u16) Error!void {
    const n = try packedLen(word_count);
    if (data.len != n) return Error.InvalidLength;
    if (output.len < word_count) return Error.OutputTooSmall;
    if (word_count % 2 != 0 and (data[n - 1] & 0x0f) != 0)
        return Error.NonCanonicalTail;

    for (0..word_count) |i| {
        const base = (i / 2) * 3;
        output[i] = if (i % 2 == 0)
            (@as(u16, data[base]) << 4) | (@as(u16, data[base + 1]) >> 4)
        else
            ((@as(u16, data[base + 1]) & 0x0f) << 8) | @as(u16, data[base + 2]);
    }
}

test "D12 dense fixed vector preserves boundaries and leading zeros" {
    const source = [_]u16{ 0x800, 0xfff, 0x000, 0x001, 0x7ff };
    var bytes: [8]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 8), try encode(&source, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0x80, 0x0f, 0xff, 0x00, 0x00, 0x01, 0x7f, 0xf0 }, &bytes);

    var decoded: [source.len]u16 = undefined;
    try decode(&bytes, source.len, &decoded);
    try std.testing.expectEqualSlices(u16, &source, &decoded);
}

test "D12 dense exhaustive 4096 raw words with complementary partner" {
    for (0..4096) |i| {
        const a: u16 = @intCast(i);
        const source = [_]u16{ a, a ^ 0x0fff };
        var bytes: [3]u8 = undefined;
        try std.testing.expectEqual(@as(usize, 3), try encode(&source, &bytes));
        var decoded: [2]u16 = undefined;
        try decode(&bytes, source.len, &decoded);
        try std.testing.expectEqualSlices(u16, &source, &decoded);
    }
}

test "D12 dense exact byte ordering and run lengths" {
    const pairs = [_]struct { words: [2]u16, bytes: [3]u8 }{
        .{ .words = .{ 0x000, 0xfff }, .bytes = .{ 0x00, 0x0f, 0xff } },
        .{ .words = .{ 0xfff, 0x000 }, .bytes = .{ 0xff, 0xf0, 0x00 } },
        .{ .words = .{ 0xabc, 0x123 }, .bytes = .{ 0xab, 0xc1, 0x23 } },
        .{ .words = .{ 0x7ff, 0x800 }, .bytes = .{ 0x7f, 0xf8, 0x00 } },
    };
    for (pairs) |sample| {
        var bytes: [3]u8 = undefined;
        _ = try encode(&sample.words, &bytes);
        try std.testing.expectEqualSlices(u8, &sample.bytes, &bytes);
        var decoded: [2]u16 = undefined;
        try decode(&bytes, 2, &decoded);
        try std.testing.expectEqualSlices(u16, &sample.words, &decoded);
    }

    const counts = [_]usize{ 1, 2, 3, 4, 5, 16, 127, 128, 129 };
    const lengths = [_]usize{ 2, 3, 5, 6, 8, 24, 191, 192, 194 };
    for (counts, lengths) |count, expected| {
        try std.testing.expectEqual(expected, try packedLen(count));
    }
}

test "D12 dense rejects invalid payload without modifying output" {
    var bytes = [_]u8{0xa5} ** 3;
    try std.testing.expectError(Error.InvalidWord, encode(&.{ 0x1000, 0x000 }, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5 }, &bytes);

    var short = [_]u8{0xa5} ** 2;
    try std.testing.expectError(Error.OutputTooSmall, encode(&.{ 0xabc, 0x123 }, &short));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5 }, &short);

    var decoded = [_]u16{0xaaaa};
    try std.testing.expectError(Error.NonCanonicalTail, decode(&.{ 0xab, 0xc1 }, 1, &decoded));
    try std.testing.expectError(Error.InvalidLength, decode(&.{0xab}, 1, &decoded));
    try std.testing.expectError(Error.InvalidLength, decode(&.{ 0xab, 0xc0, 0x00 }, 1, &decoded));
    try std.testing.expectEqualSlices(u16, &.{0xaaaa}, &decoded);

    try std.testing.expectError(Error.EmptyRun, packedLen(0));
    try std.testing.expectError(Error.TooLarge, packedLen(std.math.maxInt(usize)));
}
