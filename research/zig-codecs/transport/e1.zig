//! E1 (S3/v1 physical carrier): bounded reader for Zig 0.16.
//! Pure carrier preflight only; width and payload are opaque transport data.
//! It is NOT .sens T5, .senc F3C, E2/E3, or SENS semantic authority.
//! This heapless/OS-free reader does NOT verify D2 or optimal-DP canonicality.
//! A physical success must NOT be used as E1 executable/admission PASS.
const std = @import("std");
const fields = @import("fields.zig");

pub const Word = struct { width: u8, bits: u16 };
pub const MAX_WORDS: usize = 4096;
pub const MAX_BLOCK_WORDS: usize = 128;
pub const MAX_FILE_BYTES: usize = 1024 * 1024;
pub const Error = error{
    Truncated, TooLarge, BadVersion, InvalidBlock, InvalidWidth,
    NonCanonical, IntegrityMismatch, BufferTooSmall, OverlappingBuffers,
};

fn readCount(input: []const u8, cursor: *usize) Error!usize {
    var n: u64 = 0;
    for (0..5) |i| {
        if (cursor.* >= input.len) return error.Truncated;
        const byte = input[cursor.*];
        cursor.* += 1;
        const shift: u6 = @intCast(i * 7);
        n |= @as(u64, byte & 0x7f) << shift;
        if ((byte & 0x80) == 0) {
            if (i > 0 and (byte & 0x7f) == 0) return error.NonCanonical;
            if (n > @as(u64, MAX_WORDS)) return error.TooLarge;
            return @intCast(n);
        }
    }
    return error.NonCanonical;
}
fn packedBit(input: []const u8, index: usize) u16 {
    return @as(u16, (input[index / 8] >>
        @as(u3, @intCast(7 - index % 8))) & 1);
}
fn parse(input: []const u8, output: ?[]Word) Error!usize {
    if (input.len > MAX_FILE_BYTES) return error.TooLarge;
    if (input.len < 8) return error.Truncated;
    if (!std.mem.eql(u8, input[0..3], &.{ 'S', '3', 1 }))
        return error.BadVersion;
    const end = input.len - 4;
    const crc = (@as(u32, input[end]) << 24) |
        (@as(u32, input[end + 1]) << 16) |
        (@as(u32, input[end + 2]) << 8) | @as(u32, input[end + 3]);
    if (fields.crc32(input[0..end]) != crc) return error.IntegrityMismatch;
    var pos: usize = 3;
    const target = try readCount(input[0..end], &pos);
    if (output) |out| {
        if (out.len < target) return error.BufferTooSmall;
    }
    var written: usize = 0;
    while (written < target) {
        if (pos >= end) return error.Truncated;
        const tag = input[pos];
        pos += 1;
        const count = try readCount(input[0..end], &pos);
        if (count == 0 or count > MAX_BLOCK_WORDS or count > target - written)
            return error.InvalidBlock;
        if (tag == 0) {
            const map_len = (count + 1) / 2;
            if (map_len > end - pos) return error.Truncated;
            const map = input[pos .. pos + map_len];
            pos += map_len;
            if (count % 2 != 0 and (map[map_len - 1] & 0x0f) != 0)
                return error.NonCanonical;
            var nbits: usize = 0;
            for (0..count) |i| {
                const pair = map[i / 2];
                const width: u8 = if (i % 2 == 0) pair >> 4 else pair & 0x0f;
                if (width == 0 or width > 9) return error.InvalidWidth;
                nbits += width;
            }
            const bytes = (nbits + 7) / 8;
            if (bytes > end - pos) return error.Truncated;
            const payload = input[pos .. pos + bytes];
            if (nbits % 8 != 0) {
                const unused: u3 = @intCast(8 - nbits % 8);
                const mask: u8 = (@as(u8, 1) << unused) - 1;
                if ((payload[payload.len - 1] & mask) != 0)
                    return error.NonCanonical;
            }
            var bit: usize = 0;
            for (0..count) |i| {
                const pair = map[i / 2];
                const width: u8 = if (i % 2 == 0) pair >> 4 else pair & 0x0f;
                var bits: u16 = 0;
                for (0..width) |_| {
                    bits = (bits << 1) | packedBit(payload, bit);
                    bit += 1;
                }
                if (output) |out| out[written + i] = .{ .width = width, .bits = bits };
            }
            pos += bytes;
        } else if (tag == 1) {
            if (pos >= end) return error.Truncated;
            const width = input[pos];
            pos += 1;
            if (width == 0 or width > 9) return error.InvalidWidth;
            const bytes = (@as(usize, width) + 7) / 8;
            if (bytes > end - pos) return error.Truncated;
            const payload = input[pos .. pos + bytes];
            const unused: u3 = @intCast(bytes * 8 - width);
            if (unused > 0) {
                const mask: u8 = (@as(u8, 1) << unused) - 1;
                if ((payload[payload.len - 1] & mask) != 0)
                    return error.NonCanonical;
            }
            var bits: u16 = 0;
            for (0..width) |i| bits = (bits << 1) | packedBit(payload, i);
            if (output) |out| {
                for (0..count) |i| out[written + i] = .{ .width = width, .bits = bits };
            }
            pos += bytes;
        } else return error.InvalidBlock;
        written += count;
    }
    if (pos != end) return error.NonCanonical;
    return target;
}

/// Physical preflight only: exact counts/bytes, CRC, block bounds/padding.
/// No SENS D2 admission or canonical DP re-encode.
pub fn inspect(input: []const u8) Error!usize {
    return parse(input, null);
}

/// Byte ranges must be disjoint. Encoding a word into the original frame
/// while still decoding that same frame would invalidate the CRC preflight.
fn slicesOverlap(left: []const u8, right: []const u8) bool {
    if (left.len == 0 or right.len == 0) return false;
    const a = @intFromPtr(left.ptr);
    const b = @intFromPtr(right.ptr);
    // Compare distances, never potentially overflowing pointer endpoints.
    return if (a <= b) b - a < left.len else a - b < right.len;
}

/// Preflight first; malformed or aliased input cannot mutate caller's buffer.
pub fn unpack(input: []const u8, output: []Word) Error!usize {
    // Reject both full and partial aliases before reading or writing.
    if (slicesOverlap(input, std.mem.sliceAsBytes(output)))
        return error.OverlappingBuffers;
    const count = try inspect(input);
    if (output.len < count) return error.BufferTooSmall;
    return parse(input, output);
}

fn framed(body: []const u8, buf: []u8) []const u8 {
    std.debug.assert(buf.len == body.len + 4);
    @memcpy(buf[0..body.len], body);
    const crc = fields.crc32(body);
    buf[body.len] = @intCast(crc >> 24);
    buf[body.len + 1] = @intCast((crc >> 16) & 0xff);
    buf[body.len + 2] = @intCast((crc >> 8) & 0xff);
    buf[body.len + 3] = @intCast(crc & 0xff);
    return buf;
}
