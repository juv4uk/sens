//! Independent external Rust exact-Q benchmark; no SENS physical or semantic ingress.
use serde_json::json;
use std::env;
use std::hint::black_box;
use std::time::Instant;

const CORPUS: [&str; 7] = ["-2/1", "-1/1", "-1/2", "0/1", "1/2", "1/1", "2/1"];
#[derive(Clone, Copy)]
struct Q { n: i128, d: i128 }
fn gcd(mut a: i128, mut b: i128) -> i128 {
    a = a.abs();
    b = b.abs();
    while b != 0 { let r = a % b; a = b; b = r; }
    a.max(1)
}
impl Q {
    fn new(mut n: i128, mut d: i128) -> Self {
        assert_ne!(d, 0);
        if d < 0 { n = -n; d = -d; }
        let g = gcd(n, d);
        Self { n: n / g, d: d / g }
    }
    fn add(self, rhs: Self) -> Self {
        Self::new(self.n * rhs.d + rhs.n * self.d, self.d * rhs.d)
    }
    fn mul(self, rhs: Self) -> Self {
        Self::new(self.n * rhs.n, self.d * rhs.d)
    }
    fn recip(self) -> Option<Self> {
        (self.n != 0).then(|| Self::new(self.d, self.n))
    }
}
fn workload(iters: usize) -> Result<(i128, usize), String> {
    let vals = [Q::new(-2,1), Q::new(-1,1), Q::new(-1,2),
                Q::new(0,1), Q::new(1,2), Q::new(1,1), Q::new(2,1)];
    let mut acc = Q::new(0,1);
    for i in 0..iters {
        let a = black_box(vals[i % vals.len()]);
        let b = black_box(vals[(i * 3 + 1) % vals.len()]);
        let term = b.recip().map(|inv| a.mul(inv)).unwrap_or(Q::new(0,1));
        acc = acc.add(term);
    }
    Ok((acc.n * 1_000_003 + acc.d, iters.checked_mul(3).ok_or("ops overflow")?))
}
fn main() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 4 || args[0] != "--iters" || args[2] != "--reps" {
        return Err("usage: core-math-demand-rust-paired --iters N --reps N".into());
    }
    let iters: usize = args[1].parse().map_err(|e| format!("invalid iters: {e}"))?;
    let reps: usize = args[3].parse().map_err(|e| format!("invalid reps: {e}"))?;
    if iters == 0 || reps == 0 { return Err("iters/reps must be positive".into()); }
    let mut samples = Vec::<f64>::with_capacity(reps);
    let mut previous_checksum = None;
    let mut operations = None;
    for _ in 0..reps {
        let start = Instant::now();
        let (checksum, ops) = black_box(workload(iters)?);
        let seconds = start.elapsed().as_secs_f64();
        if seconds <= 0.0 { return Err("zero timing resolution".into()); }
        if previous_checksum.is_some_and(|previous| previous != checksum) {
            return Err("unstable Rust checksum".into());
        }
        previous_checksum = Some(checksum);
        operations = Some(ops);
        samples.push(seconds);
    }
    samples.sort_by(f64::total_cmp);
    let median = if reps % 2 == 0 {
        (samples[reps / 2 - 1] + samples[reps / 2]) / 2.0
    } else { samples[reps / 2] };
    println!("{}", json!({
        "schema": "sens-math-q-rust-side/v1",
        "corpus": CORPUS,
        "iters": iters,
        "reps": reps,
        "ops": operations.ok_or("missing ops")?,
        "checksum": previous_checksum.ok_or("missing checksum")?.to_string(),
        "median_s": median,
    }));
    Ok(())
}
