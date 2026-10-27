//! T33: дослідний багатобайтовий фізичний носій точних (width,bits).
//! Це НЕ production-кодек і НЕ числова семантика SENS.
//! F3 33 | canonical ULEB(trit_count) | full 33-trit ranks (6 B) | T5M tail.
//! Повні блоки ранжуються серед тернарних рядків без сусідніх роздільників 22.
const std = @import("std");
const t5m = @import("t5m.zig");

pub const Word = t5m.Word;
pub const Decoded = t5m.Decoded;
pub const Error = error{
    EmptyProgram,
    WrongMagic,
    UnsupportedVersion,
    InvalidBinaryDigit,
    InvalidWidth,
    InvalidCount,
    NonCanonical,
    Truncated,
    InvalidRank,
    InvalidTail,
    EmptyDomainWord,
    AdjacentSeparator,
    TransportTooLarge,
    OutOfMemory,
};

const MAGIC = [_]u8{ 0xf3, 0x33 };
const BLOCK_TRITS: usize = 33;
const BLOCK_BYTES: usize = 6;
const TAIL_TRITS_PER_BYTE: usize = 5;
const MAX_BYTES: usize = t5m.MAX_PHYSICAL_BYTES;
const MAX_TRITS: usize = MAX_BYTES * 6;

fn buildCounts() [BLOCK_TRITS + 1][2]u64 {
    var c: [BLOCK_TRITS + 1][2]u64 = undefined;
    c[0] = .{ 1, 1 };
    for (1..BLOCK_TRITS + 1) |n| {
        c[n][0] = 2 * c[n - 1][0] + c[n - 1][1];
        c[n][1] = 2 * c[n - 1][0];
    }
    return c;
}

const counts = buildCounts();

fn lebLen(value: usize) usize {
    var n = value;
    var len: usize = 1;
    while (n >= 128) : (n >>= 7) len += 1;
    return len;
}

fn writeLeb(out: []u8, value: usize) usize {
    var n = value;
    var at: usize = 0;
    while (n >= 128) : (n >>= 7) {
        out[at] = @as(u8, @intCast(n & 0x7f)) | 0x80;
        at += 1;
    }
    out[at] = @intCast(n);
    return at + 1;
}

const Header = struct { count: usize, body: usize };

fn readHeader(data: []const u8) Error!Header {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len < 2 or data[0] != MAGIC[0]) return Error.WrongMagic;
    if (data[1] != MAGIC[1]) return Error.UnsupportedVersion;
    var at: usize = 2;
    var count: usize = 0;
    var factor: usize = 1;
    var seen: usize = 0;
    while (true) {
        if (at >= data.len) return Error.Truncated;
        const byte = data[at];
        at += 1;
        seen += 1;
        const part = std.math.mul(usize, @as(usize, byte & 0x7f), factor) catch
            return Error.InvalidCount;
        count = std.math.add(usize, count, part) catch return Error.InvalidCount;
        if ((byte & 0x80) == 0) {
            if (seen != lebLen(count)) return Error.NonCanonical;
            break;
        }
        factor = std.math.mul(usize, factor, 128) catch return Error.InvalidCount;
    }
    if (count == 0 or count > MAX_TRITS) return Error.InvalidCount;
    return .{ .count = count, .body = at };
}

fn rankBlock(trits: []const u8, initial_prev_two: bool) Error!u64 {
    std.debug.assert(trits.len == BLOCK_TRITS);
    var rank: u64 = 0;
    var prev_two = initial_prev_two;
    for (trits, 0..) |digit, i| {
        const remaining = BLOCK_TRITS - i - 1;
        const zero_ways = counts[remaining][0];
        switch (digit) {
            0 => {},
            1 => rank += zero_ways,
            2 => {
                if (prev_two) return Error.AdjacentSeparator;
                rank += 2 * zero_ways;
            },
            else => return Error.InvalidBinaryDigit,
        }
        prev_two = digit == 2;
    }
    return rank;
}

fn unrankBlock(rank_value: u64, initial_prev_two: bool, out: []u8) Error!void {
    std.debug.assert(out.len == BLOCK_TRITS);
    if (rank_value >= counts[BLOCK_TRITS][@intFromBool(initial_prev_two)])
        return Error.InvalidRank;
    var rank = rank_value;
    var prev_two = initial_prev_two;
    for (out, 0..) |*digit, i| {
        const remaining = BLOCK_TRITS - i - 1;
        const zero_ways = counts[remaining][0];
        if (rank < zero_ways) {
            digit.* = 0;
            prev_two = false;
        } else if (rank < 2 * zero_ways) {
            rank -= zero_ways;
            digit.* = 1;
            prev_two = false;
        } else if (!prev_two) {
            rank -= 2 * zero_ways;
            if (rank >= counts[remaining][1]) return Error.InvalidRank;
            digit.* = 2;
            prev_two = true;
        } else {
            return Error.InvalidRank;
        }
    }
    if (rank != 0) return Error.InvalidRank;
}

fn validateWords(words: []const Word) Error!usize {
    if (words.len == 0) return Error.EmptyProgram;
    var trit_count: usize = words.len - 1;
    for (words) |word| {
        if (word.width == 0 or word.width != word.bits.len) return Error.InvalidWidth;
        trit_count = std.math.add(usize, trit_count, word.width) catch
            return Error.TransportTooLarge;
        if (trit_count > MAX_TRITS) return Error.TransportTooLarge;
        for (word.bits) |bit| {
            if (bit != '0' and bit != '1') return Error.InvalidBinaryDigit;
        }
    }
    return trit_count;
}

pub fn encode(allocator: std.mem.Allocator, words: []const Word) Error![]u8 {
    const trit_count = try validateWords(words);
    const full = trit_count / BLOCK_TRITS;
    const tail = trit_count % BLOCK_TRITS;
    const tail_bytes = (tail + TAIL_TRITS_PER_BYTE - 1) / TAIL_TRITS_PER_BYTE;
    const len = 2 + lebLen(trit_count) + full * BLOCK_BYTES + tail_bytes;
    if (len > MAX_BYTES) return Error.TransportTooLarge;

    const trits = allocator.alloc(u8, trit_count) catch return Error.OutOfMemory;
    defer allocator.free(trits);
    var at: usize = 0;
    for (words, 0..) |word, wi| {
        if (wi != 0) {
            trits[at] = 2;
            at += 1;
        }
        for (word.bits) |bit| {
            trits[at] = bit - '0';
            at += 1;
        }
    }
    std.debug.assert(at == trit_count);

    const out = allocator.alloc(u8, len) catch return Error.OutOfMemory;
    errdefer allocator.free(out);
    out[0] = MAGIC[0];
    out[1] = MAGIC[1];
    var pos: usize = 2 + writeLeb(out[2..], trit_count);
    var prev_two = false;
    for (0..full) |block| {
        const begin = block * BLOCK_TRITS;
        const part = trits[begin .. begin + BLOCK_TRITS];
        const rank = try rankBlock(part, prev_two);
        for (0..BLOCK_BYTES) |i| {
            const shift: u6 = @intCast((BLOCK_BYTES - i - 1) * 8);
            out[pos + i] = @intCast((rank >> shift) & 0xff);
        }
        pos += BLOCK_BYTES;
        prev_two = part[BLOCK_TRITS - 1] == 2;
    }

    const begin = full * BLOCK_TRITS;
    var tail_at: usize = begin;
    for (0..tail_bytes) |_| {
        var value: u8 = 0;
        for (0..TAIL_TRITS_PER_BYTE) |_| {
            const digit: u8 = if (tail_at < trit_count) trits[tail_at] else 2;
            value = value * 3 + digit;
            tail_at += 1;
        }
        out[pos] = value;
        pos += 1;
    }
    std.debug.assert(pos == len);
    return out;
}

pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error!Decoded {
    if (data.len > MAX_BYTES) return Error.TransportTooLarge;
    const h = try readHeader(data);
    const full = h.count / BLOCK_TRITS;
    const tail = h.count % BLOCK_TRITS;
    const tail_bytes = (tail + TAIL_TRITS_PER_BYTE - 1) / TAIL_TRITS_PER_BYTE;
    if (h.body + full * BLOCK_BYTES + tail_bytes != data.len) return Error.Truncated;
    const trits = allocator.alloc(u8, h.count) catch return Error.OutOfMemory;
    defer allocator.free(trits);
    var pos = h.body;
    var prev_two = false;
    for (0..full) |block| {
        var rank: u64 = 0;
        for (0..BLOCK_BYTES) |_| {
            rank = (rank << 8) | @as(u64, data[pos]);
            pos += 1;
        }
        const begin = block * BLOCK_TRITS;
        const part = trits[begin .. begin + BLOCK_TRITS];
        try unrankBlock(rank, prev_two, part);
        prev_two = part[BLOCK_TRITS - 1] == 2;
    }
    const begin = full * BLOCK_TRITS;
    var tail_at: usize = begin;
    for (0..tail_bytes) |_| {
        var value = data[pos];
        pos += 1;
        if (value >= 243) return Error.InvalidTail;
        var group: [TAIL_TRITS_PER_BYTE]u8 = undefined;
        var i: usize = TAIL_TRITS_PER_BYTE;
        while (i > 0) {
            i -= 1;
            group[i] = value % 3;
            value /= 3;
        }
        for (group) |digit| {
            if (tail_at < h.count) {
                trits[tail_at] = digit;
            } else if (digit != 2) {
                return Error.InvalidTail;
            }
            tail_at += 1;
        }
    }
    std.debug.assert(pos == data.len);
    if (trits[0] == 2 or trits[h.count - 1] == 2) return Error.EmptyDomainWord;

    var word_count: usize = 1;
    var total_bits: usize = 0;
    var width: usize = 0;
    for (trits) |trit| {
        if (trit == 2) {
            if (width == 0) return Error.AdjacentSeparator;
            word_count += 1;
            width = 0;
        } else {
            total_bits += 1;
            width += 1;
        }
    }
    const out_words = allocator.alloc(t5m.DecodedWord, word_count) catch
        return Error.OutOfMemory;
    errdefer allocator.free(out_words);
    const storage = allocator.alloc(u8, total_bits) catch return Error.OutOfMemory;
    errdefer allocator.free(storage);

    var word_index: usize = 0;
    var offset: usize = 0;
    var word_begin: usize = 0;
    for (trits) |trit| {
        if (trit == 2) {
            out_words[word_index] = .{
                .width = offset - word_begin,
                .bits = storage[word_begin..offset],
            };
            word_index += 1;
            word_begin = offset;
        } else {
            storage[offset] = trit + '0';
            offset += 1;
        }
    }
    out_words[word_index] = .{
        .width = offset - word_begin,
        .bits = storage[word_begin..offset],
    };
    return .{ .words = out_words, .bit_storage = storage };
}

// Гра «Драбина T33»: кожна сходинка перевіряє лише фізичні (width,bits).
// Це не SENS-оракул, не визначення чисел і не дозвіл на production-заміщення.
