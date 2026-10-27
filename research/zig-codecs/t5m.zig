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

test "opaque 24-bit word uses five T5M bytes without domain interpretation" {
    const exact_bits = "000000000000000000000001";
    const words = [_]Word{.{ .width = 24, .bits = exact_bits }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    try std.testing.expectEqual(@as(usize, 5), encoded.len);

    var decoded = try decode(std.testing.allocator, encoded);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), decoded.words.len);
    try std.testing.expectEqual(@as(usize, 24), decoded.words[0].width);
    try std.testing.expectEqualStrings(exact_bits, decoded.words[0].bits);
}

test "T5M D1 word occupies one byte (five trits)" {
    const words = [_]Word{.{ .width = 1, .bits = "1" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    try std.testing.expectEqualSlices(u8, &.{0xa1}, encoded);
}

test "T5M packs each five-trit group into one byte" {
    const words = [_]Word{.{ .width = 1, .bits = "1" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);

    // 1 followed by four padding trits 2: 1*3^4 + 2*3^3 + 2*3^2 + 2*3 + 2 = 161.
    try std.testing.expectEqualSlices(u8, &.{0xa1}, encoded);
}

test "T5M preserves an exact D11 word without admitting its semantics" {
    const words = [_]Word{.{ .width = 11, .bits = "00000000001" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);

    var decoded = try decode(std.testing.allocator, encoded);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), decoded.words.len);
    try std.testing.expectEqual(@as(usize, 11), decoded.words[0].width);
    try std.testing.expectEqualStrings("00000000001", decoded.words[0].bits);
}

test "T5M preserves exact D12 boundary words and does not merge equal-value domains" {
    const words = [_]Word{
        .{ .width = 12, .bits = "100000000000" }, // D12 minimum: -2048
        .{ .width = 12, .bits = "011111111111" }, // D12 maximum: 2047
        .{ .width = 12, .bits = "000000000010" }, // D12 value 2
        .{ .width = 24, .bits = "000000000000000000000010" }, // D24 value 2
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
    try std.testing.expect(decoded.words[2].width != decoded.words[3].width);
    try std.testing.expectEqualStrings("000000000010", decoded.words[2].bits);
    try std.testing.expectEqualStrings("000000000000000000000010", decoded.words[3].bits);
}

test "T5M transports a caller-formed negative D24 two's-complement word unchanged" {
    // -5 is already represented as an exact-width D24 two's-complement word.
    // T5M must preserve those 24 bits, not reinterpret them as sign-magnitude.
    const negative_five = "111111111111111111111011";
    const source = [_]Word{.{ .width = 24, .bits = negative_five }};
    const physical = try encode(std.testing.allocator, &source);
    defer std.testing.allocator.free(physical);

    var decoded = try decode(std.testing.allocator, physical);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 24), decoded.words[0].width);
    try std.testing.expectEqualStrings(negative_five, decoded.words[0].bits);
}

test "T5M transports adjacent D24 words without interpreting ratio semantics" {
    const source = [_]Word{
        .{ .width = 24, .bits = "000000000000000001010100" }, // caller-formed numerator
        .{ .width = 24, .bits = "000000000000000000100111" }, // caller-formed denominator
    };
    const physical = try encode(std.testing.allocator, &source);
    defer std.testing.allocator.free(physical);

    var decoded = try decode(std.testing.allocator, physical);
    defer decoded.deinit(std.testing.allocator);
    try std.testing.expectEqual(source.len, decoded.words.len);
    for (source, decoded.words) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqualStrings(expected.bits, actual.bits);
    }
}

test "T5M preserves signed D12 boundary words without interpreting their meaning" {
    const words = [_]Word{
        .{ .width = 12, .bits = "100000000000" }, // caller-formed -2048
        .{ .width = 12, .bits = "111111111111" }, // caller-formed -1
        .{ .width = 12, .bits = "011111111111" }, // caller-formed 2047
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

test "T5M preserves opaque exact widths without interpreting numeric construction" {
    const widths = [_]usize{ 12, 24, 48, 96, 192, 384 };
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
    const opaque_25 = [_]Word{.{ .width = 25, .bits = "0000000000000000000000001" }};
    const encoded_25 = try encode(std.testing.allocator, &opaque_25);
    defer std.testing.allocator.free(encoded_25);
    var decoded_25 = try decode(std.testing.allocator, encoded_25);
    defer decoded_25.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 25), decoded_25.words[0].width);
    try std.testing.expectEqualStrings(opaque_25[0].bits, decoded_25.words[0].bits);
}

test "T5M transports D1 through D10 exact widths including D10 leading zeros" {
    const source = [_]Word{
        .{ .width = 1, .bits = "1" },
        .{ .width = 2, .bits = "00" },
        .{ .width = 3, .bits = "010" },
        .{ .width = 4, .bits = "0001" },
        .{ .width = 5, .bits = "00100" },
        .{ .width = 6, .bits = "000001" },
        .{ .width = 7, .bits = "0000000" },
        .{ .width = 8, .bits = "00000101" },
        .{ .width = 9, .bits = "001011001" },
        .{ .width = 10, .bits = "0000000001" },
    };
    const physical = try encode(std.testing.allocator, &source);
    defer std.testing.allocator.free(physical);
    var decoded = try decode(std.testing.allocator, physical);
    defer decoded.deinit(std.testing.allocator);

    try std.testing.expectEqual(source.len, decoded.words.len);
    for (source, decoded.words) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqualStrings(expected.bits, actual.bits);
    }
    // Transport preserves a 10-bit coordinate but does not admit an executable D10 resident.
}

test "decoder rejects invalid T5M bytes, tails, and empty words" {
    try std.testing.expectError(Error.InvalidPhysicalByte, decode(std.testing.allocator, &.{243}));
    // Base-3 20000: a separator before any word.
    try std.testing.expectError(Error.EmptyDomainWord, decode(std.testing.allocator, &.{162}));
    // Five trailing separator trits are not canonical padding for a nonempty word.
    try std.testing.expectError(Error.InvalidTail, decode(std.testing.allocator, &.{242}));
}

// The physical codec rejects malformed carriers; this is not a semantic oracle.
test "T5M encoder rejects nonbinary payload and incorrect declared width" {
    const bad_digit = [_]Word{.{ .width = 3, .bits = "10x" }};
    try std.testing.expectError(Error.InvalidBinaryDigit, encode(std.testing.allocator, &bad_digit));

    const wrong_width = [_]Word{.{ .width = 3, .bits = "10" }};
    try std.testing.expectError(Error.UnsupportedDomainWidth, encode(std.testing.allocator, &wrong_width));
}

test "T5M word separator crosses a five-trit boundary exactly" {
    // Тільки фізична механіка: жодного виконавця або значення SENS.
    // 0 | 01 | 001 -> трити 02012 00122 -> байти 59, 17.
    const source = [_]Word{
        .{ .width = 1, .bits = "0" },
        .{ .width = 2, .bits = "01" },
        .{ .width = 3, .bits = "001" },
    };
    const physical = try encode(std.testing.allocator, &source);
    defer std.testing.allocator.free(physical);
    try std.testing.expectEqualSlices(u8, &.{ 59, 17 }, physical);

    var restored = try decode(std.testing.allocator, physical);
    defer restored.deinit(std.testing.allocator);
    try std.testing.expectEqual(source.len, restored.words.len);
    for (source, restored.words) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqualStrings(expected.bits, actual.bits);
    }

    // 02212 містить два сусідні роздільники, тобто порожнє слово.
    try std.testing.expectError(Error.EmptyDomainWord, decode(std.testing.allocator, &.{77}));
}

// Механічний стресовий корпус змішаних ширин: жодної семантики SENS.
test "T5M mixed-width repeated physical roundtrip" {
    const sample = [_]Word{
        .{ .width = 1, .bits = "1" },
        .{ .width = 7, .bits = "0000001" },
        .{ .width = 10, .bits = "0000000001" },
        .{ .width = 11, .bits = "00000000001" },
        .{ .width = 24, .bits = "000000000000000000000001" },
        .{ .width = 48, .bits = "000000000000000000000000000000000000000000000001" },
    };
    const allocator = std.testing.allocator;
    for ([_]usize{ 1, 16, 128 }) |count| {
        const words = try allocator.alloc(Word, count * sample.len);
        defer allocator.free(words);
        for (0..count) |i| {
            @memcpy(words[i * sample.len ..][0..sample.len], &sample);
        }
        const bytes = try encode(allocator, words);
        defer allocator.free(bytes);
        const trits = count * (1 + 7 + 10 + 11 + 24 + 48) + words.len - 1;
        try std.testing.expectEqual((trits + 4) / 5, bytes.len);
        var decoded = try decode(allocator, bytes);
        defer decoded.deinit(allocator);
        try std.testing.expectEqual(words.len, decoded.words.len);
        for (words, decoded.words) |before, after| {
            try std.testing.expectEqual(before.width, after.width);
            try std.testing.expectEqualSlices(u8, before.bits, after.bits);
        }
    }
}
