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

// A physical byte-copy measurement, not a SENS-language law.
// The warmup is excluded from 11 samples; every sample copies the same source
// bytes 512 times. Check exact parity OUTSIDE the timed section.
test "physical byte-copy corridor: exact bytes and elapsed time" {
    const allocator = std.heap.page_allocator;
    const source = try readCorpus(allocator);
    defer allocator.free(source);
    if (source.len < batch_count) return error.CorpusTooSmall;
    const dest = try allocator.alloc(u8, source.len);
    defer allocator.free(dest);

    var samples: [samples_count]u64 = undefined;
    var checksum: u64 = 0;
    for (0..samples_count + 1) |round| {
        const start = try nowNs();
        for (0..batch_count) |offset| {
            @memcpy(dest, source);
            checksum +%= @as(u64, dest[offset]);
        }
        const finish = try nowNs();
        if (finish <= start) return error.ClockResolutionTooCoarse;
        if (!std.mem.eql(u8, dest, source)) return error.CopyMismatch;
        if (round > 0) samples[round - 1] = finish - start;
    }
    if (checksum == 0) return error.NoObservedBytes;

    // Small fixed sample set: insertion sort without allocator or external deps.
    for (1..samples_count) |i| {
        const value = samples[i];
        var j = i;
        while (j > 0 and samples[j - 1] > value) : (j -= 1) {
            samples[j] = samples[j - 1];
        }
        samples[j] = value;
    }
    std.debug.print(
        "ZIG_CORRIDOR_COPY_BENCH source=lib/core4.lisp bytes={d} batch={d} samples={d} p50_ns={d} p90_ns={d} min_ns={d} max_ns={d} checksum={d} scope=physical_only\\n",
        .{ source.len, batch_count, samples_count, samples[5], samples[9], samples[0], samples[10], checksum },
    );
}
