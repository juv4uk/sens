const raw_bitpack = @import("research/zig-codecs/transport/raw_bitpack.zig");

/// The wasm32 core needs only the raw exact-width packer. The full native
/// transport ABI (T5/T5M/F3C) is linked by native targets and remains separate.
pub export fn sens_zig_bitpack_fields(
    src: [*]const u8,
    byte_len: usize,
    dst: [*]u8,
    capacity: usize,
) isize {
    return raw_bitpack.packFields(src, byte_len, dst, capacity);
}
