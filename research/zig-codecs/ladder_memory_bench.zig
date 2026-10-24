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

fn d11Trial(batch: usize, repetitions: usize) void {
    const questions = game.questionCount(11);
    if (questions != 512 or batch == 0 or batch > questions) @panic("D11 inventory mismatch");
    // Крок 73 взаємно простий із 512: зразки покривають увесь D11.
    // Подвійний масив дозволяє зсувати вікно без пропусків координат.
    var guesses: [1024]game.D11Guess = undefined;
    for (0..512) |i| {
        const child = game.questionAt(11, (i * 73) % 512).?;
        const answer: game.D11Guess = .{
            .parent_bits = child.bits[0..10],
            .suffix = child.bits[10],
            .child_lisp = child.lisp,
        };
        guesses[i] = answer;
        guesses[512 + i] = answer;
    }
    const seed: usize = @intCast(nanoseconds() & 511);
    for (0..16) |i| {
        const offset = (seed + i * 73) & 511;
        const result = game.gradeD11(guesses[offset .. offset + batch]);
        if (result.correct != batch) @panic("D11 derivation parity");
        std.mem.doNotOptimizeAway(result);
    }
    for (0..5) |round| {
        const start_ns = nanoseconds();
        for (0..repetitions) |i| {
            // Вхід залежить від реального годинника та змінюється в кожній ітерації.
            const offset = (seed + round + i * 73) & 511;
            const result = game.gradeD11(guesses[offset .. offset + batch]);
            std.mem.doNotOptimizeAway(result);
        }
        const elapsed = nanoseconds() - start_ns;
        if (elapsed == 0) @panic("zero duration");
        std.debug.print(
            "sample impl=zig mode=d11-derivation round={d} elapsed_ns={d} reps={d} guesses_per_round={d} questions={d}\n",
            .{ round, elapsed, repetitions, batch, questions },
        );
    }
}

pub fn main() void {
    lookupTrial(3, 12000);
    lookupTrial(5, 12000);
    lookupTrial(10, 2000);
    lookupTrial(11, 2000);
    d11Trial(1, 2000);
    d11Trial(16, 500);
    d11Trial(128, 100);
    d11Trial(512, 20);
}
