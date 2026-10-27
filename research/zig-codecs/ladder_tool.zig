//! Нова реальність: драбина доменів -> фізичні байти через сам Zig-кодек.
//! Вхід: рядки "width exact_binary_bits"; ширина = домен, біти НЕ десяткові.
//! Жодного історичного реєстру, жодного Rust/Python-кодека як оракула.
//! НЕ виконує програму і НЕ судить семантику: лише транспорт і round-trip.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const ladder = @import("domain_ladder.zig");

const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;

/// Читає файл через libc — як transport.zig; жодного std.io (немає в Zig 0.16).
fn readFile(allocator: std.mem.Allocator, path: []const u8) ![]u8 {
    const zpath = try allocator.dupeZ(u8, path);
    defer allocator.free(zpath);
    const file = fopen(zpath.ptr, "rb") orelse return error.OpenFailed;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return error.SeekFailed;
    const end = ftell(file);
    if (end < 0) return error.SeekFailed;
    if (fseek(file, 0, 0) != 0) return error.SeekFailed;
    const bytes = try allocator.alloc(u8, @intCast(end));
    errdefer allocator.free(bytes);
    if (bytes.len != 0 and fread(bytes.ptr, 1, bytes.len, file) != bytes.len)
        return error.ReadFailed;
    return bytes;
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
    var out: [64]u8 = undefined;
    _ = std.fmt.bufPrint(&out, "{x}", .{digest}) catch unreachable;
    return out;
}

/// Власний hex без std.fmt (у Zig 0.16 fmtSliceHexLower відсутній).
fn hexInto(out: []u8, bytes: []const u8) []u8 {
    const digits = "0123456789abcdef";
    for (bytes, 0..) |b, i| {
        out[i * 2] = digits[b >> 4];
        out[i * 2 + 1] = digits[b & 0xf];
    }
    return out[0 .. bytes.len * 2];
}

fn parseWords(out: []t5.Word, data: []const u8) !usize {
    var count: usize = 0;
    var it = std.mem.splitScalar(u8, data, '\n');
    while (it.next()) |raw| {
        const line = std.mem.trim(u8, raw, " \t\r");
        if (line.len == 0 or line[0] == '#' or line[0] == ';') continue;
        var cols = std.mem.tokenizeAny(u8, line, " \t");
        const w_str = cols.next() orelse return error.BadLine;
        const b_str = cols.next() orelse return error.BadLine;
        if (cols.next() != null) return error.BadLine; // exact two-column record
        // Width is only a rung selector. The payload is the actual exact
        // bit string, including ALL leading zeros; no decimal intermediary.
        const width = try std.fmt.parseInt(u8, w_str, 10);
        if (width == 0 or width > 10) return error.BadWidth;
        const typed = try ladder.Coordinate.parseBinary(b_str);
        if (typed.width != width) return error.WrongDomainWidth;
        if (count >= out.len) return error.TooManyWords;
        out[count] = .{ .width = typed.width, .bits = typed.bits };
        count += 1;
    }
    if (count == 0) return error.EmptyProgram;
    return count;
}

// Optional F3C consumes ordinary D1..D9 T5; D10 is transport-only.
fn f3cCandidateWidths(words: []const t5.Word) bool {
    for (words) |w| {
        if (w.width > 9) return false;
    }
    return true;
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    const data = try readFile(allocator, "caar.lines");
    defer allocator.free(data);
    var word_buf: [4096]t5.Word = undefined;
    const count = try parseWords(&word_buf, data);
    const words = word_buf[0..count];

    // 1. T5: кодування через сам Zig-кодек.
    const t5_bytes = try t5.encodeCoordinates(allocator, words);
    defer allocator.free(t5_bytes);
    const t5_sha = sha256Hex(t5_bytes);
    var hex_buf: [8192]u8 = undefined;
    // Do not overflow the fixed diagnostic buffer on real multiword files.
    // Full data remains in the canonical T5 bytes; SHA covers every byte.
    if (t5_bytes.len <= hex_buf.len / 2) {
        std.debug.print("T5 words={d} bytes={d} sha256={s} hex={s}\n", .{
            words.len, t5_bytes.len, t5_sha[0..],
            hexInto(&hex_buf, t5_bytes),
        });
    } else {
        std.debug.print("T5 words={d} bytes={d} sha256={s} hex=omitted-large\n", .{
            words.len, t5_bytes.len, t5_sha[0..],
        });
    }

    // 2. Round-trip: decode мусить дати ті самі точні слова.
    const back = try t5.decodeCoordinates(allocator, t5_bytes);
    defer allocator.free(back);
    if (back.len != words.len) return error.RoundtripLength;
    for (back, words) |b, w| {
        if (b.width != w.width or b.bits != w.bits) return error.RoundtripMismatch;
    }
    std.debug.print("T5 roundtrip=EXACT words={d}\n", .{back.len});

    // 3. F3C is optional and currently requires the ordinary D1..D9 T5
    // profile. A valid D10 coordinate must remain in T5, not be reinterpreted
    // as executable D9 or rejected by an optional compression attempt.
    if (f3cCandidateWidths(words)) {
        const carrier_opt = try f3c.encode(allocator, t5_bytes);
        if (carrier_opt) |carrier| {
            defer allocator.free(carrier);
            const restored = try f3c.decode(allocator, carrier);
            defer allocator.free(restored);
            const ok = std.mem.eql(u8, restored, t5_bytes);
            std.debug.print("F3C bytes={d} saves={d} roundtrip={s}\n", .{
                carrier.len, t5_bytes.len - carrier.len, if (ok) "EXACT" else "MISMATCH",
            });
            if (!ok) return error.F3CRoundtripMismatch;
        } else {
            std.debug.print("F3C bytes=none (T5 retained)\n", .{});
        }
    } else {
        std.debug.print("F3C bytes=none (D10 coordinate profile; T5 retained)\n", .{});
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

