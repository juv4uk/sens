//! Zig 0.16: тільки механіка T5M encode/decode, без Lisp-оракула.
//! Фізичний файл із репозиторію, SHA/версія фіксуються CI; 11 сирих проб.
//! Замість видаленого std.time.Timer використовується Io.Clock.awake.

const std = @import("std");
const codec = @import("research/zig-codecs/t5m.zig");
const physical: []const u8 = @embedFile("benchmarks/lists.sens");

// Порядок вимірювань чергується, щоб систематичний дрейф часу
// не давав одній операції постійної переваги першого виміру.
pub const Operation = enum { decode, encode };

pub fn orderForSample(sample: usize) [2]Operation {
    return if (sample % 2 == 0)
        .{ .decode, .encode }
    else
        .{ .encode, .decode };
}

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

pub fn main(init: std.process.Init) !void {
    const allocator = std.heap.page_allocator;
    const io = init.io;
    const iterations: usize = 128;

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
        var decoded = try codec.decode(allocator, physical);
        guard += decoded.words.len;
        std.mem.doNotOptimizeAway(decoded.words.len);
        decoded.deinit(allocator);
    }
    for (0..iterations) |_| {
        const encoded = try codec.encode(allocator, words);
        guard += encoded.len;
        std.mem.doNotOptimizeAway(encoded.len);
        allocator.free(encoded);
    }

    // Калібруємо кожну пробу за мінімальною тривалістю, а не за фіксованими
    // 128 операціями. Кількість пакетів зберігаємо, щоб отримати ns/operation.
    for (0..sample_count) |sample| {
        var elapsed_decode: u64 = 0;
        var decoded_ops: u64 = 0;
        var decode_batches: usize = 0;
        var elapsed_encode: u64 = 0;
        var encoded_ops: u64 = 0;
        var encode_batches: usize = 0;

        for (orderForSample(sample)) |operation| {
            switch (operation) {
                .decode => {
                    const decode_started = std.Io.Clock.awake.now(io);
                    while (elapsed_decode < min_sample_ns) {
                        for (0..iterations) |_| {
                            var decoded = try codec.decode(allocator, physical);
                            guard += decoded.words.len;
                            std.mem.doNotOptimizeAway(decoded.words.len);
                            decoded.deinit(allocator);
                        }
                        decoded_ops += @intCast(iterations);
                        decode_batches += 1;
                        elapsed_decode = @intCast(decode_started.untilNow(io, .awake).toNanoseconds());
                        if (decode_batches >= max_batches and elapsed_decode < min_sample_ns)
                            return error.SampleBudgetExceeded;
                    }
                    if (elapsed_decode == 0 or decoded_ops == 0) return error.InsufficientClockResolution;
                    decode_ns_per_op[sample] = elapsed_decode / decoded_ops;
                },
                .encode => {
                    const encode_started = std.Io.Clock.awake.now(io);
                    while (elapsed_encode < min_sample_ns) {
                        for (0..iterations) |_| {
                            const encoded = try codec.encode(allocator, words);
                            guard += encoded.len;
                            std.mem.doNotOptimizeAway(encoded.len);
                            allocator.free(encoded);
                        }
                        encoded_ops += @intCast(iterations);
                        encode_batches += 1;
                        elapsed_encode = @intCast(encode_started.untilNow(io, .awake).toNanoseconds());
                        if (encode_batches >= max_batches and elapsed_encode < min_sample_ns)
                            return error.SampleBudgetExceeded;
                    }
                    if (elapsed_encode == 0 or encoded_ops == 0) return error.InsufficientClockResolution;
                    encode_ns_per_op[sample] = elapsed_encode / encoded_ops;
                },
            }
        }

        std.debug.print(
            "ZIG_T5M_SAMPLE sample={d} decode_elapsed_ns={d} decode_ops={d} decode_ns_per_op={d} encode_elapsed_ns={d} encode_ops={d} encode_ns_per_op={d} target_sample_ns={d}\n",
            .{ sample + 1, elapsed_decode, decoded_ops, decode_ns_per_op[sample], elapsed_encode, encoded_ops, encode_ns_per_op[sample], min_sample_ns },
        );
    }
    const d = sortedCopy(decode_ns_per_op);
    const e = sortedCopy(encode_ns_per_op);
    if (d[0] == 0 or e[0] == 0) return error.InsufficientClockResolution;
    std.debug.print(
        "ZIG_T5M_BENCH physical_bytes={d} words={d} samples={d} min_sample_ns={d} decode_min_ns_per_op={d} decode_p50_ns_per_op={d} decode_p90_ns_per_op={d} decode_max_ns_per_op={d} encode_min_ns_per_op={d} encode_p50_ns_per_op={d} encode_p90_ns_per_op={d} encode_max_ns_per_op={d} scope=zig-codec-only guard={d}\n",
        .{ physical.len, words.len, sample_count, min_sample_ns, d[0], d[5], d[9], d[sample_count - 1], e[0], e[5], e[9], e[sample_count - 1], guard },
    );
}
