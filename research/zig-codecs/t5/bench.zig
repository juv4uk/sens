//! Linux-only, manual mechanical T5 benchmark. Zig 0.16.0: zig build-exe -O ReleaseFast -lc ...
//! Matched workloads are fixed by an independent differential harness.
//! NO semantic SENS PASS. No file I/O or parsing in timed sections.
const std = @import("std");
const t5 = @import("t5.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(ts.tv_nsec));
}

fn fnv64(bytes: []const u8) u64 {
    var hash: u64 = 0xcbf29ce484222325;
    for (bytes) |b| {
        hash = (hash ^ @as(u64, b)) *% 0x100000001b3;
    }
    return hash;
}

const Pattern = [_]t5.Word{
    .{ .width = 2, .bits = 2 },
    .{ .width = 3, .bits = 4 },
    .{ .width = 2, .bits = 1 },
};

fn trial(
    comptime operation: enum { encode, decode },
    allocator: std.mem.Allocator,
    words: []const t5.Word,
    physical: []const u8,
    forms: usize,
    repetitions: usize,
) !void {
    const begin = nanoseconds();
    for (0..repetitions) |_| {
        if (operation == .encode) {
            const bytes = try t5.encode(allocator, words);
            std.mem.doNotOptimizeAway(bytes);
            allocator.free(bytes);
        } else {
            const decoded = try t5.decode(allocator, physical);
            std.mem.doNotOptimizeAway(decoded);
            allocator.free(decoded);
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
        const words = try allocator.alloc(t5.Word, forms * Pattern.len);
        defer allocator.free(words);
        for (0..forms) |j| {
            @memcpy(words[j * Pattern.len ..][0..Pattern.len], &Pattern);
        }

        const physical = try t5.encode(allocator, words);
        defer allocator.free(physical);
        const recovered = try t5.decode(allocator, physical);
        defer allocator.free(recovered);
        if (recovered.len != words.len) return error.MechanicalParityMismatch;
        for (words, recovered) |source, actual| {
            if (source.width != actual.width or source.bits != actual.bits)
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

        // Warmed isolated codec path; startup and build costs are separate.
        for (0..3) |_| {
            const temp = try t5.encode(allocator, words);
            allocator.free(temp);
            const temp_words = try t5.decode(allocator, physical);
            allocator.free(temp_words);
        }
        for (0..5) |_| {
            try trial(.encode, allocator, words, physical, forms, reps[i]);
            try trial(.decode, allocator, words, physical, forms, reps[i]);
        }
    }
}
