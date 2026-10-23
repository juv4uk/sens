//! Zig 0.16: тільки механіка T5M encode/decode, без Lisp-оракула.
//! Фізичний файл із репозиторію, SHA/версія фіксуються CI; 11 сирих проб.
//! Замість видаленого std.time.Timer використовується Io.Clock.awake.

const std = @import("std");
const codec = @import("t5m.zig");
const physical: []const u8 = @embedFile("../../benchmarks/lists.sens");

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

    var decode_ns: [11]u64 = undefined;
    var encode_ns: [11]u64 = undefined;
    var guard: usize = 0;
    for (0..decode_ns.len) |sample| {
        const started = std.Io.Clock.awake.now(io);
        for (0..iterations) |_| {
            var decoded = try codec.decode(allocator, physical);
            guard ^= decoded.words.len;
            std.mem.doNotOptimizeAway(decoded.words.len);
            decoded.deinit(allocator);
        }
        decode_ns[sample] = @intCast(started.untilNow(io, .awake).toNanoseconds());

        const encode_started = std.Io.Clock.awake.now(io);
        for (0..iterations) |_| {
            const encoded = try codec.encode(allocator, words);
            guard ^= encoded.len;
            std.mem.doNotOptimizeAway(encoded.len);
            allocator.free(encoded);
        }
        encode_ns[sample] = @intCast(encode_started.untilNow(io, .awake).toNanoseconds());
    }
    const d = sortedCopy(decode_ns);
    const e = sortedCopy(encode_ns);
    if (d[0] == 0 or e[0] == 0) return error.InsufficientClockResolution;
    std.debug.print(
        "ZIG_T5M_BENCH physical_bytes={d} words={d} iterations={d} samples=11 decode_p50_ns={d} decode_p90_ns={d} encode_p50_ns={d} encode_p90_ns={d} scope=zig-codec-only guard={d}\n",
        .{ physical.len, words.len, iterations, d[5], d[9], e[5], e[9], guard },
    );
    for (0..11) |i| {
        std.debug.print("ZIG_T5M_SAMPLE sample={d} decode_ns={d} encode_ns={d}\n", .{ i + 1, decode_ns[i], encode_ns[i] });
    }
}

test "physical T5M fixture is canonical and malformed bytes fail closed" {
    const allocator = std.testing.allocator;
    var decoded = try codec.decode(allocator, physical);
    defer decoded.deinit(allocator);
    const words = try allocator.alloc(codec.Word, decoded.words.len);
    defer allocator.free(words);
    for (decoded.words, 0..) |word, i| {
        words[i] = .{ .width = word.width, .bits = word.bits };
    }
    const replay = try codec.encode(allocator, words);
    defer allocator.free(replay);
    try std.testing.expectEqualSlices(u8, physical, replay);
    try std.testing.expectError(error.InvalidPhysicalByte, codec.decode(allocator, &.{243}));
}
