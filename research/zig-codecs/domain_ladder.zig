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

/// Mechanical MSB-first bit view over the owner-ratified width progression.
/// Borrowed bytes, not a new wire format or a source of SENS semantics.
/// D1..D10 are exact coordinates; D(24*2^n) is a physical width law.
/// E3's narrower WIDE_WIDTHS profile does NOT expand by this validation.
pub const OpaquePhysicalBitsError = error{
    UnsupportedWidth, WrongByteLength, NonCanonicalTail,
};

pub fn supportsPhysicalWidth(width: usize) bool {
    if (width >= 1 and width <= 10) return true;
    const first: usize = numeric_domains.WIDE_WIDTHS[0];
    if (width < first or width % first != 0) return false;
    const multiple = width / first;
    return (multiple & (multiple - 1)) == 0;
}

/// Declared width + meaningful bits are inseparable. Storage is caller-owned.
pub const OpaquePhysicalBits = struct {
    width: usize,
    bytes: []const u8,

    pub fn init(width: usize, raw: []const u8) OpaquePhysicalBitsError!OpaquePhysicalBits {
        if (!supportsPhysicalWidth(width)) return error.UnsupportedWidth;
        // Avoid width+7 overflow for very large law-qualified widths.
        const required = width / 8 + @as(usize, @intFromBool(width % 8 != 0));
        if (raw.len != required) return error.WrongByteLength;
        const rem = width % 8;
        if (rem != 0) {
            const unused: u3 = @intCast(8 - rem);
            const mask: u8 = (@as(u8, 1) << unused) - 1;
            if ((raw[raw.len - 1] & mask) != 0) return error.NonCanonicalTail;
        }
        return .{ .width = width, .bytes = raw };
    }

    pub fn same(self: OpaquePhysicalBits, other: OpaquePhysicalBits) bool {
        return self.width == other.width and std.mem.eql(u8, self.bytes, other.bytes);
    }
};

