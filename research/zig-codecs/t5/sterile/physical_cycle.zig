//! Physical integrity witness only: no SENS semantics can originate here.
//! Publication additionally requires provenance and an independent SENS verdict.
const std = @import("std");
const t5 = @import("../t5.zig");

pub const SemanticStatus = enum { not_verified };

pub const PhysicalReceipt = struct {
    source_sha256: [32]u8,
    replay_sha256: [32]u8,
    bytes: usize,
    semantic_status: SemanticStatus = .not_verified,
};

/// Mechanical cycle: decode -> digest -> encode -> exact physical equality.
/// A matching SHA cannot distinguish two different eras with identical bytes.
pub fn verifyPhysicalCycle(allocator: std.mem.Allocator, physical: []const u8) !PhysicalReceipt {
    const exact_words = try t5.decode(allocator, physical);
    defer allocator.free(exact_words);

    var before: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(physical, &before, .{});

    const replay = try t5.encode(allocator, exact_words);
    defer allocator.free(replay);
    if (!std.mem.eql(u8, physical, replay)) return error.PhysicalMismatch;

    var after: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(replay, &after, .{});
    if (!std.mem.eql(u8, &before, &after)) return error.DigestMismatch;

    return .{
        .source_sha256 = before,
        .replay_sha256 = after,
        .bytes = physical.len,
        .semantic_status = .not_verified,
    };
}

test "canonical physical cycle: exact bytes and SHA256" {
    const a = std.testing.allocator;
    const known = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const receipt = try verifyPhysicalCycle(a, &known);
    try std.testing.expectEqual(@as(usize, known.len), receipt.bytes);
    try std.testing.expectEqualSlices(u8, &receipt.source_sha256, &receipt.replay_sha256);
    try std.testing.expectEqual(SemanticStatus.not_verified, receipt.semantic_status);
}

test "physical validity is NOT executable semantics or era provenance" {
    const a = std.testing.allocator;
    // A physically valid solitary D2 CLOSE has no executable SENS verdict.
    const receipt = try verifyPhysicalCycle(a, &.{0x35});
    try std.testing.expectEqual(SemanticStatus.not_verified, receipt.semantic_status);
    // An invalid physical byte is rejected even before a SENS reader.
    try std.testing.expectError(t5.Error.InvalidPhysicalByte,
        verifyPhysicalCycle(a, &.{0xf3}));
}
