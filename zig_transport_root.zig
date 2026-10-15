//! Root-scoped Zig 0.16 module for the sterile, host-neutral transport ABI.
//! The root module alone can @embedFile checked-in assets in lib/; Zig copies
//! exact bytes, never decides Lisp meaning or executable SENS identities.
const std = @import("std");
const abi = @import("research/zig-codecs/transport_abi.zig");

// Keep all existing public C exports reachable without re-implementing them.
comptime {
    _ = abi.sens_zig_codec_abi_version;
    _ = abi.sens_zig_t5_validate;
    _ = abi.sens_zig_t5_validate_coordinates;
    _ = abi.sens_zig_t5_encode_be3;
    _ = abi.sens_zig_t5_decode_be3;
    _ = abi.sens_zig_e1_encode_be3;
    _ = abi.sens_zig_e1_decode_be3;
    _ = abi.sens_zig_f3c_pack;
    _ = abi.sens_zig_f3c_unpack;
}

// A single opaque asset, not a symbol registry. The caller owns memory;
// capacity=0 queries exact byte length. -2 is fail-closed, no partial write.
const linter_asset = @embedFile("lib/linter.lisp");
pub export fn sens_zig_linter_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (linter_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(linter_asset.len);
    if (capacity < linter_asset.len) return -2;
    @memcpy(dst[0..linter_asset.len], linter_asset[0..linter_asset.len]);
    return @intCast(linter_asset.len);
}

test "opaque linter bytes cross Zig without partial writes or semantic registry" {
    const required = sens_zig_linter_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(linter_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_linter_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [linter_asset.len]u8 = undefined;
    try std.testing.expectEqual(required,
        sens_zig_linter_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, linter_asset[0..linter_asset.len], &output);
}
