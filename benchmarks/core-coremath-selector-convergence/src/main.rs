use core_math_binary_exec::{apply, BinaryNumber, Law};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: core-coremath-selector-convergence <parent-bits> <delta-bit>");
        std::process::exit(2);
    }

    let parent = BinaryNumber::parse(&args[1]).expect("valid parent bits");
    let delta = BinaryNumber::parse(&args[2]).expect("valid delta bit");
    let law = Law::new(BinaryNumber::parse("10").unwrap()).unwrap();
    let child = apply(&law, &[parent, delta]).expect("selector factor law applies");
    println!("{}", child.bits());
}
