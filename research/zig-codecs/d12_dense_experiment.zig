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
    // Кожний байт записується рівно один раз: додаткове занулення зайве.
    var i: usize = 0;
    var offset: usize = 0;
    while (i + 1 < words.len) {
        const first = words[i];
        const second = words[i + 1];
        output[offset] = @intCast(first >> 4);
        output[offset + 1] = @intCast(((first & 0x000f) << 4) | (second >> 8));
        output[offset + 2] = @intCast(second & 0x00ff);
        i += 2;
        offset += 3;
    }
    if (i < words.len) {
        const last = words[i];
        output[offset] = @intCast(last >> 4);
        output[offset + 1] = @intCast((last & 0x000f) << 4);
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

test "D12 dense overwrites reused nonzero buffers canonically" {
    var output = [_]u8{0xa5} ** 8;

    const first_len = try encode(&.{0xabc}, &output);
    try std.testing.expectEqual(@as(usize, 2), first_len);
    try std.testing.expectEqualSlices(u8, &.{ 0xab, 0xc0 }, output[0..first_len]);

    const second_len = try encode(&.{ 0x123, 0x456, 0x789 }, &output);
    try std.testing.expectEqual(@as(usize, 5), second_len);
    try std.testing.expectEqualSlices(u8, &.{ 0x12, 0x34, 0x56, 0x78, 0x90 }, output[0..second_len]);

    const third_len = try encode(&.{ 0xfff, 0x000 }, &output);
    try std.testing.expectEqual(@as(usize, 3), third_len);
    try std.testing.expectEqualSlices(u8, &.{ 0xff, 0xf0, 0x00 }, output[0..third_len]);
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

test "D12 dense long and odd runs preserve bytes on reencode" {
    const counts = [_]usize{ 1, 2, 3, 5, 16, 127, 128, 129, 4095, 4096 };
    var words: [4096]u16 = undefined;
    var decoded: [4096]u16 = undefined;
    var bytes: [6144]u8 = undefined;
    var replay: [6144]u8 = undefined;

    for (counts) |count| {
        for (0..count) |i| {
            words[i] = @intCast((i * 73 + (i >> 1) * 137) & 0x0fff);
        }
        const n = try encode(words[0..count], &bytes);
        try decode(bytes[0..n], count, decoded[0..count]);
        try std.testing.expectEqualSlices(u16, words[0..count], decoded[0..count]);

        const replay_n = try encode(decoded[0..count], &replay);
        try std.testing.expectEqual(n, replay_n);
        try std.testing.expectEqualSlices(u8, bytes[0..n], replay[0..replay_n]);
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

    var short_decoded = [_]u16{0xbeef};
    try std.testing.expectError(Error.OutputTooSmall, decode(&.{ 0xab, 0xc1, 0x23 }, 2, &short_decoded));
    try std.testing.expectEqualSlices(u16, &.{0xbeef}, &short_decoded);

    var untouched = [_]u8{0xa5} ** 5;
    try std.testing.expectError(Error.InvalidWord, encode(&.{ 0xabc, 0x123, 0x1000 }, &untouched));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5, 0xa5, 0xa5 }, &untouched);

    try std.testing.expectError(Error.EmptyRun, packedLen(0));
    try std.testing.expectError(Error.TooLarge, packedLen(std.math.maxInt(usize)));
}
