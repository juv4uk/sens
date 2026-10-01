use std::env;
use std::hint::black_box;
use std::mem::size_of;

#[derive(Clone)]
struct Graph {
    offsets: Vec<usize>,
    edges: Vec<usize>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Signature {
    out_degree: u32,
    self_loop: u32,
    successor_degree_sum: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Word {
    bits: u64,
    width: u8,
}

#[derive(Default, Clone, Copy)]
struct Counters {
    relation_edge_reads: u64,
    observer_fields: u64,
    quotient_lookups: u64,
    word_compares: u64,
}

enum Prepared {
    Raw,
    Computed,
    Cached(Vec<Signature>),
    Quotient(Vec<u16>),
    Word(Vec<Word>),
    Packed(Vec<u8>),
}

impl Prepared {
    fn final_bytes(&self) -> usize {
        match self {
            Prepared::Raw | Prepared::Computed => 0,
            Prepared::Cached(v) => v.len() * size_of::<Signature>(),
            Prepared::Quotient(v) => v.len() * size_of::<u16>(),
            Prepared::Word(v) => v.len() * size_of::<Word>(),
            Prepared::Packed(v) => v.len() * size_of::<u8>(),
        }
    }

    fn digest(&self) -> u64 {
        match self {
            Prepared::Raw => 1,
            Prepared::Computed => 2,
            Prepared::Cached(v) => v.iter().fold(3u64, |a, s| {
                a.wrapping_mul(131)
                    .wrapping_add(s.out_degree as u64)
                    .wrapping_add((s.self_loop as u64) << 8)
                    .wrapping_add((s.successor_degree_sum as u64) << 16)
            }),
            Prepared::Quotient(v) => v
                .iter()
                .fold(5u64, |a, x| a.wrapping_mul(131).wrapping_add(*x as u64)),
            Prepared::Word(v) => v.iter().fold(7u64, |a, w| {
                a.wrapping_mul(131)
                    .wrapping_add(w.bits)
                    .wrapping_add((w.width as u64) << 56)
            }),
            Prepared::Packed(v) => v
                .iter()
                .fold(11u64, |a, x| a.wrapping_mul(131).wrapping_add(*x as u64)),
        }
    }
}

fn build_graph(n: usize) -> Graph {
    assert!(n >= 16 && n % 8 == 0, "size must be >=16 and divisible by 8");
    let role_edges: [&[usize]; 8] = [
        &[0, 1],
        &[0],
        &[2, 3, 4],
        &[4],
        &[],
        &[0, 4],
        &[6],
        &[1, 2],
    ];
    let mut offsets = Vec::with_capacity(n + 1);
    let mut edges = Vec::with_capacity(n * 2);
    offsets.push(0);
    for node in 0..n {
        let replica = node / 8;
        let role = node % 8;
        for &target_role in role_edges[role] {
            edges.push(replica * 8 + target_role);
        }
        offsets.push(edges.len());
    }
    Graph { offsets, edges }
}

fn degree(g: &Graph, node: usize) -> usize {
    g.offsets[node + 1] - g.offsets[node]
}

fn signature(g: &Graph, node: usize, c: &mut Counters) -> Signature {
    let start = g.offsets[node];
    let end = g.offsets[node + 1];
    let out_degree = (end - start) as u32;

    let mut self_loop = 0u32;
    for &target in &g.edges[start..end] {
        c.relation_edge_reads += 1;
        if target == node {
            self_loop = 1;
        }
    }

    let mut successor_degree_sum = 0u32;
    for &target in &g.edges[start..end] {
        c.relation_edge_reads += 1;
        successor_degree_sum += degree(g, target) as u32;
    }

    c.observer_fields += 3;
    Signature {
        out_degree,
        self_loop,
        successor_degree_sum,
    }
}

fn raw_equal(g: &Graph, x: usize, y: usize, c: &mut Counters) -> bool {
    if degree(g, x) != degree(g, y) {
        c.observer_fields += 1;
        return false;
    }
    c.observer_fields += 1;

    let sx = g.offsets[x];
    let ex = g.offsets[x + 1];
    let sy = g.offsets[y];
    let ey = g.offsets[y + 1];

    let mut x_self = false;
    let mut y_self = false;
    for &target in &g.edges[sx..ex] {
        c.relation_edge_reads += 1;
        x_self |= target == x;
    }
    for &target in &g.edges[sy..ey] {
        c.relation_edge_reads += 1;
        y_self |= target == y;
    }
    c.observer_fields += 1;
    if x_self != y_self {
        return false;
    }

    let mut x_sum = 0usize;
    let mut y_sum = 0usize;
    for &target in &g.edges[sx..ex] {
        c.relation_edge_reads += 1;
        x_sum += degree(g, target);
    }
    for &target in &g.edges[sy..ey] {
        c.relation_edge_reads += 1;
        y_sum += degree(g, target);
    }
    c.observer_fields += 1;
    x_sum == y_sum
}

fn build_signatures(g: &Graph, c: &mut Counters) -> Vec<Signature> {
    (0..g.offsets.len() - 1)
        .map(|node| signature(g, node, c))
        .collect()
}

fn quotient_from_signatures(signatures: &[Signature]) -> (Vec<u16>, usize) {
    let mut unique: Vec<Signature> = Vec::new();
    let mut classes = Vec::with_capacity(signatures.len());
    for &sig in signatures {
        let class = match unique.iter().position(|x| *x == sig) {
            Some(i) => i,
            None => {
                unique.push(sig);
                unique.len() - 1
            }
        };
        classes.push(class as u16);
    }
    (classes, unique.len())
}

fn width_for_classes(classes: usize) -> u8 {
    let mut width = 0u8;
    let mut cap = 1usize;
    while cap < classes.max(1) {
        cap <<= 1;
        width += 1;
    }
    width.max(1)
}

fn prepare(candidate: &str, g: &Graph, c: &mut Counters) -> (Prepared, usize) {
    match candidate {
        "raw-relation" => (Prepared::Raw, 0),
        "observer-computed" => (Prepared::Computed, 0),
        "observer-cached" => {
            let signatures = build_signatures(g, c);
            let final_bytes = signatures.len() * size_of::<Signature>();
            (Prepared::Cached(signatures), final_bytes)
        }
        "quotient-class" => {
            let signatures = build_signatures(g, c);
            let temporary = signatures.len() * size_of::<Signature>();
            let (classes, _) = quotient_from_signatures(&signatures);
            let final_bytes = classes.len() * size_of::<u16>();
            (Prepared::Quotient(classes), temporary + final_bytes)
        }
        "exact-word" => {
            let signatures = build_signatures(g, c);
            let temporary_signatures = signatures.len() * size_of::<Signature>();
            let (classes, class_count) = quotient_from_signatures(&signatures);
            let temporary_classes = classes.len() * size_of::<u16>();
            let width = width_for_classes(class_count);
            let words: Vec<Word> = classes
                .iter()
                .map(|&class| Word {
                    bits: class as u64,
                    width,
                })
                .collect();
            let final_bytes = words.len() * size_of::<Word>();
            (
                Prepared::Word(words),
                temporary_signatures + temporary_classes + final_bytes,
            )
        }
        "packed-binary" => {
            let signatures = build_signatures(g, c);
            let temporary_signatures = signatures.len() * size_of::<Signature>();
            let (classes, class_count) = quotient_from_signatures(&signatures);
            assert!(class_count <= 256);
            let temporary_classes = classes.len() * size_of::<u16>();
            let packed: Vec<u8> = classes.iter().map(|&class| class as u8).collect();
            let final_bytes = packed.len();
            (
                Prepared::Packed(packed),
                temporary_signatures + temporary_classes + final_bytes,
            )
        }
        _ => panic!("unknown candidate: {candidate}"),
    }
}

fn equal(
    candidate: &str,
    prepared: &Prepared,
    g: &Graph,
    x: usize,
    y: usize,
    c: &mut Counters,
) -> bool {
    match (candidate, prepared) {
        ("raw-relation", Prepared::Raw) => raw_equal(g, x, y, c),
        ("observer-computed", Prepared::Computed) => {
            let a = signature(g, x, c);
            let b = signature(g, y, c);
            a == b
        }
        ("observer-cached", Prepared::Cached(v)) => {
            c.observer_fields += 6;
            v[x] == v[y]
        }
        ("quotient-class", Prepared::Quotient(v)) => {
            c.quotient_lookups += 2;
            v[x] == v[y]
        }
        ("exact-word", Prepared::Word(v)) => {
            c.word_compares += 1;
            v[x].width == v[y].width && v[x].bits == v[y].bits
        }
        ("packed-binary", Prepared::Packed(v)) => {
            c.word_compares += 1;
            v[x] == v[y]
        }
        _ => unreachable!(),
    }
}

fn queries(n: usize) -> Vec<(usize, usize)> {
    let mut out = Vec::with_capacity(64);
    let replicas = n / 8;
    for i in 0..64usize {
        let x = (i * 13 + 5) % n;
        let y = if i % 2 == 0 {
            let role = x % 8;
            let rep = (x / 8 + 1 + (i % replicas)) % replicas;
            rep * 8 + role
        } else {
            let role = (x % 8 + 1 + (i % 7)) % 8;
            (x / 8) * 8 + role
        };
        out.push((x, y));
    }
    out
}

fn baseline_answers(g: &Graph, pairs: &[(usize, usize)]) -> Vec<bool> {
    let mut c = Counters::default();
    pairs
        .iter()
        .map(|&(x, y)| signature(g, x, &mut c) == signature(g, y, &mut c))
        .collect()
}

fn verify(n: usize) {
    let g = build_graph(n);
    let pairs: Vec<(usize, usize)> = (0..n)
        .flat_map(|x| (0..n).map(move |y| (x, y)))
        .collect();
    let baseline = baseline_answers(&g, &pairs);
    let candidates = [
        "raw-relation",
        "observer-computed",
        "observer-cached",
        "quotient-class",
        "exact-word",
        "packed-binary",
    ];

    for candidate in candidates {
        let mut prep = Counters::default();
        let (prepared, _) = prepare(candidate, &g, &mut prep);
        let mut exec = Counters::default();
        for (idx, &(x, y)) in pairs.iter().enumerate() {
            let got = equal(candidate, &prepared, &g, x, y, &mut exec);
            assert_eq!(
                got, baseline[idx],
                "parity failure candidate={candidate} x={x} y={y}"
            );
        }
    }

    println!("FOUNDATION_VERIFY\tok\tsize={n}\tpairs={}", pairs.len());
}

fn parse_arg(name: &str, default: Option<&str>) -> String {
    let args: Vec<String> = env::args().collect();
    for i in 0..args.len() {
        if args[i] == name && i + 1 < args.len() {
            return args[i + 1].clone();
        }
    }
    default
        .unwrap_or_else(|| panic!("missing {name}"))
        .to_string()
}

fn main() {
    if env::args().any(|a| a == "--verify") {
        let n: usize = parse_arg("--size", Some("128")).parse().unwrap();
        verify(n);
        return;
    }

    let candidate = parse_arg("--candidate", None);
    let mode = parse_arg("--mode", Some("full"));
    let n: usize = parse_arg("--size", Some("128")).parse().unwrap();
    let reps: usize = parse_arg("--reps", Some("1")).parse().unwrap();

    let g = build_graph(n);
    let mut prep_counters = Counters::default();
    let (prepared, peak_bytes) = prepare(&candidate, &g, &mut prep_counters);
    let prepared_bytes = prepared.final_bytes();
    let mut checksum = prepared.digest();
    let mut exec_counters = Counters::default();

    if mode == "full" {
        let pairs = queries(n);
        for _ in 0..reps {
            for &(x, y) in &pairs {
                let result = equal(
                    &candidate,
                    &prepared,
                    &g,
                    black_box(x),
                    black_box(y),
                    &mut exec_counters,
                );
                checksum = checksum.rotate_left(5)
                    ^ (result as u64)
                        .wrapping_add((x as u64) << 1)
                        .wrapping_add((y as u64) << 9);
            }
        }
    } else if mode != "prepare" {
        panic!("mode must be prepare or full");
    }

    black_box(checksum);
    println!(
        "FOUNDATION_RESULT\tcandidate={}\tmode={}\tsize={}\treps={}\tchecksum={}\tprepared_bytes={}\tpeak_prepare_bytes={}\tprep_relation_edge_reads={}\tprep_observer_fields={}\tprep_quotient_lookups={}\tprep_word_compares={}\texec_relation_edge_reads={}\texec_observer_fields={}\texec_quotient_lookups={}\texec_word_compares={}",
        candidate,
        mode,
        n,
        reps,
        checksum,
        prepared_bytes,
        peak_bytes,
        prep_counters.relation_edge_reads,
        prep_counters.observer_fields,
        prep_counters.quotient_lookups,
        prep_counters.word_compares,
        exec_counters.relation_edge_reads,
        exec_counters.observer_fields,
        exec_counters.quotient_lookups,
        exec_counters.word_compares,
    );
}
