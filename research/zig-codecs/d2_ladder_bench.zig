//! Драбина D2: нативний мікробенчмарк дослідного pack/unpack.
//! Підмножина без D2:11 (крапка), без карти позицій у змішаній програмі.
//! Це payload-only: порівняння байтів НЕ доводить перевагу повного кодека.
//! zig run -O ReleaseFast -lc research/zig-codecs/d2_ladder_bench.zig
const std = @import("std");
const codec = @import("d2_ladder_game.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(ts.tv_nsec));
}

const merged = [_]u8{ 2, 0, 2, 0, 2, 0, 2, 0, 1, 0, 2, 0, 1, 1, 0, 2, 0, 1, 1, 1 };
const merged_runs = [_][]const u8{&merged};
const interrupted = [_][]const u8{
    &.{2}, &.{ 0, 2 }, &.{ 0, 2 }, &.{ 0, 2 }, &.{0},
    &.{ 1, 0, 2 }, &.{0}, &.{ 1, 1, 0, 2 }, &.{0}, &.{ 1, 1, 1 },
};

fn operation(
    comptime op: enum { encode, decode },
    allocator: std.mem.Allocator,
    runs: []const []const u8,
    physical: []const []const u8,
) !void {
    for (runs, physical) |run, bytes| {
        if (op == .encode) {
            const encoded = try codec.pack(allocator, run);
            std.mem.doNotOptimizeAway(encoded);
            allocator.free(encoded);
        } else {
            const decoded = try codec.unpack(allocator, bytes, run.len);
            std.mem.doNotOptimizeAway(decoded);
            allocator.free(decoded);
        }
    }
}

fn trial(
    comptime op: enum { encode, decode },
    allocator: std.mem.Allocator,
    name: []const u8,
    runs: []const []const u8,
    physical: []const []const u8,
    round: usize,
    repetitions: usize,
) !void {
    const start = nanoseconds();
    for (0..repetitions) |_| try operation(op, allocator, runs, physical);
    const elapsed = nanoseconds() - start;
    if (elapsed == 0) return error.InvalidMeasurement;
    std.debug.print(
        "sample impl=zig mode=d2-payload case={s} op={s} round={d} elapsed_ns={d} reps={d} runs={d} alloc=c\n",
        .{ name, @tagName(op), round, elapsed, repetitions, runs.len },
    );
}

fn benchmark(allocator: std.mem.Allocator, name: []const u8, runs: []const []const u8, repetitions: usize) !void {
    var buffers: [10][]u8 = undefined;
    var physical: [10][]const u8 = undefined;
    if (runs.len > buffers.len) return error.TooManyRuns;
    var trits: usize = 0;
    var bytes: usize = 0;
    var fixed_two_bit_runs: usize = 0;
    for (runs, 0..) |run, i| {
        buffers[i] = try codec.pack(allocator, run);
        physical[i] = buffers[i];
        trits += run.len;
        bytes += buffers[i].len;
        fixed_two_bit_runs += (run.len * 2 + 7) / 8;
        const recovered = try codec.unpack(allocator, buffers[i], run.len);
        defer allocator.free(recovered);
        if (!std.mem.eql(u8, run, recovered)) return error.ParityMismatch;
    }
    defer {
        for (buffers[0..runs.len]) |buffer| allocator.free(buffer);
    }
    const fixed_two_bit = (trits * 2 + 7) / 8;
    std.debug.print(
        "fixture impl=zig case={s} trits={d} runs={d} physical_bytes={d} fixed2_global_lower_bound={d} fixed2_per_run_bytes={d} position_map=ABSENT full_codec=NO\n",
        .{ name, trits, runs.len, bytes, fixed_two_bit, fixed_two_bit_runs },
    );
    for (0..16) |_| {
        try operation(.encode, allocator, runs, physical[0..runs.len]);
        try operation(.decode, allocator, runs, physical[0..runs.len]);
    }
    for (0..5) |round| {
        if (round % 2 == 0) {
            try trial(.encode, allocator, name, runs, physical[0..runs.len], round, repetitions);
            try trial(.decode, allocator, name, runs, physical[0..runs.len], round, repetitions);
        } else {
            try trial(.decode, allocator, name, runs, physical[0..runs.len], round, repetitions);
            try trial(.encode, allocator, name, runs, physical[0..runs.len], round, repetitions);
        }
    }
}

pub fn main() !void {
    const allocator = std.heap.c_allocator;
    try benchmark(allocator, "merged-caar", &merged_runs, 10000);
    try benchmark(allocator, "interrupted-caar", &interrupted, 2000);
}
