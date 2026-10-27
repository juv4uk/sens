//! T5M3: five-trit T5M digits grouped as fifteen trits in three little-endian bytes.
//! This is an optional 3-byte physical variant; the default T5M is one byte per five trits.
//! 3^15 = 14348907 < 2^24 = 16777216  -> exactly 15 trits fit in 24 bits.
//!
//! T5M3 is distinct from default T5M and is never selected by the default REPL bridge.
const std = @import("std");

pub const Error = error{ EmptyProgram, InvalidDigit, OutOfMemory };
const TRITS_PER_GROUP: usize = 15; // 3 bytes
const GROUP_BYTES: usize = 3;
const MAX_TRIT_VALUE: u32 = 14348907; // 3^15

/// Encode exact binary words (each "0"/"1" string) into 3-byte T5M3 groups.
/// Separator trit 2 between words; final group padded with trit 2 to a multiple of 15.
pub fn encode(allocator: std.mem.Allocator, words: []const []const u8) Error![]u8 {
    if (words.len == 0) return Error.EmptyProgram;

    var trits: std.ArrayList(u8) = .empty;
    defer trits.deinit(allocator);
    for (words, 0..) |word, i| {
        if (i != 0) try trits.append(allocator, 2);
        for (word) |ch| {
            if (ch != '0' and ch != '1') return Error.InvalidDigit;
            try trits.append(allocator, ch - '0');
        }
    }
    while (trits.items.len % TRITS_PER_GROUP != 0) try trits.append(allocator, 2);

    var out: std.ArrayList(u8) = .empty;
    errdefer out.deinit(allocator);
    var i: usize = 0;
    while (i < trits.items.len) : (i += TRITS_PER_GROUP) {
        var value: u32 = 0;
        for (trits.items[i .. i + TRITS_PER_GROUP]) |t| value = value * 3 + t;
        // little-endian 3 bytes
        try out.append(allocator, @intCast(value & 0xFF));
        try out.append(allocator, @intCast((value >> 8) & 0xFF));
        try out.append(allocator, @intCast((value >> 16) & 0xFF));
    }
    return out.toOwnedSlice(allocator);
}

/// Decode 3-byte groups back to exact binary words (trailing pad trits 2 stripped).
pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error![][]u8 {
    if (data.len == 0 or data.len % GROUP_BYTES != 0) return Error.InvalidDigit;
    var trits: std.ArrayList(u8) = .empty;
    defer trits.deinit(allocator);
    var i: usize = 0;
    while (i < data.len) : (i += GROUP_BYTES) {
        const value: u32 = @as(u32, data[i]) |
            (@as(u32, data[i + 1]) << 8) |
            (@as(u32, data[i + 2]) << 16);
        if (value >= MAX_TRIT_VALUE) return Error.InvalidDigit;
        var g: [TRITS_PER_GROUP]u8 = undefined;
        var v = value;
        var j: usize = TRITS_PER_GROUP;
        while (j > 0) {
            j -= 1;
            g[j] = @intCast(v % 3);
            v /= 3;
        }
        try trits.appendSlice(allocator, &g);
    }
    while (trits.items.len > 0 and trits.items[trits.items.len - 1] == 2) _ = trits.pop();

    var words: std.ArrayList([]u8) = .empty;
    errdefer words.deinit(allocator);
    var cur: std.ArrayList(u8) = .empty;
    defer cur.deinit(allocator);
    for (trits.items) |t| {
        if (t == 2) {
            try words.append(allocator, try cur.toOwnedSlice(allocator));
            cur = .empty;
        } else try cur.append(allocator, t + '0');
    }
    if (cur.items.len > 0) try words.append(allocator, try cur.toOwnedSlice(allocator));
    return words.toOwnedSlice(allocator);
}

