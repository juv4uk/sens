//! Нова реальність: драбина доменів -> фізичні байти через сам Zig-кодек.
//! Вхід (stdin): "D2 10" або "2 10"; ширина — лише метадані,
//! payload — РІВНО стільки двійкових бітів, без десяткового перекодування.
//! Жодного історичного реєстру, жодного Rust/Python-кодека як оракула.
//! НЕ виконує програму і НЕ судить семантику: лише транспорт і round-trip.
const std = @import("std");
const t5 = @import("../t5/t5.zig");
const f3c = @import("../f3c/f3c.zig");

// Zig 0.16 removed std.io.getStdIn(). Host-side POSIX read is deliberately
// isolated HERE, never in the freestanding T5/F3C codec or SENS semantics.
extern "c" fn read(fd: c_int, buffer: [*]u8, count: usize) isize;
const MAX_SOURCE_BYTES: usize = 1024 * 1024;

fn stdinSource(allocator: std.mem.Allocator) ![]u8 {
    const buf = try allocator.alloc(u8, MAX_SOURCE_BYTES + 1);
    errdefer allocator.free(buf);
    var count: usize = 0;
    while (count < buf.len) {
        const received = read(0, buf[count..].ptr, buf.len - count);
        if (received < 0) return error.InputReadFailed;
        if (received == 0) break;
        count += @intCast(received);
    }
    if (count > MAX_SOURCE_BYTES) return error.InputTooLarge;
    // Return a single caller-owned bounded buffer.
    const source = try allocator.dupe(u8, buf[0..count]);
    allocator.free(buf);
    return source;
}


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
    return std.fmt.bytesToHex(digest, .lower);
}

fn parseWords(allocator: std.mem.Allocator, data: []const u8) ![]t5.Word {
    var list: std.ArrayList(t5.Word) = .empty;
    errdefer list.deinit(allocator);
    var it = std.mem.splitScalar(u8, data, '\n');
    while (it.next()) |raw| {
        const line = std.mem.trim(u8, raw, " \t\r");
        if (line.len == 0 or line[0] == '#' or line[0] == ';') continue;
        var cols = std.mem.tokenizeAny(u8, line, " \t");
        const w_str = cols.next() orelse return error.BadLine;
        const b_str = cols.next() orelse return error.BadLine;
        if (cols.next() != null) return error.BadLine;
        const width_label = if (std.mem.startsWith(u8, w_str, "D")) w_str[1..] else w_str;
        // Decimal here denotes the width of a domain, NEVER a payload/code.
        const width = std.fmt.parseInt(u8, width_label, 10) catch return error.BadWidth;
        if (width == 0 or width > 10) return error.BadWidth;
        if (b_str.len != width) return error.WidthMismatch;
        var bits: u16 = 0;
        for (b_str) |bit| {
            if (bit != '0' and bit != '1') return error.InvalidBit;
            bits = (bits << 1) | @as(u16, bit - '0');
        }
        try list.append(allocator, .{ .width = width, .bits = bits });
    }
    if (list.items.len == 0) return error.EmptyProgram;
    return list.toOwnedSlice(allocator);
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    const data = try stdinSource(allocator);
    defer allocator.free(data);
    const words = try parseWords(allocator, data);
    defer allocator.free(words);

    // 1. T5: кодування через сам Zig-кодек.
    const t5_bytes = try t5.encodeCoordinates(allocator, words);
    defer allocator.free(t5_bytes);
    const t5_sha = sha256Hex(t5_bytes);
    std.debug.print("T5 words={d} bytes={d} sha256={s}\n", .{
        words.len, t5_bytes.len, &t5_sha,
    });

    // 2. Round-trip: decode мусить дати ті самі точні слова.
    const back = try t5.decodeCoordinates(allocator, t5_bytes);
    defer allocator.free(back);
    if (back.len != words.len) return error.RoundtripLength;
    for (back, words) |b, w| {
        if (b.width != w.width or b.bits != w.bits) return error.RoundtripMismatch;
    }
    std.debug.print("T5 roundtrip=EXACT words={d}\n", .{back.len});

    // 3. F3C: чи зменшує (opt-in). null = лишити T5.
    const f3c_ordinary = blk: {
        for (words) |word| {
            if (word.width > 9) break :blk false;
        }
        break :blk true;
    };
    // D10 is a valid physical coordinate, not an F3C/ordinary admission.
    const carrier_opt = if (f3c_ordinary) try f3c.encode(allocator, t5_bytes) else null;
    if (carrier_opt) |carrier| {
        defer allocator.free(carrier);
        const restored = try f3c.decode(allocator, carrier);
        defer allocator.free(restored);
        const ok = std.mem.eql(u8, restored, t5_bytes);
        if (!ok) return error.F3CRoundtripMismatch;
        std.debug.print("F3C bytes={d} saves={d} roundtrip=EXACT\n", .{
            carrier.len, t5_bytes.len - carrier.len,
        });
    } else {
        std.debug.print("F3C bytes=none (T5 retained)\n", .{});
    }

    // 4. Бенч: encode/decode, ns/op (механічний транспорт, не семантика).
    const reps: usize = 20000;
    var begin = nanoseconds();
    for (0..reps) |_| {
        const bytes = try t5.encodeCoordinates(allocator, words);
        std.mem.doNotOptimizeAway(bytes);
        allocator.free(bytes);
    }
    const enc_ns = nanoseconds() - begin;
    begin = nanoseconds();
    for (0..reps) |_| {
        const decoded = try t5.decodeCoordinates(allocator, t5_bytes);
        std.mem.doNotOptimizeAway(decoded);
        allocator.free(decoded);
    }
    const dec_ns = nanoseconds() - begin;
    std.debug.print("sample impl=zig op=encode ns_per_op={d} reps={d}\n", .{ enc_ns / reps, reps });
    std.debug.print("sample impl=zig op=decode ns_per_op={d} reps={d}\n", .{ dec_ns / reps, reps });
}

