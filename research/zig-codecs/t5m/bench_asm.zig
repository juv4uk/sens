//! T5M asm-бекенд — механічний бенчмарк. x86-64 SysV асемблерний pack/unpack
//! (research/asm-t5m/t5m_pack.S, 5 трітів/байт, 3^5=243<256).
//! Міряє ядро asm (trit→byte / byte→trit) на заздалегідь побудованому потоці
//! тритів; крос-бекенд паритет байтів звіряє драйвер ДО таймінгу.
//! Це транспортна механіка, НЕ SENS-семантика. Формат виводу — як у bench.zig.
const std = @import("std");

/// Локальний мінімальний опис слова (width біт, значення bits) — як t5.Word,
/// але без імпорту кодека: asm-бенч самодостатній, а паритет байтів звіряє драйвер.
const Word = struct { width: u8, bits: u16 };

extern fn sens_t5m_pack(trits: [*]const u8, n: usize, out: [*]u8) u64;
extern fn sens_t5m_unpack(bytes: [*]const u8, n: usize, trits: [*]u8) void;

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

/// Слова → плоский потік тритів: роздільник 2 між словами, доповнення 2 до кратного 5.
fn tritStream(allocator: std.mem.Allocator, words: []const Word) ![]u8 {
    var total: usize = 0;
    for (words) |w| total += w.width;
    if (words.len > 0) total += words.len - 1;
    while (total % 5 != 0) total += 1;
    const trits = try allocator.alloc(u8, total);
    var at: usize = 0;
    for (words, 0..) |w, idx| {
        if (idx != 0) {
            trits[at] = 2;
            at += 1;
        }
        var i: u8 = w.width;
        while (i > 0) {
            i -= 1;
            trits[at] = @intCast((w.bits >> @intCast(i)) & 1);
            at += 1;
        }
    }
    while (at < total) : (at += 1) trits[at] = 2;
    return trits;
}

fn trial(
    comptime operation: enum { encode, decode },
    trits: []const u8,
    physical: []const u8,
    forms: usize,
    repetitions: usize,
    out_bytes: []u8,
    out_trits: []u8,
) void {
    const begin = nanoseconds();
    for (0..repetitions) |_| {
        if (operation == .encode) {
            const written = sens_t5m_pack(trits.ptr, trits.len, out_bytes.ptr);
            std.mem.doNotOptimizeAway(written);
        } else {
            sens_t5m_unpack(physical.ptr, physical.len, out_trits.ptr);
            std.mem.doNotOptimizeAway(out_trits.ptr);
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
        const words = try allocator.alloc(Word, forms * Pattern.len);
        defer allocator.free(words);
        for (0..forms) |j| {
            @memcpy(words[j * Pattern.len ..][0..Pattern.len], &Pattern);
        }

        const trits = try tritStream(allocator, words);
        defer allocator.free(trits);

        const physical = try allocator.alloc(u8, trits.len / 5);
        defer allocator.free(physical);
        const written = sens_t5m_pack(trits.ptr, trits.len, physical.ptr);
        if (written != physical.len) return error.MechanicalParityMismatch;

        // Локальний round-trip asm→asm; крос-бекенд паритет звіряє драйвер.
        const asm_trits = try allocator.alloc(u8, physical.len * 5);
        defer allocator.free(asm_trits);
        sens_t5m_unpack(physical.ptr, physical.len, asm_trits.ptr);
        if (!std.mem.eql(u8, asm_trits, trits)) return error.MechanicalParityMismatch;

        std.debug.print("fixture impl=asm forms={d} words={d} bytes={d} fnv64={x}\n", .{
            forms, words.len, physical.len, fnv64(physical),
        });
        std.debug.print("physical impl=asm forms={d} hex=", .{forms});
        const alphabet = "0123456789abcdef";
        for (physical) |byte| {
            std.debug.print("{c}{c}", .{ alphabet[byte >> 4], alphabet[byte & 15] });
        }
        std.debug.print("\n", .{});

        for (0..3) |_| {
            _ = sens_t5m_pack(trits.ptr, trits.len, physical.ptr);
            sens_t5m_unpack(physical.ptr, physical.len, asm_trits.ptr);
        }
        for (0..5) |_| {
            trial(.encode, trits, physical, forms, reps[i], physical, asm_trits);
            trial(.decode, trits, physical, forms, reps[i], physical, asm_trits);
        }
    }
}
