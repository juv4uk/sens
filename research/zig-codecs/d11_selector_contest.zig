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
const benchmark_byte_capacity: usize = selector_count * @sizeOf(u16); // raw16 is the widest contest mode

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
    var accumulator: u64 = 0;
    var pending: u7 = 0;
    var output_index: usize = 0;
    for (words) |word| {
        accumulator = (accumulator << width) | @as(u64, word - base);
        pending += width;
        while (pending >= 8) {
            pending -= 8;
            output[output_index] = @truncate(accumulator >> @as(u6, @intCast(pending)));
            output_index += 1;
        }
        accumulator &= (@as(u64, 1) << @as(u6, @intCast(pending))) - 1;
    }
    if (pending != 0) {
        output[output_index] = @truncate(accumulator << @as(u6, @intCast(8 - pending)));
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
    var accumulator: u64 = 0;
    var pending: u7 = 0;
    var input_index: usize = 0;
    const value_mask = (@as(u64, 1) << width) - 1;
    for (output[0..count]) |*word| {
        while (pending < width) {
            accumulator = (accumulator << 8) | data[input_index];
            input_index += 1;
            pending += 8;
        }
        pending -= width;
        word.* = base + @as(u16, @intCast((accumulator >> @as(u6, @intCast(pending))) & value_mask));
        accumulator &= (@as(u64, 1) << @as(u6, @intCast(pending))) - 1;
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

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;
const sample_count: usize = 15;
const minimum_sample_ns: u64 = 2_000_000;
const maximum_repetitions: usize = 1 << 20;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

const Codec = enum { selector9, dense11, raw16 };

fn codecName(codec: Codec) []const u8 {
    return switch (codec) {
        .selector9 => "selector9",
        .dense11 => "dense11",
        .raw16 => "raw16",
    };
}

/// Явний байтовий еталон без стискання: абсолютна координата u16 big-endian.
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

fn encode(codec: Codec, words: []const u16, output: []u8) Error!usize {
    return switch (codec) {
        .selector9 => encodeSelectors(words, output),
        .dense11 => encodeD11(words, output),
        .raw16 => encodeRaw16(words, output),
    };
}

fn decode(codec: Codec, data: []const u8, count: usize, output: []u16) Error!void {
    return switch (codec) {
        .selector9 => decodeSelectors(data, count, output),
        .dense11 => decodeD11(data, count, output),
        .raw16 => decodeRaw16(data, count, output),
    };
}

const Measurement = struct {
    ns_per_roundtrip: u64,
    repetitions: usize,
};

/// Одна одиниця роботи — encode + decode того самого набору координат.
/// Перевірка семантичного результату тут відсутня: це механічне вимірювання.
fn timedBatch(
    codec: Codec,
    words: []const u16,
    repetitions: usize,
    bytes: *[benchmark_byte_capacity]u8,
    restored: *[selector_count]u16,
) Error!u64 {
    const start = nanoseconds();
    for (0..repetitions) |_| {
        const n = try encode(codec, words, bytes);
        try decode(codec, bytes[0..n], words.len, restored);
        std.mem.doNotOptimizeAway(bytes[0..n]);
        std.mem.doNotOptimizeAway(restored[0..words.len]);
    }
    return nanoseconds() - start;
}

fn measure(
    codec: Codec,
    words: []const u16,
    bytes: *[benchmark_byte_capacity]u8,
    restored: *[selector_count]u16,
) Error!Measurement {
    var repetitions: usize = 1;
    while (true) {
        const elapsed = try timedBatch(codec, words, repetitions, bytes, restored);
        if (elapsed >= minimum_sample_ns or repetitions >= maximum_repetitions) {
            return .{
                .ns_per_roundtrip = @max(@as(u64, 1), elapsed / @as(u64, @intCast(repetitions))),
                .repetitions = repetitions,
            };
        }
        repetitions *= 2;
    }
}

fn percentile(samples_in: [sample_count]u64, rank: usize) u64 {
    var sorted = samples_in;
    // Small fixed-size insertion sort avoids an extra library or allocation.
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

fn benchmarkCount(count: usize, offset: usize) !void {
    var words: [selector_count]u16 = undefined;
    for (0..count) |i| {
        // 64-word workload exercises a dispersed subset; 512 covers every selector.
        words[i] = selector_first + @as(u16, @intCast((i * 73 + offset) % selector_count));
    }
    const input = words[0..count];

    var bytes: [benchmark_byte_capacity]u8 = undefined;
    var restored: [selector_count]u16 = undefined;
    const codecs = [_]Codec{ .selector9, .dense11, .raw16 };
    var byte_sizes: [codecs.len]usize = undefined;

    // Same-word, exact-roundtrip preflight precedes any timing.
    for (codecs, 0..) |codec, index| {
        const n = try encode(codec, input, &bytes);
        byte_sizes[index] = n;
        try decode(codec, bytes[0..n], count, &restored);
        if (!std.mem.eql(u16, input, restored[0..count])) return error.RoundtripMismatch;
    }

    var samples: [codecs.len][sample_count]u64 = undefined;
    var minimum_reps: [codecs.len]usize = undefined;
    var maximum_reps: [codecs.len]usize = undefined;
    for (0..codecs.len) |i| {
        minimum_reps[i] = maximum_repetitions;
        maximum_reps[i] = 0;
    }

    // Identical unmeasured warmups; then alternate codec order by sample.
    for (codecs) |codec| {
        _ = try timedBatch(codec, input, 4, &bytes, &restored);
    }
    for (0..sample_count) |sample_index| {
        for (0..codecs.len) |slot| {
            const codec_index = if (sample_index % 2 == 0) slot else codecs.len - 1 - slot;
            const result = try measure(codecs[codec_index], input, &bytes, &restored);
            samples[codec_index][sample_index] = result.ns_per_roundtrip;
            minimum_reps[codec_index] = @min(minimum_reps[codec_index], result.repetitions);
            maximum_reps[codec_index] = @max(maximum_reps[codec_index], result.repetitions);
        }
    }

    const raw16_p50 = percentile(samples[2], 7);
    for (codecs, 0..) |codec, index| {
        const p50 = percentile(samples[index], 7);
        const p90 = percentile(samples[index], 13);
        const bytes_per_word_milli = byte_sizes[index] * 1000 / count;
        const ratio_vs_raw16_milli = p50 * 1000 / @max(@as(u64, 1), raw16_p50);
        std.debug.print(
            "D11_CONTEST mode={s} words={d} bytes={d} bytes_per_word_milli={d} p50_ns_per_roundtrip={d} p90_ns_per_roundtrip={d} ratio_vs_raw16_milli={d} samples={d} reps_min={d} reps_max={d} roundtrip=EXACT paired=YES\n",
            .{
                codecName(codec),    count,               byte_sizes[index],    bytes_per_word_milli,
                p50,                 p90,                 ratio_vs_raw16_milli, sample_count,
                minimum_reps[index], maximum_reps[index],
            },
        );
    }
}

pub fn main() !void {
    // For every size, all codecs see exactly the same D11 coordinates.
    try benchmarkCount(64, 0);
    try benchmarkCount(selector_count, 0);
    std.debug.print(
        "D11_CONTEST_METHOD paired=YES alternating=YES samples={d} target_sample_ns={d} semantic_oracle=NOT_USED modes=selector9,dense11,raw16\n",
        .{ sample_count, minimum_sample_ns },
    );
}
