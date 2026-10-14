//! Exact-width SENS domain ladder in Zig. No historic identity registry.
//! This is a representation, not a SENS semantic evaluator or oracle.
//! D10 is a mechanical coordinate only; no callability is inferred.
const std = @import("std");
const numeric_domains = @import("numeric_domains.zig");
const t5 = @import("t5/t5.zig");


/// A single exact binary coordinate; width itself is identity, NOT the
/// allocation size of the Zig payload or a language operation number.
pub const CoordinateError = error{
    InvalidWidth, PayloadOverflow, InvalidBinaryDigit,
    WrongDomainWidth, BufferLengthMismatch,
};

pub const Coordinate = struct {
    width: u8,
    bits: u16,

    pub fn init(width: u8, bits: u16) CoordinateError!Coordinate {
        if (width == 0 or width > 10) return error.InvalidWidth;
        const limit: u16 = @as(u16, 1) << @as(u4, @intCast(width));
        if (bits >= limit) return error.PayloadOverflow;
        return .{ .width = width, .bits = bits };
    }

    pub fn parseBinary(source: []const u8) CoordinateError!Coordinate {
        if (source.len == 0 or source.len > 10) return error.InvalidWidth;
        var payload_bits: u16 = 0;
        for (source) |digit| {
            if (digit != '0' and digit != '1') return error.InvalidBinaryDigit;
            payload_bits = (payload_bits << 1) | @as(u16, digit - '0');
        }
        return init(@intCast(source.len), payload_bits);
    }

    /// Writes exactly width source bits; no decimal conversion, padding or
    /// invisible removal of leading zeros.
    pub fn writeBinary(self: Coordinate, output: []u8) CoordinateError!void {
        _ = try init(self.width, self.bits);
        if (output.len != self.width) return error.BufferLengthMismatch;
        for (output, 0..) |*digit, index| {
            const shift: u4 = @intCast(@as(usize, self.width) - 1 - index);
            digit.* = if (((self.bits >> shift) & 1) == 0) '0' else '1';
        }
    }

    /// Only an explicit helper ABI [width, payload-MSB, payload-LSB].
    /// Not a serialized .sens/.senc or executable semantic function.
    pub fn fromTriplet(raw: [3]u8) CoordinateError!Coordinate {
        const payload_bits = (@as(u16, raw[1]) << 8) | @as(u16, raw[2]);
        return init(raw[0], payload_bits);
    }

    pub fn triplet(self: Coordinate) [3]u8 {
        return .{ self.width, @intCast(self.bits >> 8), @intCast(self.bits & 0xff) };
    }

    pub fn same(self: Coordinate, other: Coordinate) bool {
        return self.width == other.width and self.bits == other.bits;
    }
};

/// Each width names a DISTINCT Zig type. The packed payload contains exactly
/// width bits; a physical byte's storage size never defines its domain.
pub fn DomainWord(comptime width: u8) type {
    if (width < 1 or width > 10)
        @compileError("SENS domain ladder supports exact widths D1..D10");
    return packed struct {
        const Self = @This();
        pub const domain_width: u8 = width;
        pub const Payload = @Int(.unsigned, width);

        bits: Payload,

        pub fn init(bits: Payload) Self {
            return .{ .bits = bits };
        }


        pub fn fromBinary(source: []const u8) CoordinateError!Self {
            return fromCoordinate(try Coordinate.parseBinary(source));
        }

        pub fn fromCoordinate(source: Coordinate) CoordinateError!Self {
            if (source.width != width) return error.WrongDomainWidth;
            _ = try Coordinate.init(source.width, source.bits);
            return .{ .bits = @intCast(source.bits) };
        }

        pub fn coordinate(self: Self) Coordinate {
            return .{ .width = width, .bits = @as(u16, self.bits) };
        }

        pub fn writeBinary(self: Self, output: []u8) CoordinateError!void {
            return self.coordinate().writeBinary(output);
        }

        /// Explicit erasure into a *physical* carrier word, never a semantic ID.
        pub fn toCarrier(self: Self) t5.Word {
            return .{ .width = width, .bits = @intCast(self.bits) };
        }
    };
}

pub const D1 = DomainWord(1);
pub const D2 = DomainWord(2);
pub const D3 = DomainWord(3);
pub const D4 = DomainWord(4);
pub const D5 = DomainWord(5);
pub const D6 = DomainWord(6);
pub const D7 = DomainWord(7);
pub const D8 = DomainWord(8);
pub const D9 = DomainWord(9);
pub const D10 = DomainWord(10);

pub const CarrierError = error{ WrongDomainWidth, BitsOutOfRange };

/// A physical word does not silently acquire a domain type. Its exact declared
/// width and all higher bits must be checked before explicit admission.
pub fn fromCarrier(comptime width: u8, carrier: t5.Word) CarrierError!DomainWord(width) {
    const Domain = DomainWord(width);
    if (carrier.width != width) return error.WrongDomainWidth;
    if (carrier.bits >= (@as(u16, 1) << @as(u4, @intCast(width))))
        return error.BitsOutOfRange;
    return Domain.init(@intCast(carrier.bits));
}


/// Explicit typed-to-physical single-word T5 adapter. A DomainWord is
/// required at compile time: arbitrary width/payload pairs cannot be passed
/// as if they were trusted typed coordinates. The result is physical only.
pub fn encodeTypedWord(
    comptime width: u8,
    allocator: std.mem.Allocator,
    word: DomainWord(width),
) ![]u8 {
    const physical = [_]t5.Word{word.toCarrier()};
    return if (width == 10)
        t5.encodeCoordinates(allocator, &physical)
    else
        t5.encode(allocator, &physical);
}

/// Restore exactly one typed coordinate; no executable-domain admission.
/// D10 uses the coordinate-only T5 path, never the <=D9 execution path.
pub fn decodeTypedWord(
    comptime width: u8,
    allocator: std.mem.Allocator,
    physical: []const u8,
) !DomainWord(width) {
    const words = if (width == 10)
        try t5.decodeCoordinates(allocator, physical)
    else
        try t5.decode(allocator, physical);
    defer allocator.free(words);
    if (words.len != 1) return error.NotSingleWord;
    return fromCarrier(width, words[0]);
}

test "all 2046 typed ladder coordinates roundtrip over canonical T5" {
    const allocator = std.testing.allocator;
    var seen: usize = 0;
    inline for (1..11) |w| {
        const width: u8 = @intCast(w);
        const D = DomainWord(width);
        const limit = @as(usize, 1) << w;
        for (0..limit) |n| {
            const typed = D.init(@intCast(n));
            const wire = try encodeTypedWord(width, allocator, typed);
            defer allocator.free(wire);
            const restored = try decodeTypedWord(width, allocator, wire);
            try std.testing.expectEqual(typed.bits, restored.bits);
            seen += 1;
        }
    }
    try std.testing.expectEqual(@as(usize, 2046), seen);
}

test "typed T5 admission fails closed on wrong rung or multiple words" {
    const allocator = std.testing.allocator;
    const d1 = try encodeTypedWord(1, allocator, D1.init(1));
    defer allocator.free(d1);
    try std.testing.expectError(error.WrongDomainWidth,
        decodeTypedWord(2, allocator, d1));

    const d9 = try encodeTypedWord(9, allocator, D9.init(0b010101000));
    defer allocator.free(d9);
    try std.testing.expectError(error.WrongDomainWidth,
        decodeTypedWord(8, allocator, d9));

    const d10 = try encodeTypedWord(10, allocator, D10.init(0b1000000000));
    defer allocator.free(d10);
    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        t5.decode(allocator, d10));

    const two = [_]t5.Word{ .{ .width = 1, .bits = 1 }, .{ .width = 1, .bits = 0 } };
    const wire = try t5.encode(allocator, &two);
    defer allocator.free(wire);
    try std.testing.expectError(error.NotSingleWord,
        decodeTypedWord(1, allocator, wire));
}

test "all 2046 D1..D10 coordinates retain exact width and payload" {
    inline for (1..11) |w| {
        const D = DomainWord(@intCast(w));
        try std.testing.expectEqual(@as(usize, w), @bitSizeOf(D));
        try std.testing.expectEqual(@as(u8, @intCast(w)), D.domain_width);
        const capacity = @as(usize, 1) << w;
        for (0..capacity) |n| {
            const value = D.init(@intCast(n));
            const physical = value.toCarrier();
            try std.testing.expectEqual(@as(u8, @intCast(w)), physical.width);
            try std.testing.expectEqual(@as(u16, @intCast(n)), physical.bits);
            const recovered = try fromCarrier(@intCast(w), physical);
            try std.testing.expectEqual(value.bits, recovered.bits);
        }
    }
}

test "equal payloads of different domains cannot collapse into one Zig type" {
    const one = DomainWord(1).init(1);
    const two = DomainWord(2).init(1);
    const eight = DomainWord(8).init(0b10101010);
    const nine = DomainWord(9).init(0b010101010);
    try std.testing.expect(@TypeOf(one) != @TypeOf(two));
    try std.testing.expect(@TypeOf(eight) != @TypeOf(nine));
    try std.testing.expectEqual(@as(u16, 1), one.toCarrier().bits);
    try std.testing.expectEqual(@as(u16, 1), two.toCarrier().bits);
    try std.testing.expectEqual(@as(u16, 0b10101010), nine.toCarrier().bits);
    try std.testing.expectError(error.WrongDomainWidth, fromCarrier(1, two.toCarrier()));
    try std.testing.expectError(error.WrongDomainWidth, fromCarrier(9, eight.toCarrier()));
    try std.testing.expectError(error.BitsOutOfRange, fromCarrier(2, .{ .width = 2, .bits = 4 }));
}

test "D10 remains a mechanical coordinate, not a callable D9" {
    const word = DomainWord(10).init(0b1000000000);
    const physical = [_]t5.Word{word.toCarrier()};
    const bytes = try t5.encodeCoordinates(std.testing.allocator, &physical);
    defer std.testing.allocator.free(bytes);
    const recovered = try t5.decodeCoordinates(std.testing.allocator, bytes);
    defer std.testing.allocator.free(recovered);
    try std.testing.expectEqualSlices(t5.Word, &physical, recovered);
    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        t5.decode(std.testing.allocator, bytes));
}


/// Numeric-domain bit carriers, separate from the executable D1..D10 T5 path.
/// Only the already declared D24/D48/D96/D192 widths are represented here.
/// This is NOT numeric arithmetic, host Number conversion, domain membership,
/// function admission, or a new SENS law. Only SENS decides those questions.
pub fn WideDomainWord(comptime width: u16) type {
    if (!numeric_domains.isWide(width))
        @compileError("Only declared wide SENS domain widths are available here");
    return packed struct {
        const Self = @This();
        pub const domain_width: u16 = width;
        pub const Payload = @Int(.unsigned, width);

        bits: Payload,

        pub fn init(bits: Payload) Self {
            return .{ .bits = bits };
        }

        /// Exact source bits, not a decimal string or an integer parser.
        /// There is no inference of arithmetic, resident status or callability.
        pub fn fromBinary(source: []const u8) CoordinateError!Self {
            if (source.len != @as(usize, width)) return error.WrongDomainWidth;
            var payload: Payload = 0;
            for (source) |digit| {
                if (digit != '0' and digit != '1') return error.InvalidBinaryDigit;
                payload = (payload << 1) | @as(Payload, digit - '0');
            }
            return init(payload);
        }

        /// Render exactly the declared rung width, including leading zeros.
        pub fn writeBinary(self: Self, out: []u8) CoordinateError!void {
            if (out.len != @as(usize, width)) return error.BufferLengthMismatch;
            var remaining = self.bits;
            var cursor = out.len;
            while (cursor != 0) {
                cursor -= 1;
                out[cursor] = if ((remaining & 1) == 0) '0' else '1';
                remaining >>= 1;
            }
        }

        pub const byte_len: usize = @divExact(width, 8);

        /// Explicit MSB-first *physical bytes*, not a numeric value or
        /// an executable D24+ word. No implicit type/width erasure.
        pub fn writeBytes(self: Self) [byte_len]u8 {
            var out: [byte_len]u8 = undefined;
            for (&out, 0..) |*byte, i| {
                const shift: std.math.Log2IntCeil(Payload) =
                    @intCast((byte_len - 1 - i) * 8);
                byte.* = @truncate(self.bits >> shift);
            }
            return out;
        }

        /// No padding, truncation, guessed width or semantic admission.
        pub fn fromBytes(raw: []const u8) error{WrongByteLength}!Self {
            if (raw.len != byte_len) return error.WrongByteLength;
            var bits: Payload = 0;
            for (raw) |byte| {
                bits = (bits << @as(std.math.Log2IntCeil(Payload), 8)) |
                    @as(Payload, byte);
            }
            return init(bits);
        }
    };
}

test "D24 D48 D96 D192 are distinct exact-bit opaque carriers" {
    inline for (numeric_domains.WIDE_WIDTHS) |width| {
        const D = WideDomainWord(width);
        try std.testing.expectEqual(@as(usize, width), @bitSizeOf(D));
        try std.testing.expectEqual(@as(usize, width), @bitSizeOf(D.Payload));
        try std.testing.expectEqual(width, D.domain_width);
        const one = D.init(1);
        try std.testing.expectEqual(@as(D.Payload, 1), one.bits);
        // The wide type cannot silently turn into a physical T5 opcode word.
        try std.testing.expect(!@hasDecl(D, "toCarrier"));
    }
    try std.testing.expect(WideDomainWord(numeric_domains.WIDE_WIDTHS[0]) != WideDomainWord(numeric_domains.WIDE_WIDTHS[1]));
    try std.testing.expect(WideDomainWord(numeric_domains.WIDE_WIDTHS[1]) != WideDomainWord(numeric_domains.WIDE_WIDTHS[2]));
    try std.testing.expect(WideDomainWord(numeric_domains.WIDE_WIDTHS[2]) != WideDomainWord(numeric_domains.WIDE_WIDTHS[3]));
    try std.testing.expect(WideDomainWord(numeric_domains.WIDE_WIDTHS[0]) != DomainWord(10));
}


test "wide ladder MSB bytes retain every bit without admitting mathematics" {
    inline for (numeric_domains.WIDE_WIDTHS) |width| {
        const D = WideDomainWord(width);
        const one = D.init(1);
        const raw = one.writeBytes();
        try std.testing.expectEqual(D.byte_len, raw.len);
        for (raw[0 .. raw.len - 1]) |byte|
            try std.testing.expectEqual(@as(u8, 0), byte);
        try std.testing.expectEqual(@as(u8, 1), raw[raw.len - 1]);
        try std.testing.expectEqual(one.bits, (try D.fromBytes(&raw)).bits);

        const max = D.init(~@as(D.Payload, 0));
        const full = max.writeBytes();
        for (full) |byte|
            try std.testing.expectEqual(@as(u8, 0xff), byte);
        try std.testing.expectEqual(max.bits, (try D.fromBytes(&full)).bits);

        var mutant = raw;
        mutant[0] ^= 0b10000000;
        // Every bit pattern is a valid opaque physical carrier. A flipped
        // bit must change identity, NOT manufacture a new SENS law.
        try std.testing.expect((try D.fromBytes(&mutant)).bits != one.bits);
        try std.testing.expectError(error.WrongByteLength,
            D.fromBytes(raw[0 .. raw.len - 1]));
        const extra = [_]u8{0} ** (D.byte_len + 1);
        try std.testing.expectError(error.WrongByteLength, D.fromBytes(&extra));
        try std.testing.expect(!@hasDecl(D, "toCarrier"));
    }

    const coordinate = WideDomainWord(numeric_domains.WIDE_WIDTHS[0]).init(0b00000000_00000001_10101000);
    const bytes = coordinate.writeBytes();
    try std.testing.expectEqualSlices(u8, &.{ 0x00, 0x01, 0xa8 }, &bytes);
    try std.testing.expectError(error.WrongByteLength,
        WideDomainWord(numeric_domains.WIDE_WIDTHS[1]).fromBytes(&bytes));
}

test "all wide rungs source bits roundtrip and every one-bit mutant remains width-qualified" {
    inline for (numeric_domains.WIDE_WIDTHS) |width| {
        const D = WideDomainWord(width);
        const zero = D.init(0);
        var raw: [width]u8 = undefined;
        try zero.writeBinary(&raw);
        for (raw) |char| try std.testing.expectEqual(@as(u8, '0'), char);
        try std.testing.expectEqual(zero.bits, (try D.fromBinary(&raw)).bits);

        // Exercise each possible bit position independently without T5 or
        // external truth tables: a bit's *position* belongs to its domain.
        for (0..width) |bit_index| {
            var changed = raw;
            changed[bit_index] = '1';
            const decoded = try D.fromBinary(&changed);
            try std.testing.expectEqual(@as(u32, 1), @popCount(decoded.bits));
            var projected: [width]u8 = undefined;
            try decoded.writeBinary(&projected);
            try std.testing.expectEqualSlices(u8, &changed, &projected);
            const physical = decoded.writeBytes();
            try std.testing.expectEqual(decoded.bits,
                (try D.fromBytes(&physical)).bits);
        }
        try std.testing.expectError(error.WrongDomainWidth,
            D.fromBinary(raw[0 .. width - 1]));
        var erroneous: [width]u8 = raw;
        erroneous[width - 1] = '2';
        try std.testing.expectError(error.InvalidBinaryDigit,
            D.fromBinary(&erroneous));
        var too_short: [width - 1]u8 = undefined;
        try std.testing.expectError(error.BufferLengthMismatch,
            D.init(1).writeBinary(&too_short));
        try std.testing.expect(!@hasDecl(D, "toCarrier"));
    }
}

test "2046 binary sources and 3-byte host triplets preserve every domain bit" {
    var seen: usize = 0;
    var width: u8 = 1;
    while (width <= 10) : (width += 1) {
        const limit: u16 = @as(u16, 1) << @as(u4, @intCast(width));
        var payload_bits: u16 = 0;
        while (payload_bits < limit) : (payload_bits += 1) {
            const original = try Coordinate.init(width, payload_bits);
            var data: [10]u8 = undefined;
            const bits = data[0..@as(usize, width)];
            try original.writeBinary(bits);
            try std.testing.expect(original.same(try Coordinate.parseBinary(bits)));
            try std.testing.expect(original.same(try Coordinate.fromTriplet(original.triplet())));
            seen += 1;
        }
        try std.testing.expectError(error.PayloadOverflow, Coordinate.init(width, limit));
    }
    try std.testing.expectEqual(@as(usize, 2046), seen);
}

test "D1 D2 D8 D9 D10 cannot silently change rung" {
    const d1 = try D1.fromBinary("1");
    const d2 = try D2.fromBinary("01");
    const d8 = try D8.fromBinary("00000001");
    const d9 = try D9.fromBinary("000000001");
    const d10 = try D10.fromBinary("0000000001");
    try std.testing.expect(@TypeOf(d1) != @TypeOf(d2));
    try std.testing.expect(@TypeOf(d8) != @TypeOf(d9));
    try std.testing.expect(@TypeOf(d9) != @TypeOf(d10));
    try std.testing.expect(!d1.coordinate().same(d2.coordinate()));
    try std.testing.expect(!d8.coordinate().same(d9.coordinate()));
    var exact: [10]u8 = undefined;
    try d10.writeBinary(&exact);
    try std.testing.expectEqualStrings("0000000001", &exact);
    try std.testing.expectError(error.WrongDomainWidth,
        D8.fromCoordinate(d9.coordinate()));
    try std.testing.expectError(error.WrongDomainWidth,
        D10.fromCoordinate(d1.coordinate()));
}

test "reject invalid binary characters, extra bit and invalid ABI triplets" {
    try std.testing.expectError(error.InvalidWidth, Coordinate.parseBinary(""));
    try std.testing.expectError(error.InvalidWidth, Coordinate.parseBinary("00000000000"));
    try std.testing.expectError(error.InvalidWidth, Coordinate.init(0, 0));
    try std.testing.expectError(error.InvalidWidth, Coordinate.init(11, 0));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.init(8, 256));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.init(10, 1024));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("0x1"));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("0 1"));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("02"));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.fromTriplet(.{ 1, 0, 2 }));
    try std.testing.expectError(error.InvalidWidth, Coordinate.fromTriplet(.{ 11, 0, 1 }));
    var short: [1]u8 = undefined;
    try std.testing.expectError(error.BufferLengthMismatch,
        (try D3.fromBinary("001")).writeBinary(&short));
}

test "single bit mutants preserve rung and are rejected as another coordinate" {
    var width: u8 = 1;
    while (width <= 10) : (width += 1) {
        const original = try Coordinate.init(width, 0);
        var bit: u8 = 0;
        while (bit < width) : (bit += 1) {
            const next = try Coordinate.init(width, @as(u16, 1) << @as(u4, @intCast(bit)));
            try std.testing.expect(!original.same(next));
            try std.testing.expectEqual(original.width, next.width);
            try std.testing.expectEqual(@as(u32, 1),
                @popCount(original.bits ^ next.bits));
        }
    }
}
