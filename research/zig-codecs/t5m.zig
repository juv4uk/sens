//! T5M physical transport: 15 logical trits (0/1 bits, 2 word separators)
//! are ranked in base 3 and stored as one little-endian 24-bit group.
//! This layer preserves exact word widths and bits; it assigns no semantics.
const std = @import("std");
const domain_ladder = @import("domain_ladder.zig");

pub const MAX_PHYSICAL_BYTES: usize = 4 * 1024 * 1024;
const TRITS_PER_GROUP: usize = 15;
const BYTES_PER_GROUP: usize = 3;
const MAX_GROUP_VALUE: u32 = 14_348_907; // 3^15

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

fn appendDigit(out: []u8, group_index: *usize, current: *u32, used: *u8, digit: u8) void {
    std.debug.assert(digit <= 2);
    current.* = current.* * 3 + @as(u32, digit);
    used.* += 1;
    if (used.* == TRITS_PER_GROUP) {
        const offset = group_index.* * BYTES_PER_GROUP;
        out[offset] = @truncate(current.*);
        out[offset + 1] = @truncate(current.* >> 8);
        out[offset + 2] = @truncate(current.* >> 16);
        group_index.* += 1;
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
    const trit_budget = (MAX_PHYSICAL_BYTES / BYTES_PER_GROUP) * TRITS_PER_GROUP;
    if (trit_count > trit_budget) return Error.TransportTooLarge;
    const padded_trits = std.math.add(usize, trit_count, TRITS_PER_GROUP - 1) catch
        return Error.TransportTooLarge;
    const group_count = padded_trits / TRITS_PER_GROUP;
    const byte_len = std.math.mul(usize, group_count, BYTES_PER_GROUP) catch
        return Error.TransportTooLarge;
    const out = allocator.alloc(u8, byte_len) catch return Error.OutOfMemory;
    errdefer allocator.free(out);

    var group_index: usize = 0;
    var current: u32 = 0;
    var used: u8 = 0;
    for (words, 0..) |word, word_index| {
        if (word_index != 0) appendDigit(out, &group_index, &current, &used, 2);
        for (word.bits) |bit| appendDigit(out, &group_index, &current, &used, bit - '0');
    }
    while (used != 0) appendDigit(out, &group_index, &current, &used, 2);
    std.debug.assert(group_index == group_count);
    return out;
}

fn validateWordWidth(width: usize) Error!void {
    if (!supportsWidth(width)) return Error.UnsupportedDomainWidth;
}

/// Decode the mechanical T5M stream, retaining exact leading zeros and widths.
pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error!Decoded {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len > MAX_PHYSICAL_BYTES) return Error.TransportTooLarge;
    if (data.len % BYTES_PER_GROUP != 0) return Error.InvalidPhysicalByte;
    const group_count = data.len / BYTES_PER_GROUP;
    const trit_count = std.math.mul(usize, group_count, TRITS_PER_GROUP) catch
        return Error.TransportTooLarge;
    const trits = allocator.alloc(u8, trit_count) catch return Error.OutOfMemory;
    defer allocator.free(trits);
    for (0..group_count) |group_index| {
        const offset = group_index * BYTES_PER_GROUP;
        var value: u32 = @as(u32, data[offset]) |
            (@as(u32, data[offset + 1]) << 8) |
            (@as(u32, data[offset + 2]) << 16);
        if (value >= MAX_GROUP_VALUE) return Error.InvalidPhysicalGroup;
        var place: usize = TRITS_PER_GROUP;
        while (place > 0) {
            place -= 1;
            trits[group_index * TRITS_PER_GROUP + place] = @intCast(value % 3);
            value /= 3;
        }
    }

    var padding: usize = 0;
    while (padding < trits.len and trits[trits.len - padding - 1] == 2) : (padding += 1) {}
    if (padding >= TRITS_PER_GROUP) return Error.InvalidTail;
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

test "D24 exact word uses two T5M groups without a numeric marker" {
    const d24_one = "000000000000000000000001";
    const words = [_]Word{.{ .width = 24, .bits = d24_one }};
    const expected = [_]u8{ 0, 0, 0, 0xb1, 0x05, 0 };

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

test "T5M D1 bytes use one 15-trit group" {
    const words = [_]Word{.{ .width = 1, .bits = "1" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);
    try std.testing.expectEqualSlices(u8, &.{ 241, 246, 145 }, encoded);
}

test "T5M packs one exact word as a 15-trit little-endian group" {
    const words = [_]Word{.{ .width = 1, .bits = "1" }};
    const encoded = try encode(std.testing.allocator, &words);
    defer std.testing.allocator.free(encoded);

    // 1 followed by fourteen padding trits 2, ranked in base 3 then stored LE.
    try std.testing.expectEqualSlices(u8, &.{ 241, 246, 145 }, encoded);
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

test "T5M preserves opaque exact widths without interpreting numeric construction" {
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

test "decoder rejects invalid T5M groups, malformed lengths, and empty words" {
    try std.testing.expectError(Error.InvalidPhysicalByte, decode(std.testing.allocator, &.{243}));
    try std.testing.expectError(Error.InvalidPhysicalGroup, decode(std.testing.allocator, &.{ 255, 255, 255 }));
    // Base-3 2 followed by fourteen zero trits: a separator before any word.
    try std.testing.expectError(Error.EmptyDomainWord, decode(std.testing.allocator, &.{ 242, 246, 145 }));
    // Fifteen trailing trits 2 are not canonical padding for a nonempty word.
    try std.testing.expectError(Error.InvalidTail, decode(std.testing.allocator, &.{ 106, 242, 218 }));
}
