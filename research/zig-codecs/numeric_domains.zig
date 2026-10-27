//! Mechanical width profile of the four currently implemented D24+ SENS numeric carrier widths.
//! Source: contracts/numeric-domains-ratification.lisp (historical D24 carrier profile).
//!
//! These are opaque *physical bit widths*, NOT a numeric-domain authority,
//! decimal conversion, arithmetic engine, executable admission or registry.
//! The current mathematical law starts at D12; this Zig carrier still
//! implements only D24/D48/D96/D192. D12 physical admission remains unproved.
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

