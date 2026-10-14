//! Package-root Zig 0.16.0 tests: physical codecs and freestanding ABI share this module root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const ladder = @import("domain_ladder.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const freestanding = @import("freestanding.zig");
const envelope_fields = @import("transport/fields.zig");
const e1_physical = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");
const ladder = @import("ladder.zig");

test "import exact-width transport suites" {
    std.debug.assert(@sizeOf(t5.Word) > 0);
    std.debug.assert(f3c.FRAME_LABEL == 0xf3);
    std.debug.assert(freestanding.F3C_SCRATCH_BYTES == 8192);
    std.debug.assert(freestanding.F3C_SUFFIX_ROM_BYTES == 4000);
    _ = t5;
    _ = ladder;
    _ = f3c;
    _ = abi;
    _ = freestanding;
    _ = envelope_fields;
    _ = e1_physical;
    _ = e1_writer;
    _ = ladder;
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
