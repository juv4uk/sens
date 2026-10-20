//! T5M-3 Rust-еталон з C-ABI для спільного харнеса (asm + Zig + C + Rust).
//! Дзеркалить research/zig-codecs/t5m3.zig і lib/core4.lisp т5м-у-байти / т5м-з-байтів.
//! 15 тритів → 3 байти little-endian; value = value*3 + trit.
//! Збірка: rustc -O --edition 2021 --crate-type staticlib t5m_ref.rs -o librust_t5m_ref.a

#[no_mangle]
pub extern "C" fn rust_t5m_pack(trits: *const u8, n: usize, out: *mut u8) -> usize {
    let t = unsafe { std::slice::from_raw_parts(trits, n) };
    let o = unsafe { std::slice::from_raw_parts_mut(out, n / 15 * 3) };
    let mut oi = 0usize;
    let mut i = 0usize;
    while i < n {
        let mut v: u32 = 0;
        for j in 0..15 {
            v = v * 3 + t[i + j] as u32;
        }
        o[oi] = v as u8;
        o[oi + 1] = (v >> 8) as u8;
        o[oi + 2] = (v >> 16) as u8;
        oi += 3;
        i += 15;
    }
    oi
}

#[no_mangle]
pub extern "C" fn rust_t5m_unpack(bytes: *const u8, n_groups: usize, trits: *mut u8) {
    let b = unsafe { std::slice::from_raw_parts(bytes, n_groups * 3) };
    let t = unsafe { std::slice::from_raw_parts_mut(trits, n_groups * 15) };
    for g in 0..n_groups {
        let mut v: u32 =
            b[g * 3] as u32 | ((b[g * 3 + 1] as u32) << 8) | ((b[g * 3 + 2] as u32) << 16);
        for j in (0..15).rev() {
            t[g * 15 + j] = (v % 3) as u8;
            v /= 3;
        }
    }
}
