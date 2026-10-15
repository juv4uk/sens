//! Exact-width physical T5 inspection; no publication or source identity.
//! SENS alone owns semantic admission; this module only checks byte identity.
//! D10 coordinates are physical-only; ordinary transport remains <= D9.
const std = @import("std");
const t5 = @import("t5/t5.zig");

pub const PhysicalInspection = struct {
    physical_bytes: usize,
    exact_word_count: usize,
    meaningful_bits: usize,
};

/// Mechanical round-trip only: NOT permission to execute or publish.
/// Semantic/provenance admission must come from a SENS-owned verifier.
pub fn inspectOrdinaryCarrier(allocator: std.mem.Allocator, physical: []const u8) !PhysicalInspection {
    return inspectPhysical(allocator, physical, false);
}

/// Read exact physical D1..D10 coordinates WITHOUT admitting a program.
/// D10 stays forbidden on the ordinary D1..D9 preflight path.
/// This is byte integrity only, not SENS residency or callability.
pub fn inspectCoordinateCarrier(
    allocator: std.mem.Allocator,
    physical: []const u8,
) !PhysicalInspection {
    return inspectPhysical(allocator, physical, true);
}

fn inspectPhysical(
    allocator: std.mem.Allocator,
    physical: []const u8,
    comptime coordinate_only: bool,
) !PhysicalInspection {
    const words = if (coordinate_only)
        try t5.decodeCoordinates(allocator, physical)
    else
        try t5.decode(allocator, physical);
    defer allocator.free(words);

    var bit_len: usize = 0;
    for (words) |word| {
        bit_len = try std.math.add(usize, bit_len, word.width);
    }

    const replay = if (coordinate_only)
        try t5.encodeCoordinates(allocator, words)
    else
        try t5.encode(allocator, words);
    defer allocator.free(replay);
    if (!std.mem.eql(u8, physical, replay)) return error.PhysicalMismatch;

    return .{
        .physical_bytes = physical.len,
        .exact_word_count = words.len,
        .meaningful_bits = bit_len,
    };
}

test "exact physical T5 bytes and digest round-trip" {
    const fixture = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const result = try inspectOrdinaryCarrier(std.testing.allocator, &fixture);
    try std.testing.expectEqual(@as(usize, 4), result.physical_bytes);
    try std.testing.expectEqual(@as(usize, 5), result.exact_word_count);
    try std.testing.expectEqual(@as(usize, 12), result.meaningful_bits);
}

test "physical D2 close is canonical transport but never executable permission" {
    const result = try inspectOrdinaryCarrier(std.testing.allocator, &.{0x35});
    try std.testing.expectEqual(@as(usize, 2), result.meaningful_bits);
}

test "corrupted physical carrier is rejected" {
    try std.testing.expectError(t5.Error.InvalidPhysicalByte,
        inspectOrdinaryCarrier(std.testing.allocator, &.{0xf3}));
    try std.testing.expectError(t5.Error.EmptyProgram,
        inspectOrdinaryCarrier(std.testing.allocator, &.{}));
}

test "D1 and D2 equal payload cannot collapse into the same carrier" {
    const one = try inspectOrdinaryCarrier(std.testing.allocator, &.{0xa1});
    const two = try inspectOrdinaryCarrier(std.testing.allocator, &.{0x35});
    try std.testing.expectEqual(@as(usize, 1), one.meaningful_bits);
    try std.testing.expectEqual(@as(usize, 2), two.meaningful_bits);
    try std.testing.expect(!std.mem.eql(u8, &.{0xa1}, &.{0x35}));
}

test "D10 coordinate inspection checks exact bits but never grants execution" {
    const allocator = std.testing.allocator;
    const d10 = [_]t5.Word{.{ .width = 10, .bits = 0b0010101010 }};
    const d9 = [_]t5.Word{.{ .width = 9, .bits = 0b010101010 }};
    const ten_bytes = try t5.encodeCoordinates(allocator, &d10);
    defer allocator.free(ten_bytes);
    const nine_bytes = try t5.encode(allocator, &d9);
    defer allocator.free(nine_bytes);

    const ten = try inspectCoordinateCarrier(allocator, ten_bytes);
    const nine = try inspectCoordinateCarrier(allocator, nine_bytes);
    try std.testing.expectEqual(@as(usize, 10), ten.meaningful_bits);
    try std.testing.expectEqual(@as(usize, 9), nine.meaningful_bits);
    try std.testing.expectEqual(@as(usize, 1), ten.exact_word_count);
    try std.testing.expect(!std.mem.eql(u8, ten_bytes, nine_bytes));

    // The ordinary physical inspection must NOT widen to include D10.
    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        inspectOrdinaryCarrier(allocator, ten_bytes));

    const one_bit_mutant = [_]t5.Word{.{ .width = 10, .bits = 0b0010101011 }};
    const changed_bytes = try t5.encodeCoordinates(allocator, &one_bit_mutant);
    defer allocator.free(changed_bytes);
    const changed = try inspectCoordinateCarrier(allocator, changed_bytes);
    try std.testing.expect(!std.mem.eql(u8, changed_bytes, ten_bytes));
    try std.testing.expectEqual(@as(usize, 10), changed.meaningful_bits);

    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        t5.encodeCoordinates(allocator, &.{.{ .width = 11, .bits = 0 }}));
    try std.testing.expectError(t5.Error.InvalidPhysicalByte,
        inspectCoordinateCarrier(allocator, &.{0xff}));
    try std.testing.expectError(t5.Error.EmptyProgram,
        inspectCoordinateCarrier(allocator, &.{}));
}
