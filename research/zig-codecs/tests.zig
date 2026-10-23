//! Package-root Zig 0.16.0 tests: physical codecs and freestanding ABI share this module root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const t5m = @import("t5m.zig");
const t5m3 = @import("t5m3.zig");
const physical_cycle = @import("physical_cycle.zig");
const ladder = @import("domain_ladder.zig");
const ladder_e1 = @import("domain_e1.zig");
const domain_sequence = @import("domain_sequence.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const freestanding = @import("freestanding.zig");
const envelope_fields = @import("transport/fields.zig");
const e1_physical = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");
const physical_parity_manifest = @import("parity_t5.zig");
const ladder_stdin_tool = @import("tools/ladder_tool.zig");
const transport_cli = @import("transport.zig");

test "import exact-width transport suites" {
    std.debug.assert(@sizeOf(t5.Word) > 0);
    std.debug.assert(f3c.FRAME_LABEL == 0xf3);
    std.debug.assert(freestanding.F3C_SCRATCH_BYTES == 8192);
    std.debug.assert(freestanding.F3C_SUFFIX_ROM_BYTES == 4000);
    _ = t5;
    _ = t5m;
    _ = t5m3;
    _ = physical_cycle;
    _ = ladder;
    _ = ladder_e1;
    _ = domain_sequence;
    _ = f3c;
    _ = abi;
    _ = freestanding;
    _ = envelope_fields;
    _ = e1_physical;
    _ = e1_writer;
    _ = physical_parity_manifest;
    _ = ladder_stdin_tool;
    _ = transport_cli;
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
    try std.testing.expectError(error.UnsupportedDomainWidth, t5.encodeTripletsInto(&left, &d10));
}

test "modern D8 and D9 share payload but not their T5 identity" {
    // Both have payload 10101000; the D9 source has its own leading zero.
    const eight = (try ladder.D8.fromBinary("10101000")).coordinate();
    const nine = (try ladder.D9.fromBinary("010101000")).coordinate();
    try std.testing.expectEqual(eight.bits, nine.bits);
    try std.testing.expect(!eight.same(nine));
    try std.testing.expectError(error.WrongDomainWidth, ladder.fromCarrier(8, .{ .width = nine.width, .bits = nine.bits }));
    try std.testing.expectError(error.WrongDomainWidth, ladder.fromCarrier(9, .{ .width = eight.width, .bits = eight.bits }));

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
        try std.testing.expectError(error.WrongDomainWidth, ladder.fromCarrier(8, d9.toCarrier()));
        try std.testing.expectError(error.WrongDomainWidth, ladder.fromCarrier(9, d8.toCarrier()));

        const e = eight.triplet();
        const n = nine.triplet();
        var physical_eight: [2]u8 = undefined;
        var physical_nine: [2]u8 = undefined;
        const elen = try t5.encodeTripletsInto(&physical_eight, &e);
        const nlen = try t5.encodeTripletsInto(&physical_nine, &n);
        try std.testing.expectEqual(@as(usize, 2), elen);
        try std.testing.expectEqual(@as(usize, 2), nlen);
        try std.testing.expect(!std.mem.eql(u8, physical_eight[0..elen], physical_nine[0..nlen]));
    }
}

test "D1 zero and D3 three zero bits stay different T5 words" {
    // Neither this test nor Zig assigns either word a SENS semantic law.
    const one = (try ladder.D1.fromBinary("0")).coordinate().triplet();
    const three = (try ladder.D3.fromBinary("000")).coordinate().triplet();
    var left: [1]u8 = undefined;
    var right: [1]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 1), try t5.encodeTripletsInto(&left, &one));
    try std.testing.expectEqual(@as(usize, 1), try t5.encodeTripletsInto(&right, &three));
    try std.testing.expectEqual(@as(u8, 0x50), left[0]);
    try std.testing.expectEqual(@as(u8, 0x08), right[0]);
}

test "typed ladder via public Zig ABI v2, D10 fail closed" {
    const a = std.testing.allocator;
    inline for (.{
        ladder.D8.init(0b10101000),
        ladder.D9.init(0b010101000),
    }, .{ @as(u8, 8), @as(u8, 9) }) |word, width| {
        const be3 = word.coordinate().triplet();
        var wire: [3]u8 = [_]u8{0xa5} ** 3;
        const n = abi.sens_zig_t5_encode_be3(&be3, be3.len, &wire, wire.len);
        try std.testing.expectEqual(@as(isize, 2), n);
        const typed_wire = try ladder.encodeTypedWord(width, a, word);
        defer a.free(typed_wire);
        try std.testing.expectEqualSlices(u8, typed_wire, wire[0..@intCast(n)]);
        const decoded = try ladder.decodeTypedWord(width, a, wire[0..@intCast(n)]);
        try std.testing.expectEqual(word.bits, decoded.bits);
        try std.testing.expectEqual(@as(c_int, 0), abi.sens_zig_t5_validate(&wire, @intCast(n)));
    }
    const d10 = ladder.D10.init(0b1000000000).coordinate().triplet();
    var failed: [3]u8 = [_]u8{0xa5} ** 3;
    try std.testing.expectEqual(@as(isize, -1), abi.sens_zig_t5_encode_be3(&d10, d10.len, &failed, failed.len));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5 }, &failed);

    const d8 = ladder.D8.init(0b10101000).coordinate().triplet();
    try std.testing.expectEqual(@as(isize, -2), abi.sens_zig_t5_encode_be3(&d8, d8.len, &failed, 1));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5 }, &failed);
}

test "Zig ABI v2 F3C returns physical statuses without publishing error bytes" {
    // Same Zig physical exports service Rust and the independent C host.
    // Errors and no-saving are NOT executable SENS D1 truth values.
    const quote_t5 = [_]u8{ 0x63, 0x89, 0x06, 0xa1 };
    const quote_f3c = [_]u8{ 0xf3, 0x40, 0x60 };
    const untouched = [_]u8{0x75} ** 32;
    var output: [32]u8 = untouched;

    try std.testing.expectEqual(@as(isize, -2), abi.sens_zig_f3c_pack(&quote_t5, quote_t5.len, &output, 2));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -1), abi.sens_zig_f3c_pack(&.{0xff}, 1, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -3), abi.sens_zig_f3c_pack(&.{0x64}, 1, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);

    try std.testing.expectEqual(@as(isize, quote_f3c.len), abi.sens_zig_f3c_pack(&quote_t5, quote_t5.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &quote_f3c, output[0..quote_f3c.len]);
    try std.testing.expectEqual(@as(u8, 0x75), output[quote_f3c.len]);

    output = untouched;
    try std.testing.expectEqual(@as(isize, -2), abi.sens_zig_f3c_unpack(&quote_f3c, quote_f3c.len, &output, 3));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, -1), abi.sens_zig_f3c_unpack(&.{ 0xf4, 0x40, 0x60 }, 3, &output, output.len));
    try std.testing.expectEqualSlices(u8, &untouched, &output);
    try std.testing.expectEqual(@as(isize, quote_t5.len), abi.sens_zig_f3c_unpack(&quote_f3c, quote_f3c.len, &output, output.len));
    try std.testing.expectEqualSlices(u8, &quote_t5, output[0..quote_t5.len]);
    try std.testing.expectEqual(@as(u8, 0x75), output[quote_t5.len]);

    // Both physical directions admit shared caller-owned input/output:
    // Zig stages the candidate separately and never outsources allocation.
    var shared: [32]u8 = untouched;
    @memcpy(shared[0..quote_t5.len], &quote_t5);
    try std.testing.expectEqual(@as(isize, quote_f3c.len), abi.sens_zig_f3c_pack(shared[0..].ptr, quote_t5.len, shared[0..].ptr, shared.len));
    try std.testing.expectEqualSlices(u8, &quote_f3c, shared[0..quote_f3c.len]);
    try std.testing.expectEqual(@as(isize, quote_t5.len), abi.sens_zig_f3c_unpack(shared[0..].ptr, quote_f3c.len, shared[0..].ptr, shared.len));
    try std.testing.expectEqualSlices(u8, &quote_t5, shared[0..quote_t5.len]);
}


test "Zig T5M BE3 rejects incomplete source without touching the output" {
    // Це виключно механізм ABI; жодного Lisp-значення тут не тлумачимо.
    const incomplete = [_]u8{ 3, 0 };
    var destination: [8]u8 = .{0xA5} ** 8;
    try std.testing.expectEqual(
        @as(isize, -1),
        abi.sens_zig_t5m_encode_be3(&incomplete, incomplete.len, &destination, destination.len),
    );
    for (destination) |byte| {
        try std.testing.expectEqual(@as(u8, 0xA5), byte);
    }
}
