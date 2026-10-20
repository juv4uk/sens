//! T5M (дефолтний, 5 трітів/байт) — механічний бенчмарк Zig-бекенда.
//! Використовує справжній T5M-кодек `research/zig-codecs/t5m.zig` (НЕ legacy T5).
//! Формат виводу — fixture/physical/sample, як у `t5/bench.zig`, щоб драйвер
//! `t5m/run_paired_bench.py` порівнював усі бекенди на одному корпусі.
//! Це транспортна механіка, НЕ SENS-семантика.
const std = @import("std");
const t5m = @import("t5m.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

fn fnv64(bytes: []const u8) u64 {
    var hash: u64 = 0xcbf29ce484222325;
    for (bytes) |b| hash = (hash ^ @as(u64, b)) *% 0x100000001b3;
    return hash;
}

const Pattern = [_]t5m.Word{
    .{ .width = 2, .bits = "10" },
    .{ .width = 3, .bits = "100" },
    .{ .width = 2, .bits = "01" },
};

fn trial(
    comptime operation: enum { encode, decode },
    allocator: std.mem.Allocator,
    words: []const t5m.Word,
    physical: []const u8,
    forms: usize,
    repetitions: usize,
) !void {
    const begin = nanoseconds();
    for (0..repetitions) |_| {
        if (operation == .encode) {
            const bytes = try t5m.encode(allocator, words);
            std.mem.doNotOptimizeAway(bytes);
            allocator.free(bytes);
        } else {
            var decoded = try t5m.decode(allocator, physical);
            std.mem.doNotOptimizeAway(decoded.words);
            decoded.deinit(allocator);
        }
    }
    const elapsed = nanoseconds() - begin;
    std.debug.print("sample impl=zig forms={d} op={s} elapsed_ns={d} reps={d}\n", .{
        forms, @tagName(operation), elapsed, repetitions,
    });
}

pub fn main() !void {
    const allocator = std.heap.c_allocator;
    const cases = [_]usize{ 1, 16, 128, 1024 };
    const reps = [_]usize{ 12000, 3000, 600, 100 };

    for (cases, 0..) |forms, i| {
        const words = try allocator.alloc(t5m.Word, forms * Pattern.len);
        defer allocator.free(words);
        for (0..forms) |j| {
            @memcpy(words[j * Pattern.len ..][0..Pattern.len], &Pattern);
        }

        const physical = try t5m.encode(allocator, words);
        defer allocator.free(physical);
        var recovered = try t5m.decode(allocator, physical);
        defer recovered.deinit(allocator);
        if (recovered.words.len != words.len) return error.MechanicalParityMismatch;
        for (words, recovered.words) |source, actual| {
            if (source.width != actual.width or !std.mem.eql(u8, source.bits, actual.bits))
                return error.MechanicalParityMismatch;
        }

        std.debug.print("fixture impl=zig forms={d} words={d} bytes={d} fnv64={x}\n", .{
            forms, words.len, physical.len, fnv64(physical),
        });
        std.debug.print("physical impl=zig forms={d} hex=", .{forms});
        const alphabet = "0123456789abcdef";
        for (physical) |byte| {
            std.debug.print("{c}{c}", .{ alphabet[byte >> 4], alphabet[byte & 15] });
        }
        std.debug.print("\n", .{});

        for (0..3) |_| {
            const temp = try t5m.encode(allocator, words);
            allocator.free(temp);
            var back = try t5m.decode(allocator, physical);
            back.deinit(allocator);
        }
        for (0..5) |_| {
            try trial(.encode, allocator, words, physical, forms, reps[i]);
            try trial(.decode, allocator, words, physical, forms, reps[i]);
        }
    }
}
