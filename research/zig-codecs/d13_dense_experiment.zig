//! Драбина D13: дослідна фізична щільність 13-бітних слів.
//! Це НЕ ратифікація семантичного D13 і НЕ ESC13 (окремий формат кадру).
//! Чинний математичний закон: D12, D24, D48...; D13 до нього не входить.
//! Контекст ширини, версії та кількості слів мусить надати зовнішня рамка.
//! Zig перевіряє лише точне перенесення бітів; Lisp/SENS визначає семантику.

const std = @import("std");

pub const width: usize = 13;
pub const max_word: u16 = 0x1fff;
pub const Error = error{
    EmptyRun,
    TooLarge,
    InvalidWord,
    OutputTooSmall,
    InvalidLength,
    NonCanonicalTail,
};

pub fn packedLen(count: usize) Error!usize {
    if (count == 0) return error.EmptyRun;
    const bits = std.math.mul(usize, count, width) catch return error.TooLarge;
    const rounded = std.math.add(usize, bits, 7) catch return error.TooLarge;
    return rounded / 8;
}

/// MSB-first; усі зайві молодші біти останнього байта дорівнюють нулю.
/// Недопустиме слово чи замалий буфер залишають output незмінним.
pub fn encode(words: []const u16, output: []u8) Error!usize {
    const n = try packedLen(words.len);
    for (words) |word| {
        if (word > max_word) return error.InvalidWord;
    }
    if (output.len < n) return error.OutputTooSmall;
    @memset(output[0..n], 0);
    for (words, 0..) |word, i| {
        for (0..width) |j| {
            const cursor = i * width + j;
            const bit: u8 = @intCast((word >> @as(u4, @intCast(width - j - 1))) & 1);
            output[cursor / 8] |= bit << @as(u3, @intCast(7 - cursor % 8));
        }
    }
    return n;
}

/// Немає auto-detect ширини або толерантності до зіпсованого хвоста.
/// За помилки вихідні слова не змінюються.
pub fn decode(data: []const u8, count: usize, output: []u16) Error!void {
    const n = try packedLen(count);
    if (data.len != n) return error.InvalidLength;
    if (output.len < count) return error.OutputTooSmall;
    const padding = n * 8 - count * width;
    if (padding != 0) {
        const mask: u8 = (@as(u8, 1) << @as(u3, @intCast(padding))) - 1;
        if ((data[n - 1] & mask) != 0) return error.NonCanonicalTail;
    }
    for (0..count) |i| {
        var word: u16 = 0;
        for (0..width) |j| {
            const cursor = i * width + j;
            word = (word << 1) | @as(u16, (data[cursor / 8] >> @as(u3, @intCast(7 - cursor % 8))) & 1);
        }
        output[i] = word;
    }
}

test "D13 research: all 8192 possible raw words roundtrip" {
    for (0..8192) |i| {
        const source = [_]u16{@intCast(i)};
        var bytes: [2]u8 = undefined;
        try std.testing.expectEqual(@as(usize, 2), try encode(&source, &bytes));
        var restored: [1]u16 = undefined;
        try decode(&bytes, 1, &restored);
        try std.testing.expectEqualSlices(u16, &source, &restored);
    }
}

test "D13 research: exact order, leading zeros and useful lengths" {
    const sample = [_]u16{ 0x0000, 0x1fff };
    var bytes: [4]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 4), try encode(&sample, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0x00, 0x07, 0xff, 0xc0 }, &bytes);
    var restored: [2]u16 = undefined;
    try decode(&bytes, 2, &restored);
    try std.testing.expectEqualSlices(u16, &sample, &restored);

    const counts = [_]usize{ 1, 2, 3, 4, 5, 64, 512 };
    const lengths = [_]usize{ 2, 4, 5, 7, 9, 104, 832 };
    for (counts, lengths) |count, expected| {
        try std.testing.expectEqual(expected, try packedLen(count));
    }
}

test "D13 research: long streams are bit- and byte-exact" {
    const counts = [_]usize{ 1, 2, 3, 7, 31, 32, 33, 64, 511, 512 };
    var source: [512]u16 = undefined;
    var restored: [512]u16 = undefined;
    var bytes: [832]u8 = undefined;
    var replay: [832]u8 = undefined;
    for (counts) |count| {
        for (0..count) |i| {
            source[i] = @intCast((i * 113 + (i >> 1) * 41) & 0x1fff);
        }
        const n = try encode(source[0..count], &bytes);
        try decode(bytes[0..n], count, restored[0..count]);
        try std.testing.expectEqualSlices(u16, source[0..count], restored[0..count]);
        const replay_n = try encode(restored[0..count], &replay);
        try std.testing.expectEqual(n, replay_n);
        try std.testing.expectEqualSlices(u8, bytes[0..n], replay[0..replay_n]);
    }
}

test "D13 research: malformed input fails without touching output" {
    var bytes = [_]u8{0xa5} ** 4;
    try std.testing.expectError(error.InvalidWord, encode(&.{ 0x1fff, 0x2000 }, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5, 0xa5 }, &bytes);
    try std.testing.expectError(error.OutputTooSmall, encode(&.{ 0x0000, 0x1fff }, bytes[0..3]));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5, 0xa5 }, &bytes);

    var restored = [_]u16{0xbeef};
    try std.testing.expectError(error.NonCanonicalTail, decode(&.{ 0xff, 0xf9 }, 1, &restored));
    try std.testing.expectError(error.InvalidLength, decode(&.{0xff}, 1, &restored));
    try std.testing.expectError(error.InvalidLength, decode(&.{ 0xff, 0xf8, 0x00 }, 1, &restored));
    try std.testing.expectError(error.OutputTooSmall, decode(&.{ 0x00, 0x07, 0xff, 0xc0 }, 2, &restored));
    try std.testing.expectEqual(@as(u16, 0xbeef), restored[0]);

    try std.testing.expectError(error.EmptyRun, packedLen(0));
    try std.testing.expectError(error.TooLarge, packedLen(std.math.maxInt(usize)));
}

const CTimespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *CTimespec) c_int;
const clock_monotonic: c_int = 1;
const sample_count: usize = 15;
const minimum_sample_ns: u64 = 2_000_000;
const maximum_repetitions: usize = 1 << 20;

fn nowNs() u64 {
    var ts: CTimespec = undefined;
    if (clock_gettime(clock_monotonic, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

const Mode = enum { dense13, raw16 };

fn modeName(mode: Mode) []const u8 {
    return switch (mode) {
        .dense13 => "dense13",
        .raw16 => "raw16",
    };
}

/// Raw16 є тільки порівняльним byte carrier, а не доменом D16.
fn encodeRaw16(words: []const u16, output: []u8) Error!usize {
    if (words.len == 0) return error.EmptyRun;
    const n = std.math.mul(usize, words.len, 2) catch return error.TooLarge;
    if (output.len < n) return error.OutputTooSmall;
    for (words, 0..) |word, i| {
        output[2 * i] = @intCast(word >> 8);
        output[2 * i + 1] = @truncate(word);
    }
    return n;
}

fn decodeRaw16(data: []const u8, count: usize, output: []u16) Error!void {
    if (count == 0) return error.EmptyRun;
    const n = std.math.mul(usize, count, 2) catch return error.TooLarge;
    if (data.len != n) return error.InvalidLength;
    if (output.len < count) return error.OutputTooSmall;
    for (0..count) |i| {
        output[i] = (@as(u16, data[2 * i]) << 8) | @as(u16, data[2 * i + 1]);
    }
}

fn timedBatch(
    mode: Mode,
    words: []const u16,
    repetitions: usize,
    bytes: *[1024]u8,
    restored: *[512]u16,
) Error!u64 {
    const start = nowNs();
    for (0..repetitions) |_| {
        const n = switch (mode) {
            .dense13 => try encode(words, bytes),
            .raw16 => try encodeRaw16(words, bytes),
        };
        switch (mode) {
            .dense13 => try decode(bytes[0..n], words.len, restored),
            .raw16 => try decodeRaw16(bytes[0..n], words.len, restored),
        }
        std.mem.doNotOptimizeAway(bytes[0..n]);
        std.mem.doNotOptimizeAway(restored[0..words.len]);
    }
    return nowNs() - start;
}

fn sample(mode: Mode, words: []const u16, bytes: *[1024]u8, restored: *[512]u16) Error!u64 {
    var repetitions: usize = 1;
    while (true) {
        const elapsed = try timedBatch(mode, words, repetitions, bytes, restored);
        if (elapsed >= minimum_sample_ns or repetitions >= maximum_repetitions) {
            return @max(@as(u64, 1), elapsed / @as(u64, @intCast(repetitions)));
        }
        repetitions *= 2;
    }
}

fn percentile(input: [sample_count]u64, rank: usize) u64 {
    var sorted = input;
    for (1..sorted.len) |i| {
        const value = sorted[i];
        var j = i;
        while (j > 0 and sorted[j - 1] > value) : (j -= 1) {
            sorted[j] = sorted[j - 1];
        }
        sorted[j] = value;
    }
    return sorted[rank];
}

fn benchmark(count: usize) !void {
    var source: [512]u16 = undefined;
    for (0..count) |i| {
        source[i] = @intCast((i * 113 + (i >> 1) * 41) & 0x1fff);
    }
    const words = source[0..count];
    var bytes: [1024]u8 = undefined;
    var restored: [512]u16 = undefined;
    const modes = [_]Mode{ .dense13, .raw16 };
    var sizes: [2]usize = undefined;
    for (modes, 0..) |mode, i| {
        sizes[i] = switch (mode) {
            .dense13 => try encode(words, &bytes),
            .raw16 => try encodeRaw16(words, &bytes),
        };
        switch (mode) {
            .dense13 => try decode(bytes[0..sizes[i]], count, &restored),
            .raw16 => try decodeRaw16(bytes[0..sizes[i]], count, &restored),
        }
        if (!std.mem.eql(u16, words, restored[0..count])) return error.RoundtripMismatch;
    }
    for (modes) |mode| {
        _ = try timedBatch(mode, words, 4, &bytes, &restored);
    }
    var samples: [2][sample_count]u64 = undefined;
    for (0..sample_count) |run| {
        for (0..modes.len) |slot| {
            const i = if (run % 2 == 0) slot else modes.len - 1 - slot;
            samples[i][run] = try sample(modes[i], words, &bytes, &restored);
        }
    }
    const raw_p50 = percentile(samples[1], 7);
    for (modes, 0..) |mode, i| {
        const p50 = percentile(samples[i], 7);
        const p90 = percentile(samples[i], 13);
        std.debug.print(
            "D13_EXPERIMENT mode={s} words={d} bytes={d} p50_ns_roundtrip={d} p90_ns_roundtrip={d} ratio_raw16_milli={d} samples={d} roundtrip=EXACT frame=EXCLUDED semantics=NOT_TESTED\n",
            .{ modeName(mode), count, sizes[i], p50, p90, p50 * 1000 / @max(@as(u64, 1), raw_p50), sample_count },
        );
    }
}

pub fn main() !void {
    try benchmark(64);
    try benchmark(512);
    std.debug.print("D13_EXPERIMENT_METHOD width=13 corpus=deterministic-113-plus-41 paired=YES alternating=YES samples=15 benchmark=encode-plus-decode only\n", .{});
}
