// d11-families: ті самі три операції, що в SENS-бенчмарку benchmarks/d11-families.lisp,
// але нативно Rust-ом. Мета — чесне порівняння «наша мова проти хоста».
// Операції: відбір за предикатом, пошук першого запису в асоціаціях, лічба кратностей.
// Вивід: p50/p90 у мкс на N повторів — як у нативному SENS-кроці CI.
use std::time::Instant;

fn filtr(xs: &[i64], p: i64) -> Vec<i64> {
    xs.iter().copied().filter(|&x| x == p).collect()
}
fn alist_lookup(k: i64, xs: &[(i64, i64)]) -> Option<(i64, i64)> {
    xs.iter().copied().find(|&(key, _)| key == k)
}
fn freq(xs: &[i64]) -> Vec<(i64, usize)> {
    let mut out: Vec<(i64, usize)> = Vec::new();
    for &x in xs {
        if let Some(e) = out.iter_mut().find(|(key, _)| *key == x) {
            e.1 += 1;
        } else {
            out.push((x, 1));
        }
    }
    out
}
fn once() -> usize {
    let xs = [1i64, 2, 1, 3, 1, 4, 1];
    let alist = [(1i64, 10i64), (2, 20), (3, 30)];
    let a = filtr(&xs, 1);
    let b = alist_lookup(2, &alist);
    let c = freq(&xs);
    a.len() + b.map(|_| 1).unwrap_or(0) + c.len()
}
fn main() {
    let reps = 200_000usize;
    let mut t: Vec<u128> = Vec::with_capacity(reps);
    let mut sink = 0usize;
    for _ in 0..reps {
        let s = Instant::now();
        sink += once();
        t.push(s.elapsed().as_nanos());
    }
    t.sort_unstable();
    let p50 = t[reps / 2] as f64 / 1000.0;
    let p90 = t[reps * 9 / 10] as f64 / 1000.0;
    println!("D11-FAMILIES-RUST p50={:.3}us p90={:.3}us reps={} sink={}", p50, p90, reps, sink);
}
