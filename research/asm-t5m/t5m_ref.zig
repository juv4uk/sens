//! T5M-3 Zig-реалізація з C-ABI для спільного харнеса (asm + Zig + C).
//! Дзеркалить research/zig-codecs/t5m3.zig і lib/core4.lisp т5м-у-байти / т5м-з-байтів.
//! 15 тритів → 3 байти little-endian; value = value*3 + trit.

export fn zig_t5m_pack(trits: [*]const u8, n: usize, out: [*]u8) usize {
    var o: usize = 0;
    var i: usize = 0;
    while (i < n) : (i += 15) {
        var v: u32 = 0;
        var j: usize = 0;
        while (j < 15) : (j += 1) v = v * 3 + trits[i + j];
        out[o] = @truncate(v);
        out[o + 1] = @truncate(v >> 8);
        out[o + 2] = @truncate(v >> 16);
        o += 3;
    }
    return o;
}

export fn zig_t5m_unpack(bytes: [*]const u8, n_groups: usize, trits: [*]u8) void {
    var g: usize = 0;
    while (g < n_groups) : (g += 1) {
        const v: u32 = @as(u32, bytes[g * 3]) |
            (@as(u32, bytes[g * 3 + 1]) << 8) |
            (@as(u32, bytes[g * 3 + 2]) << 16);
        var x = v;
        var j: usize = 15;
        while (j > 0) {
            j -= 1;
            trits[g * 15 + j] = @truncate(x % 3);
            x /= 3;
        }
    }
}
