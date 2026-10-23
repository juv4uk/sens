//! T5M (ДЕФОЛТНИЙ) Zig-реалізація з C-ABI. 5 трітів → 1 байт (3^5=243<256).
//! Дзеркалить lib/core4.lisp (трітів-у-байті 5) і scripts/sens_t5_t5m_codec.py.
export fn zig_t5m_pack(trits: [*]const u8, n: usize, out: [*]u8) usize {
    var o: usize = 0;
    var i: usize = 0;
    while (i < n) : (i += 5) {
        var v: u32 = 0;
        var j: usize = 0;
        while (j < 5) : (j += 1) v = v * 3 + trits[i + j];
        out[o] = @truncate(v);
        o += 1;
    }
    return o;
}
export fn zig_t5m_unpack(bytes: [*]const u8, n: usize, trits: [*]u8) void {
    var g: usize = 0;
    while (g < n) : (g += 1) {
        var x: u32 = bytes[g];
        var j: usize = 5;
        while (j > 0) {
            j -= 1;
            trits[g * 5 + j] = @truncate(x % 3);
            x /= 3;
        }
    }
}
