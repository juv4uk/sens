//! Width-qualified physical domain ladder, independent of host ABI.
//! These are mechanical coordinates, NEVER execution or truth permissions.
//! Only the SENS language can admit a coordinate as a callable law.
const std = @import("std");

/// A binary word whose width is a *part of its Zig type*.
/// A DomainWord(1) argument cannot become DomainWord(8) implicitly.
pub fn DomainWord(comptime width: u8) type {
    if (width < 1 or width > 10)
        @compileError("physical ladder requires a declared 1..10-bit width");
    const Bits = @Int(.unsigned, width);
    return struct {
        bits: Bits,

        pub fn init(exact: Bits) @This() {
            return .{ .bits = exact };
        }

        /// Validate bits from a physical file at the ABI boundary.
        /// This is transport validation, not semantic domain admission.
        pub fn fromPhysical(raw: u16) ?@This() {
            if (raw > @as(u16, std.math.maxInt(Bits))) return null;
            return .{ .bits = @intCast(raw) };
        }

        pub fn physicalBits(self: @This()) u16 {
            return @as(u16, self.bits);
        }
    };
}

/// Compile-time same-width relation. There is intentionally no untyped
/// equality operation that could equate two different domain widths.
pub fn sameWord(comptime width: u8, a: DomainWord(width), b: DomainWord(width)) bool {
    return a.bits == b.bits;
}

/// An ABI edge receives a width byte and an exact payload. The only way
/// into the sterile ladder from such bytes is explicit tagged admission.
/// These tags are physical word-widths, NOT semantic IDs.
pub const LadderWord = union(enum) {
    w1: DomainWord(1),
    w2: DomainWord(2),
    w3: DomainWord(3),
    w4: DomainWord(4),
    w5: DomainWord(5),
    w6: DomainWord(6),
    w7: DomainWord(7),
    w8: DomainWord(8),
    w9: DomainWord(9),
    w10: DomainWord(10),

    pub fn fromCarrier(width: u8, bits: u16) ?@This() {
        return switch (width) {
            1 => if (DomainWord(1).fromPhysical(bits)) |w| .{ .w1 = w } else null,
            2 => if (DomainWord(2).fromPhysical(bits)) |w| .{ .w2 = w } else null,
            3 => if (DomainWord(3).fromPhysical(bits)) |w| .{ .w3 = w } else null,
            4 => if (DomainWord(4).fromPhysical(bits)) |w| .{ .w4 = w } else null,
            5 => if (DomainWord(5).fromPhysical(bits)) |w| .{ .w5 = w } else null,
            6 => if (DomainWord(6).fromPhysical(bits)) |w| .{ .w6 = w } else null,
            7 => if (DomainWord(7).fromPhysical(bits)) |w| .{ .w7 = w } else null,
            8 => if (DomainWord(8).fromPhysical(bits)) |w| .{ .w8 = w } else null,
            9 => if (DomainWord(9).fromPhysical(bits)) |w| .{ .w9 = w } else null,
            10 => if (DomainWord(10).fromPhysical(bits)) |w| .{ .w10 = w } else null,
            else => null,
        };
    }

    pub fn physicalWidth(self: @This()) u8 {
        return switch (self) {
            .w1 => 1, .w2 => 2, .w3 => 3, .w4 => 4, .w5 => 5,
            .w6 => 6, .w7 => 7, .w8 => 8, .w9 => 9, .w10 => 10,
        };
    }

    pub fn physicalBits(self: @This()) u16 {
        return switch (self) {
            inline else => |typed| typed.physicalBits(),
        };
    }
};

test "physical ladder distinguishes exact bit widths at comptime" {
    comptime {
        if (DomainWord(1) == DomainWord(8))
            @compileError("different widths may not be the same type");
    }
    const one = DomainWord(1).init(0b1);
    const eight = DomainWord(8).init(0b0000_0001);
    try std.testing.expect(sameWord(1, one, DomainWord(1).init(0b1)));
    try std.testing.expectEqual(@as(u16, 0b1), one.physicalBits());
    try std.testing.expectEqual(@as(u16, 0b0000_0001), eight.physicalBits());

    const d1 = LadderWord.fromCarrier(1, 0b1).?;
    const d8 = LadderWord.fromCarrier(8, 0b0000_0001).?;
    try std.testing.expect(d1.physicalWidth() != d8.physicalWidth());
    try std.testing.expectEqual(d1.physicalBits(), d8.physicalBits());
    try std.testing.expect(LadderWord.fromCarrier(1, 0b10) == null);
    try std.testing.expect(LadderWord.fromCarrier(8, 0b1_0000_0000) == null);
    try std.testing.expect(LadderWord.fromCarrier(0, 0) == null);
    try std.testing.expect(LadderWord.fromCarrier(11, 0) == null);
}

test "every admitted physical ladder width retains maximum bit payload" {
    inline for (1..11) |n| {
        const width: u8 = @intCast(n);
        const Bits = @Int(.unsigned, width);
        const max = @as(u16, std.math.maxInt(Bits));
        const typed = LadderWord.fromCarrier(width, max).?;
        try std.testing.expectEqual(width, typed.physicalWidth());
        try std.testing.expectEqual(max, typed.physicalBits());
        try std.testing.expect(LadderWord.fromCarrier(width, max + 1) == null);
    }
}
