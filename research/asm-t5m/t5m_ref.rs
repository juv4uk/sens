//! T5M-3 Rust-еталон з C-ABI для спільного харнеса (asm + Zig + C + Rust).
//! Дзеркалить research/zig-codecs/t5m3.zig і lib/core4.lisp т5м-у-байти / т5м-з-байтів.
//! 15 тритів → 3 байти little-endian; value = value*3 + trit.
//!
//! #![no_std] — навмисно: щоб об'єкт не тягнув std з розкруткою стека
//! (інакше zig-лінкувальник не знаходить _Unwind_*). Лише сирі вказівники.
//! Збірка: rustc -O --edition 2021 --crate-type lib --emit obj -C panic=abort \
//!           -o rust_t5m_ref.o t5m_ref.rs
#![no_std]

#[no_mangle]
pub unsafe extern "C" fn rust_t5m_pack(trits: *const u8, n: usize, out: *mut u8) -> usize {
    let mut oi: usize = 0;
    let mut i: usize = 0;
    while i < n {
        let mut v: u32 = 0;
        let mut j: usize = 0;
        while j < 15 {
            v = v * 3 + *trits.add(i + j) as u32;
            j += 1;
        }
        *out.add(oi) = v as u8;
        *out.add(oi + 1) = (v >> 8) as u8;
        *out.add(oi + 2) = (v >> 16) as u8;
        oi += 3;
        i += 15;
    }
    oi
}

#[no_mangle]
pub unsafe extern "C" fn rust_t5m_unpack(bytes: *const u8, n_groups: usize, trits: *mut u8) {
    let mut g: usize = 0;
    while g < n_groups {
        let mut v: u32 = *bytes.add(g * 3) as u32
            | ((*bytes.add(g * 3 + 1) as u32) << 8)
            | ((*bytes.add(g * 3 + 2) as u32) << 16);
        let mut j: usize = 15;
        while j > 0 {
            j -= 1;
            *trits.add(g * 15 + j) = (v % 3) as u8;
            v /= 3;
        }
        g += 1;
    }
}
