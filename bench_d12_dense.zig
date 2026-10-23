//! Драбина кодеків: чесний A/B щільних D12 слів і явного BE16.
//! 4096 однакових 12-бітних слів; caller-owned buffers, жодної семантики SENS.
//! Повний roundtrip і byte-exact replay перед 11 парними пробами.
//! Це порівняння payload-механізмів, не T5M/F3C кадрів.

const std = @import("std");
const dense = @import("research/zig-codecs/d12_dense_experiment.zig");

const word_count: usize = 4096;
const dense_bytes: usize = 6144;
const be16_bytes: usize = 8192;
const samples: usize = 11;
const min_sample_ns: u64 = 25_000_000;
const batch: usize = 128;
const max_batches: usize = 100_000;

fn encodeBe16(words: []const u16, out: []u8) !void {
    if (out.len != words.len * 2) return error.InvalidLength;
    for (words) |word| {
        if (word > 0x0fff) return error.InvalidWord;
    }
    for (words, 0..) |word, i| {
        out[2 * i] = @intCast(word >> 8);
        out[2 * i + 1] = @intCast(word & 0xff);
    }
}

fn decodeBe16(bytes: []const u8, out: []u16) !void {
    if (bytes.len != out.len * 2) return error.InvalidLength;
    for (0..out.len) |i| {
        if ((bytes[2 * i] & 0xf0) != 0) return error.InvalidWord;
    }
    for (0..out.len) |i| {
        out[i] = (@as(u16, bytes[2 * i]) << 8) | @as(u16, bytes[2 * i + 1]);
    }
}

fn sortedCopy(values: [samples]u64) [samples]u64 {
    var result = values;
    for (1..result.len) |i| {
        var j = i;
        while (j > 0 and result[j] < result[j - 1]) : (j -= 1) {
            std.mem.swap(u64, &result[j], &result[j - 1]);
        }
    }
    return result;
}

const Operation = enum { dense_encode, be16_encode, dense_decode, be16_decode };

fn measure(
    comptime operation: Operation,
    io: std.Io,
    words: []const u16,
    dense_buf: []u8,
    bytes16: []u8,
    restored: []u16,
) !u64 {
    const started = std.Io.Clock.awake.now(io);
    var elapsed_ns: u64 = 0;
    var calls: u64 = 0;
    var batches: usize = 0;
    while (elapsed_ns < min_sample_ns) {
        for (0..batch) |_| {
            switch (operation) {
                .dense_encode => {
                    const size = try dense.encode(words, dense_buf);
                    std.mem.doNotOptimizeAway(dense_buf[size - 1]);
                },
                .be16_encode => {
                    try encodeBe16(words, bytes16);
                    std.mem.doNotOptimizeAway(bytes16[bytes16.len - 1]);
                },
                .dense_decode => {
                    try dense.decode(dense_buf, words.len, restored);
                    std.mem.doNotOptimizeAway(restored[restored.len - 1]);
                },
                .be16_decode => {
                    try decodeBe16(bytes16, restored);
                    std.mem.doNotOptimizeAway(restored[restored.len - 1]);
                },
            }
        }
        calls += batch;
        batches += 1;
        elapsed_ns = @intCast(started.untilNow(io, .awake).toNanoseconds());
        if (batches >= max_batches and elapsed_ns < min_sample_ns)
            return error.SampleBudgetExceeded;
    }
    if (calls == 0 or elapsed_ns < calls) return error.InsufficientClockResolution;
    return elapsed_ns / calls;
}

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    var words: [word_count]u16 = undefined;
    for (0..word_count) |i| {
        words[i] = @intCast((i * 73 + (i >> 1) * 137) & 0x0fff);
    }
    var dense_buf: [dense_bytes]u8 = undefined;
    var bytes16: [be16_bytes]u8 = undefined;
    var restored: [word_count]u16 = undefined;
    var replay: [dense_bytes]u8 = undefined;
    var replay16: [be16_bytes]u8 = undefined;

    // Приймання в конкурс: однакові слова і побайтова канонічна оберненість.
    if (try dense.encode(&words, &dense_buf) != dense_bytes) return error.DenseLength;
    try dense.decode(&dense_buf, word_count, &restored);
    if (!std.mem.eql(u16, &words, &restored)) return error.DenseRoundtrip;
    if (try dense.encode(&restored, &replay) != dense_bytes) return error.DenseReplayLength;
    if (!std.mem.eql(u8, &dense_buf, &replay)) return error.DenseReplay;
    try encodeBe16(&words, &bytes16);
    try decodeBe16(&bytes16, &restored);
    if (!std.mem.eql(u16, &words, &restored)) return error.Be16Roundtrip;
    try encodeBe16(&restored, &replay16);
    if (!std.mem.eql(u8, &bytes16, &replay16)) return error.Be16Replay;

    // Один прогрів кожного шляху, поза таймером.
    _ = try dense.encode(&words, &dense_buf);
    try encodeBe16(&words, &bytes16);
    try dense.decode(&dense_buf, word_count, &restored);
    try decodeBe16(&bytes16, &restored);

    var de: [samples]u64 = undefined;
    var be: [samples]u64 = undefined;
    var dd: [samples]u64 = undefined;
    var bd: [samples]u64 = undefined;
    for (0..samples) |i| {
        if (i % 2 == 0) {
            de[i] = try measure(.dense_encode, io, &words, &dense_buf, &bytes16, &restored);
            be[i] = try measure(.be16_encode, io, &words, &dense_buf, &bytes16, &restored);
            dd[i] = try measure(.dense_decode, io, &words, &dense_buf, &bytes16, &restored);
            bd[i] = try measure(.be16_decode, io, &words, &dense_buf, &bytes16, &restored);
        } else {
            be[i] = try measure(.be16_encode, io, &words, &dense_buf, &bytes16, &restored);
            de[i] = try measure(.dense_encode, io, &words, &dense_buf, &bytes16, &restored);
            bd[i] = try measure(.be16_decode, io, &words, &dense_buf, &bytes16, &restored);
            dd[i] = try measure(.dense_decode, io, &words, &dense_buf, &bytes16, &restored);
        }
        std.debug.print(
            "D12_AB_SAMPLE index={d} dense_encode_ns={d} be16_encode_ns={d} dense_decode_ns={d} be16_decode_ns={d}\n",
            .{ i + 1, de[i], be[i], dd[i], bd[i] },
        );
    }
    const de_sorted = sortedCopy(de);
    const be_sorted = sortedCopy(be);
    const dd_sorted = sortedCopy(dd);
    const bd_sorted = sortedCopy(bd);
    std.debug.print(
        "D12_AB_RESULT words={d} dense_bytes={d} be16_bytes={d} samples={d} min_sample_ns={d} dense_encode_p50_ns={d} be16_encode_p50_ns={d} dense_decode_p50_ns={d} be16_decode_p50_ns={d} dense_encode_p90_ns={d} be16_encode_p90_ns={d} dense_decode_p90_ns={d} be16_decode_p90_ns={d} scope=raw-payload-only semantic=NOT_TESTED\n",
        .{ word_count, dense_bytes, be16_bytes, samples, min_sample_ns, de_sorted[5], be_sorted[5], dd_sorted[5], bd_sorted[5], de_sorted[9], be_sorted[9], dd_sorted[9], bd_sorted[9] },
    );
}
