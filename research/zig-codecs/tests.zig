//! Package-root Zig 0.16.0 tests: physical codecs and freestanding ABI share this module root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const publication_cycle = @import("publication_cycle.zig");
const ladder = @import("domain_ladder.zig");
const ladder_e1 = @import("domain_e1.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const freestanding = @import("freestanding.zig");
const envelope_fields = @import("transport/fields.zig");
const e1_physical = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");

test "import exact-width transport suites" {
    std.debug.assert(@sizeOf(t5.Word) > 0);
    std.debug.assert(f3c.FRAME_LABEL == 0xf3);
    std.debug.assert(freestanding.F3C_SCRATCH_BYTES == 8192);
    std.debug.assert(freestanding.F3C_SUFFIX_ROM_BYTES == 4000);
    _ = t5;
    _ = publication_cycle;
    _ = ladder;
    _ = ladder_e1;
    _ = f3c;
    _ = abi;
    _ = freestanding;
    _ = envelope_fields;
    _ = e1_physical;
    _ = e1_writer;
}


test "ladder D1 and D2 stay distinct through canonical T5 physical adapter" {
    const yes = (try ladder.D1.fromBinary("1")).coordinate().triplet();
    const structural = (try ladder.D2.fromBinary("01")).coordinate().triplet();
    var left: [8]u8 = undefined;
    var right: [8]u8 = undefined;
    const l = try t5.encodeTripletsInto(&left, &yes);
    const r = try t5.encodeTripletsInto(&right, &structural);
    try std.testing.expectEqual(@as(usize, 1), l);
    try std.testing.expectEqual(@as(usize, 1), r);
    try std.testing.expect(!std.mem.eql(u8, left[0..l], right[0..r]));
    try std.testing.expectEqual(@as(u8, 0xa1), left[0]);
    try std.testing.expectEqual(@as(u8, 0x35), right[0]);

    // D10 is a valid rung but not automatically a T5 executable word.
    const d10 = (try ladder.D10.fromBinary("0000000001")).coordinate().triplet();
    try std.testing.expectError(error.UnsupportedDomainWidth,
        t5.encodeTripletsInto(&left, &d10));
}

test "modern D8 and D9 share payload but not their T5 identity" {
    // Both have payload 10101000; the D9 source has its own leading zero.
    const eight = (try ladder.D8.fromBinary("10101000")).coordinate();
    const nine = (try ladder.D9.fromBinary("010101000")).coordinate();
    try std.testing.expectEqual(eight.bits, nine.bits);
    try std.testing.expect(!eight.same(nine));
    try std.testing.expectError(error.WrongDomainWidth,
        ladder.fromCarrier(8, .{ .width = nine.width, .bits = nine.bits }));
    try std.testing.expectError(error.WrongDomainWidth,
        ladder.fromCarrier(9, .{ .width = eight.width, .bits = eight.bits }));

    const e = eight.triplet();
    const n = nine.triplet();
    var e_out: [2]u8 = undefined;
    var n_out: [2]u8 = undefined;
    const elen = try t5.encodeTripletsInto(&e_out, &e);
    const nlen = try t5.encodeTripletsInto(&n_out, &n);
    try std.testing.expectEqual(@as(usize, 2), elen);
    try std.testing.expectEqual(@as(usize, 2), nlen);
    try std.testing.expectEqualSlices(u8, &.{ 0x5b, 0x08 }, &e_out);
    try std.testing.expectEqualSlices(u8, &.{ 0x1e, 0x53 }, &n_out);
}

// Current owner-ratified domain ladder only. Exhaust all D8 payloads and
// compare with independent D9 identities carrying the SAME payload bits.
// This is a transport/width law, not a historical mapping or a SENS evaluator.
test "D8 exhaustive current-ladder physical width stays distinct from D9" {
    for (0..256) |payload| {
        const d8 = ladder.D8.init(@intCast(payload));
        const d9 = ladder.D9.init(@intCast(payload));
        const eight = d8.coordinate();
        const nine = d9.coordinate();
        try std.testing.expectEqual(@as(u16, @intCast(payload)), eight.bits);
        try std.testing.expectEqual(eight.bits, nine.bits);
        try std.testing.expect(!eight.same(nine));
        try std.testing.expect(@TypeOf(d8) != @TypeOf(d9));
        try std.testing.expectError(error.WrongDomainWidth,
            ladder.fromCarrier(8, d9.toCarrier()));
        try std.testing.expectError(error.WrongDomainWidth,
            ladder.fromCarrier(9, d8.toCarrier()));

        const e = eight.triplet();
        const n = nine.triplet();
        var physical_eight: [2]u8 = undefined;
        var physical_nine: [2]u8 = undefined;
        const elen = try t5.encodeTripletsInto(&physical_eight, &e);
        const nlen = try t5.encodeTripletsInto(&physical_nine, &n);
        try std.testing.expectEqual(@as(usize, 2), elen);
        try std.testing.expectEqual(@as(usize, 2), nlen);
        try std.testing.expect(!std.mem.eql(u8, physical_eight[0..elen],
            physical_nine[0..nlen]));
    }
}

test "D1 zero and D3 three zero bits stay different T5 words" {
    // Neither this test nor Zig assigns either word a SENS semantic law.
    const one = (try ladder.D1.fromBinary("0")).coordinate().triplet();
    const three = (try ladder.D3.fromBinary("000")).coordinate().triplet();
    var left: [1]u8 = undefined;
    var right: [1]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 1),
        try t5.encodeTripletsInto(&left, &one));
    try std.testing.expectEqual(@as(usize, 1),
        try t5.encodeTripletsInto(&right, &three));
    try std.testing.expectEqual(@as(u8, 0x50), left[0]);
    try std.testing.expectEqual(@as(u8, 0x08), right[0]);
}
