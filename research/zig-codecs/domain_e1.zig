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
    const opaque = [_]e1.Word{.{
        .width = carrier.width,
        .bits = carrier.bits,
    }};
    var steps: [2]writer.Step = undefined;
    return writer.encode(&opaque, output, &steps);
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

test "every D1..D9 typed coordinate survives canonical E1 with exact identity" {
    var verified: usize = 0;
    inline for (1..10) |w| {
        const width: u8 = @intCast(w);
        const Domain = ladder.DomainWord(width);
        for (0..(@as(usize, 1) << w)) |n| {
            const source = Domain.init(@intCast(n));
            var buf: [16]u8 = undefined;
            const len = try encodeOne(width, source, &buf);
            const restored = try decodeOne(width, buf[0..len]);
            try std.testing.expectEqual(source.bits, restored.bits);
            try std.testing.expectEqual(@as(u8, width), restored.coordinate().width);
            verified += 1;
        }
    }
    try std.testing.expectEqual(@as(usize, 1022), verified);
}

test "same payload D8 D9 must not collapse across E1, D10 cannot truncate" {
    const current_eight = ladder.D8.init(0b10101000);
    const nine = ladder.D9.init(0b010101000);
    try std.testing.expectEqual(current_eight.coordinate().bits, nine.coordinate().bits);
    var frame_eight: [16]u8 = undefined;
    var frame_nine: [16]u8 = undefined;
    const e_len = try encodeOne(8, current_eight, &frame_eight);
    const n_len = try encodeOne(9, nine, &frame_nine);
    try std.testing.expect(!std.mem.eql(u8, frame_eight[0..e_len], frame_nine[0..n_len]));
    try std.testing.expectError(error.WrongDomainWidth,
        decodeOne(9, frame_eight[0..e_len]));
    try std.testing.expectError(error.WrongDomainWidth,
        decodeOne(8, frame_nine[0..n_len]));
    var buf: [16]u8 = undefined;
    try std.testing.expectError(error.UnsupportedDomainWidth,
        encodeOne(10, ladder.D10.init(0b0000000001), &buf));
    try std.testing.expectError(error.UnsupportedDomainWidth,
        decodeOne(10, frame_nine[0..n_len]));
}

test "E1 canonical aliases, CRC one-bit mutants and two-word envelopes reject" {
    var canonical: [16]u8 = undefined;
    const end = try encodeOne(1, ladder.D1.init(1), &canonical);
    // REPEAT for one word has the same physical length as RAW, but the
    // ratified canonical RAW tie wins. Valid CRC is not enough.
    const alias_head = [_]u8{ 'S', '3', 1, 1, 1, 1, 1, 0x80 };
    var alias: [12]u8 = undefined;
    @memcpy(alias[0..8], &alias_head);
    const crc = fields.crc32(&alias_head);
    alias[8] = @intCast(crc >> 24);
    alias[9] = @intCast((crc >> 16) & 255);
    alias[10] = @intCast((crc >> 8) & 255);
    alias[11] = @intCast(crc & 255);
    try std.testing.expectEqual(@as(usize, 1), try e1.inspect(&alias));
    try std.testing.expectError(error.NonCanonical, decodeOne(1, &alias));

    canonical[end - 1] ^= 1;
    try std.testing.expectError(error.IntegrityMismatch,
        decodeOne(1, canonical[0..end]));

    const two_words = [_]e1.Word{
        .{ .width = 1, .bits = 1 }, .{ .width = 1, .bits = 0 },
    };
    var two: [32]u8 = undefined;
    var steps: [3]writer.Step = undefined;
    const two_len = try writer.encode(&two_words, &two, &steps);
    try std.testing.expectError(error.NotSingleWord,
        decodeOne(1, two[0..two_len]));
}
