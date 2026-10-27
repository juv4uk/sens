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

