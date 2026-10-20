// Ті самі вхідні дані та математичний підрахунок у Rust.
// Ітератори лишають реалізацію природною для мови.
const N: usize = 65536;
const ROUNDS: usize = 2048;

fn main() {
    let mut a: Vec<f64> = (0..N).map(|i| ((i % 97 + 1) as f64) * 0.001).collect();
    let b: Vec<f64> = (0..N).map(|i| ((i % 89 + 1) as f64) * 0.002).collect();
    let mut total = 0.0_f64;
    for round in 0..ROUNDS {
        a[round % N] += 1.0e-9;
        let dot: f64 = a.iter().zip(b.iter()).map(|(x, y)| *x * *y).sum();
        total += dot;
    }
    println!("{total:.16e}");
}
