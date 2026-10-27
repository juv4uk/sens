//! E1 S3/v1 exact physical encoder and canonical byte replay, Zig 0.16.
//! Fully caller-owned storage: no heap, OS, file I/O, runtime host callbacks.
//! Width + payload are opaque; executable meaning belongs ONLY to binary SENS.
//! This module is NOT a D2 parser or authorization to execute a program.
const std = @import("std");
const e1 = @import("e1.zig");
const fields = @import("fields.zig");

pub const Word = e1.Word;
pub const Error = e1.Error || error{ InvalidBits, OverlappingBuffers };

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
    // The DP planner writes scratch before encoding; the writer then reads
    // both words and scratch while writing output. No buffers may alias.
    const word_bytes = std.mem.sliceAsBytes(words);
    const scratch_bytes = std.mem.sliceAsBytes(scratch);
    if (slicesOverlap(word_bytes, scratch_bytes) or
        slicesOverlap(word_bytes, output) or
        slicesOverlap(scratch_bytes, output))
        return error.OverlappingBuffers;
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

/// Distinct caller-owned read/write buffers are mandatory for byte replay.
/// Comparing a frame with itself after encoding into overlapping memory would
/// turn a CRC-correct noncanonical alias into a false canonical witness.
fn slicesOverlap(left: []const u8, right: []const u8) bool {
    if (left.len == 0 or right.len == 0) return false;
    const a = @intFromPtr(left.ptr);
    const b = @intFromPtr(right.ptr);
    // Differences avoid endpoint addition and usize overflow.
    return if (a <= b) b - a < left.len else a - b < right.len;
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
    // Decode and planning also write caller-owned memory. Reject every
    // frame/output/workspace alias before unpacking or rewriting anything.
    const decoded_bytes = std.mem.sliceAsBytes(decoded);
    const scratch_bytes = std.mem.sliceAsBytes(scratch);
    if (slicesOverlap(frame, replay) or
        slicesOverlap(frame, decoded_bytes) or
        slicesOverlap(frame, scratch_bytes) or
        slicesOverlap(decoded_bytes, scratch_bytes) or
        slicesOverlap(decoded_bytes, replay) or
        slicesOverlap(scratch_bytes, replay))
        return error.OverlappingBuffers;
    const count = try e1.inspect(frame);
    if (decoded.len < count or scratch.len <= count) return error.BufferTooSmall;
    // A byte-exact canonical replay must contain at least frame.len bytes.
    // Reject a short caller-owned replay BEFORE touching decoded or DP scratch.
    if (replay.len < frame.len) return error.BufferTooSmall;
    _ = try e1.unpack(frame, decoded[0..count]);
    const size = try encode(decoded[0..count], replay, scratch);
    if (!std.mem.eql(u8, frame, replay[0..size])) return error.NonCanonical;
    return count;
}

fn nibble(char: u8) !u8 {
    if (char >= '0' and char <= '9') return char - '0';
    if (char >= 'a' and char <= 'f') return char - 'a' + 10;
    return error.InvalidHexDigit;
}

// One immutable *physical* fixture corpus for independent encode/decode on
// each implementation. Its binary words do not confer SENS call authority.
