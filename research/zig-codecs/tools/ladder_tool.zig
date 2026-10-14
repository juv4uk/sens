//! Нова реальність: драбина доменів -> фізичні байти через сам Zig-кодек.
//! Вхід (stdin): рядки "width bits" (десяткові), ширина = ідентичність.
//! Жодного історичного реєстру, жодного Rust/Python-кодека як оракула.
//! НЕ виконує програму і НЕ судить семантику: лише транспорт і round-trip.
const std = @import("std");
const t5 = @import("../t5/t5.zig");
const f3c = @import("../f3c/f3c.zig");

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

fn sha256Hex(bytes: []const u8) [64]u8 {
    var digest: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(bytes, &digest, .{});
    var out: [64]u8 = undefined;
    _ = std.fmt.bufPrint(&out, "{x}", .{digest}) catch unreachable;
    return out;
}

fn parseWords(allocator: std.mem.Allocator, data: []const u8) ![]t5.Word {
    var list = std.ArrayList(t5.Word).init(allocator);
    errdefer list.deinit();
    var it = std.mem.splitScalar(u8, data, '\n');
    while (it.next()) |raw| {
        const line = std.mem.trim(u8, raw, " \t\r");
        if (line.len == 0 or line[0] == '#' or line[0] == ';') continue;
        var cols = std.mem.tokenizeAny(u8, line, " \t");
        const w_str = cols.next() orelse return error.BadLine;
        const b_str = cols.next() orelse return error.BadLine;
        const width = try std.fmt.parseInt(u8, w_str, 10);
        const bits = try std.fmt.parseInt(u16, b_str, 10);
        if (width == 0 or width > 10) return error.BadWidth;
        if (bits >= (@as(u32, 1) << @as(u5, @intCast(width)))) return error.BitsOverflow;
        try list.append(.{ .width = width, .bits = bits });
    }
    if (list.items.len == 0) return error.EmptyProgram;
    return list.toOwnedSlice();
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    const data = try std.io.getStdIn().reader().readAllAlloc(allocator, 1 << 20);
    defer allocator.free(data);
    const words = try parseWords(allocator, data);
    defer allocator.free(words);

    // 1. T5: кодування через сам Zig-кодек.
    const t5_bytes = try t5.encode(allocator, words);
    defer allocator.free(t5_bytes);
    const t5_sha = sha256Hex(t5_bytes);
    std.debug.print("T5 words={d} bytes={d} sha256={s} hex={s}\n", .{
        words.len, t5_bytes.len, t5_sha[0..16], t5_bytes[0..@min(t5_bytes.len, 24)],
    });

    // 2. Round-trip: decode мусить дати ті самі точні слова.
    const back = try t5.decode(allocator, t5_bytes);
    defer allocator.free(back);
    if (back.len != words.len) return error.RoundtripLength;
    for (back, words) |b, w| {
        if (b.width != w.width or b.bits != w.bits) return error.RoundtripMismatch;
    }
    std.debug.print("T5 roundtrip=EXACT words={d}\n", .{back.len});

    // 3. F3C: чи зменшує (opt-in). null = лишити T5.
    const packed = try f3c.encode(allocator, t5_bytes);
    if (packed) |carrier| {
        defer allocator.free(carrier);
        const restored = try f3c.decode(allocator, carrier);
        defer allocator.free(restored);
        const ok = std.mem.eql(u8, restored, t5_bytes);
        std.debug.print("F3C bytes={d} saves={d} roundtrip={s}\n", .{
            carrier.len, t5_bytes.len - carrier.len, if (ok) "EXACT" else "MISMATCH",
        });
    } else {
        std.debug.print("F3C bytes=none (T5 retained)\n", .{});
    }

    // 4. Бенч: encode/decode, ns/op (механічний транспорт, не семантика).
    const reps: usize = 20000;
    var begin = nanoseconds();
    for (0..reps) |_| {
        const bytes = try t5.encode(allocator, words);
        std.mem.doNotOptimizeAway(bytes);
        allocator.free(bytes);
    }
    const enc_ns = nanoseconds() - begin;
    begin = nanoseconds();
    for (0..reps) |_| {
        const decoded = try t5.decode(allocator, t5_bytes);
        std.mem.doNotOptimizeAway(decoded);
        allocator.free(decoded);
    }
    const dec_ns = nanoseconds() - begin;
    std.debug.print("sample impl=zig op=encode ns_per_op={d} reps={d}\n", .{ enc_ns / reps, reps });
    std.debug.print("sample impl=zig op=decode ns_per_op={d} reps={d}\n", .{ dec_ns / reps, reps });
}
