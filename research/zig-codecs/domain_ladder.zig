//! Exact-width SENS domain ladder in Zig. No historic identity registry.
//! This is a representation, not a SENS semantic evaluator or oracle.
//! D10 is a mechanical coordinate only; no callability is inferred.
const std = @import("std");
const t5 = @import("t5/t5.zig");

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

        /// Explicit erasure into a *physical* carrier word, never a semantic ID.
        pub fn toCarrier(self: Self) t5.Word {
            return .{ .width = width, .bits = @intCast(self.bits) };
        }
    };
}

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
