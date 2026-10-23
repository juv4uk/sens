//! Парний механічний A/B: чинний T5M проти дослідного DWC1.
//! Один і той самий exact-width corpus, без SENS-семантики й host-оракулів.
const std = @import("std");
const t5m = @import("t5m.zig");
const dwc = @import("domain_codebook_experiment.zig");

const Corpus = struct {
    name: []const u8,
    physical: []const u8,
};
const corpora = [_]Corpus{
    .{ .name = "train-core", .physical = @embedFile("../../lib/core.sens") },
    .{ .name = "holdout-lists", .physical = @embedFile("../../benchmarks/lists.sens") },
    .{ .name = "holdout-arithmetic", .physical = @embedFile("../../benchmarks/arithmetic.sens") },
    .{ .name = "holdout-persistent-vector", .physical = @embedFile("../../lib/persistent-vector.sens") },
};
const Lane = enum { t5m_encode, dwc_encode, t5m_decode, dwc_decode };
const samples: usize = 11;
const target_ns: u64 = 15_000_000;

fn sortedCopy(values: [samples]u64) [samples]u64 {
    var sorted = values;
    for (1..sorted.len) |i| {
        var j = i;
        while (j > 0 and sorted[j] < sorted[j - 1]) : (j -= 1) {
            std.mem.swap(u64, &sorted[j], &sorted[j - 1]);
        }
    }
    return sorted;
}

fn measure(
    init: std.process.Init,
    comptime lane: Lane,
    words: []const t5m.Word,
    physical: []const u8,
    compressed: []const u8,
    guard: *usize,
) !u64 {
    const allocator = std.heap.page_allocator;
    const io = init.io;
    const started = std.Io.Clock.awake.now(io);
    var elapsed: u64 = 0;
    var ops: u64 = 0;
    var batches: usize = 0;
    while (elapsed < target_ns) {
        for (0..32) |_| {
            switch (lane) {
                .t5m_encode => {
                    const result = try t5m.encode(allocator, words);
                    guard.* +%= result.len;
                    std.mem.doNotOptimizeAway(result.len);
                    allocator.free(result);
                },
                .dwc_encode => {
                    const result = try dwc.encode(allocator, words);
                    guard.* +%= result.len;
                    std.mem.doNotOptimizeAway(result.len);
                    allocator.free(result);
                },
                .t5m_decode => {
                    var result = try t5m.decode(allocator, physical);
                    guard.* +%= result.words.len;
                    std.mem.doNotOptimizeAway(result.words.len);
                    result.deinit(allocator);
                },
                .dwc_decode => {
                    var result = try dwc.decode(allocator, compressed);
                    guard.* +%= result.words.len;
                    std.mem.doNotOptimizeAway(result.words.len);
                    result.deinit(allocator);
                },
            }
        }
        ops += 32;
        batches += 1;
        elapsed = @intCast(started.untilNow(io, .awake).toNanoseconds());
        if (batches >= 100_000 and elapsed < target_ns) return error.SampleBudgetExceeded;
    }
    if (elapsed == 0 or ops == 0) return error.InsufficientClockResolution;
    return elapsed / ops;
}

fn runCorpus(init: std.process.Init, corpus: Corpus) !void {
    const allocator = std.heap.page_allocator;
    var decoded = try t5m.decode(allocator, corpus.physical);
    defer decoded.deinit(allocator);
    const words = try allocator.alloc(t5m.Word, decoded.words.len);
    defer allocator.free(words);
    for (decoded.words, 0..) |word, i| {
        words[i] = .{ .width = word.width, .bits = word.bits };
    }

    const baseline = try t5m.encode(allocator, words);
    defer allocator.free(baseline);
    if (!std.mem.eql(u8, baseline, corpus.physical))
        return error.NonCanonicalT5MCorpus;
    const compressed = try dwc.encode(allocator, words);
    defer allocator.free(compressed);
    var roundtrip = try dwc.decode(allocator, compressed);
    defer roundtrip.deinit(allocator);
    if (roundtrip.words.len != words.len) return error.WordCountMismatch;
    for (words, roundtrip.words) |expected, actual| {
        if (expected.width != actual.width or !std.mem.eql(u8, expected.bits, actual.bits))
            return error.ExactWordMismatch;
    }

    // Прогрів: обидва кодеки, обидва напрями, той самий physical corpus.
    var guard: usize = 0;
    for (0..16) |_| {
        const t = try t5m.encode(allocator, words);
        guard +%= t.len;
        allocator.free(t);
        const d = try dwc.encode(allocator, words);
        guard +%= d.len;
        allocator.free(d);
        var td = try t5m.decode(allocator, corpus.physical);
        guard +%= td.words.len;
        td.deinit(allocator);
        var dd = try dwc.decode(allocator, compressed);
        guard +%= dd.words.len;
        dd.deinit(allocator);
    }

    var te: [samples]u64 = undefined;
    var de: [samples]u64 = undefined;
    var td: [samples]u64 = undefined;
    var dd: [samples]u64 = undefined;
    for (0..samples) |i| {
        // AB/BA: порядок чергується для зменшення перекосу прогріву CPU.
        if (i % 2 == 0) {
            te[i] = try measure(init, .t5m_encode, words, corpus.physical, compressed, &guard);
            de[i] = try measure(init, .dwc_encode, words, corpus.physical, compressed, &guard);
            td[i] = try measure(init, .t5m_decode, words, corpus.physical, compressed, &guard);
            dd[i] = try measure(init, .dwc_decode, words, corpus.physical, compressed, &guard);
        } else {
            dd[i] = try measure(init, .dwc_decode, words, corpus.physical, compressed, &guard);
            td[i] = try measure(init, .t5m_decode, words, corpus.physical, compressed, &guard);
            de[i] = try measure(init, .dwc_encode, words, corpus.physical, compressed, &guard);
            te[i] = try measure(init, .t5m_encode, words, corpus.physical, compressed, &guard);
        }
    }
    const a = sortedCopy(te);
    const b = sortedCopy(de);
    const c = sortedCopy(td);
    const d = sortedCopy(dd);
    std.debug.print(
        "DWC1_BENCH corpus={s} words={d} t5m_bytes={d} dwc1_bytes={d} samples={d} sample_target_ns={d} t5m_encode_p50_ns={d} dwc1_encode_p50_ns={d} t5m_decode_p50_ns={d} dwc1_decode_p50_ns={d} t5m_encode_p90_ns={d} dwc1_encode_p90_ns={d} t5m_decode_p90_ns={d} dwc1_decode_p90_ns={d} exact_roundtrip=PASS semantic=NOT_TESTED guard={d}\n",
        .{ corpus.name, words.len, baseline.len, compressed.len, samples, target_ns, a[5], b[5], c[5], d[5], a[9], b[9], c[9], d[9], guard },
    );
}

pub fn main(init: std.process.Init) !void {
    for (corpora) |corpus| try runCorpus(init, corpus);
}
