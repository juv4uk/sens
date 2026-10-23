//! Конкурс «Драбина D11»: запам'ятати всі 512 селекторів і щільно передати їх.
//! Лише експериментальний Zig-транспорт: 9-бітний зсув застосовний ТІЛЬКИ
//! до явно оголошеного потоку селекторів D11 [01100000000, 10011111111].
//! Контекст (режим, кількість слів, версія) має надати зовнішній кадр.
//! Це не SENS-eval, не новий opcode і не ратифікація інших координат D11.

const std = @import("std");

const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fgets([*]u8, c_int, *CFile) ?[*]u8;

pub const selector_first: u16 = 0b01100000000;
pub const selector_last: u16 = 0b10011111111;
pub const selector_count: usize = 512;

pub const Error = error{
    EmptyRun,
    TooLarge,
    InvalidWord,
    OutputTooSmall,
    InvalidLength,
    NonCanonicalTail,
};

fn packedLen(comptime width: usize, count: usize) Error!usize {
    if (count == 0) return error.EmptyRun;
    const bits = std.math.mul(usize, count, width) catch return error.TooLarge;
    const rounded = std.math.add(usize, bits, 7) catch return error.TooLarge;
    return rounded / 8;
}

pub fn selectorPackedLen(count: usize) Error!usize {
    return packedLen(9, count);
}

fn encodeWords(comptime width: usize, comptime base: u16, words: []const u16, output: []u8) Error!usize {
    const n = try packedLen(width, words.len);
    const limit: u16 = base + (@as(u16, 1) << @as(u4, @intCast(width)));
    for (words) |word| {
        if (word < base or word >= limit) return error.InvalidWord;
    }
    if (output.len < n) return error.OutputTooSmall;
    @memset(output[0..n], 0);
    for (words, 0..) |word, i| {
        const value: u16 = word - base;
        for (0..width) |j| {
            const cursor = i * width + j;
            const bit: u8 = @intCast((value >> @as(u4, @intCast(width - j - 1))) & 1);
            output[cursor / 8] |= bit << @as(u3, @intCast(7 - cursor % 8));
        }
    }
    return n;
}

fn decodeWords(comptime width: usize, comptime base: u16, data: []const u8, count: usize, output: []u16) Error!void {
    const n = try packedLen(width, count);
    if (data.len != n) return error.InvalidLength;
    if (output.len < count) return error.OutputTooSmall;
    const padding = n * 8 - count * width;
    if (padding != 0) {
        const mask: u8 = (@as(u8, 1) << @as(u3, @intCast(padding))) - 1;
        if ((data[n - 1] & mask) != 0) return error.NonCanonicalTail;
    }
    for (0..count) |i| {
        var value: u16 = 0;
        for (0..width) |j| {
            const cursor = i * width + j;
            value = (value << 1) | @as(u16, (data[cursor / 8] >> @as(u3, @intCast(7 - cursor % 8))) & 1);
        }
        output[i] = base + value;
    }
}

/// 9-бітний локальний індекс; режим потоку має бути заданий явно.
pub fn encodeSelectors(words: []const u16, output: []u8) Error!usize {
    return encodeWords(9, selector_first, words, output);
}

pub fn decodeSelectors(data: []const u8, count: usize, output: []u16) Error!void {
    return decodeWords(9, selector_first, data, count, output);
}

/// Референсний щільний D11 — 11 біт на координату, без спеціалізації.
pub fn encodeD11(words: []const u16, output: []u8) Error!usize {
    return encodeWords(11, 0, words, output);
}

pub fn decodeD11(data: []const u8, count: usize, output: []u16) Error!void {
    return decodeWords(11, 0, data, count, output);
}

/// Незалежно від таблиці відтворити всі 512 Lisp-імен за законом селектора.
/// Старший біт індексу вибирає D/A, наступні 8 біт — A/D.
fn selectorName(word: u16) [11]u8 {
    const offset = word - selector_first;
    var name: [11]u8 = undefined;
    name[0] = 'C';
    name[1] = if ((offset & 0x100) == 0) 'D' else 'A';
    for (0..8) |i| {
        name[i + 2] = if (((offset >> @as(u4, @intCast(7 - i))) & 1) == 0) 'A' else 'D';
    }
    name[10] = 'R';
    return name;
}

test "D11 Драбина: усі 512 селекторів мають точний roundtrip" {
    for (0..selector_count) |i| {
        const source = [_]u16{selector_first + @as(u16, @intCast(i))};
        var payload: [2]u8 = undefined;
        try std.testing.expectEqual(@as(usize, 2), try encodeSelectors(&source, &payload));
        var decoded: [1]u16 = undefined;
        try decodeSelectors(&payload, 1, &decoded);
        try std.testing.expectEqualSlices(u16, &source, &decoded);
    }
}

test "D11 Драбина: запам'ятати всі 512 координат і Lisp-імен таблиці" {
    const file = fopen("lib/domains/d11.lisp", "rb") orelse return error.TableNotFound;
    defer _ = fclose(file);
    var line_buffer: [2048]u8 = undefined;
    var next: u16 = selector_first;
    while (fgets(line_buffer[0..].ptr, @intCast(line_buffer.len), file) != null) {
        const end = std.mem.indexOfScalar(u8, &line_buffer, 0) orelse return error.LineTooLong;
        const line = line_buffer[0..end];
        if (!std.mem.startsWith(u8, line, "  (")) continue;
        if (line.len < 15 or line[14] != ' ') continue;
        const bits = line[3..14];
        const word = std.fmt.parseInt(u16, bits, 2) catch return error.InvalidWord;
        try std.testing.expectEqual(next, word);
        const name = selectorName(word);
        var needle_buf: [24]u8 = undefined;
        const needle = try std.fmt.bufPrint(&needle_buf, "(LISP {s})", .{name[0..]});
        try std.testing.expect(std.mem.indexOf(u8, line, needle) != null);
        next += 1;
    }
    try std.testing.expectEqual(selector_last + 1, next);
}

test "D11 Драбина: 9, 11 і 16 біт — чесний облік байтів" {
    try std.testing.expectEqual(@as(usize, 72), try selectorPackedLen(64));
    try std.testing.expectEqual(@as(usize, 88), try packedLen(11, 64));
    try std.testing.expectEqual(@as(usize, 128), try packedLen(16, 64));
    var source: [64]u16 = undefined;
    for (&source, 0..) |*word, i| {
        word.* = selector_first + @as(u16, @intCast((i * 73) % selector_count));
    }
    var compressed: [72]u8 = undefined;
    var general: [88]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 72), try encodeSelectors(&source, &compressed));
    try std.testing.expectEqual(@as(usize, 88), try encodeD11(&source, &general));
    var decoded: [64]u16 = undefined;
    try decodeSelectors(&compressed, source.len, &decoded);
    try std.testing.expectEqualSlices(u16, &source, &decoded);
    try decodeD11(&general, source.len, &decoded);
    try std.testing.expectEqualSlices(u16, &source, &decoded);
}

test "D11 Драбина: чужі координати, обрізання та хвіст не змінюють вихід" {
    const sentinel = [_]u8{0xa5} ** 9;
    var output = sentinel;
    try std.testing.expectError(error.InvalidWord, encodeSelectors(&.{selector_first - 1}, &output));
    try std.testing.expectEqualSlices(u8, &sentinel, &output);
    try std.testing.expectError(error.InvalidWord, encodeSelectors(&.{selector_last + 1}, &output));
    try std.testing.expectEqualSlices(u8, &sentinel, &output);
    try std.testing.expectError(error.EmptyRun, encodeSelectors(&.{}, &output));
    try std.testing.expectError(error.OutputTooSmall, encodeSelectors(&.{ selector_first, selector_last }, output[0..1]));
    try std.testing.expectEqualSlices(u8, &sentinel, &output);

    const source = [_]u16{selector_first};
    var bytes: [2]u8 = undefined;
    _ = try encodeSelectors(&source, &bytes);
    var back = [_]u16{0xbeef};
    bytes[1] |= 1; // 7 незначущих хвостових бітів для одного 9-бітного слова
    try std.testing.expectError(error.NonCanonicalTail, decodeSelectors(&bytes, 1, &back));
    try std.testing.expectEqual(@as(u16, 0xbeef), back[0]);
    try std.testing.expectError(error.InvalidLength, decodeSelectors(bytes[0..1], 1, &back));
    try std.testing.expectEqual(@as(u16, 0xbeef), back[0]);
}

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

fn benchmark(comptime width: usize, comptime base: u16, label: []const u8, words: []const u16) !void {
    var bytes: [88]u8 = undefined;
    var restored: [64]u16 = undefined;
    const n = try encodeWords(width, base, words, &bytes);
    try decodeWords(width, base, bytes[0..n], words.len, &restored);
    if (!std.mem.eql(u16, words, &restored)) return error.RoundtripMismatch;
    const reps: usize = 20_000;
    var start = nanoseconds();
    for (0..reps) |_| {
        _ = try encodeWords(width, base, words, &bytes);
        std.mem.doNotOptimizeAway(&bytes);
    }
    const encode_ns = nanoseconds() - start;
    start = nanoseconds();
    for (0..reps) |_| {
        try decodeWords(width, base, bytes[0..n], words.len, &restored);
        std.mem.doNotOptimizeAway(&restored);
    }
    const decode_ns = nanoseconds() - start;
    std.debug.print("D11_CONTEST mode={s} words={d} bytes={d} encode_ns_per_op={d} decode_ns_per_op={d} reps={d} roundtrip=EXACT\n", .{
        label, words.len, n, encode_ns / reps, decode_ns / reps, reps,
    });
}

pub fn main() !void {
    var words: [64]u16 = undefined;
    for (&words, 0..) |*word, i| {
        word.* = selector_first + @as(u16, @intCast((i * 73) % selector_count));
    }
    try benchmark(9, selector_first, "selector9", &words);
    try benchmark(11, 0, "dense11", &words);
    std.debug.print("D11_CONTEST raw16_bytes=128 selector9_scope=EXPLICIT_ONLY semantics=NOT_TESTED\n", .{});
}
