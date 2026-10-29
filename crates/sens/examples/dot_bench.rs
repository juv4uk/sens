// Бенчмарк машинного шару SENS: скалярний (SSE2) проти AVX2/FMA.
//
// Що міряється: `machine_math::dot_f64` на однаковому масиві.
// Це порівняння ВСЕРЕДИНІ самої мови: та сама задача, та сама семантика,
// різниця лише в інструкціях процесора. Тому воно не залежить від того,
// чи коректне міжмовне порівняння — і не потребує завершення Lazarus.
//
// Енергія тут НЕ міряється: RAPL є в wsm-lazarus/scripts/energy/measure.py.
// Цей файл дає лише час і контрольну суму, щоб той вимірювач мав що міряти.
//
// Запуск: cargo run --release --example dot_bench -- <n> <повторів>

use std::time::Instant;

fn main() {
    let mut args = std::env::args().skip(1);
    let n: usize = args.next().and_then(|s| s.parse().ok()).unwrap_or(1 << 20);
    let reps: usize = args.next().and_then(|s| s.parse().ok()).unwrap_or(32);

    // Детермінований вхід: без RNG, щоб прогін був відтворюваний.
    let a: Vec<f64> = (0..n).map(|i| (i % 251) as f64 * 0.5).collect();
    let b: Vec<f64> = (0..n).map(|i| (i % 253) as f64 * 0.25).collect();

    // Прогрів: перший виклик не має потрапити в замір.
    let warm = sens::machine_math::dot_f64(&a, &b).expect("dot_f64 на прогріві");
    println!("BACKEND {:?}", sens::machine_math::backend());
    println!("WARM {warm}");

    let start = Instant::now();
    let mut acc = 0.0f64;
    for _ in 0..reps {
        acc += sens::machine_math::dot_f64(&a, &b).expect("dot_f64 у циклі");
    }
    let elapsed = start.elapsed();

    println!("N {n}");
    println!("REPS {reps}");
    println!("SUM {acc}");
    println!("WALL_NS {}", elapsed.as_nanos());
    println!("DOT_OK");
}
