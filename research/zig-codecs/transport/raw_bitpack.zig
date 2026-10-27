const std = @import("std");
const fields = @import("fields.zig");

/// Canonical raw MSB-first bit packing shared by native and wasm32 ABI roots.
/// Each caller-owned record is [width:u8][value:u64 big-endian].
/// Returns byte length, -1 for invalid input, -2 for short destination.
/// capacity=0 queries size and never touches destination memory.
pub fn packFields(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    const record_size: usize = 9;
    if (byte_len == 0 or byte_len % record_size != 0) return -1;
    const count = byte_len / record_size;
    const source_addr = @intFromPtr(src);
    const dest_addr = @intFromPtr(dst);
    if (capacity > 0 and
        ((source_addr <= dest_addr and dest_addr - source_addr < byte_len) or
            (dest_addr < source_addr and source_addr - dest_addr < capacity))) return -1;

    const values = std.heap.page_allocator.alloc(fields.Field, count) catch return -1;
    defer std.heap.page_allocator.free(values);
    var offset: usize = 0;
    for (values) |*field| {
        const width = src[offset];
        if (width == 0 or width > 64) return -1;
        var value: u64 = 0;
        for (src[offset + 1 .. offset + record_size]) |byte| {
            value = (value << 8) | @as(u64, byte);
        }
        field.* = .{ .width = width, .bits = value };
        offset += record_size;
    }

    const bit_len = fields.measure(values) catch return -1;
    const required = bit_len / 8 + @as(usize, @intFromBool(bit_len % 8 != 0));
    const max_result_bytes: usize = @intCast(std.math.maxInt(isize));
    if (required > max_result_bytes) return -1;
    if (capacity == 0) return @intCast(required);
    if (capacity < required) return -2;
    const written = fields.pack(dst[0..required], values) catch return -1;
    if (written != bit_len) return -1;
    return @intCast(required);
}

