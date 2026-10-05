use std::{env, hint::black_box, mem::size_of};

#[derive(Clone, Copy)]
struct Node {
    car: u32,
    cdr: u32,
}

#[derive(Clone, Copy)]
struct Word {
    root: u8,
    suffix: u8,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct ExecPath {
    bits: u32,
    len: u8,
    pad: [u8; 3],
}

const fn path(bits: u32) -> ExecPath {
    ExecPath { bits, len: 4, pad: [0; 3] }
}

#[cfg(lane_flat)]
static FLAT16: [ExecPath; 16] = [
    path(0), path(1), path(2), path(3),
    path(4), path(5), path(6), path(7),
    path(8), path(9), path(10), path(11),
    path(12), path(13), path(14), path(15),
];

fn decode(word: Word) -> ExecPath {
    path((word.suffix as u32) | ((word.root as u32) << 3))
}

fn dense_index(word: Word) -> usize {
    ((word.root as usize) << 3) | word.suffix as usize
}

fn workload(calls: usize) -> Vec<Word> {
    (0..calls)
        .map(|i| {
            let index = i & 15;
            Word {
                root: ((index >> 3) & 1) as u8,
                suffix: (index & 7) as u8,
            }
        })
        .collect()
}

fn tree() -> Vec<Node> {
    let levels = 4usize;
    let total = (1usize << (levels + 1)) - 1;
    let internal = (1usize << levels) - 1;
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

#[inline(always)]
fn run_path(path: ExecPath, tree: &[Node]) -> u32 {
    let mut index = 0u32;
    for bit in 0..path.len {
        let node = tree[index as usize];
        index = if ((path.bits >> bit) & 1) == 0 {
            node.car
        } else {
            node.cdr
        };
    }
    index
}

#[cfg(lane_flat)]
fn execute(words: &[Word], tree: &[Node]) -> (u64, usize) {
    let mut sum = 0u64;
    for &word in words {
        let p = FLAT16[dense_index(word)];
        sum = sum.wrapping_add(run_path(p, tree) as u64);
    }
    (black_box(sum), size_of::<[ExecPath; 16]>())
}

#[cfg(lane_generator)]
fn execute(words: &[Word], tree: &[Node]) -> (u64, usize) {
    let mut sum = 0u64;
    for &word in words {
        sum = sum.wrapping_add(run_path(decode(word), tree) as u64);
    }
    (black_box(sum), 0)
}

#[cfg(lane_compiled)]
struct Compiled {
    paths: [ExecPath; 16],
    calls: Vec<u8>,
}

#[cfg(lane_compiled)]
fn prepare_compiled(words: &[Word]) -> Compiled {
    let mut paths = [path(0); 16];
    for index in 0..16 {
        paths[index] = decode(Word {
            root: ((index >> 3) & 1) as u8,
            suffix: (index & 7) as u8,
        });
    }
    let calls = words.iter().copied().map(dense_index).map(|i| i as u8).collect();
    Compiled { paths, calls }
}

#[cfg(lane_compiled)]
fn execute(words: &[Word], tree: &[Node]) -> (u64, usize) {
    let compiled = prepare_compiled(words);
    let mut sum = 0u64;
    for &index in &compiled.calls {
        sum = sum.wrapping_add(run_path(compiled.paths[index as usize], tree) as u64);
    }
    let prepared = size_of::<[ExecPath; 16]>() + compiled.calls.len() * size_of::<u8>();
    (black_box(sum), prepared)
}

fn lane_name() -> &'static str {
    #[cfg(lane_flat)]
    { return "flat16"; }
    #[cfg(lane_generator)]
    { return "generator-direct"; }
    #[cfg(lane_compiled)]
    { return "generator-compiled"; }
    #[allow(unreachable_code)]
    "invalid"
}

fn main() {
    let calls = env::args()
        .nth(1)
        .and_then(|s| s.parse::<usize>().ok())
        .filter(|n| *n > 0)
        .unwrap_or(100_000);

    let words = workload(calls);
    let nodes = tree();
    let (checksum, prepared_bytes) = execute(&words, &nodes);

    println!("LANE\t{}", lane_name());
    println!("CALLS\t{calls}");
    println!("CHECKSUM\t{checksum}");
    println!("PREPARED_BYTES\t{prepared_bytes}");
    println!("EXEC_PATH_BYTES\t{}", size_of::<ExecPath>());
}
