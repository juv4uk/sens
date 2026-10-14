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
    const words = try t5.decode(allocator, physical);
    defer allocator.free(words);

    var bit_len: usize = 0;
    for (words) |word| {
        bit_len = try std.math.add(usize, bit_len, word.width);
    }

    const replay = try t5.encode(allocator, words);
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
