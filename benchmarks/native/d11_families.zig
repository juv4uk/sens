// D11 families: fixed workload and timed boundary match d11_families.rs.
// Reusable fixed buffers; no heap allocation; this is a mechanism benchmark, not a SENS law.
const std = @import("std");

const sample_count: usize = 15;
const minimum_sample_ns: u64 = 2_000_000;
const maximum_repetitions: usize = 1 << 20;
const clock_monotonic: c_int = 1;

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
extern "c" fn getenv(name: [*:0]const u8) ?[*:0]const u8;

const Workspace = struct {
    filtered: [8]i64 = [_]i64{0} ** 8,
    keys: [8]i64 = [_]i64{0} ** 8,
    counts: [8]usize = [_]usize{0} ** 8,
};

fn nowNs() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(clock_monotonic, &ts) != 0) @panic("clock_gettime(CLOCK_MONOTONIC) failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

fn filterEqual(xs: []const i64, predicate: i64, output: []i64) usize {
    @memset(output, 0);
    var count: usize = 0;
    for (xs) |value| {
        if (value == predicate) {
            output[count] = value;
            count += 1;
        }
    }
    return count;
}

fn alistLookup(key: i64, keys: []const i64, values: []const i64) ?struct { key: i64, value: i64 } {
    for (keys, 0..) |candidate, index| {
        if (candidate == key) return .{ .key = candidate, .value = values[index] };
    }
    return null;
}

fn frequencies(xs: []const i64, keys: []i64, counts: []usize) usize {
    @memset(keys, 0);
    @memset(counts, 0);
    var distinct: usize = 0;
    for (xs) |value| {
        var found = false;
        for (keys[0..distinct], 0..) |candidate, index| {
            if (candidate == value) {
                counts[index] += 1;
                found = true;
                break;
            }
        }
        if (!found) {
            keys[distinct] = value;
            counts[distinct] = 1;
            distinct += 1;
        }
    }
    return distinct;
}

fn once(xs: []const i64, assoc_keys: []const i64, assoc_values: []const i64, work: *Workspace) usize {
    std.mem.doNotOptimizeAway(xs);
    std.mem.doNotOptimizeAway(assoc_keys);
    std.mem.doNotOptimizeAway(assoc_values);
    const filtered = filterEqual(xs, 1, &work.filtered);
    const found = alistLookup(2, assoc_keys, assoc_values);
    const distinct = frequencies(xs, &work.keys, &work.counts);
    std.mem.doNotOptimizeAway(work.filtered[0..filtered]);
    std.mem.doNotOptimizeAway(work.keys[0..distinct]);
    std.mem.doNotOptimizeAway(work.counts[0..distinct]);
    std.mem.doNotOptimizeAway(&found);
    return filtered + @as(usize, @intFromBool(found != null)) + distinct;
}

fn preflight() !void {
    const xs = [_]i64{ 1, 2, 1, 3, 1, 4, 1 };
    const assoc_keys = [_]i64{ 1, 2, 3 };
    const assoc_values = [_]i64{ 10, 20, 30 };
    var work = Workspace{};
    const filtered = filterEqual(&xs, 1, &work.filtered);
    if (filtered != 4 or !std.mem.eql(i64, work.filtered[0..filtered], &.{ 1, 1, 1, 1 })) return error.FilterPreflight;
    const found = alistLookup(2, &assoc_keys, &assoc_values) orelse return error.AssocPreflight;
    if (found.key != 2 or found.value != 20) return error.AssocPreflight;
    const distinct = frequencies(&xs, &work.keys, &work.counts);
    if (distinct != 4) return error.FrequencyPreflight;
    if (!std.mem.eql(i64, work.keys[0..distinct], &.{ 1, 2, 3, 4 })) return error.FrequencyKeysPreflight;
    if (!std.mem.eql(usize, work.counts[0..distinct], &.{ 4, 1, 1, 1 })) return error.FrequencyCountsPreflight;
    if (filtered + 1 + distinct != 9) return error.ChecksumPreflight;
    std.debug.print("D11_FAMILIES_PREFLIGHT impl=zig filtered=4 assoc_value=20 distinct=4 counts=4,1,1,1 checksum=9 allocations=0\n", .{});
}

fn runSample(sample: usize) !void {
    if (sample >= sample_count) return error.InvalidSample;
    const xs = [_]i64{ 1, 2, 1, 3, 1, 4, 1 };
    const assoc_keys = [_]i64{ 1, 2, 3 };
    const assoc_values = [_]i64{ 10, 20, 30 };
    var work = Workspace{};

    var warm_sink: usize = 0;
    for (0..4) |_| {
        warm_sink += once(&xs, &assoc_keys, &assoc_values, &work);
    }
    std.mem.doNotOptimizeAway(&warm_sink);

    var repetitions: usize = 1;
    while (true) {
        const start = nowNs();
        var sink: usize = 0;
        for (0..repetitions) |_| {
            sink += once(&xs, &assoc_keys, &assoc_values, &work);
        }
        std.mem.doNotOptimizeAway(&sink);
        const elapsed = nowNs() - start;
        if (elapsed >= minimum_sample_ns or repetitions >= maximum_repetitions) {
            std.debug.print(
                "D11_FAMILIES_SAMPLE impl=zig sample={d} reps={d} ns_per_round={d} checksum={d} allocations=0\n",
                .{ sample, repetitions, @max(@as(u64, 1), elapsed / @as(u64, @intCast(repetitions))), sink / repetitions },
            );
            return;
        }
        repetitions = @min(repetitions * 2, maximum_repetitions);
    }
}

fn envEquals(name: [*:0]const u8, expected: []const u8) bool {
    const raw = getenv(name) orelse return false;
    return std.mem.eql(u8, std.mem.span(raw), expected);
}

fn sampleFromEnv() ?usize {
    const raw = getenv("D11_FAMILIES_SAMPLE") orelse return null;
    return std.fmt.parseInt(usize, std.mem.span(raw), 10) catch @panic("D11_FAMILIES_SAMPLE must be an integer");
}

pub fn main() !void {
    if (envEquals("D11_FAMILIES_PREFLIGHT_ONLY", "1")) {
        try preflight();
        return;
    }
    if (sampleFromEnv()) |sample| {
        try runSample(sample);
        return;
    }
    try preflight();
    for (0..sample_count) |sample| try runSample(sample);
}
