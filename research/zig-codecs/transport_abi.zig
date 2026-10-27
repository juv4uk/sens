//! Single caller-owned transport ABI v2; no padded host structs cross the boundary.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const t5m = @import("t5m.zig");
const f3c = @import("f3c/f3c.zig");
const e1 = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");
const raw_bitpack = @import("transport/raw_bitpack.zig");
// ABI v2 uses caller-owned byte triplets; no padded host structs cross the boundary.
/// ABI v2: the preferred boundary uses explicit [width, payload-MSB, payload-LSB]
/// per word, NOT a C struct with host-dependent padding/alignment/endianness.
/// This triplet stream is an in-process FFI representation, NEVER .sens wire.
pub export fn sens_zig_codec_abi_version() u32 {
    return 2;
}

/// Dense raw MSB-first binary packing for exact-width words.
/// Input records are fixed [width:u8][value:u64 big-endian] triples of bytes
/// expanded to nine bytes per word. This is an in-process ABI, not wire data.
/// capacity=0 queries exact byte count; -1 rejects malformed records; -2 is
/// insufficient output capacity. No output bytes are written on either error.
pub export fn sens_zig_bitpack_fields(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    return raw_bitpack.packFields(src, byte_len, dst, capacity);
}

/// Default physical transport ABI: T5M stores five trits in one byte.
/// This narrow BE3 host adapter carries current W1..W9 source words only;
/// the physical T5M codec itself preserves arbitrary exact widths.
pub export fn sens_zig_t5m_validate(src: [*]const u8, len: usize) c_int {
    if (len == 0 or len > t5m.MAX_PHYSICAL_BYTES) return -1;
    var decoded = t5m.decode(std.heap.page_allocator, src[0..len]) catch return -1;
    defer decoded.deinit(std.heap.page_allocator);
    return 0;
}

pub export fn sens_zig_t5m_encode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len % 3 != 0) return -1;
    const count = byte_len / 3;
    if (count > t5m.MAX_PHYSICAL_BYTES * 5) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity))) return -1;

    const words = std.heap.page_allocator.alloc(t5m.Word, count) catch return -1;
    defer std.heap.page_allocator.free(words);
    var storage_len: usize = 0;
    for (0..count) |i| {
        const at = i * 3;
        const width: usize = src[at];
        if (width == 0 or width > 9) return -1;
        storage_len += width;
    }
    const storage = std.heap.page_allocator.alloc(u8, storage_len) catch return -1;
    defer std.heap.page_allocator.free(storage);
    var cursor: usize = 0;
    for (0..count) |i| {
        const at = i * 3;
        const width: usize = src[at];
        const value = (@as(u16, src[at + 1]) << 8) | src[at + 2];
        if (width < 16 and value >= (@as(u16, 1) << @as(u4, @intCast(width)))) return -1;
        for (0..width) |bit| {
            storage[cursor + bit] = if ((value >> @as(u4, @intCast(width - bit - 1))) & 1 == 0) '0' else '1';
        }
        words[i] = .{ .width = width, .bits = storage[cursor .. cursor + width] };
        cursor += width;
    }
    const physical = t5m.encode(std.heap.page_allocator, words) catch return -1;
    defer std.heap.page_allocator.free(physical);
    if (physical.len > capacity) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}

pub export fn sens_zig_t5m_decode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len > t5m.MAX_PHYSICAL_BYTES) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity))) return -1;
    var decoded = t5m.decode(std.heap.page_allocator, src[0..byte_len]) catch return -1;
    defer decoded.deinit(std.heap.page_allocator);
    const need = decoded.words.len * 3;
    // Спершу валідність всього BE3: -1 має перевагу над браком місткості.
    for (decoded.words) |word| {
        if (word.width > 9) return -1;
    }
    if (need > capacity) return -2;
    for (decoded.words, 0..) |word, i| {
        var value: u16 = 0;
        for (word.bits) |bit| value = (value << 1) | @as(u16, bit - '0');
        const at = i * 3;
        dst[at] = @intCast(word.width);
        dst[at + 1] = @intCast(value >> 8);
        dst[at + 2] = @truncate(value);
    }
    return @intCast(need);
}

/// Точні записи T5M: u32 big-endian ширини, далі width байтів зі значенням 0/1.
/// Це фізичний ABI; доменна identity та викличність тут не визначаються.
pub export fn sens_zig_t5m_encode_words(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len < 5 or byte_len > t5m.MAX_PHYSICAL_BYTES * 5) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity))) return -1;

    var count: usize = 0;
    var total_bits: usize = 0;
    var offset: usize = 0;
    while (offset < byte_len) {
        if (byte_len - offset < 4) return -1;
        const width_u32 = (@as(u32, src[offset]) << 24) |
            (@as(u32, src[offset + 1]) << 16) |
            (@as(u32, src[offset + 2]) << 8) |
            @as(u32, src[offset + 3]);
        if (width_u32 == 0) return -1;
        const width: usize = @intCast(width_u32);
        offset += 4;
        if (width > byte_len - offset) return -1;
        for (src[offset .. offset + width]) |bit| if (bit > 1) return -1;
        total_bits = std.math.add(usize, total_bits, width) catch return -1;
        count = std.math.add(usize, count, 1) catch return -1;
        offset += width;
    }
    if (count == 0 or total_bits > t5m.MAX_PHYSICAL_BYTES * 5) return -1;
    const words = std.heap.page_allocator.alloc(t5m.Word, count) catch return -1;
    defer std.heap.page_allocator.free(words);
    const storage = std.heap.page_allocator.alloc(u8, total_bits) catch return -1;
    defer std.heap.page_allocator.free(storage);
    offset = 0;
    var cursor: usize = 0;
    for (0..count) |i| {
        const width_u32 = (@as(u32, src[offset]) << 24) |
            (@as(u32, src[offset + 1]) << 16) |
            (@as(u32, src[offset + 2]) << 8) |
            @as(u32, src[offset + 3]);
        const width: usize = @intCast(width_u32);
        offset += 4;
        const bits = storage[cursor .. cursor + width];
        for (src[offset .. offset + width], 0..) |bit, bit_index| {
            bits[bit_index] = if (bit == 0) '0' else '1';
        }
        words[i] = .{ .width = width, .bits = storage[cursor .. cursor + width] };
        cursor += width;
        offset += width;
    }
    const physical = t5m.encode(std.heap.page_allocator, words) catch return -1;
    defer std.heap.page_allocator.free(physical);
    if (physical.len > capacity) return -2;
    @memcpy(dst[0..physical.len], physical);
    return @intCast(physical.len);
}

pub export fn sens_zig_t5m_decode_words(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len > t5m.MAX_PHYSICAL_BYTES) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity))) return -1;
    var decoded = t5m.decode(std.heap.page_allocator, src[0..byte_len]) catch return -1;
    defer decoded.deinit(std.heap.page_allocator);
    var need: usize = 0;
    for (decoded.words) |word| {
        const record_len = std.math.add(usize, 4, word.width) catch return -1;
        need = std.math.add(usize, need, record_len) catch return -1;
        if (word.width > std.math.maxInt(u32)) return -1;
    }
    if (need > capacity) return -2;
    var offset: usize = 0;
    for (decoded.words) |word| {
        const width: u32 = @intCast(word.width);
        dst[offset] = @truncate(width >> 24);
        dst[offset + 1] = @truncate(width >> 16);
        dst[offset + 2] = @truncate(width >> 8);
        dst[offset + 3] = @truncate(width);
        offset += 4;
        for (word.bits) |bit| {
            dst[offset] = bit - '0';
            offset += 1;
        }
    }
    return @intCast(need);
}

pub export fn sens_zig_t5_validate(src: [*]const u8, len: usize) c_int {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    t5.validatePhysical(src[0..len]) catch return -1;
    return 0;
}

/// Separate D1..D10 physical COORDINATE profile for any C-compatible host.
/// A 10-bit word remains opaque data: this does not grant SENS callability.
/// The ordinary sens_zig_t5_validate and BE3 execution routes stay <= D9.
/// ABI v2 addition: same caller-owned pointer/length and 0/-1 result contract.
pub export fn sens_zig_t5_validate_coordinates(src: [*]const u8, len: usize) c_int {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    t5.validateCoordinatesPhysical(src[0..len]) catch return -1;
    return 0;
}
pub export fn sens_zig_t5_encode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len % 3 != 0) return -1;
    const count = byte_len / 3;
    if (count > t5.MAX_PHYSICAL_BYTES * 5) return -1;
    const written = t5.encodeTripletsInto(dst[0..capacity], src[0..byte_len]) catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
}

pub export fn sens_zig_t5_decode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len > t5.MAX_PHYSICAL_BYTES) return -1;
    const written = t5.decodeTripletsInto(dst[0..capacity], src[0..byte_len]) catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
}

pub export fn sens_zig_e1_encode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len % 3 != 0) return -1;
    const count = byte_len / 3;
    if (count > e1.MAX_WORDS) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity)))
        return -1;
    var words: [e1.MAX_WORDS]e1.Word = undefined;
    var scratch: [e1.MAX_WORDS + 1]e1_writer.Step = undefined;
    for (0..count) |i| {
        const at = i * 3;
        const width = src[at];
        const bits = (@as(u16, src[at + 1]) << 8) | @as(u16, src[at + 2]);
        if (width == 0 or width > 9) return -1;
        if (bits >= (@as(u16, 1) << @as(u4, @intCast(width)))) return -1;
        words[i] = .{ .width = width, .bits = bits };
    }
    const size = e1_writer.encode(words[0..count], dst[0..capacity], scratch[0 .. count + 1]) catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(size);
}

/// Decode canonical E1 physical carrier to BE3 [width, MSB, LSB] triplets.
/// -1 invalid/noncanonical/alias; -2 BE3 output too small.
pub export fn sens_zig_e1_decode_be3(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    if (byte_len == 0 or byte_len > e1.MAX_FILE_BYTES) return -1;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity)))
        return -1;
    const max_frame: usize = 64 * 1024;
    if (byte_len > max_frame) return -1;
    var words: [e1.MAX_WORDS]e1.Word = undefined;
    var scratch: [e1.MAX_WORDS + 1]e1_writer.Step = undefined;
    var replay: [max_frame]u8 = undefined;
    const count = e1_writer.inspectCanonical(
        src[0..byte_len],
        words[0..],
        scratch[0..],
        replay[0..byte_len],
    ) catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    const need = count * 3;
    if (need > capacity) return -2;
    for (0..count) |i| {
        const w = words[i];
        if (w.width == 0 or w.width > 9) return -1;
        if (w.bits >= (@as(u16, 1) << @as(u4, @intCast(w.width)))) return -1;
        const at = i * 3;
        dst[at] = w.width;
        dst[at + 1] = @intCast(w.bits >> 8);
        dst[at + 2] = @intCast(w.bits & 0xff);
    }
    return @intCast(need);
}

pub export fn sens_zig_f3c_pack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len == 0 or len > f3c.MAX_TINY_T5_BYTES) return -1;
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    const written = (f3c.encodeInto(src[0..len], dst[0..cap], &scratch) catch |err| return if (err == error.BufferTooSmall) -2 else -1) orelse return -3;
    return @intCast(written);
}
pub export fn sens_zig_f3c_unpack(src: [*]const u8, len: usize, dst: [*]u8, cap: usize) isize {
    if (len < 2 or len >= f3c.MAX_TINY_T5_BYTES) return -1;
    var scratch: [f3c.ABI_SCRATCH_BYTES]u8 = undefined;
    const written = f3c.decodeInto(src[0..len], dst[0..cap], &scratch) catch |err| return if (err == error.BufferTooSmall) -2 else -1;
    return @intCast(written);
}
// Перевірка Zig ABI: версія та межі фізичного T5M-входу.
// Архітектурну відсутність Rust-обходу перевіряють окремі source-route guards;
// ці runtime-assertions самі по собі її не доводять.
