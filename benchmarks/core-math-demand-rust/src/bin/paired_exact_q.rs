//! Independent host benchmark of the exact-Q law, not SENS semantic admission.
//! A result is evidence about Rust arithmetic only; SENS needs its own T5 fixture.
use std::env;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Q { n: i128, d: i128 }

fn gcd(mut a: i128, mut b: i128) -> i128 {
    a = a.abs(); b = b.abs();
    while b != 0 { let r = a % b; a = b; b = r; }
    if a == 0 { 1 } else { a }
}
fn multiply(a: i128, b: i128) -> i128 { a.checked_mul(b).expect("exact Q overflow") }
fn add_int(a: i128, b: i128) -> i128 { a.checked_add(b).expect("exact Q overflow") }
impl Q {
    fn new(mut n: i128, mut d: i128) -> Self {
        assert_ne!(d, 0, "zero exact-Q denominator");
        if d < 0 { n = n.checked_neg().expect("exact Q overflow"); d = -d; }
        let g = gcd(n, d);
        Self { n: n/g, d: d/g }
    }
    fn add(self, x: Self) -> Self {
        Self::new(add_int(multiply(self.n,x.d), multiply(x.n,self.d)), multiply(self.d,x.d))
    }
    fn mul(self, x: Self) -> Self { Self::new(multiply(self.n,x.n), multiply(self.d,x.d)) }
    fn recip(self) -> Option<Self> {
        if self.n == 0 { None } else { Some(Self::new(self.d,self.n)) }
    }
}
const CORPUS: [Q;7] = [
    Q{n:-2,d:1},Q{n:-1,d:1},Q{n:-1,d:2},Q{n:0,d:1},
    Q{n:1,d:2},Q{n:1,d:1},Q{n:2,d:1},
];
fn workload(iters: usize) -> (i128, usize) {
    let mut acc=Q::new(0,1);
    for i in 0..iters {
        let a=CORPUS[i%CORPUS.len()];
        let b=CORPUS[((i%CORPUS.len())*3+1)%CORPUS.len()];
        // Python reference: zero reciprocal contributes the exact Q(0,1).
        let term=match b.recip() {Some(r)=>a.mul(r),None=>Q::new(0,1)};
        acc=acc.add(term);
    }
    (add_int(multiply(acc.n,1_000_003),acc.d), iters.checked_mul(3).expect("ops overflow"))
}
fn main() {
    let args: Vec<_> = env::args().skip(1).collect();
    if args.len()!=2 || args[0]!="--iters" {
        eprintln!("usage: paired_exact_q --iters N");
        std::process::exit(2);
    }
    let iters=match args[1].parse::<usize>() {
        Ok(n) => n,
        Err(e) => {eprintln!("invalid iterations: {e}");std::process::exit(2)}
    };
    let (checksum,ops)=workload(iters);
    println!(r#"{{"schema":"sens-paired-exact-q-rust/v1","iters":{},"ops":{},"checksum":"{}"}}"#,iters,ops,checksum);
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_q_canonical_and_zero_reciprocal() {
        assert_eq!(Q::new(2,4),Q::new(1,2));
        assert_eq!(Q::new(1,-2),Q::new(-1,2));
        assert_eq!(Q::new(1,2).add(Q::new(1,3)),Q::new(5,6));
        assert_eq!(Q::new(2,3).mul(Q::new(3,4)),Q::new(1,2));
        assert_eq!(Q::new(0,1).recip(),None);
    }
    #[test]
    fn same_corpus_produces_exact_predictable_checksum() {
        assert_eq!(workload(0),(1,0));
        assert_eq!(workload(1),(-2_000_005,3));
        assert_eq!(workload(200_000),(57_143_171_433,600_000));
    }
    #[test]
    #[should_panic(expected="exact Q overflow")]
    fn overflow_fails_closed() {
        let _=Q::new(i128::MAX,1).add(Q::new(1,1));
    }
}
