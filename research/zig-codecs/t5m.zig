//! T5M: ordinary T5 bit/separator stream extended to numeric D24+ words.
//! Експериментальний транспортний зріз; вимоги перед семантичним прийняттям:
//! - Не плутати відсутню інтеграцію T5M із відсутньою математикою SENS:
//!   парсер уже має точні десяткові/раціональні значення, Core — D24+ арифметику.
//! - На межі T5M виконувати точні двійкові НСД і ділення для канонізації дробу;
//!   не використовувати f64, десяткове округлення чи втрату значущих бітів.
//! - Числовий атом Dn зберігає всі n бітів як натуральне число. Знак — окрема
//!   NEG-композиція, не зарезервований біт усередині Dn.
//! - Для RATIO вимагати q>0 і gcd(|p|,q)=1; нуль зводити до доменного нуля,
//!   знаменник 1 — до цілого/NEG, нульовий або від'ємний знаменник відхиляти.
//! - Зберігати ширини й ідентичності складників; структуру NEG/RATIO декодувати
//!   однозначно, не виводити її лише з довільного сусідства слів.
//! - Якщо результат не вміщується, точно розширити D24→D48→… або повернути
//!   явну помилку; ніколи не обрізати й не округляти. Перевірити round-trip
//!   десяткових, дробових, від'ємних і граничних значень.
//! Поточні makeSignedWord/encodeRatio цього набору ще НЕ виконують:
//! знак займає біт Dn, а НСД/канонізація не реалізовані.
const std = @import("std");
const domain_ladder = @import("domain_ladder.zig");

pub const MAX_PHYSICAL_BYTES: usize = 4 * 1024 * 1024;
const TRITS_PER_BYTE: usize = 5;

pub const Error = error{
    EmptyProgram,
    UnsupportedDomainWidth,
    InvalidMagnitudeWidth,
    InvalidBinaryDigit,
    InvalidPhysicalByte,
    InvalidTail,
    EmptyDomainWord,
    ZeroDenominator,
    TransportTooLarge,
    OutOfMemory,
};

/// Width comes from the typed SENS value, not from its magnitude.
/// D1..D9 preserve ordinary T5; admitted D24+ widths are numeric words.
pub const Word = struct {
    width: usize,
    bits: []const u8,
};

/// A signed D24+ value supplied as its already-converted magnitude bits.
pub const SignedMagnitude = struct {
    width: usize,
    negative: bool,
    magnitude_bits: []const u8,
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
    return (width >= 1 and width <= 9) or
        (width >= 24 and domain_ladder.supportsPhysicalWidth(width));
}

/// Build a D24+ sign-magnitude number. The sign occupies the first bit:
/// 0 is negative, 1 is positive; remaining bits hold the unsigned magnitude.
pub fn makeSignedWord(
    allocator: std.mem.Allocator,
    width: usize,
    negative: bool,
    magnitude_bits: []const u8,
) Error![]u8 {
    if (width < 24 or !domain_ladder.supportsPhysicalWidth(width)) {
        return Error.UnsupportedDomainWidth;
    }
    if (magnitude_bits.len != width - 1) return Error.InvalidMagnitudeWidth;
    for (magnitude_bits) |bit| {
        if (bit != '0' and bit != '1') return Error.InvalidBinaryDigit;
    }

    const bits = allocator.alloc(u8, width) catch return Error.OutOfMemory;
    bits[0] = if (negative) '0' else '1';
    @memcpy(bits[1..], magnitude_bits);
    return bits;
}

/// Encode a rational as adjacent signed numerator and denominator words.
/// Decimal parsing/reduction belongs to the SENS reader/runtime, not T5M.
pub fn encodeRatio(
    allocator: std.mem.Allocator,
    numerator: SignedMagnitude,
    denominator: SignedMagnitude,
) Error![]u8 {
    const numerator_bits = try makeSignedWord(
        allocator,
        numerator.width,
        numerator.negative,
        numerator.magnitude_bits,
    );
    defer allocator.free(numerator_bits);

    const denominator_bits = try makeSignedWord(
        allocator,
        denominator.width,
        denominator.negative,
        denominator.magnitude_bits,
    );
    defer allocator.free(denominator_bits);

    var denominator_nonzero = false;
    for (denominator_bits[1..]) |bit| {
        if (bit == '1') denominator_nonzero = true;
    }
    if (!denominator_nonzero) return Error.ZeroDenominator;

    const words = [_]Word{
        .{ .width = numerator.width, .bits = numerator_bits },
        .{ .width = denominator.width, .bits = denominator_bits },
    };
    return encode(allocator, &words);
}

fn appendDigit(out: []u8, index: *usize, current: *u8, used: *u8, digit: u8) void {
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

/// Encode the ordinary T5 stream: 0/1 bits and trit 2 between words.
/// No marker for numeric type is added; the explicit D24+ word width remains.
pub fn encode(allocator: std.mem.Allocator, words: []const Word) Error![]u8 {
    if (words.len == 0) return Error.EmptyProgram;

    var trit_count: usize = words.len - 1;
    for (words) |word| {
        if (!supportsWidth(word.width)) return Error.UnsupportedDomainWidth;
        if (word.bits.len != word.width) return Error.UnsupportedDomainWidth;
        for (word.bits) |bit| {
            if (bit != '0' and bit != '1') return Error.InvalidBinaryDigit;
        }
        trit_count = std.math.add(usize, trit_count, word.width) catch
            return Error.TransportTooLarge;
    }
    const trit_budget = MAX_PHYSICAL_BYTES * TRITS_PER_BYTE;
    if (trit_count > trit_budget) return Error.TransportTooLarge;
    const byte_len = (trit_count + TRITS_PER_BYTE - 1) / TRITS_PER_BYTE;
    const out = allocator.alloc(u8, byte_len) catch return Error.OutOfMemory;
    errdefer allocator.free(out);

    var index: usize = 0;
    var current: u8 = 0;
    var used: u8 = 0;
    for (words, 0..) |word, word_index| {
        if (word_index != 0) appendDigit(out, &index, &current, &used, 2);
        for (word.bits) |bit| appendDigit(out, &index, &current, &used, bit - '0');
    }
    while (used != 0) appendDigit(out, &index, &current, &used, 2);
    std.debug.assert(index == byte_len);
    return out;
}

fn validateWordWidth(width: usize) Error!void {
    if (!supportsWidth(width)) return Error.UnsupportedDomainWidth;
}

/// Decode ordinary T5 words plus admitted D24+ numeric words, retaining zeros.
/// Each number carries its sign in its first bit; ratios are adjacent signed
/// D24+ words, while semantic D2 separates independent numbers.
pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error!Decoded {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len > MAX_PHYSICAL_BYTES) return Error.TransportTooLarge;
    for (data) |byte| {
        if (byte >= 243) return Error.InvalidPhysicalByte;
    }
    const trit_count = std.math.mul(usize, data.len, TRITS_PER_BYTE) catch
        return Error.TransportTooLarge;
    const trits = allocator.alloc(u8, trit_count) catch return Error.OutOfMemory;
    defer allocator.free(trits);
    for (data, 0..) |byte, byte_index| {
        var value = byte;
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

test "D24 natural uses the ordinary T5 bit-and-separator stream without a marker" {
    const d24_one = "000000000000000000000001";
    const words = [_]Word{.{ .width = 24, .bits = d24_one }};
    const expected = [_]u8{ 0, 0, 0, 0, 5 };

    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    try std.testing.expectEqualSlices(u8, &expected, encoded);

    var decoded = try decode(std.testing.allocator, encoded);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), decoded.words.len);
    try std.testing.expectEqual(@as(usize, 24), decoded.words[0].width);
    try std.testing.expectEqualStrings(d24_one, decoded.words[0].bits);
    try std.testing.expect(domain_ladder.supportsPhysicalWidth(decoded.words[0].width));
}

test "ordinary T5 D1 bytes remain identical" {
    const words = [_]Word{.{ .width = 1, .bits = "1" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    try std.testing.expectEqualSlices(u8, &.{0xa1}, encoded);
}

test "ordinary SENS difference and quotient words compose with D24 operands" {
    // D5 DIFFERENCE (01011): 0 - 1, then D5 QUOTIENT (10111): 1 / 3.
    // These remain normal operator words; D24 identity is the numeric domain.
    const words = [_]Word{
        .{ .width = 5, .bits = "01011" },
        .{ .width = 24, .bits = "000000000000000000000000" },
        .{ .width = 24, .bits = "000000000000000000000001" },
        .{ .width = 5, .bits = "10111" },
        .{ .width = 24, .bits = "000000000000000000000001" },
        .{ .width = 24, .bits = "000000000000000000000011" },
    };
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    var decoded = try decode(std.testing.allocator, encoded);
    defer decoded.deinit(std.testing.allocator);

    try std.testing.expectEqual(words.len, decoded.words.len);
    for (words, decoded.words) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqualStrings(expected.bits, actual.bits);
    }
}

test "signed numeric word stores sign first and preserves the full domain width" {
    var magnitude: [23]u8 = undefined;
    @memset(&magnitude, '0');
    magnitude[22] = '1';

    const positive = try makeSignedWord(std.testing.allocator, 24, false, &magnitude);
    defer std.testing.allocator.free(positive);
    const negative = try makeSignedWord(std.testing.allocator, 24, true, &magnitude);
    defer std.testing.allocator.free(negative);

    try std.testing.expectEqual(@as(usize, 24), positive.len);
    try std.testing.expectEqual(@as(u8, '1'), positive[0]);
    try std.testing.expectEqual(@as(u8, '0'), negative[0]);
    try std.testing.expectEqualSlices(u8, &magnitude, positive[1..]);
    try std.testing.expectEqualSlices(u8, &magnitude, negative[1..]);
}

test "signed numeric word rejects unsupported widths and malformed magnitudes" {
    const short_magnitude = "00000000000000000000000";
    try std.testing.expectError(Error.UnsupportedDomainWidth, makeSignedWord(std.testing.allocator, 9, false, short_magnitude));
    try std.testing.expectError(Error.InvalidMagnitudeWidth, makeSignedWord(std.testing.allocator, 24, false, "1"));
    try std.testing.expectError(Error.InvalidBinaryDigit, makeSignedWord(std.testing.allocator, 24, false, "0000000000000000000000x"));
}

test "encodeRatio carries exact 2.1564 as adjacent D24 signed values" {
    const encoded = try encodeRatio(std.testing.allocator, .{ .width = 24, .negative = false, .magnitude_bits = "00000000001010100001111" }, .{ .width = 24, .negative = false, .magnitude_bits = "00000000000100111000100" });
    defer std.testing.allocator.free(encoded);

    var decoded = try decode(std.testing.allocator, encoded);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 2), decoded.words.len);
    try std.testing.expectEqual(@as(usize, 24), decoded.words[0].width);
    try std.testing.expectEqualStrings("100000000001010100001111", decoded.words[0].bits);
    try std.testing.expectEqual(@as(usize, 24), decoded.words[1].width);
    try std.testing.expectEqualStrings("100000000000100111000100", decoded.words[1].bits);
}

test "encodeRatio rejects a zero denominator" {
    try std.testing.expectError(Error.ZeroDenominator, encodeRatio(std.testing.allocator, .{ .width = 24, .negative = false, .magnitude_bits = "00000000001010100001111" }, .{ .width = 24, .negative = false, .magnitude_bits = "00000000000000000000000" }));
}

test "D2 separates independent numbers while adjacent D24 words carry a ratio" {
    var magnitude_one: [23]u8 = undefined;
    @memset(&magnitude_one, '0');
    magnitude_one[22] = '1';
    var magnitude_three: [23]u8 = undefined;
    @memset(&magnitude_three, '0');
    magnitude_three[21] = '1';
    magnitude_three[22] = '1';

    const positive_one = try makeSignedWord(std.testing.allocator, 24, false, &magnitude_one);
    defer std.testing.allocator.free(positive_one);
    const negative_one = try makeSignedWord(std.testing.allocator, 24, true, &magnitude_one);
    defer std.testing.allocator.free(negative_one);
    const positive_three = try makeSignedWord(std.testing.allocator, 24, false, &magnitude_three);
    defer std.testing.allocator.free(positive_three);
    const denominator_three = try makeSignedWord(std.testing.allocator, 24, false, &magnitude_three);
    defer std.testing.allocator.free(denominator_three);

    const separate_numbers = [_]Word{
        .{ .width = 24, .bits = positive_one },
        .{ .width = 2, .bits = "00" }, // semantic D2 separator
        .{ .width = 24, .bits = positive_three },
    };
    const ratio = [_]Word{
        .{ .width = 24, .bits = positive_one },
        .{ .width = 24, .bits = denominator_three }, // positive sign + full-width D24 word
    };
    const negative_ratio = [_]Word{
        .{ .width = 24, .bits = negative_one },
        .{ .width = 24, .bits = denominator_three },
    };

    inline for (.{ &separate_numbers, &ratio, &negative_ratio }) |source| {
        const encoded = try encode(std.testing.allocator, source);
        defer std.testing.allocator.free(encoded);
        var decoded = try decode(std.testing.allocator, encoded);
        defer decoded.deinit(std.testing.allocator);
        try std.testing.expectEqual(source.len, decoded.words.len);
        for (source, decoded.words) |expected, actual| {
            try std.testing.expectEqual(expected.width, actual.width);
            try std.testing.expectEqualStrings(expected.bits, actual.bits);
        }
    }

    try std.testing.expectEqual(@as(usize, 24), ratio[1].width);
}

test "T5M admits exact D24 ladder widths and rejects neighboring widths" {
    const widths = [_]usize{ 24, 48, 96, 192, 384 };
    for (widths) |width| {
        const bits = try std.testing.allocator.alloc(u8, width);
        defer std.testing.allocator.free(bits);
        @memset(bits, '0');
        bits[width - 1] = '1';
        const words = [_]Word{.{ .width = width, .bits = bits }};
        const encoded = try encode(std.testing.allocator, &words);
        defer std.testing.allocator.free(encoded);
        var decoded = try decode(std.testing.allocator, encoded);
        defer decoded.deinit(std.testing.allocator);
        try std.testing.expectEqual(width, decoded.words[0].width);
        try std.testing.expectEqualSlices(u8, bits, decoded.words[0].bits);
    }
    const d25 = [_]Word{.{ .width = 25, .bits = "0000000000000000000000001" }};
    const d10 = [_]Word{.{ .width = 10, .bits = "0000000001" }};
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(std.testing.allocator, &d25));
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(std.testing.allocator, &d10));
}

test "decoder rejects non-T5 physical bytes and empty words" {
    try std.testing.expectError(Error.InvalidPhysicalByte, decode(std.testing.allocator, &.{243}));
    // Base-3 22000: a separator before any domain word.
    try std.testing.expectError(Error.EmptyDomainWord, decode(std.testing.allocator, &.{216}));
}
