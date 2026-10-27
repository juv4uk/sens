//! T5M physical transport: five logical trits (0/1 bits, 2 word separators)
//! are ranked in base 3 and stored in one byte. T5M3 is the separate 15-trit/3-byte codec.
//! This layer preserves exact word widths and bits; it assigns no semantics.
const std = @import("std");

pub const MAX_PHYSICAL_BYTES: usize = 4 * 1024 * 1024;
const TRITS_PER_BYTE: usize = 5;
const MAX_BYTE_VALUE: u8 = 243; // 3^5; valid physical byte values are 0..242.

pub const Error = error{
    EmptyProgram,
    UnsupportedDomainWidth,
    InvalidBinaryDigit,
    InvalidPhysicalByte,
    InvalidPhysicalGroup,
    InvalidTail,
    EmptyDomainWord,
    TransportTooLarge,
    OutOfMemory,
};

/// Exact width is supplied by the SENS caller. The transport does not infer
/// a domain, a numeric type, or callability from the bit count.
pub const Word = struct {
    width: usize,
    bits: []const u8,
};

pub const DecodedWord = struct {
    width: usize,
    bits: []const u8,
};

pub const Decoded = struct {
    words: []DecodedWord,
    bit_storage: []u8,

    pub fn deinit(self: *Decoded, allocator: std.mem.Allocator) void {
        allocator.free(self.words);
        allocator.free(self.bit_storage);
        self.* = undefined;
    }
};

fn supportsWidth(width: usize) bool {
    return width != 0;
}

fn appendDigit(out: []u8, byte_index: *usize, current: *u8, used: *u8, digit: u8) void {
    std.debug.assert(digit <= 2);
    current.* = current.* * 3 + digit;
    used.* += 1;
    if (used.* == TRITS_PER_BYTE) {
        out[byte_index.*] = current.*;
        byte_index.* += 1;
        current.* = 0;
        used.* = 0;
    }
}

/// Encode exact-width binary words; 2 separates words and pads the final group.
/// No numeric marker or domain meaning is added by T5M.
pub fn encode(allocator: std.mem.Allocator, words: []const Word) Error![]u8 {
    if (words.len == 0) return Error.EmptyProgram;

    var trit_count: usize = words.len - 1;
    for (words) |word| {
        if (!supportsWidth(word.width)) return Error.UnsupportedDomainWidth;
        if (word.bits.len != word.width) return Error.UnsupportedDomainWidth;
        if (word.bits.len == 0) return Error.EmptyDomainWord;
        for (word.bits) |bit| {
            if (bit != '0' and bit != '1') return Error.InvalidBinaryDigit;
        }
        trit_count = std.math.add(usize, trit_count, word.width) catch
            return Error.TransportTooLarge;
    }
    const trit_budget = MAX_PHYSICAL_BYTES * TRITS_PER_BYTE;
    if (trit_count > trit_budget) return Error.TransportTooLarge;
    const padded_trits = std.math.add(usize, trit_count, TRITS_PER_BYTE - 1) catch
        return Error.TransportTooLarge;
    const byte_len = padded_trits / TRITS_PER_BYTE;
    const out = allocator.alloc(u8, byte_len) catch return Error.OutOfMemory;
    errdefer allocator.free(out);

    var byte_index: usize = 0;
    var current: u8 = 0;
    var used: u8 = 0;
    for (words, 0..) |word, word_index| {
        if (word_index != 0) appendDigit(out, &byte_index, &current, &used, 2);
        for (word.bits) |bit| appendDigit(out, &byte_index, &current, &used, bit - '0');
    }
    while (used != 0) appendDigit(out, &byte_index, &current, &used, 2);
    std.debug.assert(byte_index == byte_len);
    return out;
}

fn validateWordWidth(width: usize) Error!void {
    if (!supportsWidth(width)) return Error.UnsupportedDomainWidth;
}

/// Decode the mechanical T5M stream, retaining exact leading zeros and widths.
pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error!Decoded {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len > MAX_PHYSICAL_BYTES) return Error.TransportTooLarge;
    const trit_count = std.math.mul(usize, data.len, TRITS_PER_BYTE) catch
        return Error.TransportTooLarge;
    const trits = allocator.alloc(u8, trit_count) catch return Error.OutOfMemory;
    defer allocator.free(trits);
    for (data, 0..) |raw, byte_index| {
        if (raw >= MAX_BYTE_VALUE) return Error.InvalidPhysicalByte;
        var value = raw;
        var place: usize = TRITS_PER_BYTE;
        while (place > 0) {
            place -= 1;
            trits[byte_index * TRITS_PER_BYTE + place] = value % 3;
            value /= 3;
        }
    }

    var padding: usize = 0;
    while (padding < trits.len and trits[trits.len - padding - 1] == 2) : (padding += 1) {}
    if (padding >= TRITS_PER_BYTE) return Error.InvalidTail;
    const body_len = trits.len - padding;
    if (body_len == 0) return Error.EmptyDomainWord;

    var word_count: usize = 1;
    var total_bits: usize = 0;
    var current_width: usize = 0;
    for (trits[0..body_len]) |trit| {
        if (trit == 2) {
            if (current_width == 0) return Error.EmptyDomainWord;
            try validateWordWidth(current_width);
            word_count += 1;
            total_bits = std.math.add(usize, total_bits, current_width) catch
                return Error.TransportTooLarge;
            current_width = 0;
        } else {
            current_width += 1;
        }
    }
    if (current_width == 0) return Error.EmptyDomainWord;
    try validateWordWidth(current_width);
    total_bits = std.math.add(usize, total_bits, current_width) catch
        return Error.TransportTooLarge;

    const words = allocator.alloc(DecodedWord, word_count) catch return Error.OutOfMemory;
    errdefer allocator.free(words);
    const bit_storage = allocator.alloc(u8, total_bits) catch return Error.OutOfMemory;
    errdefer allocator.free(bit_storage);

    var word_index: usize = 0;
    var bit_offset: usize = 0;
    var word_start: usize = 0;
    for (trits[0..body_len]) |trit| {
        if (trit == 2) {
            const width = bit_offset - word_start;
            words[word_index] = .{ .width = width, .bits = bit_storage[word_start..bit_offset] };
            word_index += 1;
            word_start = bit_offset;
        } else {
            bit_storage[bit_offset] = if (trit == 0) '0' else '1';
            bit_offset += 1;
        }
    }
    words[word_index] = .{ .width = bit_offset - word_start, .bits = bit_storage[word_start..bit_offset] };
    return .{ .words = words, .bit_storage = bit_storage };
}

// The physical codec rejects malformed carriers; this is not a semantic oracle.
// Механічний стресовий корпус змішаних ширин: жодної семантики SENS.
