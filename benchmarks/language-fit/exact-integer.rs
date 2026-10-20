//! Контрольний бенчмарк ТОЧНОЇ арифметики: реальні ASM-ядра SENS проти Rust.
//! Це не семантичний оракул і не доказ загальної переваги асемблера.
//! Джерело ASM спільне з production (ніяких копій машинних інструкцій).
#[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
compile_error!("Точний ASM бенчмарк призначено для x86-64 Linux");

use std::hint::black_box;
use std::time::Instant;

core::arch::global_asm!(
    include_str!("../../crates/sens/src/machine_math_skylake.S"),
    options(att_syntax)
);

unsafe extern "C" {
    fn sens_i24_add_exact(a: i64, b: i64) -> i64;
    fn sens_i48_mul_exact(a: i64, b: i64, high: *mut i64) -> i64;
    fn sens_i96_add_exact(a_lo: u64, a_hi: i64, b_lo: u64, b_hi: i64, high: *mut i64) -> u64;
}

#[inline(never)]
fn rust_d24_add(a: i128, b: i128) -> i128 {
    (a as i64 + b as i64) as i128
}

#[inline(never)]
fn rust_d48_mul(a: i128, b: i128) -> i128 {
    (a as i64 as i128) * (b as i64 as i128)
}

#[inline(never)]
fn rust_d96_add(a: i128, b: i128) -> i128 {
    a + b
}

#[inline(never)]
fn asm_d24_add(a: i128, b: i128) -> i128 {
    unsafe { sens_i24_add_exact(a as i64, b as i64) as i128 }
}

#[inline(never)]
fn asm_d48_mul(a: i128, b: i128) -> i128 {
    let mut high = 0_i64;
    let low = unsafe { sens_i48_mul_exact(a as i64, b as i64, &mut high) };
    (i128::from(high) << 64) | i128::from(low as u64)
}

#[inline(never)]
fn asm_d96_add(a: i128, b: i128) -> i128 {
    let mut high = 0_i64;
    let low = unsafe {
        sens_i96_add_exact(a as u64, (a >> 64) as i64,
                           b as u64, (b >> 64) as i64, &mut high)
    };
    (i128::from(high) << 64) | i128::from(low)
}

fn xorshift(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

fn signed_word(state: &mut u64, width: u32) -> i128 {
    let raw = if width == 96 {
        ((u128::from(xorshift(state)) << 32)
            | u128::from(xorshift(state) & 0xffff_ffff)) & ((1_u128 << 96) - 1)
    } else {
        u128::from(xorshift(state)) & ((1_u128 << width) - 1)
    };
    let shift = 128 - width;
    ((raw as i128) << shift) >> shift
}

fn inputs(width: u32) -> Vec<(i128, i128)> {
    let limit = 1_i128 << (width - 1);
    let boundary = [-limit, -limit + 1, -1, 0, 1, limit - 2, limit - 1];
    let mut values = Vec::with_capacity(4096 + boundary.len() * boundary.len());
    for &a in &boundary {
        for &b in &boundary {
            values.push((a,b));
        }
    }
    let mut seed = 0xf375_9cbe_2148_6ad0_u64;
    for _ in 0..4096 {
        values.push((signed_word(&mut seed, width), signed_word(&mut seed, width)));
    }
    values
}

fn median_per_operation(
    data: &[(i128,i128)],
    function: fn(i128, i128) -> i128,
) -> f64 {
    let mut samples = [0.0_f64; 5];
    for sample in &mut samples {
        let start = Instant::now();
        let mut check = 0_i128;
        for _ in 0..128 {
            for &(a,b) in data {
                // Однакова кількість реальних викликів та black_box
                // для обох реалізацій; введення-виведення поза виміром.
                let value = function(black_box(a), black_box(b));
                check = check.wrapping_add(black_box(value));
            }
        }
        black_box(check);
        *sample = start.elapsed().as_nanos() as f64 / (128 * data.len()) as f64;
    }
    samples.sort_by(|a,b| a.total_cmp(b));
    samples[2]
}

fn one_case(
    label: &str, width: u32, rust: fn(i128,i128)->i128, asm: fn(i128,i128)->i128,
) -> Result<(f64,f64), String> {
    let data = inputs(width);
    for &(a,b) in &data {
        let expected = rust(a,b);
        let actual = asm(a,b);
        if actual != expected {
            return Err(format!("{label}: невідповідність ASM: a={a}, b={b}, очікувано={expected}, отримано={actual}"));
        }
    }
    // Чергуємо Rust і ASM, щоб зменшити позиційний шум.
    black_box(median_per_operation(&data, rust));
    black_box(median_per_operation(&data, asm));
    let rust_ns = median_per_operation(&data, rust);
    let asm_ns = median_per_operation(&data, asm);
    Ok((rust_ns,asm_ns))
}

fn run() -> Result<(), String> {
    let cases: [(&str,u32,fn(i128,i128)->i128,fn(i128,i128)->i128);3] = [
        ("D24 ADD",24,rust_d24_add,asm_d24_add),
        ("D48 IMUL",48,rust_d48_mul,asm_d48_mul),
        ("D96 ADD",96,rust_d96_add,asm_d96_add),
    ];
    println!("## Точні цілі SENS: ASM проти Rust на поточному CPU");
    println!();
    println!("Механічні операції без витрат на доменний reader; 4145 пар, 128 повторів × 5 вимірів.");
    println!("Результат ASM перевірено на всіх входах до вимірювання; жодного f64 в арифметиці.");
    println!();
    println!("| Операція | Rust, нс/оп | ASM, нс/оп | Rust/ASM |");
    println!("|---|---:|---:|---:|");
    let mut short = Vec::new();
    for (name,width,rust,asm) in cases {
        let (rust_ns,asm_ns) = one_case(name,width,rust,asm)?;
        println!("| {name} | {rust_ns:.2} | {asm_ns:.2} | {:.2}× |",rust_ns/asm_ns);
        short.push(format!("{name}: Rust {rust_ns:.2} / ASM {asm_ns:.2} нс"));
    }
    println!();
    println!("**Без автоматичного переможця:** ABI-виклики та цілочисельні цикли — окрема метрика; не переносити висновок на D24+ семантику.");
    if std::env::var("GITHUB_ACTIONS").as_deref() == Ok("true") {
        println!("::notice title=SENS точна математика ASM::{}; parity=PASS; нс/оп, медіана 5 серій; без автоматичного вибору",
                 short.join("; "));
    }
    Ok(())
}

fn main() {
    if let Err(reason) = run() {
        eprintln!("::error title=SENS точна математика::{reason}");
        std::process::exit(1);
    }
}
