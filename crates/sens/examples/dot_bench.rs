// Бенчмарк машинного шару SENS: sens_dot_scalar (SSE2) проти sens_dot_avx2 (AVX2/FMA).
//
// ЗНАЙДЕНА ПРОГАЛИНА: у crates/sens/src/machine_math.rs оголошено ЛИШЕ
// `sens_dot_avx2`. Символ `sens_dot_scalar` експортований у
// machine_math_skylake.S (.globl sens_dot_scalar), але в Rust не підключений,
// тому скалярний шлях виконується чистим Rust-фолдом (scalar_dot), а не
// асемблером. Це не помилка семантики, але означає, що порівняння
// «асемблер SSE2 проти асемблера AVX2» досі НЕ відбувалось.
//
// Тут обидва викликаються напряму через власний extern-блок, щоб
// порівняння було саме між двома асемблерними шляхами.
//
// Запуск: cargo run --release --example dot_bench -- <n> <повторів>

use std::time::Instant;

unsafe extern "C" {
    fn sens_dot_scalar(a: *const f64, b: *const f64, n: usize) -> f64;
    fn sens_dot_avx2(a: *const f64, b: *const f64, n: usize) -> f64;
}

fn time<F: FnMut() -> f64>(reps: usize, mut f: F) -> (u128, f64) {
    let start = Instant::now();
    let mut acc = 0.0f64;
    for _ in 0..reps {
        acc += f();
    }
    (start.elapsed().as_nanos(), acc)
}

fn main() {
    let mut args = std::env::args().skip(1);
    let n: usize = args.next().and_then(|s| s.parse().ok()).unwrap_or(1 << 20);
    let reps: usize = args.next().and_then(|s| s.parse().ok()).unwrap_or(32);

    // Детермінований вхід: без RNG, щоб прогін був відтворюваний.
    let a: Vec<f64> = (0..n).map(|i| (i % 251) as f64 * 0.5).collect();
    let b: Vec<f64> = (0..n).map(|i| (i % 253) as f64 * 0.25).collect();

    println!("BACKEND {:?}", sens::machine_math::backend());
    println!("N {n}");
    println!("REPS {reps}");

    // Прогрів обох шляхів, щоб перший виклик не потрапив у замір.
    let w1 = unsafe { sens_dot_scalar(a.as_ptr(), b.as_ptr(), n) };
    let w2 = unsafe { sens_dot_avx2(a.as_ptr(), b.as_ptr(), n) };
    println!("WARM_SCALAR {w1}");
    println!("WARM_AVX2 {w2}");

    let (ns_scalar, sum_scalar) =
        time(reps, || unsafe { sens_dot_scalar(a.as_ptr(), b.as_ptr(), n) });
    let (ns_avx2, sum_avx2) = time(reps, || unsafe { sens_dot_avx2(a.as_ptr(), b.as_ptr(), n) });

    println!("SCALAR_WALL_NS {ns_scalar}");
    println!("AVX2_WALL_NS {ns_avx2}");
    println!("SCALAR_SUM {sum_scalar}");
    println!("AVX2_SUM {sum_avx2}");

    // Співвідношення: >1 означає, що AVX2 швидший.
    if ns_avx2 > 0 {
        println!("RATIO_SCALAR_OVER_AVX2 {:.4}", ns_scalar as f64 / ns_avx2 as f64);
    }

    // Результати мусять збігатися з точністю до похибки накопичення:
    // AVX2 має 4 акумулятори, тому порядок додавання інший.
    let diff = (sum_scalar - sum_avx2).abs();
    let scale = sum_scalar.abs().max(1.0);
    if diff / scale > 1e-9 {
        println!("SUM_MISMATCH diff={diff} scale={scale}");
        std::process::exit(4);
    }
    println!("DOT_OK");
}
