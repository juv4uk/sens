//! Typed SENS domain ladder to/from the E1 physical envelope.
//! E1 is not a grammar, a function table, or a source of executable authority.
//! Width belongs to the compile-time domain type, never to historical bytes.
//! Caller supplies all storage. No allocator, libc, OS or semantic runtime.
const std = @import("std");
const ladder = @import("domain_ladder.zig");
const e1 = @import("transport/e1.zig");
const writer = @import("transport/e1_writer.zig");
const fields = @import("transport/fields.zig");

pub const Error = writer.Error || ladder.CarrierError ||
    error{ UnsupportedDomainWidth, NotSingleWord };

/// Typed single-coordinate export. D10 is a valid ladder word, but this
/// particular E1 physical profile represents exact widths D1..D9 only.
/// Never truncate or use a numeric proxy to squeeze D10 into D9.
pub fn encodeOne(
    comptime width: u8,
    value: ladder.DomainWord(width),
    output: []u8,
) Error!usize {
    if (width > 9) return error.UnsupportedDomainWidth;
    const carrier = value.toCarrier();
    const physical_words = [_]e1.Word{.{
        .width = carrier.width,
        .bits = carrier.bits,
    }};
    var steps: [2]writer.Step = undefined;
    return writer.encode(&physical_words, output, &steps);
}

/// Explicit typed restoration, not D2/evaluator admission.
/// Accept only strict canonical E1 physical bytes and exactly one coordinate.
/// The resulting type is determined by the requested domain width.
pub fn decodeOne(
    comptime width: u8,
    frame: []const u8,
) Error!ladder.DomainWord(width) {
    if (width > 9) return error.UnsupportedDomainWidth;
    const count = try e1.inspect(frame);
    if (count != 1) return error.NotSingleWord;
    // A single canonical E1 word occupies <=13 bytes (including CRC).
    // Larger physical aliases cannot accidentally become trusted types.
    if (frame.len > 16) return error.NonCanonical;
    var decoded: [1]e1.Word = undefined;
    var steps: [2]writer.Step = undefined;
    var replay: [16]u8 = undefined;
    _ = try writer.inspectCanonical(frame, &decoded, &steps, &replay);
    return ladder.fromCarrier(width, .{
        .width = decoded[0].width,
        .bits = decoded[0].bits,
    });
}

