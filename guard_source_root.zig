//! WSM Guard's static bootstrap crosses Zig/T5M as exact domain-word records.
//! Zig restores transport only; Rust/SENS owns domain identity and execution.
const std = @import("std");
const t5m = @import("research/zig-codecs/t5m.zig");

const core_asset = @embedFile("lib/core.sens");
const unify_asset = @embedFile("lib/unify.sens");
const guard_asset = @embedFile("lib/guard.sens");

fn assetFor(id: u32) ?[]const u8 {
    return switch (id) {
        0 => core_asset,
        1 => unify_asset,
        2 => guard_asset,
        else => null,
    };
}

// FFI records are u32 big-endian width followed by width numeric 0/1 bytes.
// They are typed transport records, not a domain registry or .sens wire.
fn copyT5mWords(asset: []const u8, dst: [*]u8, capacity: usize) isize {
    var decoded = t5m.decode(std.heap.page_allocator, asset) catch return -1;
    defer decoded.deinit(std.heap.page_allocator);

    var required: usize = 0;
    for (decoded.words) |word| {
        const record_len = std.math.add(usize, 4, word.width) catch return -1;
        required = std.math.add(usize, required, record_len) catch return -1;
    }
    if (required == 0) return -1;
    if (capacity == 0) return std.math.cast(isize, required) orelse return -1;
    if (capacity < required) return -2;

    var offset: usize = 0;
    for (decoded.words) |word| {
        std.mem.writeInt(u32, dst[offset..][0..4], @intCast(word.width), .big);
        offset += 4;
        for (word.bits) |bit| {
            dst[offset] = bit - '0';
            offset += 1;
        }
    }
    return std.math.cast(isize, required) orelse return -1;
}

pub export fn sens_zig_guard_t5m_words_copy(id: u32, dst: [*]u8, capacity: usize) isize {
    const asset = assetFor(id) orelse return -1;
    return copyT5mWords(asset, dst, capacity);
}

fn verifyT5mWords(comptime asset: []const u8) !void {
    var decoded = try t5m.decode(std.testing.allocator, asset);
    defer decoded.deinit(std.testing.allocator);
    const required = copyT5mWords(asset, undefined, 0);
    var expected_len: usize = 0;
    for (decoded.words) |word| expected_len += 4 + word.width;
    try std.testing.expectEqual(@as(isize, @intCast(expected_len)), required);
    const exact = try std.testing.allocator.alloc(u8, expected_len);
    defer std.testing.allocator.free(exact);
    try std.testing.expectEqual(required, copyT5mWords(asset, exact.ptr, exact.len));

    var offset: usize = 0;
    for (decoded.words) |word| {
        try std.testing.expectEqual(word.width, std.mem.readInt(u32, exact[offset..][0..4], .big));
        offset += 4;
        for (word.bits) |bit| {
            try std.testing.expectEqual(bit - '0', exact[offset]);
            offset += 1;
        }
    }

    const short = try std.testing.allocator.alloc(u8, expected_len - 1);
    defer std.testing.allocator.free(short);
    @memset(short, 0xA5);
    try std.testing.expectEqual(@as(isize, -2), copyT5mWords(asset, short.ptr, short.len));
    for (short) |byte| try std.testing.expectEqual(@as(u8, 0xA5), byte);
}

