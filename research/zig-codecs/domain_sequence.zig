//! Zig mixed SENS domain ladder: exact width + bits, zero semantic authority.
//! Physical E1 can transport D1..D9; D10 is never silently truncated.
//! Every buffer belongs to the caller. No heap, libc, interpreter or registry.
const std = @import("std");
const ladder = @import("domain_ladder.zig");
const e1 = @import("transport/e1.zig");
const writer = @import("transport/e1_writer.zig");
const fields = @import("transport/fields.zig");

pub const Error = writer.Error || ladder.CoordinateError ||
    error{UnsupportedCarrierWidth};

pub fn fromTyped(comptime width: u8, word: ladder.DomainWord(width)) ladder.Coordinate {
    return word.coordinate();
}

/// Pure physical overlap check, safe from pointer-end addition overflow.
fn overlaps(left: []const u8, right: []const u8) bool {
    if (left.len == 0 or right.len == 0) return false;
    const a = @intFromPtr(left.ptr);
    const b = @intFromPtr(right.ptr);
    return if (a <= b) b - a < left.len else a - b < right.len;
}

/// Validates the complete mixed-width source before publishing output bytes.
pub fn encode(
    source: []const ladder.Coordinate,
    output: []u8,
    words: []e1.Word,
    steps: []writer.Step,
) Error!usize {
    if (source.len > e1.MAX_WORDS) return error.TooLarge;
    for (source) |coordinate| {
        _ = try ladder.Coordinate.init(coordinate.width, coordinate.bits);
        if (coordinate.width > 9) return error.UnsupportedCarrierWidth;
    }
    if (words.len < source.len or steps.len <= source.len)
        return error.BufferTooSmall;
    // Validate ALL caller memory boundaries before staging the first word.
    // The lower-level writer checks too, but previously checked too late.
    const src_bytes = std.mem.sliceAsBytes(source);
    const word_bytes = std.mem.sliceAsBytes(words);
    const step_bytes = std.mem.sliceAsBytes(steps);
    if (overlaps(src_bytes, word_bytes) or
        overlaps(src_bytes, step_bytes) or
        overlaps(src_bytes, output) or
        overlaps(word_bytes, step_bytes) or
        overlaps(word_bytes, output) or
        overlaps(step_bytes, output))
        return error.OverlappingBuffers;
    for (source, 0..) |coordinate, i|
        words[i] = .{ .width = coordinate.width, .bits = coordinate.bits };
    return writer.encode(words[0..source.len], output, steps);
}

/// CRC + canonical E1 byte replay before returning ANY exact coordinate.
/// The restored width is explicit; it never decides SENS executable identity.
pub fn decode(
    input: []const u8,
    out: []ladder.Coordinate,
    words: []e1.Word,
    steps: []writer.Step,
    replay: []u8,
) Error!usize {
    const count = try e1.inspect(input);
    if (out.len < count or words.len < count or steps.len <= count)
        return error.BufferTooSmall;
    // Canonical replay writes intermediate buffers before publishing out.
    // Never let any host-provided slice alias another writable region.
    const out_bytes = std.mem.sliceAsBytes(out);
    const word_bytes = std.mem.sliceAsBytes(words);
    const step_bytes = std.mem.sliceAsBytes(steps);
    if (overlaps(input, out_bytes) or
        overlaps(input, word_bytes) or
        overlaps(input, step_bytes) or
        overlaps(input, replay) or
        overlaps(out_bytes, word_bytes) or
        overlaps(out_bytes, step_bytes) or
        overlaps(out_bytes, replay) or
        overlaps(word_bytes, step_bytes) or
        overlaps(word_bytes, replay) or
        overlaps(step_bytes, replay))
        return error.OverlappingBuffers;
    _ = try writer.inspectCanonical(input, words[0..count], steps, replay);
    for (words[0..count]) |word|
        _ = try ladder.Coordinate.init(word.width, word.bits);
    for (words[0..count], 0..) |word, i|
        out[i] = .{ .width = word.width, .bits = word.bits };
    return count;
}

