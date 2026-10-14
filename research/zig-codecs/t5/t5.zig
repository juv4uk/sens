//! Незалежний механічний T5-декодер/кодер (Zig 0.16.0).
//! SENS залишається двійковим: трит 2 — лише межа у фізичному носії.
//! Точна ширина й біти первинні; T5 є лише фізичним носієм.
//! ВАЖЛИВО: цей модуль НЕ перевіряє D2-синтаксис і НЕ є оракулом семантики.
const std = @import("std");

pub const Word = struct {
    /// D1..D9 — саме ширина слова, НЕ десятковий ідентифікатор функції.
    width: u8,
    /// Точні біти слова; провідні нулі зберігаються полем width.
    bits: u16,
};

pub const MAX_PHYSICAL_BYTES: usize = 4 * 1024 * 1024;
const TRITS_PER_BYTE: usize = 5;

pub const Error = error{
    EmptyProgram,
    UnsupportedDomainWidth,
    TransportTooLarge,
    InvalidPhysicalByte,
    InvalidTail,
    EmptyDomainWord,
    NoncanonicalEncoding,
};

fn validWord(word: Word, max_width: u8) bool {
    if (word.width == 0 or word.width > max_width) return false;
    const limit: u32 = @as(u32, 1) << @as(u5, @intCast(word.width));
    return @as(u32, word.bits) < limit;
}

fn appendDigit(
    out: []u8,
    index: *usize,
    current: *u8,
    used: *u8,
    digit: u8,
) void {
    std.debug.assert(digit <= 2);
    current.* = current.* * 3 + digit;
    used.* += 1;
    if (used.* == TRITS_PER_BYTE) {
        out[index.*] = current.*;
        index.* += 1;
        current.* = 0;
        used.* = 0;
    }
}

/// Чистий T5 для вже типізованих слів (НЕ допуск виконуваної програми).
/// Caller owns returned bytes and must free them with the same allocator.
pub fn encode(allocator: std.mem.Allocator, words: []const Word) ![]u8 {
    return encodeWidth(allocator, words, 9);
}

/// D10 is a *mechanical coordinate* only; this does NOT enable calls.
pub fn encodeCoordinates(allocator: std.mem.Allocator, words: []const Word) ![]u8 {
    return encodeWidth(allocator, words, 10);
}

fn encodeWidth(allocator: std.mem.Allocator, words: []const Word, max_width: u8) ![]u8 {
    if (words.len == 0) return Error.EmptyProgram;

    const trit_budget = MAX_PHYSICAL_BYTES * TRITS_PER_BYTE;
    var total_trits: usize = 0;
    for (words, 0..) |word, i| {
        if (!validWord(word, max_width)) return Error.UnsupportedDomainWidth;
        const cost: usize = @as(usize, word.width) + @as(usize, @intFromBool(i != 0));
        if (cost > trit_budget - total_trits) return Error.TransportTooLarge;
        total_trits += cost;
    }
    const len = (total_trits + TRITS_PER_BYTE - 1) / TRITS_PER_BYTE;
    const out = try allocator.alloc(u8, len);
    errdefer allocator.free(out);

    var index: usize = 0;
    var current: u8 = 0;
    var used: u8 = 0;
    for (words, 0..) |word, i| {
        if (i != 0) appendDigit(out, &index, &current, &used, 2);
        var shift: u8 = word.width;
        while (shift > 0) {
            shift -= 1;
            const digit: u8 = @intCast((word.bits >> @as(u4, @intCast(shift))) & 1);
            appendDigit(out, &index, &current, &used, digit);
        }
    }
    while (used != 0) {
        appendDigit(out, &index, &current, &used, 2);
    }
    std.debug.assert(index == len);
    return out;
}

/// Allocation-free T5 physical validation for hosted and freestanding
/// adapters. This checks only the wire (ternary byte range, separator, tail,
/// declared width), never a function identity, domain meaning, or SENS law.
///
/// The canonical T5 encoder emits one separator trit between opaque words and
/// pads the final physical byte with 0..4 separator trits. These conditions
/// are sufficient for byte-for-byte canonical replay without allocating words.
pub fn validatePhysical(data: []const u8) Error!void {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len > MAX_PHYSICAL_BYTES) return Error.TransportTooLarge;
    for (data) |byte| {
        if (byte >= 243) return Error.InvalidPhysicalByte;
    }

    var tail: usize = 0;
    tail_scan: {
        var i = data.len;
        while (i > 0) {
            i -= 1;
            var byte = data[i];
            for (0..TRITS_PER_BYTE) |_| {
                if (byte % 3 != 2) break :tail_scan;
                tail += 1;
                byte /= 3;
            }
        }
    }
    if (tail >= TRITS_PER_BYTE) return Error.InvalidTail;
    const useful_trits = data.len * TRITS_PER_BYTE - tail;

    var consumed: usize = 0;
    var width: u8 = 0;
    for (data) |raw| {
        if (consumed == useful_trits) break;
        var byte = raw;
        var digits: [TRITS_PER_BYTE]u8 = undefined;
        var j: usize = TRITS_PER_BYTE;
        while (j > 0) {
            j -= 1;
            digits[j] = byte % 3;
            byte /= 3;
        }
        for (digits) |digit| {
            if (consumed == useful_trits) break;
            consumed += 1;
            if (digit == 2) {
                if (width == 0) return Error.EmptyDomainWord;
                width = 0;
            } else {
                if (width >= 9) return Error.UnsupportedDomainWidth;
                width += 1;
            }
        }
    }
    if (width == 0) return Error.EmptyDomainWord;
}

/// Декодує тільки фізичний T5; для виконання далі потрібен чинний SENS reader.
/// Caller owns returned words and must free them with the same allocator.
pub fn decode(allocator: std.mem.Allocator, data: []const u8) ![]Word {
    return decodeWidth(allocator, data, 9);
}

/// Read D1–D10 coordinates as physical words; never grant execution authority.
pub fn decodeCoordinates(allocator: std.mem.Allocator, data: []const u8) ![]Word {
    return decodeWidth(allocator, data, 10);
}

fn decodeWidth(allocator: std.mem.Allocator, data: []const u8, max_width: u8) ![]Word {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len > MAX_PHYSICAL_BYTES) return Error.TransportTooLarge;
    for (data) |byte| {
        if (byte >= 243) return Error.InvalidPhysicalByte;
    }

    // Тільки 0..4 термінальних тритів 2; цілий байт padding — помилка.
    var tail: usize = 0;
    tail_scan: {
        var i = data.len;
        while (i > 0) {
            i -= 1;
            var byte = data[i];
            var j: usize = 0;
            while (j < TRITS_PER_BYTE) : (j += 1) {
                if (byte % 3 != 2) break :tail_scan;
                tail += 1;
                byte /= 3;
            }
        }
    }
    if (tail >= TRITS_PER_BYTE) return Error.InvalidTail;
    const useful_trits = data.len * TRITS_PER_BYTE - tail;

    var decoded: std.ArrayList(Word) = .empty;
    defer decoded.deinit(allocator);
    var width: u8 = 0;
    var bits: u16 = 0;
    var consumed: usize = 0;

    for (data) |raw| {
        if (consumed >= useful_trits) break;
        var byte = raw;
        var digits: [TRITS_PER_BYTE]u8 = undefined;
        var j: usize = TRITS_PER_BYTE;
        while (j > 0) {
            j -= 1;
            digits[j] = byte % 3;
            byte /= 3;
        }
        for (digits) |digit| {
            if (consumed == useful_trits) break;
            consumed += 1;
            if (digit == 2) {
                if (width == 0) return Error.EmptyDomainWord;
                try decoded.append(allocator, .{ .width = width, .bits = bits });
                width = 0;
                bits = 0;
            } else {
                if (width >= max_width) return Error.UnsupportedDomainWidth;
                width += 1;
                bits = (bits << 1) | @as(u16, digit);
            }
        }
    }
    if (width == 0) return Error.EmptyDomainWord;
    try decoded.append(allocator, .{ .width = width, .bits = bits });

    // Приймаємо тільки канонічне фізичне представлення.
    const canonical = try encodeWidth(allocator, decoded.items, max_width);
    defer allocator.free(canonical);
    if (!std.mem.eql(u8, canonical, data)) return Error.NoncanonicalEncoding;
    return decoded.toOwnedSlice(allocator);
}

test "D10 mechanical coordinate bits do not become executable D9" {
    const a = std.testing.allocator;
    var bits: u16 = 0;
    while (bits < 1024) : (bits += 1) {
        const source = [_]Word{.{ .width = 10, .bits = bits }};
        const physical = try encodeCoordinates(a, &source);
        defer a.free(physical);
        const recovered = try decodeCoordinates(a, physical);
        defer a.free(recovered);
        try std.testing.expectEqualSlices(Word, &source, recovered);
        try std.testing.expectError(Error.UnsupportedDomainWidth, decode(a, physical));
    }
    try std.testing.expectError(
        Error.UnsupportedDomainWidth,
        encodeCoordinates(a, &.{.{ .width = 10, .bits = 1024 }}),
    );
}

test "T5 відомі фізичні вектори exact-width" {
    const Fixture = struct {
        words: []const Word,
        bytes: []const u8,
    };
    const vectors = [_]Fixture{
        .{ .words = &.{.{ .width = 1, .bits = 0 }}, .bytes = &.{0x50} },
        .{ .words = &.{.{ .width = 1, .bits = 1 }}, .bytes = &.{0xa1} },
        .{ .words = &.{.{ .width = 2, .bits = 2 }}, .bytes = &.{0x6b} },
        .{ .words = &.{.{ .width = 2, .bits = 1 }}, .bytes = &.{0x35} },
        .{ .words = &.{ .{ .width = 2, .bits = 0 }, .{ .width = 1, .bits = 1 } }, .bytes = &.{0x17} },
        .{ .words = &.{ .{ .width = 2, .bits = 2 }, .{ .width = 3, .bits = 4 }, .{ .width = 2, .bits = 1 } }, .bytes = &.{ 0x66, 0x3b } },
        .{ .words = &.{ .{ .width = 1, .bits = 1 }, .{ .width = 2, .bits = 1 }, .{ .width = 3, .bits = 1 } }, .bytes = &.{ 0x8c, 0x11 } },
        .{ .words = &.{.{ .width = 9, .bits = 256 }}, .bytes = &.{ 0x51, 0x02 } },
    };
    for (vectors) |v| {
        const physical = try encode(std.testing.allocator, v.words);
        defer std.testing.allocator.free(physical);
        try std.testing.expectEqualSlices(u8, v.bytes, physical);
        const recovered = try decode(std.testing.allocator, v.bytes);
        defer std.testing.allocator.free(recovered);
        try std.testing.expectEqualSlices(Word, v.words, recovered);
    }
}

test "кожне значення D1..D9 roundtrip без обрізання провідних нулів" {
    var width: u8 = 1;
    while (width <= 9) : (width += 1) {
        const count: u16 = @as(u16, 1) << @as(u4, @intCast(width));
        var bits: u16 = 0;
        while (bits < count) : (bits += 1) {
            const source = [_]Word{.{ .width = width, .bits = bits }};
            const physical = try encode(std.testing.allocator, &source);
            defer std.testing.allocator.free(physical);
            const recovered = try decode(std.testing.allocator, physical);
            defer std.testing.allocator.free(recovered);
            try std.testing.expectEqualSlices(Word, &source, recovered);
        }
    }
}

test "межі T5: invalid physical, tail, empty, надлишкова ширина" {
    const a = std.testing.allocator;
    try std.testing.expectError(Error.EmptyProgram, encode(a, &.{}));
    try std.testing.expectError(Error.EmptyProgram, decode(a, &.{}));
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(a, &.{.{ .width = 0, .bits = 0 }}));
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(a, &.{.{ .width = 2, .bits = 4 }}));
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(a, &.{.{ .width = 10, .bits = 0 }}));
    try std.testing.expectError(Error.InvalidPhysicalByte, decode(a, &.{0xf3}));
    try std.testing.expectError(Error.InvalidPhysicalByte, decode(a, &.{0xff}));
    try std.testing.expectError(Error.InvalidTail, decode(a, &.{0xf2}));
    try std.testing.expectError(Error.EmptyDomainWord, decode(a, &.{0xa2}));
    try std.testing.expectError(Error.EmptyDomainWord, decode(a, &.{0x4d}));
    try std.testing.expectError(Error.UnsupportedDomainWidth, decode(a, &.{ 0x00, 0x00 }));
}

test "heapless physical admission agrees with allocating T5 on all one-byte inputs" {
    const allocator = std.testing.allocator;
    for (0..256) |n| {
        const physical = [_]u8{@intCast(n)};
        const fast_ok = blk: {
            validatePhysical(&physical) catch break :blk false;
            break :blk true;
        };
        const reference_ok = blk: {
            const decoded = decode(allocator, &physical) catch break :blk false;
            allocator.free(decoded);
            break :blk true;
        };
        try std.testing.expectEqual(reference_ok, fast_ok);
    }
}

test "heapless T5 validator preserves opaque 8-bit widths and rejects damaged wire" {
    const allocator = std.testing.allocator;
    const source = [_]Word{
        .{ .width = 8, .bits = 0xa8 },
        .{ .width = 8, .bits = 0 },
        .{ .width = 1, .bits = 1 },
    };
    const physical = try encode(allocator, &source);
    defer allocator.free(physical);
    try validatePhysical(physical);
    const recovered = try decode(allocator, physical);
    defer allocator.free(recovered);
    try std.testing.expectEqualSlices(Word, &source, recovered);
    try std.testing.expectError(Error.EmptyProgram, validatePhysical(&.{}));
    try std.testing.expectError(Error.InvalidPhysicalByte, validatePhysical(&.{0xff}));
    try std.testing.expectError(Error.InvalidTail, validatePhysical(&.{0xf2}));
    try std.testing.expectError(Error.EmptyDomainWord, validatePhysical(&.{0xa2}));
    try std.testing.expectError(Error.UnsupportedDomainWidth, validatePhysical(&.{0x00, 0x00}));
}
