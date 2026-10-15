//! Opaque exact-byte carrier for WSM Guard's three bootstrap sources.
//! Zig is *only* the sterile physical corridor; SENS alone executes semantics.
//! No semantic registry or execution decision; source bytes stay untouched.
const std = @import("std");

const core_asset = @embedFile("lib/core.lisp");
const unify_asset = @embedFile("lib/unify.lisp");
const guard_asset = @embedFile("lib/guard.lisp");

// capacity=0 asks for size; short/nonpositive rejects with no partial write.
// The host owns the output and gets exactly the unchanged source bytes.
fn copyExact(comptime asset: []const u8, dst: [*]u8, capacity: usize) isize {
    if (asset.len == 0) return -1;
    if (capacity == 0) return @intCast(asset.len);
    if (capacity < asset.len) return -2;
    @memcpy(dst[0..asset.len], asset[0..asset.len]);
    return @intCast(asset.len);
}

pub export fn sens_zig_guard_core_source_copy(dst: [*]u8, capacity: usize) isize {
    return copyExact(core_asset, dst, capacity);
}

pub export fn sens_zig_guard_unify_source_copy(dst: [*]u8, capacity: usize) isize {
    return copyExact(unify_asset, dst, capacity);
}

pub export fn sens_zig_guard_policy_source_copy(dst: [*]u8, capacity: usize) isize {
    return copyExact(guard_asset, dst, capacity);
}

fn verifyExact(comptime asset: []const u8, comptime copier: anytype) !void {
    const required = copier(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), copier(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var exact: [asset.len]u8 = undefined;
    try std.testing.expectEqual(required, copier(&exact, exact.len));
    try std.testing.expectEqualSlices(u8, asset[0..asset.len], &exact);
}

test "guard static sources traverse Zig as opaque bytes, reject short buffer" {
    try verifyExact(core_asset, sens_zig_guard_core_source_copy);
    try verifyExact(unify_asset, sens_zig_guard_unify_source_copy);
    try verifyExact(guard_asset, sens_zig_guard_policy_source_copy);
}
