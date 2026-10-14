//! Чиста механічна драбина SENS, D1–D10 (Zig 0.16).
//! Координата = точна бітова ширина + незмінені біти.
//! Відсутні мапи функцій, таблиці значень, callability та виконавець.
//! Лише ратифікований двійковий SENS визначає значення і допуск.
//! D10 є фізичною координатою, а не обіцянкою executable T5/E1.
const std = @import("std");

pub const MAX_RUNG: u8 = 10;
pub const Error = error{
    InvalidWidth,
    PayloadOverflow,
    WidthMismatch,
    InvalidBinaryDigit,
    BufferLengthMismatch,
};

/// Механічне відображення бітів; два рівні з однаковим payload не тотожні.
/// Не створюється із десяткового тексту і не має semantic dispatch.
pub const Coordinate = struct {
    width: u8,
    bits: u16,

    pub fn init(width: u8, bits: u16) Error!Coordinate {
        if (width == 0 or width > MAX_RUNG) return error.InvalidWidth;
        const limit: u16 = @as(u16, 1) << @as(u4, @intCast(width));
        if (bits >= limit) return error.PayloadOverflow;
        return .{ .width = width, .bits = bits };
    }

    /// Exact binary source: the count of 0/1 characters IS the rung.
    pub fn parseBinary(source: []const u8) Error!Coordinate {
        if (source.len == 0 or source.len > MAX_RUNG) return error.InvalidWidth;
        var payload: u16 = 0;
        for (source) |digit| {
            if (digit != '0' and digit != '1') return error.InvalidBinaryDigit;
            payload = (payload << 1) | @as(u16, digit - '0');
        }
        return init(@intCast(source.len), payload);
    }

    /// Writes exactly width ASCII binary digits, including every leading zero.
    /// Requires exact-length output: no partial source nor hidden byte padding.
    pub fn writeBinary(self: Coordinate, output: []u8) Error!void {
        _ = try init(self.width, self.bits);
        if (output.len != self.width) return error.BufferLengthMismatch;
        for (output, 0..) |*digit, i| {
            const shift: u4 = @intCast(@as(usize, self.width) - 1 - i);
            digit.* = if (((self.bits >> shift) & 1) == 0) '0' else '1';
        }
    }

    /// Explicit 3-byte host ABI [width, high payload, low payload].
    /// This is NOT physical .sens T5 or an executable source.
    pub fn fromTriplet(wire: [3]u8) Error!Coordinate {
        const payload = (@as(u16, wire[1]) << 8) | @as(u16, wire[2]);
        return init(wire[0], payload);
    }

    pub fn triplet(self: Coordinate) [3]u8 {
        return .{
            self.width,
            @intCast(self.bits >> 8),
            @intCast(self.bits & 0xff),
        };
    }

    pub fn same(self: Coordinate, other: Coordinate) bool {
        return self.width == other.width and self.bits == other.bits;
    }
};

/// Width as a comptime law: a D3 value CANNOT be passed as D4.
/// Values are opaque until a caller explicitly asks for a mechanical
/// Coordinate or host triplet. No function IDs or semantic meaning exist here.
pub fn DomainWord(comptime width: u8) type {
    if (width == 0 or width > MAX_RUNG)
        @compileError("D1-D10 are the admitted mechanical ladder widths");
    const Payload = std.meta.Int(.unsigned, width);
    return struct {
        const Self = @This();
        payload: Payload,

        pub fn fromBinary(source: []const u8) Error!Self {
            return fromCoordinate(try Coordinate.parseBinary(source));
        }

        pub fn fromCoordinate(coordinate: Coordinate) Error!Self {
            if (coordinate.width != width) return error.WidthMismatch;
            _ = try Coordinate.init(coordinate.width, coordinate.bits);
            return .{ .payload = @intCast(coordinate.bits) };
        }

        pub fn coordinate(self: Self) Coordinate {
            return .{ .width = width, .bits = @as(u16, self.payload) };
        }

        pub fn writeBinary(self: Self, output: []u8) Error!void {
            return self.coordinate().writeBinary(output);
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

test "2046 exact D1-D10 coordinates roundtrip source and host triplets" {
    var count: usize = 0;
    var width: u8 = 1;
    while (width <= MAX_RUNG) : (width += 1) {
        const limit: u16 = @as(u16, 1) << @as(u4, @intCast(width));
        var payload: u16 = 0;
        while (payload < limit) : (payload += 1) {
            const coordinate = try Coordinate.init(width, payload);
            var binary: [10]u8 = undefined;
            const source = binary[0..@as(usize, width)];
            try coordinate.writeBinary(source);
            const parsed = try Coordinate.parseBinary(source);
            try std.testing.expect(coordinate.same(parsed));
            const triplet = coordinate.triplet();
            try std.testing.expect(coordinate.same(try Coordinate.fromTriplet(triplet)));
            count += 1;
        }
        try std.testing.expectError(error.PayloadOverflow, Coordinate.init(width, limit));
    }
    try std.testing.expectEqual(@as(usize, 2046), count);
}

test "each rung is a distinct static type even when payload bits are equal" {
    const d1 = try D1.fromBinary("1");
    const d2 = try D2.fromBinary("01");
    const d3 = try D3.fromBinary("001");
    const d8 = try D8.fromBinary("00000001");
    const d9 = try D9.fromBinary("000000001");
    const d10 = try D10.fromBinary("0000000001");
    try std.testing.expect(@TypeOf(d1) != @TypeOf(d2));
    try std.testing.expect(@TypeOf(d3) != @TypeOf(d8));
    try std.testing.expect(@TypeOf(d8) != @TypeOf(d9));
    try std.testing.expect(@TypeOf(d9) != @TypeOf(d10));
    try std.testing.expect(!d1.coordinate().same(d2.coordinate()));
    try std.testing.expect(!d8.coordinate().same(d9.coordinate()));
    try std.testing.expect(!d9.coordinate().same(d10.coordinate()));
    var binary: [10]u8 = undefined;
    try d10.writeBinary(&binary);
    try std.testing.expectEqualStrings("0000000001", &binary);
    try std.testing.expectError(error.WidthMismatch, D8.fromCoordinate(d9.coordinate()));
    try std.testing.expectError(error.WidthMismatch, D10.fromCoordinate(d1.coordinate()));
}

test "fail closed on rung, source, overflow and noncanonical ABI input" {
    try std.testing.expectError(error.InvalidWidth, Coordinate.parseBinary(""));
    try std.testing.expectError(error.InvalidWidth, Coordinate.parseBinary("00000000000"));
    try std.testing.expectError(error.InvalidWidth, Coordinate.init(0, 0));
    try std.testing.expectError(error.InvalidWidth, Coordinate.init(11, 0));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.init(8, 256));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.init(10, 1024));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("01 1"));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("0x1"));
    try std.testing.expectError(error.InvalidBinaryDigit, Coordinate.parseBinary("02"));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.fromTriplet(.{ 1, 0, 2 }));
    try std.testing.expectError(error.PayloadOverflow, Coordinate.fromTriplet(.{ 9, 2, 0 }));
    try std.testing.expectError(error.InvalidWidth, Coordinate.fromTriplet(.{ 11, 0, 1 }));
    var short: [1]u8 = undefined;
    try std.testing.expectError(
        error.BufferLengthMismatch,
        (try D3.fromBinary("001")).writeBinary(&short),
    );
}

test "one changed payload bit never changes width or another rung" {
    var width: u8 = 1;
    while (width <= MAX_RUNG) : (width += 1) {
        const original = try Coordinate.init(width, 0);
        var slot: u8 = 0;
        while (slot < width) : (slot += 1) {
            const shift: u4 = @intCast(slot);
            const mutated = try Coordinate.init(width, @as(u16, 1) << shift);
            try std.testing.expect(!original.same(mutated));
            try std.testing.expectEqual(original.width, mutated.width);
            try std.testing.expectEqual(@as(u32, 1),
                @popCount(original.bits ^ mutated.bits));
            var visible: [10]u8 = undefined;
            try mutated.writeBinary(visible[0..@as(usize, width)]);
            try std.testing.expect(mutated.same(
                try Coordinate.parseBinary(visible[0..@as(usize, width)]),
            ));
        }
    }
}
