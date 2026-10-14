//! Mechanical width profile of the first four owner-ratified SENS numeric rungs.
//! Source: knowledge/number-width-ratified.json (ratified_prefix_bits).
//!
//! These are opaque *physical bit widths*, NOT a numeric-domain authority,
//! decimal conversion, arithmetic engine, executable admission or registry.
//! The full SENS law also admits D384, D768, ...; this Zig carrier currently
//! implements only the explicitly listed D24/D48/D96/D192 prefix.
//! Keep this non-authoritative physical profile in sync with the SENS source.

const std = @import("std");

/// The current Zig WideDomainWord carrier supports these four exact widths.
/// Do not infer callability or host arithmetic from membership in this list.
pub const WIDE_WIDTHS = [_]u16{ 24, 48, 96, 192 };

pub fn isWide(width: u16) bool {
    inline for (WIDE_WIDTHS) |known_width| {
        if (width == known_width) return true;
    }
    return false;
}

test "owner-ratified numeric prefix: four distinct exact widths, not host numbers" {
    try std.testing.expectEqual(@as(usize, 4), WIDE_WIDTHS.len);
    var previous: u16 = 0;
    inline for (WIDE_WIDTHS, 0..) |width, index| {
        try std.testing.expect(isWide(width));
        try std.testing.expectEqual(@as(u16, 24) << @as(u4, @intCast(index)), width);
        try std.testing.expect(width > previous);
        previous = width;
    }
    for ([_]u16{ 0, 1, 7, 8, 9, 10, 11, 23, 25, 47, 49, 95, 97, 191, 193, 384 }) |width| {
        // 384 is allowed by the SENS numeric FAMILY, but is not yet a Zig
        // WideDomainWord transport profile. This test cannot revoke its law.
        try std.testing.expect(!isWide(width));
    }
}
