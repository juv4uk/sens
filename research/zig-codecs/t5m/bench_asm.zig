//! T5M asm-бекенд — механічний бенчмарк. x86-64 SysV асемблерний кодек
//! (research/asm-t5m/t5m_words.S + t5m_pack.S, 5 трітів/байт, 3^5=243<256).
//! Міряє ТОЙ САМИЙ шлях слово→байт / байт→слово, що й bench.zig та Rust,
//! тож рядки порівнювані. Це транспортна механіка, НЕ SENS-семантика.
//! Формат виводу — як у bench.zig (fixture/physical/sample).
const std = @import("std");

/// Локальний мінімальний опис слова (width біт, значення bits) — як t5.Word.
const Word = struct { width: u8, bits: u16 };

extern fn sens_t5m_encode(bits: [*]const u16, widths: [*]const u8, n: usize,
    scratch: [*]u8, out: [*]u8) u64;
extern fn sens_t5m_decode(bytes: [*]const u8, n_bytes: usize, scratch: [*]u8,
    out_bits: [*]u16, out_widths: [*]u8) u64;

const Timespec = extern struct { tv_sec: c_long, tv_nsec: c_long };
extern "c" fn clock_gettime(clock_id: c_int, ts: *Timespec) c_int;
const CLOCK_MONOTONIC: c_int = 1;

fn nanoseconds() u64 {
    var ts: Timespec = undefined;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) @panic("clock_gettime failed");
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 + @as(u64, @intCast(ts.tv_nsec));
}

fn fnv64(bytes: []const u8) u64 {
    var hash: u64 = 0xcbf29ce484222325;
    for (bytes) |b| hash = (hash ^ @as(u64, b)) *% 0x100000001b3;
    return hash;
}

const Pattern = [_]Word{
    .{ .width = 2, .bits = 2 },
    .{ .width = 3, .bits = 4 },
    .{ .width = 2, .bits = 1 },
};

fn trial(
    comptime operation: enum { encode, decode },
    n: usize,
    n_bytes: usize,
    bits: []const u16,
    widths: []const u8,
    physical: []const u8,
    forms: usize,
    repetitions: usize,
    scratch: []u8,
    out_bytes: []u8,
    out_bits: []u16,
    out_widths: []u8,
) void {
    const begin = nanoseconds();
    for (0..repetitions) |_| {
        if (operation == .encode) {
            const written = sens_t5m_encode(bits.ptr, widths.ptr, n, scratch.ptr, out_bytes.ptr);
            std.mem.doNotOptimizeAway(written);
        } else {
            const words = sens_t5m_decode(physical.ptr, n_bytes, scratch.ptr,
                out_bits.ptr, out_widths.ptr);
            std.mem.doNotOptimizeAway(words);
        }
    }
    const elapsed = nanoseconds() - begin;
    std.debug.print("sample impl=asm forms={d} op={s} elapsed_ns={d} reps={d}\n", .{
        forms, @tagName(operation), elapsed, repetitions,
    });
}

pub fn main() !void {
    const allocator = std.heap.c_allocator;
    const cases = [_]usize{ 1, 16, 128, 1024 };
    const reps = [_]usize{ 12000, 3000, 600, 100 };

    for (cases, 0..) |forms, i| {
        const n = forms * Pattern.len;
        const bits = try allocator.alloc(u16, n);
        defer allocator.free(bits);
        const widths = try allocator.alloc(u8, n);
        defer allocator.free(widths);
        for (0..forms) |j| {
            for (Pattern, 0..) |w, k| {
                bits[j * Pattern.len + k] = w.bits;
                widths[j * Pattern.len + k] = w.width;
            }
        }
        const scratch = try allocator.alloc(u8, 6 * n + 8);
        defer allocator.free(scratch);
        const physical = try allocator.alloc(u8, 2 * n + 8);
        defer allocator.free(physical);
        const out_bits = try allocator.alloc(u16, n);
        defer allocator.free(out_bits);
        const out_widths = try allocator.alloc(u8, n);
        defer allocator.free(out_widths);

        const written = sens_t5m_encode(bits.ptr, widths.ptr, n, scratch.ptr, physical.ptr);
        const decoded = sens_t5m_decode(physical.ptr, written, scratch.ptr, out_bits.ptr, out_widths.ptr);
        if (decoded != n) return error.MechanicalParityMismatch;
        for (0..n) |k| {
            if (out_bits[k] != bits[k] or out_widths[k] != widths[k])
                return error.MechanicalParityMismatch;
        }

        std.debug.print("fixture impl=asm forms={d} words={d} bytes={d} fnv64={x}\n", .{
            forms, n, written, fnv64(physical[0..written]),
        });
        std.debug.print("physical impl=asm forms={d} hex=", .{forms});
        const alphabet = "0123456789abcdef";
        for (physical[0..written]) |byte| {
            std.debug.print("{c}{c}", .{ alphabet[byte >> 4], alphabet[byte & 15] });
        }
        std.debug.print("\n", .{});

        for (0..3) |_| {
            _ = sens_t5m_encode(bits.ptr, widths.ptr, n, scratch.ptr, physical.ptr);
            _ = sens_t5m_decode(physical.ptr, written, scratch.ptr, out_bits.ptr, out_widths.ptr);
        }
        for (0..5) |_| {
            trial(.encode, n, written, bits, widths, physical, forms, reps[i], scratch, physical, out_bits, out_widths);
            trial(.decode, n, written, bits, widths, physical, forms, reps[i], scratch, physical, out_bits, out_widths);
        }
    }
}
