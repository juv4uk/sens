use std::collections::HashMap;
use std::env;
use std::hint::black_box;
use std::mem::size_of;

#[derive(Clone, Copy)]
struct Node {
    car: u32,
    cdr: u32,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
struct Word {
    root: u8,   // abstract branch: 0 = current CAR/root 100, 1 = current CDR/root 011
    suffix: u32,
    depth: u8,
}

#[derive(Clone, Copy)]
struct ExecPath {
    // Execution order, low bit first: innermost selector first.
    bits: u32,
    len: u8,
}

impl Word {
    fn key(self) -> u64 {
        ((self.depth as u64) << 33) | ((self.root as u64) << 32) | self.suffix as u64
    }

    fn dense_index(self) -> usize {
        ((self.root as usize) << self.depth) | self.suffix as usize
    }
}

fn suffix_mask(depth: u8) -> u32 {
    if depth == 0 { 0 } else { (1u32 << depth) - 1 }
}

fn decode(word: Word) -> ExecPath {
    // Suffix integer bit 0 is the rightmost appended bit, so it is the first
    // operation applied. The root operation is outermost and is applied last.
    ExecPath {
        bits: word.suffix | ((word.root as u32) << word.depth),
        len: word.depth + 1,
    }
}

fn build_tree(levels: u8) -> Vec<Node> {
    let total = (1usize << (levels as usize + 1)) - 1;
    let internal = (1usize << levels as usize) - 1;
    let mut nodes = vec![Node { car: 0, cdr: 0 }; total];
    for i in 0..internal {
        nodes[i] = Node {
            car: (2 * i + 1) as u32,
            cdr: (2 * i + 2) as u32,
        };
    }
    for i in internal..total {
        nodes[i] = Node { car: i as u32, cdr: i as u32 };
    }
    nodes
}

fn run_path(path: ExecPath, tree: &[Node]) -> u32 {
    let mut index = 0u32;
    for i in 0..path.len {
        let node = tree[index as usize];
        index = if ((path.bits >> i) & 1) == 0 { node.car } else { node.cdr };
    }
    index
}

fn make_workload(depth: u8, pattern: &str, calls: usize) -> Vec<Word> {
    let mask = suffix_mask(depth);
    let repeated_suffix = 0xAAAA_AAAAu32 & mask;
    let mut state = 0x9E37_79B9_7F4A_7C15u64;
    let mut out = Vec::with_capacity(calls);

    for i in 0..calls {
        let word = match pattern {
            "repeated" => Word {
                root: 0,
                suffix: repeated_suffix,
                depth,
            },
            "random" => {
                state = state
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                Word {
                    root: ((state >> 32) & 1) as u8,
                    suffix: (state as u32) & mask,
                    depth,
                }
            }
            "alternating" => Word {
                root: (i & 1) as u8,
                suffix: if i & 1 == 0 { repeated_suffix } else { (!repeated_suffix) & mask },
                depth,
            },
            _ => panic!("unknown pattern: {pattern}"),
        };
        out.push(word);
    }
    out
}

fn build_flat(depth: u8) -> Vec<ExecPath> {
    let entries = 1usize << (depth as usize + 1);
    let mask = suffix_mask(depth) as usize;
    let mut table = Vec::with_capacity(entries);
    for index in 0..entries {
        let word = Word {
            root: ((index >> depth) & 1) as u8,
            suffix: (index & mask) as u32,
            depth,
        };
        table.push(decode(word));
    }
    table
}

fn build_cache(workload: &[Word]) -> HashMap<u64, ExecPath> {
    let mut cache = HashMap::new();
    for &word in workload {
        cache.entry(word.key()).or_insert_with(|| decode(word));
    }
    cache
}

fn unique_count(workload: &[Word]) -> usize {
    let mut keys = HashMap::<u64, ()>::new();
    for &word in workload {
        keys.insert(word.key(), ());
    }
    keys.len()
}

fn checksum_flat(workload: &[Word], tree: &[Node], table: &[ExecPath]) -> u64 {
    let mut sum = 0u64;
    for &word in workload {
        let path = table[word.dense_index()];
        sum = sum.wrapping_add(run_path(path, tree) as u64);
    }
    sum
}

fn checksum_cold(workload: &[Word], tree: &[Node]) -> u64 {
    let mut sum = 0u64;
    for &word in workload {
        sum = sum.wrapping_add(run_path(decode(word), tree) as u64);
    }
    sum
}

fn checksum_cached(
    workload: &[Word],
    tree: &[Node],
    cache: &HashMap<u64, ExecPath>,
) -> u64 {
    let mut sum = 0u64;
    for &word in workload {
        let path = *cache.get(&word.key()).expect("prewarmed cache entry");
        sum = sum.wrapping_add(run_path(path, tree) as u64);
    }
    sum
}

fn build_compiled(workload: &[Word]) -> (Vec<ExecPath>, Vec<u32>) {
    let mut by_key = HashMap::<u64, u32>::new();
    let mut paths = Vec::<ExecPath>::new();
    let mut calls = Vec::<u32>::with_capacity(workload.len());

    for &word in workload {
        let key = word.key();
        let index = if let Some(&index) = by_key.get(&key) {
            index
        } else {
            let index = paths.len() as u32;
            paths.push(decode(word));
            by_key.insert(key, index);
            index
        };
        calls.push(index);
    }
    (paths, calls)
}

fn checksum_compiled(paths: &[ExecPath], calls: &[u32], tree: &[Node]) -> u64 {
    let mut sum = 0u64;
    for &index in calls {
        sum = sum.wrapping_add(run_path(paths[index as usize], tree) as u64);
    }
    sum
}

fn checksum_hybrid(
    workload: &[Word],
    tree: &[Node],
    cache: &HashMap<u64, ExecPath>,
) -> u64 {
    let mut sum = 0u64;
    for &word in workload {
        let path = if word.depth == 0 {
            ExecPath { bits: word.root as u32, len: 1 }
        } else if let Some(path) = cache.get(&word.key()) {
            *path
        } else {
            // Valid selector words use the generator arm. This fallback models
            // the branch without assigning semantic meaning to residue.
            decode(word)
        };
        sum = sum.wrapping_add(run_path(path, tree) as u64);
    }
    sum
}

fn print_metrics(mode: &str, depth: u8, calls: usize, distinct: usize, cache_entries: usize) {
    let d = depth as u64;
    let n = calls as u64;
    let u = distinct as u64;
    let family_entries = 1usize << (depth as usize + 1);
    let flat_table_bytes = family_entries * size_of::<ExecPath>();

    println!("METRIC\tcalls\t{n}");
    println!("METRIC\tdistinct_words\t{u}");
    println!("METRIC\tpath_depth\t{d}");
    println!("METRIC\tselector_family_entries\t{family_entries}");
    println!(
        "METRIC\tflat_table_bytes\t{}",
        if mode == "flat" { flat_table_bytes } else { 0 }
    );

    match mode {
        "flat" => {
            println!("METRIC\tregistry_lookups\t{n}");
            println!("METRIC\troot_selections\t0");
            println!("METRIC\tprefix_bits_consumed\t0");
            println!("METRIC\tgenerator_applications\t0");
            println!("METRIC\tcache_hits\t0");
            println!("METRIC\tcache_misses\t0");
            println!("METRIC\tresidue_lookups\t0");
        }
        "cold" => {
            println!("METRIC\tregistry_lookups\t0");
            println!("METRIC\troot_selections\t{n}");
            println!("METRIC\tprefix_bits_consumed\t{}", n * d);
            println!("METRIC\tgenerator_applications\t{}", n * d);
            println!("METRIC\tcache_hits\t0");
            println!("METRIC\tcache_misses\t0");
            println!("METRIC\tresidue_lookups\t0");
        }
        "compiled" => {
            println!("METRIC\tregistry_lookups\t0");
            println!("METRIC\troot_selections\t0");
            println!("METRIC\tprefix_bits_consumed\t0");
            println!("METRIC\tgenerator_applications\t0");
            println!("METRIC\tcache_hits\t0");
            println!("METRIC\tcache_misses\t0");
            println!("METRIC\tprepare_path_decodes\t{u}");
            println!("METRIC\tprepare_prefix_bits\t{}", u * d);
            println!("METRIC\tcompiled_descriptor_loads\t{n}");
            println!("METRIC\tresidue_lookups\t0");
        }
        "cached" => {
            println!("METRIC\tregistry_lookups\t0");
            println!("METRIC\troot_selections\t0");
            println!("METRIC\tprefix_bits_consumed\t0");
            println!("METRIC\tgenerator_applications\t0");
            println!("METRIC\tcache_hits\t{n}");
            println!("METRIC\tcache_misses\t0");
            println!("METRIC\tprepare_path_decodes\t{u}");
            println!("METRIC\tprepare_prefix_bits\t{}", u * d);
            println!("METRIC\tresidue_lookups\t0");
        }
        "hybrid" => {
            println!("METRIC\tregistry_lookups\t0");
            println!("METRIC\troot_selections\t{}", if depth == 0 { n } else { 0 });
            println!("METRIC\tprefix_bits_consumed\t0");
            println!("METRIC\tgenerator_applications\t0");
            println!("METRIC\tcache_hits\t{}", if depth == 0 { 0 } else { n });
            println!("METRIC\tcache_misses\t0");
            println!("METRIC\thybrid_route_branches\t{n}");
            println!("METRIC\tresidue_lookups\t0");
        }
        _ => {}
    }
    println!("METRIC\tcache_entries\t{cache_entries}");
    println!("METRIC\ttree_data_edges\t{}", n * (d + 1));
}

fn verify(depth: u8, pattern: &str, calls: usize) {
    let workload = make_workload(depth, pattern, calls);
    let tree = build_tree(depth + 1);
    let flat = build_flat(depth);
    let cache = build_cache(&workload);

    let a = checksum_flat(&workload, &tree, &flat);
    let b = checksum_cold(&workload, &tree);
    let (compiled_paths, compiled_calls) = build_compiled(&workload);
    let c = checksum_compiled(&compiled_paths, &compiled_calls, &tree);
    let d = checksum_cached(&workload, &tree, &cache);
    let e = checksum_hybrid(&workload, &tree, &cache);
    assert_eq!(a, b);
    assert_eq!(a, c);
    assert_eq!(a, d);
    assert_eq!(a, e);
    println!("VERIFY\tPASS\tdepth={depth}\tpattern={pattern}\tcalls={calls}\tchecksum={a}");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 6 {
        eprintln!("usage: bench MODE PHASE DEPTH PATTERN CALLS");
        std::process::exit(2);
    }

    let mode = args[1].as_str();
    let phase = args[2].as_str();
    let depth: u8 = args[3].parse().expect("depth");
    let pattern = args[4].as_str();
    let calls: usize = args[5].parse().expect("calls");

    assert!(depth <= 20, "bounded benchmark depth <= 20");
    assert!(calls > 0);

    if mode == "verify" {
        verify(depth, pattern, calls);
        return;
    }

    let workload = make_workload(depth, pattern, calls);
    let distinct = unique_count(&workload);
    let tree = build_tree(depth + 1);

    let flat = if mode == "flat" { Some(build_flat(depth)) } else { None };
    let compiled = if mode == "compiled" {
        Some(build_compiled(&workload))
    } else {
        None
    };
    let cache = if mode == "cached" || mode == "hybrid" {
        Some(build_cache(&workload))
    } else {
        None
    };

    black_box(&workload);
    black_box(&tree);
    black_box(&flat);
    black_box(&compiled);
    black_box(&cache);

    if phase == "prepare" {
        let compiled_size = compiled
            .as_ref()
            .map_or(0usize, |(paths, calls)| paths.len() + calls.len());
        let prepared = flat.as_ref().map_or(0usize, Vec::len)
            + compiled_size
            + cache.as_ref().map_or(0usize, HashMap::len)
            + workload.len()
            + tree.len();
        println!("CHECKSUM\t{prepared}");
        print_metrics(mode, depth, calls, distinct, cache.as_ref().map_or(0, HashMap::len));
        return;
    }
    assert_eq!(phase, "full", "phase must be prepare or full");

    let checksum = match mode {
        "flat" => checksum_flat(&workload, &tree, flat.as_ref().unwrap()),
        "cold" => checksum_cold(&workload, &tree),
        "compiled" => {
            let (paths, calls) = compiled.as_ref().unwrap();
            checksum_compiled(paths, calls, &tree)
        }
        "cached" => checksum_cached(&workload, &tree, cache.as_ref().unwrap()),
        "hybrid" => checksum_hybrid(&workload, &tree, cache.as_ref().unwrap()),
        _ => panic!("unknown mode: {mode}"),
    };

    println!("CHECKSUM\t{}", black_box(checksum));
    print_metrics(mode, depth, calls, distinct, cache.as_ref().map_or(0, HashMap::len));
}
