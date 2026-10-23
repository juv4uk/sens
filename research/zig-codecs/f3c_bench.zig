//! Matched physical F3C benchmark: Rust example zig_f3c_matched_bench.rs.
//! Zig 0.16.0, Linux x86_64 + libc; mechanics only, not SENS semantics.
const std = @import("std");
const f3c = @import("f3c/f3c.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;
fn nowNs() u64 {
    var t: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) @panic("clock_gettime");
    return @as(u64, @intCast(t.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(t.tv_nsec));
}
const alphabet = "0123456789abcdef";
fn printPhysical(comptime label: []const u8, name: []const u8, data: []const u8) void {
    std.debug.print("{s} impl=zig case={s} hex=", .{ label, name });
    for (data) |b| std.debug.print("{c}{c}", .{ alphabet[b >> 4], alphabet[b & 15] });
    std.debug.print("\n", .{});
}
fn trial(
    comptime op: enum { encode, decode },
    allocator: std.mem.Allocator,
    name: []const u8,
    t5_bytes: []const u8,
    f3c_bytes: []const u8,
    repetitions: usize,
) !u64 {
    const start = nowNs();
    for (0..repetitions) |_| {
        if (op == .encode) {
            const bytes = (try f3c.encode(allocator, t5_bytes)) orelse
                return error.UnexpectedCompressionRejection;
            std.mem.doNotOptimizeAway(bytes);
            allocator.free(bytes);
        } else {
            const bytes = try f3c.decode(allocator, f3c_bytes);
            std.mem.doNotOptimizeAway(bytes);
            allocator.free(bytes);
        }
    }
    const elapsed = nowNs() - start;
    std.debug.print("sample impl=zig case={s} op={s} elapsed_ns={d} reps={d}\n", .{
        name, @tagName(op), elapsed, repetitions,
    });
    return elapsed;
}

/// Сортуємо 11 однотипних проб без залежності від мінливого std.sort API Zig.
fn reportSamples(name: []const u8, op: []const u8, raw: [11]u64, reps: usize) void {
    var times = raw;
    for (1..times.len) |i| {
        var j = i;
        while (j > 0 and times[j - 1] > times[j]) : (j -= 1) {
            const value = times[j];
            times[j] = times[j - 1];
            times[j - 1] = value;
        }
    }
    std.debug.print(
        "summary impl=zig case={s} op={s} p50_ns_per_op={d} p90_ns_per_op={d} samples=11 warmup=5 reps={d} scope=allocating_transport_only release=NOT_CERTIFIED\n",
        .{ name, op, times[5] / reps, times[9] / reps, reps },
    );
}
pub fn main() !void {
    const allocator = std.heap.c_allocator;
    const cases = .{
        .{ "quote", &[_]u8{ 0x63, 0x89, 0x06, 0xa1 }, &[_]u8{ 0xf3, 0x40, 0x60 }, @as(usize, 512) },
        .{ "car_cons", &[_]u8{ 0x66, 0x38, 0x67, 0x89, 0x89, 0x3b, 0x35 }, &[_]u8{ 0xf3, 0x36, 0x5f, 0x1b, 0xd0, 0xc9 }, @as(usize, 256) },
    };
    inline for (cases) |item| {
        const name = item[0];
        const source = item[1];
        const expected = item[2];
        const reps = item[3];

        const encoded = (try f3c.encode(allocator, source)) orelse return error.CandidateRejected;
        defer allocator.free(encoded);
        if (!std.mem.eql(u8, encoded, expected)) return error.WrongPhysicalF3C;
        const decoded = try f3c.decode(allocator, expected);
        defer allocator.free(decoded);
        if (!std.mem.eql(u8, decoded, source)) return error.WrongPhysicalT5;
        printPhysical("physical", name, encoded);
        std.debug.print("fixture impl=zig case={s} t5_bytes={d} f3c_bytes={d}\n", .{
            name, source.len, encoded.len,
        });
        // Те саме фізичне навантаження й 5 прогрівів, що у Rust reference.
        for (0..5) |_| {
            const a = (try f3c.encode(allocator, source)).?;
            allocator.free(a);
            const b = try f3c.decode(allocator, expected);
            allocator.free(b);
        }
        var encode_ns: [11]u64 = undefined;
        var decode_ns: [11]u64 = undefined;
        for (0..11) |i| {
            encode_ns[i] = try trial(.encode, allocator, name, source, expected, reps);
            decode_ns[i] = try trial(.decode, allocator, name, source, expected, reps);
        }
        reportSamples(name, "encode", encode_ns, reps);
        reportSamples(name, "decode", decode_ns, reps);
    }
}
