//! Нативний механічний benchmark raw13 vs BE16; не SENS eval.
//! Zig 0.16.0, -O ReleaseFast -lc. Обидва codec мають BE32 count header.
//! Preallocated buffers, без alloc/free/I/O всередині часу.
const std = @import("std");
const raw13 = @import("d13_raw_experiment.zig");
const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
fn now() !u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(1, &ts) != 0) return error.ClockFailure;
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}
const Op = enum { encode, decode };
fn batch(comptime codec: raw13.Codec, comptime op: Op, words: []const u16, frame: []u8, output: []u16) !u64 {
    const start = try now();
    for (0..300) |_| {
        if (op == .encode) {
            const n = try raw13.encode(codec, words, frame);
            std.mem.doNotOptimizeAway(frame[0..n]);
        } else {
            const n = try raw13.decode(codec, frame, output);
            std.mem.doNotOptimizeAway(output[0..n]);
        }
    }
    const elapsed = (try now()) - start;
    if (elapsed == 0) return error.InvalidMeasurement;
    return elapsed;
}
fn measure(comptime codec: raw13.Codec, name: []const u8, words: []const u16) !void {
    var frame: [8196]u8 = undefined;
    var output: [4096]u16 = undefined;
    const size = try raw13.encode(codec, words, &frame);
    const count = try raw13.decode(codec, frame[0..size], &output);
    if (count != words.len or !std.mem.eql(u16, words, output[0..count])) return error.RoundtripMismatch;
    std.debug.print("fixture case={s} codec={s} words={d} payload_bytes={d} metadata_bytes=4 frame_bytes={d} roundtrip=EXACT\n",
        .{ name, @tagName(codec), words.len, size - 4, size });
    _ = try batch(codec, .encode, words, frame[0..size], &output);
    _ = try batch(codec, .decode, words, frame[0..size], &output);
    var enc: [21]u64 = undefined;
    var dec: [21]u64 = undefined;
    for (0..21) |i| {
        if (i % 2 == 0) {
            enc[i] = try batch(codec, .encode, words, frame[0..size], &output);
            dec[i] = try batch(codec, .decode, words, frame[0..size], &output);
        } else {
            dec[i] = try batch(codec, .decode, words, frame[0..size], &output);
            enc[i] = try batch(codec, .encode, words, frame[0..size], &output);
        }
        std.debug.print("sample case={s} codec={s} words={d} index={d} encode_ns={d} decode_ns={d} reps=300\n",
            .{ name, @tagName(codec), words.len, i, enc[i], dec[i] });
    }
    std.mem.sort(u64, &enc, {}, std.sort.asc(u64));
    std.mem.sort(u64, &dec, {}, std.sort.asc(u64));
    inline for (.{ Op.encode, Op.decode }) |op| {
        const samples = if (op == .encode) enc else dec;
        std.debug.print("summary case={s} codec={s} words={d} op={s} p50_ns_per_op={d:.3} p95_ns_per_op={d:.3} batches=21 scope=preallocated_frame_api\n",
            .{ name, @tagName(codec), words.len, @tagName(op),
               @as(f64, @floatFromInt(samples[10])) / 300.0,
               @as(f64, @floatFromInt(samples[19])) / 300.0 });
    }
}
pub fn main() !void {
    std.debug.print("scope=physical_raw13_vs_be16 numeric_D13=NOT_ADMITTED SENS_eval=NOT_MEASURED seed=0x13c0ffee\n", .{});
    var words: [4096]u16 = undefined;
    var state: u32 = 0x13c0ffee;
    for (&words) |*word| {
        state = state *% 1664525 +% 1013904223;
        word.* = @intCast((state >> 16) & 0x1fff);
    }
    for ([_]usize{ 1, 2, 7, 8, 9, 63, 64, 65, 1023, 1024, 1025, 4096 }) |count| {
        if (count % 2 == 0) {
            try measure(.dense13, "lcg13-v1", words[0..count]);
            try measure(.be16, "lcg13-v1", words[0..count]);
        } else {
            try measure(.be16, "lcg13-v1", words[0..count]);
            try measure(.dense13, "lcg13-v1", words[0..count]);
        }
    }
    const extremes = [_]u16{ 0, 1, 0x0fff, 0x1000, 0x1ffe, 0x1fff };
    try measure(.dense13, "extremes13-v1", &extremes);
    try measure(.be16, "extremes13-v1", &extremes);
}
