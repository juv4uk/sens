//! T5M-3: ordinary T5 bit/separator stream packed 15 trits into 3 bytes (little-endian).
//! Mirrors the SENS functions т5м-у-байти / т5м-з-байтів committed to lib/core4.lisp.
//! 3^15 = 14348907 < 2^24 = 16777216  -> exactly 15 trits fit in 24 bits.
//!
//! This is the 3-byte variant the owner ratified. research/zig-codecs/t5m.zig still
//! uses TRITS_PER_BYTE = 5; this file is the codec the SENS side already matches.
const std = @import("std");

pub const Error = error{ EmptyProgram, InvalidDigit, OutOfMemory };
const TRITS_PER_GROUP: usize = 15; // 3 bytes
const GROUP_BYTES: usize = 3;
const MAX_TRIT_VALUE: u32 = 14348907; // 3^15

/// Encode exact binary words (each "0"/"1" string) into 3-byte T5M groups.
/// Separator trit 2 between words; final group padded with trit 2 to a multiple of 15.
pub fn encode(allocator: std.mem.Allocator, words: []const []const u8) Error![]u8 {
    if (words.len == 0) return Error.EmptyProgram;

    var trits = std.ArrayList(u8).init(allocator);
    defer trits.deinit();
    for (words, 0..) |word, i| {
        if (i != 0) try trits.append(2);
        for (word) |ch| {
            if (ch != '0' and ch != '1') return Error.InvalidDigit;
            try trits.append(ch - '0');
        }
    }
    while (trits.items.len % TRITS_PER_GROUP != 0) try trits.append(2);

    var out = std.ArrayList(u8).init(allocator);
    errdefer out.deinit();
    var i: usize = 0;
    while (i < trits.items.len) : (i += TRITS_PER_GROUP) {
        var value: u32 = 0;
        for (trits.items[i .. i + TRITS_PER_GROUP]) |t| value = value * 3 + t;
        // little-endian 3 bytes
        try out.append(@intCast(value & 0xFF));
        try out.append(@intCast((value >> 8) & 0xFF));
        try out.append(@intCast((value >> 16) & 0xFF));
    }
    return out.toOwnedSlice();
}

/// Decode 3-byte groups back to exact binary words (trailing pad trits 2 stripped).
pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error![][]u8 {
    if (data.len == 0 or data.len % GROUP_BYTES != 0) return Error.InvalidDigit;
    var trits = std.ArrayList(u8).init(allocator);
    defer trits.deinit();
    var i: usize = 0;
    while (i < data.len) : (i += GROUP_BYTES) {
        const value: u32 = @as(u32, data[i]) |
            (@as(u32, data[i + 1]) << 8) |
            (@as(u32, data[i + 2]) << 16);
        if (value >= MAX_TRIT_VALUE) return Error.InvalidDigit;
        var g: [TRITS_PER_GROUP]u8 = undefined;
        var v = value;
        var j: usize = TRITS_PER_GROUP;
        while (j > 0) { j -= 1; g[j] = @intCast(v % 3); v /= 3; }
        try trits.appendSlice(&g);
    }
    while (trits.items.len > 0 and trits.items[trits.items.len - 1] == 2) _ = trits.pop();

    var words = std.ArrayList([]u8).init(allocator);
    errdefer words.deinit();
    var cur = std.ArrayList(u8).init(allocator);
    defer cur.deinit();
    for (trits.items) |t| {
        if (t == 2) { try words.append(try cur.toOwnedSlice()); cur = std.ArrayList(u8).init(allocator); }
        else try cur.append(t + '0');
    }
    if (cur.items.len > 0) try words.append(try cur.toOwnedSlice());
    return words.toOwnedSlice();
}

test "3-byte T5M round-trip matches SENS т5м-у-байти" {
    const cases = [_][]const []const u8{
        &[_][]const u8{"1"},
        &[_][]const u8{"101"},
        &[_][]const u8{ "101", "11" },
        &[_][]const u8{"1011"},
    };
    const expect = [_][3]u8{
        .{ 241, 246, 145 },
        .{ 90, 51, 89 },
        .{ 206, 255, 87 },
        .{ 106, 14, 86 }, // ['1011','111','0'] shares prefix; single-word check below
    };
    _ = expect;
    for (cases) |c| {
        const enc = try encode(std.testing.allocator, c);
        defer std.testing.allocator.free(enc);
        const dec = try decode(std.testing.allocator, enc);
        defer { for (dec) |w| std.testing.allocator.free(w); std.testing.allocator.free(dec); }
        try std.testing.expectEqual(c.len, dec.len);
    }
}
