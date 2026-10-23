//! Відтворюваний мікробенчмарк гри «Драбина» на канонічних Lisp-таблицях.
//! Вимірює пошук і перевірку D11; не вимірює SENS-обчислення чи T5M-кодек.
//! zig build-exe -lc -O ReleaseFast research/zig-codecs/ladder_memory_bench.zig
//! ./ladder_memory_bench
const std = @import("std");
const game = @import("ladder_memory_game.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(ts.tv_nsec));
}

fn lookupTrial(width: u8, repetitions: usize) void {
    const count = game.questionCount(width);
    if (count == 0) @panic("empty question bank");
    var samples: [8]game.Record = undefined;
    for (&samples, 0..) |*sample, i| {
        sample.* = game.questionAt(width, (i * count) / samples.len).?;
        const actual = game.lookup(width, sample.bits).?;
        if (!std.mem.eql(u8, actual.lisp, sample.lisp)) @panic("lookup parity");
    }
    for (0..16) |_| {
        for (samples) |item| std.mem.doNotOptimizeAway(game.lookup(width, item.bits));
    }
    for (0..5) |round| {
        const start = nanoseconds();
        for (0..repetitions) |i| {
            const found = game.lookup(width, samples[i % samples.len].bits).?;
            std.mem.doNotOptimizeAway(found);
        }
        const elapsed = nanoseconds() - start;
        if (elapsed == 0) @panic("zero duration");
        std.debug.print(
            "sample impl=zig mode=ladder-lookup width={d} round={d} elapsed_ns={d} reps={d} questions={d}\n",
            .{ width, round, elapsed, repetitions, count },
        );
    }
}

fn d11Trial(repetitions: usize) void {
    const questions = game.questionCount(11);
    if (questions != 512) @panic("D11 inventory mismatch");
    const first = game.questionAt(11, 0).?;
    const guess = [_]game.D11Guess{.{
        .parent_bits = first.bits[0..10],
        .suffix = first.bits[10],
        .child_lisp = first.lisp,
    }};
    if (game.gradeD11(&guess).correct != 1) @panic("D11 derivation parity");
    for (0..16) |_| std.mem.doNotOptimizeAway(game.gradeD11(&guess));
    for (0..5) |round| {
        const start = nanoseconds();
        for (0..repetitions) |_| {
            const result = game.gradeD11(&guess);
            std.mem.doNotOptimizeAway(result);
        }
        const elapsed = nanoseconds() - start;
        if (elapsed == 0) @panic("zero duration");
        std.debug.print(
            "sample impl=zig mode=d11-derivation round={d} elapsed_ns={d} reps={d} questions={d}\n",
            .{ round, elapsed, repetitions, questions },
        );
    }
}

pub fn main() void {
    lookupTrial(3, 12000);
    lookupTrial(5, 12000);
    lookupTrial(10, 2000);
    lookupTrial(11, 2000);
    d11Trial(2000);
}
