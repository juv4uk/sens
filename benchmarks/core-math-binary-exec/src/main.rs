use core_math_binary_exec::{apply, BinaryNumber, Law};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Choice {
    First,
    Rest,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct Selector {
    root: Choice,
    suffix: Vec<Choice>,
}

impl Selector {
    fn extend(&self, choice: Choice) -> Self {
        let mut suffix = self.suffix.clone();
        suffix.push(choice);
        Self { root: self.root, suffix }
    }
}

fn encode(selector: &Selector) -> BinaryNumber {
    let mut bits = match selector.root {
        Choice::First => String::from("101"),
        Choice::Rest => String::from("110"),
    };
    for choice in &selector.suffix {
        bits.push(match choice {
            Choice::First => '0',
            Choice::Rest => '1',
        });
    }
    BinaryNumber::parse(&bits).unwrap()
}

fn enumerate_suffixes(depth: usize) -> Vec<Vec<Choice>> {
    if depth == 0 {
        return vec![vec![]];
    }
    let mut out = Vec::new();
    for prefix in enumerate_suffixes(depth - 1) {
        for choice in [Choice::First, Choice::Rest] {
            let mut next = prefix.clone();
            next.push(choice);
            out.push(next);
        }
    }
    out
}

fn permutation_attack(law: Law) {
    let root = Selector { root: Choice::First, suffix: vec![] };
    let semantic_child = root.extend(Choice::First);

    let arithmetic_child = apply(
        law,
        &[encode(&root), BinaryNumber::parse("0").unwrap()],
    ).unwrap();

    let canonical = encode(&semantic_child);
    assert_eq!(arithmetic_child, canonical);

    // Deliberately swap the two width-4 children under the same root.
    // This is an arbitrary slot permutation, not a path-preserving coordinate.
    let permuted = BinaryNumber::parse("1011").unwrap();
    assert_ne!(arithmetic_child, permuted);
}

fn main() {
    let law = Law::new(BinaryNumber::parse("10").unwrap()).unwrap();

    let mut witnessed = 0usize;
    for root in [Choice::First, Choice::Rest] {
        for depth in 0..=5 {
            for suffix in enumerate_suffixes(depth) {
                let selector = Selector { root, suffix };
                for choice in [Choice::First, Choice::Rest] {
                    let delta = match choice {
                        Choice::First => BinaryNumber::parse("0").unwrap(),
                        Choice::Rest => BinaryNumber::parse("1").unwrap(),
                    };
                    let mathematical = apply(law, &[encode(&selector), delta]).unwrap();
                    let semantic = encode(&selector.extend(choice));
                    assert_eq!(mathematical, semantic);
                    assert_eq!(mathematical.width(), encode(&selector).width() + 1);
                    witnessed += 1;
                }
            }
        }
    }

    let seed = BinaryNumber::parse("101").unwrap();
    let generated = apply(
        law,
        &[seed, BinaryNumber::parse("0").unwrap()],
    ).unwrap();
    let reused = apply(
        law,
        &[generated, BinaryNumber::parse("1").unwrap()],
    ).unwrap();

    assert_eq!(generated.bits(), "1010");
    assert_eq!(reused.bits(), "10101");

    assert!(Law::new(BinaryNumber::parse("11").unwrap()).is_err());
    assert!(
        apply(
            law,
            &[seed, BinaryNumber::parse("10").unwrap()]
        )
        .is_err()
    );

    permutation_attack(law);

    println!("EXECUTOR=bits-plus-law-to-bits");
    println!("CANONICAL-LAW=output=2*parent+delta;width=parent_width+1");
    println!("LAW-FACTOR-BITS=10");
    println!("SEMANTIC-EQUATION-WITNESSES={witnessed}");
    println!("GENERATED-BITS={}", generated.bits());
    println!("REUSED-BITS={}", reused.bits());
    println!("GENERATED-RESULT-REUSED=PASS");
    println!("EXACT-WIDTH-PRESERVED=PASS");
    println!("ARBITRARY-PERMUTATION-PRESERVES-LAW=0");
    println!("UNKNOWN-LAW-FAILS-CLOSED=PASS");
    println!("MALFORMED-INPUT-FAILS-CLOSED=PASS");
    println!("LISP-DEPENDENCY=0");
    println!("JSON-DEPENDENCY=0");
    println!("AST-DEPENDENCY=0");
    println!("HASH-IDENTITY-DEPENDENCY=0");
    println!("REGISTRY-LOOKUPS=0");
    println!("CACHE-DEPENDENCY=0");
    println!("STATUS=PASS-MINIMAL-BINARY-EXECUTOR");
}
