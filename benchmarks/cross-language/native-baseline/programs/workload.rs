use std::env;

fn main() {
    let n: u64 = env::args().nth(1).unwrap_or_else(|| "200000".into()).parse().unwrap();
    let mut acc: u64 = 0;
    for i in 0..=n { acc = acc.wrapping_add(i.wrapping_mul(i)); }
    println!("{acc}");
}
