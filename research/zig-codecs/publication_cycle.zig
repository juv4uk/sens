//! Mechanical pre-publication receipt for a physical T5 carrier.
//! No SENS semantic admission or source provenance exists in this module.
//! Identical physical bytes from different eras cannot be distinguished.
const std = @import("std");
const t5 = @import("t5/t5.zig");

pub const SemanticStatus = enum { not_verified };

pub const PhysicalReceipt = struct {
    source_sha256: [32]u8,
    replay_sha256: [32]u8,
    physical_bytes: usize,
    exact_word_count: usize,
    meaningful_bits: usize,
    semantic_status: SemanticStatus = .not_verified,
};

/// Mechanical round-trip only: NOT permission to execute or publish.
/// Semantic/provenance admission must come from a SENS-owned verifier.
pub fn preflight(allocator: std.mem.Allocator, physical: []const u8) !PhysicalReceipt {
    return inspectPhysical(allocator, physical, false);
}

/// Read exact physical D1..D10 coordinates WITHOUT admitting a program.
/// D10 stays forbidden on the ordinary D1..D9 preflight path.
/// This is byte integrity only, not SENS residency or callability.
pub fn inspectCoordinateCarrier(
    allocator: std.mem.Allocator,
    physical: []const u8,
) !PhysicalReceipt {
    return inspectPhysical(allocator, physical, true);
}

fn inspectPhysical(
    allocator: std.mem.Allocator,
    physical: []const u8,
    comptime coordinate_only: bool,
) !PhysicalReceipt {
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

    var source_sha: [32]u8 = undefined;
    var replay_sha: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(physical, &source_sha, .{});
    std.crypto.hash.sha2.Sha256.hash(replay, &replay_sha, .{});
    if (!std.mem.eql(u8, &source_sha, &replay_sha))
        return error.PhysicalDigestMismatch;

    return .{
        .source_sha256 = source_sha,
        .replay_sha256 = replay_sha,
        .physical_bytes = physical.len,
        .exact_word_count = words.len,
        .meaningful_bits = bit_len,
    };
}

test "exact physical T5 bytes and digest round-trip" {
    const fixture = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const result = try preflight(std.testing.allocator, &fixture);
    try std.testing.expectEqual(@as(usize, 4), result.physical_bytes);
    try std.testing.expectEqual(@as(usize, 5), result.exact_word_count);
    try std.testing.expectEqual(@as(usize, 12), result.meaningful_bits);
    try std.testing.expectEqualSlices(u8, &result.source_sha256, &result.replay_sha256);
    try std.testing.expectEqual(SemanticStatus.not_verified, result.semantic_status);
}

test "physical D2 close is canonical transport but never executable permission" {
    const result = try preflight(std.testing.allocator, &.{0x35});
    try std.testing.expectEqual(@as(usize, 2), result.meaningful_bits);
    try std.testing.expectEqual(SemanticStatus.not_verified, result.semantic_status);
}

test "corrupted physical carrier is rejected" {
    try std.testing.expectError(t5.Error.InvalidPhysicalByte,
        preflight(std.testing.allocator, &.{0xf3}));
    try std.testing.expectError(t5.Error.EmptyProgram,
        preflight(std.testing.allocator, &.{}));
}

test "D1 and D2 equal payload cannot collapse into the same carrier" {
    const one = try preflight(std.testing.allocator, &.{0xa1});
    const two = try preflight(std.testing.allocator, &.{0x35});
    try std.testing.expectEqual(@as(usize, 1), one.meaningful_bits);
    try std.testing.expectEqual(@as(usize, 2), two.meaningful_bits);
    try std.testing.expect(!std.mem.eql(u8, &one.source_sha256, &two.source_sha256));
    try std.testing.expectEqual(SemanticStatus.not_verified, one.semantic_status);
    try std.testing.expectEqual(SemanticStatus.not_verified, two.semantic_status);
}

test "D10 coordinate receipt checks exact bits but never grants execution" {
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
    try std.testing.expectEqual(SemanticStatus.not_verified, ten.semantic_status);
    try std.testing.expectEqualSlices(u8, &ten.source_sha256, &ten.replay_sha256);
    try std.testing.expect(!std.mem.eql(u8, &ten.source_sha256, &nine.source_sha256));

    // The ordinary physical preflight must NOT widen to include D10.
    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        preflight(allocator, ten_bytes));

    const one_bit_mutant = [_]t5.Word{.{ .width = 10, .bits = 0b0010101011 }};
    const changed_bytes = try t5.encodeCoordinates(allocator, &one_bit_mutant);
    defer allocator.free(changed_bytes);
    const changed = try inspectCoordinateCarrier(allocator, changed_bytes);
    try std.testing.expect(!std.mem.eql(u8, &changed.source_sha256, &ten.source_sha256));
    try std.testing.expectEqual(SemanticStatus.not_verified, changed.semantic_status);

    try std.testing.expectError(t5.Error.UnsupportedDomainWidth,
        t5.encodeCoordinates(allocator, &.{.{ .width = 11, .bits = 0 }}));
    try std.testing.expectError(t5.Error.InvalidPhysicalByte,
        inspectCoordinateCarrier(allocator, &.{0xff}));
    try std.testing.expectError(t5.Error.EmptyProgram,
        inspectCoordinateCarrier(allocator, &.{}));
}
