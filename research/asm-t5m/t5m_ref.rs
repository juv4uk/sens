//! T5M (ДЕФОЛТНИЙ) Rust-еталон з C-ABI. 5 трітів → 1 байт (3^5=243<256).
//! #![no_std], щоб об'єкт не тягнув std/_Unwind_*.
//! Збірка: rustc -O --edition 2021 --crate-type lib --emit obj -C panic=abort -o rust_t5m_ref.o t5m_ref.rs
#![no_std]
#[no_mangle]
pub unsafe extern "C" fn rust_t5m_pack(trits: *const u8, n: usize, out: *mut u8) -> usize {
    let mut oi: usize = 0;
    let mut i: usize = 0;
    while i < n {
        let mut v: u32 = 0;
        let mut j: usize = 0;
        while j < 5 {
            v = v * 3 + *trits.add(i + j) as u32;
            j += 1;
        }
        *out.add(oi) = v as u8;
        oi += 1;
        i += 5;
    }
    oi
}
#[no_mangle]
pub unsafe extern "C" fn rust_t5m_unpack(bytes: *const u8, n: usize, trits: *mut u8) {
    let mut g: usize = 0;
    while g < n {
        let mut x: u32 = *bytes.add(g) as u32;
        let mut j: usize = 5;
        while j > 0 {
            j -= 1;
            *trits.add(g * 5 + j) = (x % 3) as u8;
            x /= 3;
        }
        g += 1;
    }
}
