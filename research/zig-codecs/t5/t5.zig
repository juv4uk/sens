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

/// Caller-owned T5 encode from ABI-v2 triples [width, high bits, low bits].
/// This is an *in-process* physical bridge, not a SENS wire word or semantic ID.
/// No allocator, libc, heap, or function dispatch. Exact width stays opaque.
/// Preflight the complete source and output capacity before writing any bytes.
/// Input and written output must not overlap (checked before the first write).
pub const WriteError = Error || error{
    InvalidTriplets,
    BufferTooSmall,
    OverlappingBuffers,
};

pub fn encodeTripletsInto(out: []u8, input: []const u8) WriteError!usize {
    if (input.len == 0) return Error.EmptyProgram;
    if (input.len % 3 != 0) return error.InvalidTriplets;
    const count = input.len / 3;
    const trit_budget = MAX_PHYSICAL_BYTES * TRITS_PER_BYTE;
    var total_trits: usize = 0;

    // First pass is read-only: reject invalid words even with tiny output.
    for (0..count) |i| {
        const at = i * 3;
        const word = Word{
            .width = input[at],
            .bits = (@as(u16, input[at + 1]) << 8) | @as(u16, input[at + 2]),
        };
        if (!validWord(word, 9)) return Error.UnsupportedDomainWidth;
        const cost: usize = @as(usize, word.width) + @as(usize, @intFromBool(i != 0));
        if (cost > trit_budget - total_trits) return Error.TransportTooLarge;
        total_trits += cost;
    }

    const needed = (total_trits + TRITS_PER_BYTE - 1) / TRITS_PER_BYTE;
    if (out.len < needed) return error.BufferTooSmall;
    // Compare only the bytes actually written; never allow alias corruption.
    const src_addr = @intFromPtr(input.ptr);
    const dst_addr = @intFromPtr(out.ptr);
    if ((src_addr <= dst_addr and dst_addr - src_addr < input.len) or
        (dst_addr < src_addr and src_addr - dst_addr < needed))
        return error.OverlappingBuffers;

    var index: usize = 0;
    var current: u8 = 0;
    var used: u8 = 0;
    for (0..count) |i| {
        if (i != 0) appendDigit(out, &index, &current, &used, 2);
        const at = i * 3;
        const width = input[at];
        const bits = (@as(u16, input[at + 1]) << 8) | @as(u16, input[at + 2]);
        var shift: u8 = width;
        while (shift > 0) {
            shift -= 1;
            const digit: u8 = @intCast((bits >> @as(u4, @intCast(shift))) & 1);
            appendDigit(out, &index, &current, &used, digit);
        }
    }
    while (used != 0) appendDigit(out, &index, &current, &used, 2);
    std.debug.assert(index == needed);
    return needed;
}

/// Allocation-free T5 physical validation for hosted and freestanding
/// adapters. This checks only the wire (ternary byte range, separator, tail,
/// declared width), never a function identity, domain meaning, or SENS law.
///
/// The canonical T5 encoder emits one separator trit between opaque words and
/// pads the final physical byte with 0..4 separator trits. These conditions
/// are sufficient for byte-for-byte canonical replay without allocating words.
pub fn validatePhysical(data: []const u8) Error!void {
    return validatePhysicalWidth(data, 9);
}

/// Allocation-free D1..D10 coordinate profile. This is physical integrity
/// only: a well-formed D10 word is NOT thereby executable or resident.
pub fn validateCoordinatesPhysical(data: []const u8) Error!void {
    return validatePhysicalWidth(data, 10);
}

fn validatePhysicalWidth(data: []const u8, max_width: u8) Error!void {
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
                if (width >= max_width) return Error.UnsupportedDomainWidth;
                width += 1;
            }
        }
    }
    if (width == 0) return Error.EmptyDomainWord;
}

/// Caller-owned, allocation-free T5 -> ABI-v2 byte triples [width, MSB, LSB].
/// Physical D1..D9 only. This is NOT a language code registry or admission.
/// All validation, required size and aliasing are checked before first write.
pub fn decodeTripletsInto(out: []u8, input: []const u8) WriteError!usize {
    try validatePhysical(input);

    var last = input[input.len - 1];
    var tail: usize = 0;
    while (last % 3 == 2) : (tail += 1) last /= 3;
    const useful = input.len * TRITS_PER_BYTE - tail;

    // First pass counts exact words without retaining or interpreting them.
    var word_count: usize = 1;
    var consumed: usize = 0;
    for (input) |raw| {
        if (consumed == useful) break;
        var byte = raw;
        var digits: [TRITS_PER_BYTE]u8 = undefined;
        var j: usize = TRITS_PER_BYTE;
        while (j > 0) {
            j -= 1;
            digits[j] = byte % 3;
            byte /= 3;
        }
        for (digits) |digit| {
            if (consumed == useful) break;
            consumed += 1;
            if (digit == 2) word_count += 1;
        }
    }

    const needed = word_count * 3;
    if (out.len < needed) return error.BufferTooSmall;
    const src_addr = @intFromPtr(input.ptr);
    const dst_addr = @intFromPtr(out.ptr);
    if ((src_addr <= dst_addr and dst_addr - src_addr < input.len) or
        (dst_addr < src_addr and src_addr - dst_addr < needed))
        return error.OverlappingBuffers;

    // Second pass writes only after the entire carrier has passed preflight.
    consumed = 0;
    var written: usize = 0;
    var width: u8 = 0;
    var bits: u16 = 0;
    for (input) |raw| {
        if (consumed == useful) break;
        var byte = raw;
        var digits: [TRITS_PER_BYTE]u8 = undefined;
        var j: usize = TRITS_PER_BYTE;
        while (j > 0) {
            j -= 1;
            digits[j] = byte % 3;
            byte /= 3;
        }
        for (digits) |digit| {
            if (consumed == useful) break;
            consumed += 1;
            if (digit == 2) {
                out[written] = width;
                out[written + 1] = @intCast(bits >> 8);
                out[written + 2] = @intCast(bits & 0xff);
                written += 3;
                width = 0;
                bits = 0;
            } else {
                width += 1;
                bits = (bits << 1) | @as(u16, digit);
            }
        }
    }
    out[written] = width;
    out[written + 1] = @intCast(bits >> 8);
    out[written + 2] = @intCast(bits & 0xff);
    written += 3;
    std.debug.assert(written == needed);
    return needed;
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

