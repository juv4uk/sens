//! Zig 0.16: тільки механіка T5M encode/decode, без Lisp-оракула.
//! Детермінований корпус точних бітових слів (жодних SENS-функцій); 11 парних проб.
//! Замість видаленого std.time.Timer використовується Io.Clock.awake.

const std = @import("std");
const codec = @import("research/zig-codecs/t5m.zig");

fn sortedCopy(values: [11]u64) [11]u64 {
    var sorted = values;
    for (1..sorted.len) |i| {
        var j = i;
        while (j > 0 and sorted[j] < sorted[j - 1]) : (j -= 1) {
            std.mem.swap(u64, &sorted[j], &sorted[j - 1]);
        }
    }
    return sorted;
}

pub const Operation = enum { decode, encode };

/// Парний A/B порядок: кожна друга проба починається з encode.
pub fn orderForSample(sample: usize) [2]Operation {
    return if (sample % 2 == 0) .{ .decode, .encode } else .{ .encode, .decode };
}


fn observeDecoded(words: []const codec.DecodedWord, bit_storage: []const u8) void {
    // Escape both allocations before deinit: a length-only sink permits
    // dead-store elimination of payload work in ReleaseFast.
    std.mem.doNotOptimizeAway(words.ptr);
    std.mem.doNotOptimizeAway(bit_storage.ptr);
}

fn observeEncoded(bytes: []const u8) void {
    std.mem.doNotOptimizeAway(bytes.ptr);
}

/// One measured operation, shared by the native Zig test and timed loop.
/// The observer receives the live payload before its buffer is freed.
pub fn decodeOnce(
    allocator: std.mem.Allocator,
    bytes: []const u8,
    comptime observer: fn ([]const codec.DecodedWord, []const u8) void,
) !usize {
    var decoded = try codec.decode(allocator, bytes);
    defer decoded.deinit(allocator);
    // Keep both output allocations observable in ReleaseFast even if an
    // observer changes: the pointer escape is part of the measured helper.
    std.mem.doNotOptimizeAway(decoded.words.ptr);
    std.mem.doNotOptimizeAway(decoded.bit_storage.ptr);
    observer(decoded.words, decoded.bit_storage);
    return decoded.words.len;
}

pub fn encodeOnce(
    allocator: std.mem.Allocator,
    words: []const codec.Word,
    comptime observer: fn ([]const u8) void,
) !usize {
    const encoded = try codec.encode(allocator, words);
    defer allocator.free(encoded);
    // The bytes must remain materialized until the observer has run.
    std.mem.doNotOptimizeAway(encoded.ptr);
    observer(encoded);
    return encoded.len;
}

pub fn main(init: std.process.Init) !void {
    const allocator = std.heap.page_allocator;
    const io = init.io;
    const iterations: usize = 128;

    // Zig owns only opaque exact-width bits. Generate a reproducible physical
    // T5M input in this corridor, with no SENS language law or corpus filename.
    var input_bits: [128][7]u8 = undefined;
    var input_words: [128]codec.Word = undefined;
    for (0..input_words.len) |i| {
        for (0..7) |j| {
            input_bits[i][j] = if ((i + j) % 3 == 0) '1' else '0';
        }
        input_words[i] = .{ .width = 7, .bits = input_bits[i][0..] };
    }
    const physical = try codec.encode(allocator, input_words[0..]);
    defer allocator.free(physical);

    var original = try codec.decode(allocator, physical);
    defer original.deinit(allocator);
    const words = try allocator.alloc(codec.Word, original.words.len);
    defer allocator.free(words);
    for (original.words, 0..) |word, i| {
        words[i] = .{ .width = word.width, .bits = word.bits };
    }
    const roundtrip = try codec.encode(allocator, words);
    defer allocator.free(roundtrip);
    if (!std.mem.eql(u8, physical, roundtrip)) return error.NonCanonicalPhysicalCorpus;
    if (original.words.len == 0) return error.EmptyCorpus;

    const sample_count: usize = 11;
    const min_sample_ns: u64 = 25_000_000;
    const max_batches: usize = 100_000;
    var decode_ns_per_op: [sample_count]u64 = undefined;
    var encode_ns_per_op: [sample_count]u64 = undefined;
    var guard: usize = 0;

    // Прогрів поза таймером на тому самому корпусі і тому самому codec.
    for (0..iterations) |_| {
        guard += try decodeOnce(allocator, physical, observeDecoded);
    }
    for (0..iterations) |_| {
        guard += try encodeOnce(allocator, words, observeEncoded);
    }

    // Калібруємо кожну пробу за мінімальною тривалістю, а не за фіксованими
    // 128 операціями. Кількість пакетів зберігаємо, щоб отримати ns/operation.
    for (0..sample_count) |sample| {
        const order = orderForSample(sample);
        var decode_elapsed_sample: u64 = 0;
        var decode_ops_sample: u64 = 0;
        var encode_elapsed_sample: u64 = 0;
        var encode_ops_sample: u64 = 0;
        for (order) |operation| {
            switch (operation) {
                .decode => {
                    const decode_started = std.Io.Clock.awake.now(io);
                    var elapsed_decode: u64 = 0;
                    var decoded_ops: u64 = 0;
                    var decode_batches: usize = 0;
                    while (elapsed_decode < min_sample_ns) {
                        for (0..iterations) |_| {
                            guard += try decodeOnce(allocator, physical, observeDecoded);
                        }
                        decoded_ops += @intCast(iterations);
                        decode_batches += 1;
                        elapsed_decode = @intCast(decode_started.untilNow(io, .awake).toNanoseconds());
                        if (decode_batches >= max_batches and elapsed_decode < min_sample_ns)
                            return error.SampleBudgetExceeded;
                    }
                    if (elapsed_decode == 0 or decoded_ops == 0) return error.InsufficientClockResolution;
                    decode_ns_per_op[sample] = elapsed_decode / decoded_ops;
                    decode_elapsed_sample = elapsed_decode;
                    decode_ops_sample = decoded_ops;
                },
                .encode => {
                    const encode_started = std.Io.Clock.awake.now(io);
                    var elapsed_encode: u64 = 0;
                    var encoded_ops: u64 = 0;
                    var encode_batches: usize = 0;
                    while (elapsed_encode < min_sample_ns) {
                        for (0..iterations) |_| {
                            guard += try encodeOnce(allocator, words, observeEncoded);
                        }
                        encoded_ops += @intCast(iterations);
                        encode_batches += 1;
                        elapsed_encode = @intCast(encode_started.untilNow(io, .awake).toNanoseconds());
                        if (encode_batches >= max_batches and elapsed_encode < min_sample_ns)
                            return error.SampleBudgetExceeded;
                    }
                    if (elapsed_encode == 0 or encoded_ops == 0) return error.InsufficientClockResolution;
                    encode_ns_per_op[sample] = elapsed_encode / encoded_ops;
                    encode_elapsed_sample = elapsed_encode;
                    encode_ops_sample = encoded_ops;
                },
            }
        }
        std.debug.print(
            "ZIG_T5M_SAMPLE sample={d} decode_elapsed_ns={d} decode_ops={d} decode_ns_per_op={d} encode_elapsed_ns={d} encode_ops={d} encode_ns_per_op={d} target_sample_ns={d} first={s}\n",
            .{ sample + 1, decode_elapsed_sample, decode_ops_sample, decode_ns_per_op[sample], encode_elapsed_sample, encode_ops_sample, encode_ns_per_op[sample], min_sample_ns, @tagName(order[0]) },
        );
    }
    const d = sortedCopy(decode_ns_per_op);
    const e = sortedCopy(encode_ns_per_op);
    if (d[0] == 0 or e[0] == 0) return error.InsufficientClockResolution;
    std.debug.print(
        "ZIG_T5M_BENCH physical_bytes={d} words={d} samples={d} min_sample_ns={d} decode_min_ns_per_op={d} decode_p50_ns_per_op={d} decode_p90_ns_per_op={d} decode_max_ns_per_op={d} encode_min_ns_per_op={d} encode_p50_ns_per_op={d} encode_p90_ns_per_op={d} encode_max_ns_per_op={d} scope=zig-codec-only input=deterministic-opaque-words guard={d}\n",
        .{ physical.len, words.len, sample_count, min_sample_ns, d[0], d[5], d[9], d[sample_count - 1], e[0], e[5], e[9], e[sample_count - 1], guard },
    );
}
