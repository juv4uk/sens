//! Порівняння фізичних кодеків; НЕ benchmark виконання мови SENS.
//! Точні fixtures задаються нижче; жодної JSON/Unicode runtime-семантики.
//! Zig 0.16.0: zig test -lc research/zig-codecs/codec_compare_bench.zig
//! zig build-exe -lc -O ReleaseFast research/zig-codecs/codec_compare_bench.zig
//! Час включає alloc/free API; D12 має інше представлення і зовнішню ширину/count.
const std = @import("std");
const t5m = @import("t5m.zig");
const t33 = @import("t33_experiment.zig");
const d12 = @import("d12_dense_experiment.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
fn now() !u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(1, &ts) != 0) return error.ClockFailure;
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

const Codec = enum { t5m, t33, d12 };
const Op = enum { encode, decode };
const Fixture = struct {
    words: []const t5m.Word,
    raw: []const u16 = &.{},
};
const Pattern = [_]t5m.Word{
    .{ .width = 2, .bits = "10" },
    .{ .width = 3, .bits = "100" },
    .{ .width = 2, .bits = "01" },
};
fn checkWords(source: []const t5m.Word, decoded: []const t5m.DecodedWord) !void {
    if (source.len != decoded.len) return error.WordCountMismatch;
    for (source, decoded) |a, b| {
        if (a.width != b.width or !std.mem.eql(u8, a.bits, b.bits)) return error.WordMismatch;
    }
}
fn encode(comptime codec: Codec, a: std.mem.Allocator, fixture: Fixture) ![]u8 {
    return switch (codec) {
        .t5m => t5m.encode(a, fixture.words),
        .t33 => t33.encode(a, fixture.words),
        .d12 => blk: {
            const bytes = try a.alloc(u8, try d12.packedLen(fixture.raw.len));
            errdefer a.free(bytes);
            _ = try d12.encode(fixture.raw, bytes);
            break :blk bytes;
        },
    };
}
fn decode(comptime codec: Codec, a: std.mem.Allocator, fixture: Fixture, bytes: []const u8, verify: bool) !void {
    if (codec == .d12) {
        const restored = try a.alloc(u16, fixture.raw.len);
        defer a.free(restored);
        try d12.decode(bytes, fixture.raw.len, restored);
        std.mem.doNotOptimizeAway(restored);
        if (verify and !std.mem.eql(u16, fixture.raw, restored)) return error.WordMismatch;
    } else {
        var restored = if (codec == .t5m) try t5m.decode(a, bytes) else try t33.decode(a, bytes);
        defer restored.deinit(a);
        std.mem.doNotOptimizeAway(restored.words);
        std.mem.doNotOptimizeAway(restored.bit_storage);
        if (verify) try checkWords(fixture.words, restored.words);
    }
}
fn batch(comptime codec: Codec, comptime op: Op, fixture: Fixture, bytes: []const u8, reps: usize) !u64 {
    const a = std.heap.c_allocator;
    const start = try now();
    for (0..reps) |_| {
        if (op == .encode) {
            const result = try encode(codec, a, fixture);
            std.mem.doNotOptimizeAway(result);
            a.free(result);
        } else {
            try decode(codec, a, fixture, bytes, false);
        }
    }
    const elapsed = (try now()) - start;
    if (elapsed == 0) return error.InvalidMeasurement;
    return elapsed;
}
fn measure(comptime codec: Codec, name: []const u8, fixture: Fixture, reps: usize) !void {
    const a = std.heap.c_allocator;
    var input_bits: usize = 0;
    for (fixture.words) |word| input_bits += word.width;
    std.debug.print("corpus case={s} codec={s} words={d} input_bits={d} logical_trits={d}\n", .{ name, @tagName(codec), fixture.words.len, input_bits, input_bits + fixture.words.len - 1 });
    const bytes = try encode(codec, a, fixture);
    defer a.free(bytes);
    try decode(codec, a, fixture, bytes, true);
    // Це native length, але не доказ семантики/викличності SENS.
    if (codec == .d12) {
        std.debug.print("fixture case={s} codec=d12 words={d} payload_bytes={d} frame_bytes=NOT_DEFINED external_width=12 external_word_count={d} roundtrip=EXACT\n",
            .{ name, fixture.words.len, bytes.len, fixture.words.len });
    } else {
        std.debug.print("fixture case={s} codec={s} words={d} carrier_bytes={d} roundtrip=EXACT\n",
            .{ name, @tagName(codec), fixture.words.len, bytes.len });
    }
    inline for (.{ Op.encode, Op.decode }) |op| {
        _ = try batch(codec, op, fixture, bytes, reps); // Один прогрітий batch.
    }
    var enc: [21]u64 = undefined;
    var dec: [21]u64 = undefined;
    // Чергуємо encode/decode порядок; один процес і один corpus на пару.
    for (0..21) |i| {
        if (i % 2 == 0) {
            enc[i] = try batch(codec, .encode, fixture, bytes, reps);
            dec[i] = try batch(codec, .decode, fixture, bytes, reps);
        } else {
            dec[i] = try batch(codec, .decode, fixture, bytes, reps);
            enc[i] = try batch(codec, .encode, fixture, bytes, reps);
        }
        std.debug.print("sample case={s} codec={s} index={d} encode_ns={d} decode_ns={d} reps={d}\n",
            .{ name, @tagName(codec), i, enc[i], dec[i], reps });
    }
    std.mem.sort(u64, &enc, {}, std.sort.asc(u64));
    std.mem.sort(u64, &dec, {}, std.sort.asc(u64));
    // Nearest rank: ceil(21*.50)-1=10; ceil(21*.95)-1=19.
    // p95 — між batch averages, НЕ request latency і НЕ довірчий інтервал.
    inline for (.{ Op.encode, Op.decode }) |op| {
        const samples = if (op == .encode) enc else dec;
        std.debug.print("summary case={s} codec={s} op={s} p50_ns_per_op={d:.3} p95_ns_per_op={d:.3} batches=21 scope=codec_api_alloc_free\n",
            .{ name, @tagName(codec), @tagName(op),
               @as(f64, @floatFromInt(samples[10])) / @as(f64, @floatFromInt(reps)),
               @as(f64, @floatFromInt(samples[19])) / @as(f64, @floatFromInt(reps)) });
    }
}
pub fn main() !void {
    std.debug.print("benchmark scope=physical_codec_only native=true t33r=NOT_IMPLEMENTED evaluator=NOT_MEASURED\n", .{});
    const a = std.heap.c_allocator;
    // Типовий транспортний pattern; це НЕ виконувана семантична програма.
    for ([_]usize{ 1, 16, 128, 1024 }) |forms| {
        const words = try a.alloc(t5m.Word, forms * Pattern.len);
        defer a.free(words);
        for (0..forms) |i| @memcpy(words[i * Pattern.len ..][0..Pattern.len], &Pattern);
        const f = Fixture{ .words = words };
        try measure(.t5m, "pattern-10-100-01", f, 300);
        try measure(.t33, "pattern-10-100-01", f, 300);
    }
    const zeros = [_]u8{'0'} ** 231;
    for ([_]usize{ 1, 4, 5, 32, 33, 34, 127, 128, 231 }) |width| {
        const words = [_]t5m.Word{.{ .width = width, .bits = zeros[0..width] }};
        const f = Fixture{ .words = &words };
        try measure(.t5m, "width-boundary-zero", f, 300);
        try measure(.t33, "width-boundary-zero", f, 300);
    }
    const extreme = Fixture{
        .words = &.{
            .{ .width = 12, .bits = "000000000000" },
            .{ .width = 12, .bits = "111111111111" },
            .{ .width = 12, .bits = "100000000000" },
            .{ .width = 12, .bits = "000000000001" },
            .{ .width = 12, .bits = "011111111111" },
        },
        .raw = &.{ 0, 0xfff, 0x800, 1, 0x7ff },
    };
    try measure(.t5m, "d12-extremes", extreme, 300);
    try measure(.t33, "d12-extremes", extreme, 300);
    try measure(.d12, "d12-extremes", extreme, 300);
    // Однакові точні D12 words для усіх трьох codec API.
    // Крайові counts охоплюють odd/even, 33-trit і ULEB межі.
    for ([_]usize{ 1, 2, 3, 10, 11, 127, 128, 129, 1024 }) |count| {
        const raw = try a.alloc(u16, count);
        defer a.free(raw);
        const storage = try a.alloc([12]u8, count);
        defer a.free(storage);
        const words = try a.alloc(t5m.Word, count);
        defer a.free(words);
        for (0..count) |i| {
            raw[i] = @intCast((i * 73 + (i >> 1) * 137) & 0x0fff);
            for (0..12) |bit| {
                const shift: u4 = @intCast(11 - bit);
                storage[i][bit] = if (((raw[i] >> shift) & 1) == 0) '0' else '1';
            }
            words[i] = .{ .width = 12, .bits = &storage[i] };
        }
        const f = Fixture{ .words = words, .raw = raw };
        // Ротація порядку codec-процедур; не усуває drift одного hosted runner.
        if (count % 2 == 0) {
            try measure(.d12, "d12-affine-v1", f, 300);
            try measure(.t33, "d12-affine-v1", f, 300);
            try measure(.t5m, "d12-affine-v1", f, 300);
        } else {
            try measure(.t5m, "d12-affine-v1", f, 300);
            try measure(.t33, "d12-affine-v1", f, 300);
            try measure(.d12, "d12-affine-v1", f, 300);
        }
    }
}

