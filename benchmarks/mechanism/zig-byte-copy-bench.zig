//! Бенчмарк механізму копіювання байтів Zig 0.16, без SENS-семантики.
//! zig test -O ReleaseFast -lc benchmarks/mechanism/zig-byte-copy-bench.zig
const std = @import("std");
const source = @embedFile("../../lib/core4.lisp");
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

test "Zig byte carrier benchmark, no language oracle" {
    try std.testing.expect(source.len > 0);
    const destination = try std.testing.allocator.alloc(u8, source.len);
    defer std.testing.allocator.free(destination);
    var samples: [samples_count]u64 = undefined;
    var checksum: u8 = 0;
    // First batch is a warm-up, not part of reported samples.
    for (0..samples_count + 1) |sample| {
        const start = try nowNs();
        for (0..batch_count) |_| {
            @memcpy(destination, source[0..source.len]);
            // A volatile observation ensures the copy cannot be removed.
            const observed: *volatile const u8 = @ptrCast(destination.ptr);
            checksum ^= observed.*;
        }
        const elapsed = (try nowNs()) - start;
        try std.testing.expectEqualSlices(u8, source[0..source.len], destination);
        if (sample > 0) samples[sample - 1] = elapsed;
    }
    // Insertion sort avoids dependence on host sorting libraries.
    for (0..samples.len) |index| {
        var j = index;
        while (j > 0 and samples[j - 1] > samples[j]) : (j -= 1) {
            const previous = samples[j - 1];
            samples[j - 1] = samples[j];
            samples[j] = previous;
        }
    }
    try std.testing.expect(samples[0] > 0);
    std.debug.print(
        "ZIG_BYTE_COPY_BENCH source=lib/core4.lisp bytes={d} batch={d} samples={d} p50_ns={d} p90_ns={d} min_ns={d} max_ns={d} checksum={d} scope=mechanism_only\n",
        .{ source.len, batch_count, samples_count, samples[5], samples[9], samples[0], samples[10], checksum },
    );
}
