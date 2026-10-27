//! Бенчмарк механізму копіювання байтів Zig 0.16, без SENS-семантики.
//! zig test -O ReleaseFast -lc benchmarks/mechanism/zig-byte-copy-bench.zig
const std = @import("std");
// Zig 0.16 forbids @embedFile outside a package root. Load before timing.
const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;

fn readCorpus(allocator: std.mem.Allocator) ![]u8 {
    const file = fopen("lib/core4.lisp", "rb") orelse return error.CorpusUnavailable;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return error.SeekFailure;
    const end = ftell(file);
    if (end <= 0 or end > 64 * 1024 * 1024) return error.BadCorpusSize;
    if (fseek(file, 0, 0) != 0) return error.SeekFailure;
    const data = try allocator.alloc(u8, @intCast(end));
    errdefer allocator.free(data);
    if (fread(data.ptr, 1, data.len, file) != data.len) return error.IncompleteCorpus;
    return data;
}

const samples_count = 11;
const batch_count = 512;

const Timespec = extern struct {
    tv_sec: c_long,
    tv_nsec: c_long,
};
extern "c" fn clock_gettime(clock_id: c_int, timestamp: *Timespec) c_int;
const clock_monotonic: c_int = 1;

fn nowNs() !u64 {
    var timestamp: Timespec = undefined;
    if (clock_gettime(clock_monotonic, &timestamp) != 0) return error.ClockUnavailable;
    if (timestamp.tv_sec < 0 or timestamp.tv_nsec < 0) return error.InvalidTimestamp;
    return @as(u64, @intCast(timestamp.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(timestamp.tv_nsec));
}

