//! Freestanding envelope mechanics: no I/O, OS, libc, heap, or SENS semantic law.
//! Widths/version/profile and EOF rule belong to SENS, not this Zig module.
const std = @import("std");
pub const Field = struct { width: u8, bits: u64 };
pub const Block = struct { offset_bytes: u32, length_bytes: u32 };
pub const Error = error{
    EmptySchema, InvalidWidth, FieldOverflow, LengthOverflow,
    LengthMismatch, NonCanonicalTail, InvalidBlockMap, IntegrityMismatch,
    OverlappingBuffers,
};
fn bytesForBits(bits: usize) usize {
    return bits / 8 + @as(usize, @intFromBool(bits % 8 != 0));
}
// Caller-owned packed_bytes bytes must not overlap the structured source/destination.
// Compare address differences, not sums, to avoid pointer-range overflow.
fn overlaps(source: []const u8, destination: []const u8) bool {
    if (source.len == 0 or destination.len == 0) return false;
    const a = @intFromPtr(source.ptr);
    const b = @intFromPtr(destination.ptr);
    return if (a <= b) b - a < source.len else a - b < destination.len;
}
pub fn measure(fields: []const Field) Error!usize {
    if (fields.len == 0) return error.EmptySchema;
    var bits: usize = 0;
    for (fields) |field| {
        if (field.width == 0 or field.width > 64) return error.InvalidWidth;
        if (field.width < 64 and field.bits >> @as(u6, @intCast(field.width)) != 0)
            return error.FieldOverflow;
        if (field.width > ~@as(usize, 0) - bits) return error.LengthOverflow;
        bits += field.width;
    }
    return bits;
}
/// Exact MSB-first binary metadata; out has no implicit extra bytes.
pub fn pack(out: []u8, fields: []const Field) Error!usize {
    const size = try measure(fields);
    if (out.len != bytesForBits(size)) return error.LengthMismatch;
    // Without this check @memset can destroy input field widths or payloads.
    if (overlaps(std.mem.sliceAsBytes(fields), out)) return error.OverlappingBuffers;
    @memset(out, 0);
    var pos: usize = 0;
    for (fields) |field| {
        var n: usize = field.width;
        while (n > 0) {
            n -= 1;
            const bit: u8 = @intCast((field.bits >> @as(u6, @intCast(n))) & 1);
            out[pos / 8] |= bit << @as(u3, @intCast(7 - pos % 8));
            pos += 1;
        }
    }
    return size;
}
/// Read only with declared field widths + exact meaningful bit length.
pub fn unpack(raw: []const u8, bit_len: usize, widths: []const u8, dst: []u64) Error!void {
    if (widths.len == 0) return error.EmptySchema;
    if (widths.len != dst.len) return error.LengthMismatch;
    var count: usize = 0;
    for (widths) |width| {
        if (width == 0 or width > 64) return error.InvalidWidth;
        if (width > ~@as(usize, 0) - count) return error.LengthOverflow;
        count += width;
    }
    if (count != bit_len or raw.len != bytesForBits(count)) return error.LengthMismatch;
    if (count % 8 != 0) {
        const unused: u3 = @intCast(8 - count % 8);
        const mask: u8 = (@as(u8, 1) << unused) - 1;
        if ((raw[raw.len - 1] & mask) != 0) return error.NonCanonicalTail;
    }
    // Decoding overlapping output words could overwrite unread source bits.
    if (overlaps(raw, std.mem.sliceAsBytes(dst)) or
        overlaps(widths, std.mem.sliceAsBytes(dst)))
        return error.OverlappingBuffers;
    var pos: usize = 0;
    for (widths, 0..) |width, i| {
        var word: u64 = 0;
        for (0..width) |_| {
            const bit: u64 = @intCast((raw[pos / 8] >> @as(u3, @intCast(7 - pos % 8))) & 1);
            word = (word << 1) | bit;
            pos += 1;
        }
        dst[i] = word;
    }
}
/// Validates explicit physical block boundaries; gaps, overlaps, trailers reject.
pub fn validateBlocks(size: usize, blocks: []const Block) Error!void {
    if (blocks.len == 0) {
        if (size == 0) return;
        return error.InvalidBlockMap;
    }
    var offset: usize = 0;
    for (blocks) |block| {
        if (block.offset_bytes != offset or block.length_bytes == 0 or
            block.length_bytes > size - offset) return error.InvalidBlockMap;
        offset += block.length_bytes;
    }
    if (offset != size) return error.InvalidBlockMap;
}
/// IEEE CRC32 check of physical bytes. Corruption detection, not authentication.
pub fn crc32(data: []const u8) u32 {
    var crc: u32 = 0xffffffff;
    for (data) |b| {
        crc ^= @as(u32, b);
        for (0..8) |_| crc = (crc >> 1) ^ (0xedb88320 & (0 -% (crc & 1)));
    }
    return ~crc;
}
pub fn verifyCrc32(data: []const u8, expected: u32) Error!void {
    if (crc32(data) != expected) return error.IntegrityMismatch;
}
// This envelope stores physical MSB-first bits, not a resident/function ID.
// The calling SENS law must supply the exact widths and meaningful bit length;
// Zig must not infer a domain from the bytes or grant executable authority.
// Zig owns wire integrity, never the meaning of a SENS function.
