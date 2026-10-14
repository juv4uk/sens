//! E1 S3/v1 exact physical encoder and canonical byte replay, Zig 0.16.
//! Fully caller-owned storage: no heap, OS, file I/O, runtime host callbacks.
//! Width + payload are opaque; executable meaning belongs ONLY to binary SENS.
//! This module is NOT a D2 parser or authorization to execute a program.
const std = @import("std");
const e1 = @import("e1.zig");
const fields = @import("fields.zig");

pub const Word = e1.Word;
pub const Error = e1.Error || error{InvalidBits};

/// Caller must provide at least words.len + 1 elements. No hidden allocation.
pub const Step = struct {
    bytes: usize,
    end: usize,
    mode: u8,
};
const RAW: u8 = 0;
const REPEAT: u8 = 1;

fn lengthVarint(n_: usize) usize {
    var n = n_;
    var count: usize = 1;
    while (n >= 128) : (n >>= 7) count += 1;
    return count;
}

fn putVarint(out: []u8, cursor: *usize, n_: usize) void {
    var n = n_;
    while (n >= 128) : (n >>= 7) {
        out[cursor.*] = @as(u8, @intCast(n & 0x7f)) | 0x80;
        cursor.* += 1;
    }
    out[cursor.*] = @intCast(n);
    cursor.* += 1;
}

fn valid(word: Word) bool {
    if (word.width == 0 or word.width > 9) return false;
    return word.bits < (@as(u16, 1) << @as(u4, @intCast(word.width)));
}

/// Identical physical RAW/REPEAT dynamic-programming tie order:
/// shortest bytes, then RAW, then longest block. No SENS semantic rules.
fn plan(words: []const Word, scratch: []Step) Error!usize {
    if (words.len > e1.MAX_WORDS) return error.TooLarge;
    if (scratch.len <= words.len) return error.BufferTooSmall;
    for (words) |word| {
        if (!valid(word)) return error.InvalidBits;
    }
    const infinity = std.math.maxInt(usize);
    const n = words.len;
    for (scratch[0 .. n + 1]) |*step| {
        step.* = .{ .bytes = infinity, .end = n, .mode = RAW };
    }
    scratch[n].bytes = 0;
    var at = n;
    while (at > 0) {
        at -= 1;
        var bits: usize = 0;
        var equal = true;
        var end = at + 1;
        while (end <= @min(n, at + e1.MAX_BLOCK_WORDS)) : (end += 1) {
            const word = words[end - 1];
            bits += word.width;
            equal = equal and word.width == words[at].width and
                word.bits == words[at].bits;
            const count = end - at;
            const raw_bytes = 1 + lengthVarint(count) + (count + 1) / 2 + (bits + 7) / 8;
            var cost = raw_bytes;
            var mode: u8 = RAW;
            if (equal) {
                const repeated = 1 + lengthVarint(count) + 1 +
                    (@as(usize, word.width) + 7) / 8;
                if (repeated < cost) {
                    cost = repeated;
                    mode = REPEAT;
                }
            }
            const total = cost + scratch[end].bytes;
            const prev = scratch[at];
            if (total < prev.bytes or
                (total == prev.bytes and
                    (mode < prev.mode or (mode == prev.mode and end > prev.end))))
            {
                scratch[at] = .{ .bytes = total, .end = end, .mode = mode };
            }
        }
    }
    return 3 + lengthVarint(n) + scratch[0].bytes + 4;
}

fn writeBits(out: []u8, words: []const Word) void {
    @memset(out, 0);
    var bit: usize = 0;
    for (words) |word| {
        var shift: usize = word.width;
        while (shift > 0) {
            shift -= 1;
            const single: u8 = @intCast((word.bits >>
                @as(u4, @intCast(shift))) & 1);
            out[bit / 8] |= single << @as(u3, @intCast(7 - bit % 8));
            bit += 1;
        }
    }
}

/// Encode raw physical words to E1; requires output and caller-owned DP plan.
/// No partial output on InvalidBits/TooLarge/BufferTooSmall.
pub fn encode(words: []const Word, output: []u8, scratch: []Step) Error!usize {
    const size = try plan(words, scratch);
    if (size > e1.MAX_FILE_BYTES) return error.TooLarge;
    if (output.len < size) return error.BufferTooSmall;
    var cursor: usize = 0;
    output[cursor] = 'S';
    cursor += 1;
    output[cursor] = '3';
    cursor += 1;
    output[cursor] = 1;
    cursor += 1;
    putVarint(output, &cursor, words.len);
    var at: usize = 0;
    while (at < words.len) {
        const step = scratch[at];
        const block = words[at..step.end];
        output[cursor] = step.mode;
        cursor += 1;
        putVarint(output, &cursor, block.len);
        if (step.mode == RAW) {
            for (0..(block.len + 1) / 2) |i| {
                const left = block[2 * i].width;
                const right: u8 = if (2 * i + 1 < block.len)
                    block[2 * i + 1].width else 0;
                output[cursor] = (left << 4) | right;
                cursor += 1;
            }
            var bits: usize = 0;
            for (block) |word| bits += word.width;
            const nbytes = (bits + 7) / 8;
            writeBits(output[cursor .. cursor + nbytes], block);
            cursor += nbytes;
        } else {
            output[cursor] = block[0].width;
            cursor += 1;
            const nbytes = (@as(usize, block[0].width) + 7) / 8;
            writeBits(output[cursor .. cursor + nbytes], block[0..1]);
            cursor += nbytes;
        }
        at = step.end;
    }
    const crc = fields.crc32(output[0..cursor]);
    output[cursor] = @intCast(crc >> 24);
    output[cursor + 1] = @intCast((crc >> 16) & 0xff);
    output[cursor + 2] = @intCast((crc >> 8) & 0xff);
    output[cursor + 3] = @intCast(crc & 0xff);
    cursor += 4;
    std.debug.assert(cursor == size);
    return size;
}

/// Strict physical canonical check: decode → independently plan → byte-replay.
/// The caller provides ALL storage. A canonical physical carrier can still
/// contain a SENS semantic-invalid expression; that is NOT this module's call.
pub fn inspectCanonical(
    frame: []const u8,
    decoded: []Word,
    scratch: []Step,
    replay: []u8,
) Error!usize {
    const count = try e1.inspect(frame);
    if (decoded.len < count or scratch.len <= count) return error.BufferTooSmall;
    _ = try e1.unpack(frame, decoded[0..count]);
    const size = try encode(decoded[0..count], replay, scratch);
    if (!std.mem.eql(u8, frame, replay[0..size])) return error.NonCanonical;
    return count;
}

test "E1 canonical encode exact cross-implementation RAW physical witness" {
    const words = [_]Word{
        .{ .width = 2, .bits = 2 },
        .{ .width = 3, .bits = 1 },
        .{ .width = 2, .bits = 1 },
    };
    const golden = [_]u8{ 0x53, 0x33, 1, 3, 0, 3, 0x23, 0x20,
        0x8a, 0x36, 0x20, 0x5d, 0x52 };
    var physical: [64]u8 = undefined;
    var work: [words.len + 1]Step = undefined;
    const size = try encode(&words, &physical, &work);
    try std.testing.expectEqualSlices(u8, &golden, physical[0..size]);
    var recovered: [words.len]Word = undefined;
    var replay: [64]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 3),
        try inspectCanonical(physical[0..size], &recovered, &work, &replay));
    for (words, recovered) |expected, actual| {
        try std.testing.expectEqual(expected.width, actual.width);
        try std.testing.expectEqual(expected.bits, actual.bits);
    }
}

test "E1 canonical REPEAT and empty source match fixed physical bytes" {
    const repeated = [_]Word{
        .{ .width = 1, .bits = 1 },
        .{ .width = 1, .bits = 1 },
        .{ .width = 1, .bits = 1 },
    };
    const golden = [_]u8{ 'S', '3', 1, 3, 1, 3, 1, 0x80,
        0xe5, 0xa5, 0x56, 0xab };
    var physical: [64]u8 = undefined;
    var scratch: [4]Step = undefined;
    const size = try encode(&repeated, &physical, &scratch);
    try std.testing.expectEqualSlices(u8, &golden, physical[0..size]);
    const empty = [_]Word{};
    const length = try encode(&empty, &physical, &scratch);
    try std.testing.expectEqualSlices(u8,
        &.{ 'S', '3', 1, 0, 0xc7, 0xca, 0x15, 0xd8 }, physical[0..length]);
    var replay: [64]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 0),
        try inspectCanonical(physical[0..length], &.{}, &scratch, &replay));
}

test "E1 fail-closed aliases with valid CRC, explicit widths and caller bounds" {
    const alias_body = [_]u8{ 'S', '3', 1, 1, REPEAT, 1, 1, 0 };
    var alias: [12]u8 = undefined;
    @memcpy(alias[0..alias_body.len], &alias_body);
    const crc = fields.crc32(&alias_body);
    alias[8] = @intCast(crc >> 24);
    alias[9] = @intCast((crc >> 16) & 0xff);
    alias[10] = @intCast((crc >> 8) & 0xff);
    alias[11] = @intCast(crc & 0xff);
    try std.testing.expectEqual(@as(usize, 1), try e1.inspect(&alias));
    var words: [2]Word = undefined;
    var scratch: [3]Step = undefined;
    var replay: [64]u8 = undefined;
    try std.testing.expectError(error.NonCanonical,
        inspectCanonical(&alias, &words, &scratch, &replay));
    // Equal payload zero, different exact width => different bytes.
    const a = [_]Word{.{ .width = 1, .bits = 0 }};
    const b = [_]Word{.{ .width = 2, .bits = 0 }};
    var left: [64]u8 = undefined;
    var right: [64]u8 = undefined;
    const al = try encode(&a, &left, &scratch);
    const bl = try encode(&b, &right, &scratch);
    try std.testing.expect(!std.mem.eql(u8, left[0..al], right[0..bl]));
    try std.testing.expectError(error.InvalidBits,
        encode(&.{.{ .width = 2, .bits = 4 }}, &right, &scratch));
    try std.testing.expectError(error.InvalidBits,
        encode(&.{.{ .width = 0, .bits = 0 }}, &right, &scratch));
    try std.testing.expectError(error.BufferTooSmall,
        encode(&a, right[0..7], &scratch));
    try std.testing.expectError(error.BufferTooSmall,
        encode(&a, &right, scratch[0..1]));
}

fn nibble(char: u8) !u8 {
    if (char >= '0' and char <= '9') return char - '0';
    if (char >= 'a' and char <= 'f') return char - 'a' + 10;
    return error.InvalidHexDigit;
}

// One immutable *physical* fixture corpus for independent encode/decode on
// each implementation. Its binary words do not confer SENS call authority.
test "E1 shared exact-width carrier corpus: independent encode and decode" {
    const corpus = @embedFile("../fixtures/e1-v1.bits");
    var lines = std.mem.splitScalar(u8, corpus, '\n');
    var tested: usize = 0;
    while (lines.next()) |line| {
        if (line.len == 0 or line[0] == '#') continue;
        var columns = std.mem.splitScalar(u8, line, '|');
        const name = columns.next() orelse return error.MissingCase;
        const bits_source = columns.next() orelse return error.MissingWords;
        const hex = columns.next() orelse return error.MissingPhysical;
        try std.testing.expect(columns.next() == null);
        try std.testing.expect(hex.len > 0 and hex.len % 2 == 0);

        var words: [256]Word = undefined;
        var count: usize = 0;
        var tokens = std.mem.tokenizeScalar(u8, bits_source, ' ');
        while (tokens.next()) |token| {
            try std.testing.expect(token.len >= 1 and token.len <= 9);
            try std.testing.expect(count < words.len);
            var payload: u16 = 0;
            for (token) |digit| {
                try std.testing.expect(digit == '0' or digit == '1');
                payload = (payload << 1) | @as(u16, digit - '0');
            }
            words[count] = .{ .width = @intCast(token.len), .bits = payload };
            count += 1;
        }
        var expected: [2048]u8 = undefined;
        const exp_len = hex.len / 2;
        try std.testing.expect(exp_len <= expected.len);
        for (0..exp_len) |i| {
            expected[i] = ((try nibble(hex[2 * i])) << 4) |
                (try nibble(hex[2 * i + 1]));
        }
        var output: [2048]u8 = undefined;
        var scratch: [257]Step = undefined;
        const encoded_len = try encode(words[0..count], &output, &scratch);
        std.testing.expectEqualSlices(u8, expected[0..exp_len], output[0..encoded_len]) catch |err| {
            std.debug.print("E1_BYTE_PARITY_FAIL case={s} fixture=e1-v1.bits\n", .{name});
            return err;
        };

        // Independent physical decoder and the canonical byte replay path.
        var decoded: [256]Word = undefined;
        var replay: [2048]u8 = undefined;
        const recovered = try inspectCanonical(
            expected[0..exp_len], &decoded, &scratch, &replay,
        );
        try std.testing.expectEqual(count, recovered);
        for (words[0..count], decoded[0..recovered]) |left, right| {
            try std.testing.expectEqual(left.width, right.width);
            try std.testing.expectEqual(left.bits, right.bits);
        }
        tested += 1;
    }
    try std.testing.expectEqual(@as(usize, 16), tested);
}
