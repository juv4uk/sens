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

