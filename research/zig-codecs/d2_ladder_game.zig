//! Експеримент «Драбина D2»: п'ять структурних тритів в одному байті.
//! Лише Zig-транспорт. Жодної оцінки Lisp/SENS або зміни канонічного T5.
//! Лише підмножина D2: 00 -> 0, 01 -> 1, 10 -> 2. D2:11 (крапка) відхиляється.
//! У повному D2 чотири слова: без контексту немає гарантованого виграшу
//! відносно двох бітів на слово для всіх можливих D2-послідовностей.
//! Довжина в тритах надходить із зовнішнього контексту, НЕ вгадується з байтів.
//! Без карти позицій D2 у змішаній програмі це НЕ повний кодек програми.
const std = @import("std");

const powers = [_]u8{ 81, 27, 9, 3, 1 };

pub fn pack(allocator: std.mem.Allocator, trits: []const u8) ![]u8 {
    const byte_count = trits.len / 5 + @intFromBool(trits.len % 5 != 0);
    const bytes = try allocator.alloc(u8, byte_count);
    errdefer allocator.free(bytes);
    @memset(bytes, 0);
    for (trits, 0..) |trit, i| {
        if (trit > 2) return error.InvalidTrit;
        bytes[i / 5] += trit * powers[i % 5];
    }
    return bytes;
}

pub fn unpack(allocator: std.mem.Allocator, bytes: []const u8, trit_count: usize) ![]u8 {
    const expected_bytes = trit_count / 5 + @intFromBool(trit_count % 5 != 0);
    if (bytes.len != expected_bytes) return error.WrongLength;
    const trits = try allocator.alloc(u8, trit_count);
    errdefer allocator.free(trits);
    for (bytes, 0..) |byte, byte_index| {
        if (byte >= 243) return error.InvalidByte;
        var remainder = byte;
        for (powers, 0..) |power, position| {
            const trit = remainder / power;
            remainder %= power;
            const index = byte_index * 5 + position;
            if (index < trit_count) {
                trits[index] = trit;
            } else if (trit != 0) {
                return error.NoncanonicalPadding;
            }
        }
    }
    return trits;
}

test "усі 243 п'ятірки D2 мають точне зворотне перетворення" {
    const allocator = std.testing.allocator;
    for (0..243) |number| {
        var source: [5]u8 = undefined;
        var n = number;
        var i: usize = source.len;
        while (i > 0) {
            i -= 1;
            source[i] = @intCast(n % 3);
            n /= 3;
        }
        const physical = try pack(allocator, &source);
        defer allocator.free(physical);
        try std.testing.expectEqual(@as(usize, 1), physical.len);
        try std.testing.expectEqual(@as(u8, @intCast(number)), physical[0]);
        const back = try unpack(allocator, physical, source.len);
        defer allocator.free(back);
        try std.testing.expectEqualSlices(u8, &source, back);
    }
}

test "пошкоджені та неканонічні байти не проходять" {
    const allocator = std.testing.allocator;
    for (243..256) |number| {
        const invalid = [_]u8{@intCast(number)};
        try std.testing.expectError(error.InvalidByte, unpack(allocator, &invalid, 5));
    }
    // 3 означав би D2:11 (DOT), що поза цією трисимвольною підмножиною.
    try std.testing.expectError(error.InvalidTrit, pack(allocator, &.{ 0, 3 }));
    try std.testing.expectError(error.WrongLength, unpack(allocator, &.{ 0, 0 }, 1));
    // Один змістовний трит 2; ненульовий хвіст заборонено.
    try std.testing.expectError(error.NoncanonicalPadding, unpack(allocator, &.{189}, 1));
    const canonical = try unpack(allocator, &.{162}, 1);
    defer allocator.free(canonical);
    try std.testing.expectEqualSlices(u8, &.{2}, canonical);
}

test "CAAR: злиті D2 стискаються, перемежовані серії не дають виграшу" {
    const allocator = std.testing.allocator;
    // D2-послідовність із tools/caar.ladder без інших доменів.
    const source = [_]u8{ 2, 0, 2, 0, 2, 0, 2, 0, 1, 0, 2, 0, 1, 1, 0, 2, 0, 1, 1, 1 };
    const merged = try pack(allocator, &source);
    defer allocator.free(merged);
    try std.testing.expectEqualSlices(u8, &.{ 182, 57, 174, 175 }, merged);
    try std.testing.expectEqual(@as(usize, 4), merged.len); // 20 D2 по 2 біти = 5 байтів
    const restored = try unpack(allocator, merged, source.len);
    defer allocator.free(restored);
    try std.testing.expectEqualSlices(u8, &source, restored);

    // Реальні D2-серії перериваються словами D3/D4.
    const runs = [_][]const u8{
        &.{2}, &.{ 0, 2 }, &.{ 0, 2 }, &.{ 0, 2 }, &.{0},
        &.{ 1, 0, 2 }, &.{0}, &.{ 1, 1, 0, 2 }, &.{0}, &.{ 1, 1, 1 },
    };
    var total_bytes: usize = 0;
    for (runs) |run| {
        const packed = try pack(allocator, run);
        defer allocator.free(packed);
        total_bytes += packed.len;
        const back = try unpack(allocator, packed, run.len);
        defer allocator.free(back);
        try std.testing.expectEqualSlices(u8, run, back);
    }
    try std.testing.expectEqual(@as(usize, 10), total_bytes);
    // Позиції D2 у змішаному потоці тут ще не закодовані.
}
