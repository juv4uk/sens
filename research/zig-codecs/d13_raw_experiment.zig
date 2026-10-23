//! Research raw13: 13 фізичних бітів/слово, НЕ числовий домен SENS.
//! Нормативна numeric family D(12*2^n) НЕ містить D13.
//! Explicit route обирає codec; frame = BE32 word_count + payload.
//! В обох форматах той самий count header; ніяких auto-detect/magic.
//! Dense payload MSB-first, нульовий low tail; BE16 має нульові high 3 біти.
const std = @import("std");
pub const Codec = enum { dense13, be16 };
pub const Error = error{ EmptyRun, TooLarge, InvalidWord, OutputTooSmall, Truncated, InvalidLength, NonCanonicalTail };
pub const HEADER_BYTES: usize = 4;

pub fn payloadLen(codec: Codec, count: usize) Error!usize {
    if (count == 0) return error.EmptyRun;
    if (count > std.math.maxInt(u32)) return error.TooLarge;
    if (codec == .be16) return std.math.mul(usize, count, 2) catch return error.TooLarge;
    const bits = std.math.mul(usize, count, 13) catch return error.TooLarge;
    return (std.math.add(usize, bits, 7) catch return error.TooLarge) / 8;
}
pub fn frameLen(codec: Codec, count: usize) Error!usize {
    return std.math.add(usize, HEADER_BYTES, try payloadLen(codec, count)) catch error.TooLarge;
}
fn writeCount(out: []u8, count: usize) void {
    const n: u32 = @intCast(count);
    for (0..4) |i| {
        const shift: u5 = @intCast((3 - i) * 8);
        out[i] = @intCast((n >> shift) & 255);
    }
}
pub fn wordCount(data: []const u8) Error!usize {
    if (data.len < HEADER_BYTES) return error.Truncated;
    var count: u32 = 0;
    for (data[0..4]) |b| count = (count << 8) | b;
    if (count == 0) return error.EmptyRun;
    return @intCast(count);
}
/// До завершення перевірок помилки не змінюють жодного output byte.
pub fn encode(codec: Codec, words: []const u16, output: []u8) Error!usize {
    const size = try frameLen(codec, words.len);
    for (words) |word| if (word > 0x1fff) return error.InvalidWord;
    if (output.len < size) return error.OutputTooSmall;
    writeCount(output, words.len);
    const payload = output[HEADER_BYTES..size];
    if (codec == .be16) {
        for (words, 0..) |word, i| {
            payload[i * 2] = @intCast(word >> 8);
            payload[i * 2 + 1] = @intCast(word & 255);
        }
    } else {
        @memset(payload, 0);
        for (words, 0..) |word, i| {
            for (0..13) |bit| {
                const at = i * 13 + bit;
                const source_shift: u4 = @intCast(12 - bit);
                const dest_shift: u3 = @intCast(7 - at % 8);
                payload[at / 8] |= @as(u8, @intCast((word >> source_shift) & 1)) << dest_shift;
            }
        }
    }
    return size;
}
/// Exact frame length + canonical bits до першого запису у output.
pub fn decode(codec: Codec, data: []const u8, output: []u16) Error!usize {
    const count = try wordCount(data);
    const size = try frameLen(codec, count);
    if (data.len != size) return error.InvalidLength;
    if (output.len < count) return error.OutputTooSmall;
    const payload = data[HEADER_BYTES..];
    if (codec == .be16) {
        var at: usize = 0;
        while (at < payload.len) : (at += 2) {
            if ((payload[at] & 0xe0) != 0) return error.InvalidWord;
        }
    } else {
        const used = (count * 13) % 8;
        if (used != 0) {
            const unused: u3 = @intCast(8 - used);
            const mask: u8 = (@as(u8, 1) << unused) - 1;
            if ((payload[payload.len - 1] & mask) != 0) return error.NonCanonicalTail;
        }
    }
    for (0..count) |i| {
        if (codec == .be16) {
            output[i] = (@as(u16, payload[i * 2]) << 8) | payload[i * 2 + 1];
        } else {
            var word: u16 = 0;
            for (0..13) |bit| {
                const at = i * 13 + bit;
                const shift: u3 = @intCast(7 - at % 8);
                word = (word << 1) | @as(u16, (payload[at / 8] >> shift) & 1);
            }
            output[i] = word;
        }
    }
    return count;
}

test "raw13 exact frame, leading zeros and independent BE16 parity" {
    const source = [_]u16{ 0, 1, 0x1fff, 0x1000 };
    var frame: [12]u8 = undefined;
    const n = try encode(.dense13, &source, &frame);
    try std.testing.expectEqual(@as(usize, 11), n);
    try std.testing.expectEqualSlices(u8, &.{ 0, 0, 0, 4, 0, 0, 0, 0x7f, 0xff, 0, 0 }, frame[0..n]);
    var output: [4]u16 = undefined;
    inline for (.{ Codec.dense13, Codec.be16 }) |codec| {
        const len = try encode(codec, &source, &frame);
        try std.testing.expectEqual(source.len, try decode(codec, frame[0..len], &output));
        try std.testing.expectEqualSlices(u16, &source, &output);
    }
    try std.testing.expectEqualSlices(u8, &.{ 0, 0, 0, 4, 0, 0, 0, 1, 0x1f, 0xff, 0x10, 0 }, &frame);
}
test "raw13 exhaustive all 8192 words with complementary partner" {
    for (0..8192) |i| {
        const v: u16 = @intCast(i);
        const source = [_]u16{ v, v ^ 0x1fff };
        var frame: [8]u8 = undefined;
        var output: [2]u16 = undefined;
        inline for (.{ Codec.dense13, Codec.be16 }) |codec| {
            const len = try encode(codec, &source, &frame);
            _ = try decode(codec, frame[0..len], &output);
            try std.testing.expectEqualSlices(u16, &source, &output);
        }
    }
}
test "raw13 seeded pseudorandom boundary counts and replay" {
    var source: [1025]u16 = undefined;
    var state: u32 = 0x13c0ffee;
    for (&source) |*word| {
        state = state *% 1664525 +% 1013904223;
        word.* = @intCast((state >> 16) & 0x1fff);
    }
    var frame: [2054]u8 = undefined;
    var replay: [2054]u8 = undefined;
    var output: [1025]u16 = undefined;
    for ([_]usize{ 1, 2, 7, 8, 9, 63, 64, 65, 1023, 1024, 1025 }) |count| {
        inline for (.{ Codec.dense13, Codec.be16 }) |codec| {
            const n = try encode(codec, source[0..count], &frame);
            _ = try decode(codec, frame[0..n], &output);
            try std.testing.expectEqualSlices(u16, source[0..count], output[0..count]);
            const m = try encode(codec, output[0..count], &replay);
            try std.testing.expectEqualSlices(u8, frame[0..n], replay[0..m]);
        }
    }
}
test "raw13 rejects bad metadata range lengths and padding atomically" {
    var bytes = [_]u8{0xa5} ** 8;
    try std.testing.expectError(error.InvalidWord, encode(.dense13, &.{0x2000}, &bytes));
    try std.testing.expectEqualSlices(u8, &([_]u8{0xa5} ** 8), &bytes);
    try std.testing.expectError(error.OutputTooSmall, encode(.be16, &.{1}, bytes[0..5]));
    try std.testing.expectEqualSlices(u8, &([_]u8{0xa5} ** 8), &bytes);
    var out = [_]u16{0xbeef} ** 2;
    try std.testing.expectError(error.Truncated, decode(.dense13, &.{ 0, 0, 0 }, &out));
    try std.testing.expectError(error.EmptyRun, decode(.dense13, &.{ 0, 0, 0, 0 }, &out));
    try std.testing.expectError(error.NonCanonicalTail, decode(.dense13, &.{ 0, 0, 0, 1, 0, 1 }, &out));
    try std.testing.expectError(error.InvalidWord, decode(.be16, &.{ 0, 0, 0, 1, 0x20, 0 }, &out));
    try std.testing.expectError(error.InvalidLength, decode(.dense13, &.{ 0, 0, 0, 2, 0, 0 }, &out));
    try std.testing.expectError(error.InvalidLength, decode(.dense13, &.{ 0, 0, 0, 1, 0, 0, 0 }, &out));
    try std.testing.expectError(error.OutputTooSmall, decode(.dense13, &.{ 0, 0, 0, 2, 0, 0, 0, 0 }, out[0..1]));
    try std.testing.expectEqualSlices(u16, &.{ 0xbeef, 0xbeef }, &out);
    try std.testing.expectError(error.EmptyRun, payloadLen(.dense13, 0));
    try std.testing.expectError(error.TooLarge, frameLen(.dense13, std.math.maxInt(usize)));
}
