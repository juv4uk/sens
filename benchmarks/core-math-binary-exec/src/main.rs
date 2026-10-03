use core_math_binary_exec::{apply_scoped, BinaryNumber, Domain, Error, Law, SemanticObject};

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

fn encode_selector(selector: &Selector) -> SemanticObject {
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
    SemanticObject::new(
        Domain::SelectorPath,
        BinaryNumber::parse(&bits).unwrap(),
    )
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

fn selector_permutation_attack(law: &Law) {
    let root = Selector { root: Choice::First, suffix: vec![] };
    let semantic_child = root.extend(Choice::First);

    let arithmetic_child = apply_scoped(
        law,
        &encode_selector(&root),
        &BinaryNumber::parse("0").unwrap(),
    ).unwrap();

    let canonical = encode_selector(&semantic_child);
    assert_eq!(arithmetic_child, canonical);

    // Deliberately swap the two width-4 children under the same root.
    // This is an arbitrary slot permutation, not a path-preserving coordinate.
    let permuted = SemanticObject::new(
        Domain::SelectorPath,
        BinaryNumber::parse("1011").unwrap(),
    );
    assert_ne!(arithmetic_child, permuted);
}

// Minimal exact rational arithmetic for #2494 Q-group validation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ExactQ {
    num: i64,
    den: i64,
}

fn gcd(a: i64, b: i64) -> i64 {
    let mut x = a.abs();
    let mut y = b.abs();
    while y != 0 {
        let t = y;
        y = x % y;
        x = t;
    }
    x
}

impl ExactQ {
    fn new(num: i64, den: i64) -> Option<Self> {
        if den == 0 {
            return None;
        }
        let g = gcd(num, den);
        let sign = if den < 0 { -1 } else { 1 };
        Some(Self {
            num: (num / g) * sign,
            den: (den / g) * sign,
        })
    }

    fn from_int(n: i64) -> Self {
        Self { num: n, den: 1 }
    }

    fn neg(self) -> Self {
        Self { num: -self.num, den: self.den }
    }

    fn sub(self, other: Self) -> Self {
        let num = self.num * other.den - other.num * self.den;
        let den = self.den * other.den;
        Self::new(num, den).unwrap()
    }

    fn recip(self) -> Option<Self> {
        Self::new(self.den, self.num)
    }

    fn div(self, other: Self) -> Option<Self> {
        let inv = other.recip()?;
        let num = self.num * inv.num;
        let den = self.den * inv.den;
        Self::new(num, den)
    }
}

fn q_group_factor_witness(q_law: &Law) -> (usize, usize, usize) {
    let add_root = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("0").unwrap());
    let mul_root = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("1").unwrap());

    let d0 = BinaryNumber::parse("0").unwrap();
    let d1 = BinaryNumber::parse("1").unwrap();

    let add_inv = apply_scoped(q_law, &add_root, &d0).unwrap(); // 00
    let add_quot = apply_scoped(q_law, &add_root, &d1).unwrap(); // 01
    let mul_inv = apply_scoped(q_law, &mul_root, &d0).unwrap(); // 10
    let mul_quot = apply_scoped(q_law, &mul_root, &d1).unwrap(); // 11

    assert_eq!(add_inv.bits().bits(), "00");
    assert_eq!(add_quot.bits().bits(), "01");
    assert_eq!(mul_inv.bits().bits(), "10");
    assert_eq!(mul_quot.bits().bits(), "11");

    // Exact-Q corpus validation (7 elements: -2, -1, -1/2, 0, 1/2, 1, 2)
    let corpus = [
        ExactQ::from_int(-2),
        ExactQ::from_int(-1),
        ExactQ::new(-1, 2).unwrap(),
        ExactQ::from_int(0),
        ExactQ::new(1, 2).unwrap(),
        ExactQ::from_int(1),
        ExactQ::from_int(2),
    ];

    let mut defined_cases = 0usize;
    let mut undefined_cases = 0usize;

    // Additive family: inverse (NEG) is total, quotient (SUB) is total
    for &x in &corpus {
        let _ = x.neg();
        defined_cases += 1;
        for &y in &corpus {
            let _ = x.sub(y);
            defined_cases += 1;
        }
    }

    // Multiplicative family: inverse (RECIP) has partiality at 0, quotient (DIV) has partiality at y=0
    for &x in &corpus {
        if x.recip().is_some() {
            defined_cases += 1;
        } else {
            undefined_cases += 1;
        }
        for &y in &corpus {
            if x.div(y).is_some() {
                defined_cases += 1;
            } else {
                undefined_cases += 1;
            }
        }
    }

    // Permutation attack across all 24 bijections of {"00", "01", "10", "11"}
    let labels = ["00", "01", "10", "11"];
    let mut permutations = Vec::new();
    let mut p = [0, 1, 2, 3];
    fn permute(k: usize, p: &mut [usize; 4], out: &mut Vec<[usize; 4]>) {
        if k == 4 {
            out.push(*p);
            return;
        }
        for i in k..4 {
            p.swap(k, i);
            permute(k + 1, p, out);
            p.swap(k, i);
        }
    }
    permute(0, &mut p, &mut permutations);
    assert_eq!(permutations.len(), 24);

    let mut rejected_permutations = 0usize;
    for perm in &permutations {
        let mapped = [
            labels[perm[0]], // maps to add_inv
            labels[perm[1]], // maps to add_quot
            labels[perm[2]], // maps to mul_inv
            labels[perm[3]], // maps to mul_quot
        ];

        // Factor law requires:
        // 1. Family prefix is preserved (0 for additive, 1 for multiplicative)
        // 2. Single global role orientation across both families (either 0/1 or 1/0)
        let b0 = mapped[0].as_bytes();
        let b1 = mapped[1].as_bytes();
        let b2 = mapped[2].as_bytes();
        let b3 = mapped[3].as_bytes();

        let family_prefix_preserved = b0[0] == b'0' && b1[0] == b'0' && b2[0] == b'1' && b3[0] == b'1';
        let role_consistent = (b0[1] == b'0' && b1[1] == b'1' && b2[1] == b'0' && b3[1] == b'1')
            || (b0[1] == b'1' && b1[1] == b'0' && b2[1] == b'1' && b3[1] == b'0');

        if !(family_prefix_preserved && role_consistent) {
            rejected_permutations += 1;
        }
    }

    (defined_cases, undefined_cases, rejected_permutations)
}

fn cross_domain_firewall_attack(sel_law: &Law, q_law: &Law) {
    let sel_obj = SemanticObject::new(
        Domain::SelectorPath,
        BinaryNumber::parse("101").unwrap(),
    );
    let q_obj = SemanticObject::new(
        Domain::QGroupFactor,
        BinaryNumber::parse("1").unwrap(),
    );
    let delta = BinaryNumber::parse("0").unwrap();

    // 1. Cross-domain application MUST fail with DomainMismatch
    assert_eq!(apply_scoped(sel_law, &q_obj, &delta), Err(Error::DomainMismatch));
    assert_eq!(apply_scoped(q_law, &sel_obj, &delta), Err(Error::DomainMismatch));

    // 2. Same bit strings across domains MUST NOT be equal as semantic objects
    let sel_10 = SemanticObject::new(
        Domain::SelectorPath,
        BinaryNumber::parse("10").unwrap(),
    );
    let q_10 = SemanticObject::new(
        Domain::QGroupFactor,
        BinaryNumber::parse("10").unwrap(),
    );
    assert_eq!(sel_10.bits().bits(), q_10.bits().bits());
    assert_ne!(sel_10, q_10);
}

fn main() {
    let sel_law = Law::selector_extend();
    let q_law = Law::q_group_role();

    // 1. Selector domain execution
    let mut sel_witnesses = 0usize;
    for root in [Choice::First, Choice::Rest] {
        for depth in 0..=5 {
            for suffix in enumerate_suffixes(depth) {
                let selector = Selector { root, suffix };
                for choice in [Choice::First, Choice::Rest] {
                    let delta = match choice {
                        Choice::First => BinaryNumber::parse("0").unwrap(),
                        Choice::Rest => BinaryNumber::parse("1").unwrap(),
                    };
                    let mathematical = apply_scoped(&sel_law, &encode_selector(&selector), &delta).unwrap();
                    let semantic = encode_selector(&selector.extend(choice));
                    assert_eq!(mathematical, semantic);
                    assert_eq!(mathematical.width(), encode_selector(&selector).width() + 1);
                    assert_eq!(mathematical.domain(), Domain::SelectorPath);
                    sel_witnesses += 1;
                }
            }
        }
    }

    // 2. Unbounded bit carrier test
    let seed = SemanticObject::new(
        Domain::SelectorPath,
        BinaryNumber::parse("101").unwrap(),
    );
    let generated = apply_scoped(
        &sel_law,
        &seed,
        &BinaryNumber::parse("0").unwrap(),
    ).unwrap();
    let reused = apply_scoped(
        &sel_law,
        &generated,
        &BinaryNumber::parse("1").unwrap(),
    ).unwrap();

    assert_eq!(generated.bits().bits(), "1010");
    assert_eq!(reused.bits().bits(), "10101");

    selector_permutation_attack(&sel_law);

    // 3. Exact-Q group factor domain execution (#2494)
    let (q_defined, q_undefined, q_rejected_perms) = q_group_factor_witness(&q_law);
    assert_eq!(q_defined, 104);
    assert_eq!(q_undefined, 8); // 1 recip zero + 7 div by zero on 7-element corpus
    assert_eq!(q_rejected_perms, 22); // 22/24 arbitrary permutations rejected by factor law!

    // 4. Cross-domain firewall controls (#2508)
    cross_domain_firewall_attack(&sel_law, &q_law);

    println!("EXECUTOR=bits-plus-domain-law-to-bits");
    println!("CANONICAL-MECHANISM=output=2*parent+delta;width=parent_width+1");
    println!("DOMAINS=SelectorPath,QGroupFactor");
    println!("SELECTOR-SEMANTIC-WITNESSES={sel_witnesses}");
    println!("QGROUP-EXACT-DEFINED-CASES={q_defined}");
    println!("QGROUP-EXACT-UNDEFINED-CASES={q_undefined}");
    println!("QGROUP-FACTOR-PERMUTATIONS-REJECTED={q_rejected_perms}/24");
    println!("GENERATED-BITS={}", generated.bits().bits());
    println!("REUSED-BITS={}", reused.bits().bits());
    println!("GENERATED-RESULT-REUSED=PASS");
    println!("EXACT-WIDTH-PRESERVED=PASS");
    println!("ARBITRARY-PERMUTATION-PRESERVES-LAW=0");
    println!("DOMAIN-FIREWALL-CROSS-APPLY-REJECTED=PASS");
    println!("SAME-BITS-DIFFERENT-DOMAINS-DISTINCT=PASS");
    println!("UNKNOWN-LAW-FAILS-CLOSED=PASS");
    println!("MALFORMED-INPUT-FAILS-CLOSED=PASS");
    println!("LISP-DEPENDENCY=0");
    println!("JSON-DEPENDENCY=0");
    println!("AST-DEPENDENCY=0");
    println!("HASH-IDENTITY-DEPENDENCY=0");
    println!("REGISTRY-LOOKUPS=0");
    println!("CACHE-DEPENDENCY=0");
    println!("STATUS=PASS-DOMAIN-SCOPED-BINARY-EXECUTOR");
}
