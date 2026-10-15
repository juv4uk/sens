//! Дослідницький Rust-свідок точної ℚ арифметики для парного вимірювання.
//! Не є семантичним оракулом SENS, не читає .lisp/.sens і не виконує транспорту.
//! Той самий корпус/порядок операцій, що scripts/bench_math_sens_vs_rust.py.
use std::env;

#[derive(Clone, Copy)]
struct Q { n: i128, d: i128 }

impl Q {
    fn new(mut n: i128, mut d: i128) -> Result<Self, String> {
        if d == 0 { return Err("zero denominator".into()); }
        if d < 0 {
            n = n.checked_neg().ok_or("numerator sign overflow")?;
            d = d.checked_neg().ok_or("denominator sign overflow")?;
        }
        let mut a = n.checked_abs().ok_or("numerator abs overflow")?;
        let mut b = d;
        while b != 0 {
            let rem = a % b;
            a = b;
            b = rem;
        }
        let gcd = if a == 0 { 1 } else { a };
        Ok(Self { n: n / gcd, d: d / gcd })
    }

    fn add(self, rhs: Self) -> Result<Self, String> {
        let left = self.n.checked_mul(rhs.d).ok_or("add numerator overflow")?;
        let right = rhs.n.checked_mul(self.d).ok_or("add numerator overflow")?;
        let n = left.checked_add(right).ok_or("add numerator overflow")?;
        let d = self.d.checked_mul(rhs.d).ok_or("add denominator overflow")?;
        Self::new(n, d)
    }

    fn mul(self, rhs: Self) -> Result<Self, String> {
        let n = self.n.checked_mul(rhs.n).ok_or("mul numerator overflow")?;
        let d = self.d.checked_mul(rhs.d).ok_or("mul denominator overflow")?;
        Self::new(n, d)
    }

    fn recip(self) -> Result<Option<Self>, String> {
        if self.n == 0 { Ok(None) } else { Self::new(self.d, self.n).map(Some) }
    }
}

fn main() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 2 || args[0] != "--iters" {
        return Err("usage: sens-exact-q-rust --iters N".into());
    }
    let iters = args[1].parse::<usize>().map_err(|e| e.to_string())?;
    if iters == 0 || iters > 5_000_000 {
        return Err("iterations outside research bound 1..5000000".into());
    }

    // Mirrors Python CORPUS exactly; values are benchmark numerals, never SENS codes.
    const CORPUS: [Q; 7] = [
        Q { n: -2, d: 1 }, Q { n: -1, d: 1 }, Q { n: -1, d: 2 },
        Q { n: 0, d: 1 }, Q { n: 1, d: 2 }, Q { n: 1, d: 1 },
        Q { n: 2, d: 1 },
    ];
    let mut acc = Q { n: 0, d: 1 };
    for i in 0..iters {
        let a = CORPUS[i % CORPUS.len()];
        let b = CORPUS[((i % CORPUS.len()) * 3 + 1) % CORPUS.len()];
        let term = match b.recip()? {
            Some(inverse) => a.mul(inverse)?,
            None => Q { n: 0, d: 1 },
        };
        acc = acc.add(term)?;
    }
    let ops = iters.checked_mul(3).ok_or("op count overflow")?;
    let checksum = acc.n.checked_mul(1_000_003)
        .and_then(|x| x.checked_add(acc.d)).ok_or("checksum overflow")?;
    println!(r#"{{"schema":"sens-exact-q-rust-benchmark/v1","iters":{iters},"ops":{ops},"checksum":"{checksum}"}}"#);
    Ok(())
}
