use std::env;

fn tree(depth: u32, seed: u64) -> u64 {
    if depth == 0 { return seed; }
    let left = tree(depth - 1, seed.wrapping_mul(3).wrapping_add(1));
    let right = tree(depth - 1, seed.wrapping_mul(3).wrapping_add(2));
    left ^ right.wrapping_add(depth as u64)
}

fn main() {
    let depth: u32 = env::args().nth(1).unwrap_or_else(|| "18".into()).parse().unwrap();
    println!("{}", tree(depth, 1));
}
