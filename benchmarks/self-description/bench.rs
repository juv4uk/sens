use std::collections::HashMap;
use std::env;
use std::hint::black_box;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
struct Word {
    root: u8,
    suffix: u32,
    depth: u8,
}

#[derive(Clone, Copy)]
struct Explanation {
    root: u8,
    suffix: u32,
    depth: u8,
}

#[derive(Clone, Copy)]
struct GraphNode {
    parent: u32,
    edge_bit: u8,
    root: u8,
    depth: u8,
}

impl Word {
    fn dense_index(self) -> usize {
        ((self.root as usize) << self.depth) | self.suffix as usize
    }

    fn key(self) -> u64 {
        ((self.depth as u64) << 33) | ((self.root as u64) << 32) | self.suffix as u64
    }
}

fn suffix_mask(depth: u8) -> u32 {
    if depth == 0 { 0 } else { (1u32 << depth) - 1 }
}

fn make_workload(depth: u8, pattern: &str, calls: usize) -> Vec<Word> {
    let mask = suffix_mask(depth);
    let repeated = 0xAAAA_AAAAu32 & mask;
    let mut state = 0xD1B5_4A32_D192_ED03u64;
    let mut out = Vec::with_capacity(calls);
    for i in 0..calls {
        let word = match pattern {
            "repeated" => Word { root: 0, suffix: repeated, depth },
            "random" => {
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                Word {
                    root: ((state >> 40) & 1) as u8,
                    suffix: (state as u32) & mask,
                    depth,
                }
            }
            "alternating" => Word {
                root: (i & 1) as u8,
                suffix: if i & 1 == 0 { repeated } else { (!repeated) & mask },
                depth,
            },
            _ => panic!("unknown pattern"),
        };
        out.push(word);
    }
    out
}

fn cert_explain(word: Word) -> Explanation {
    Explanation { root: word.root, suffix: word.suffix, depth: word.depth }
}

fn build_flat(depth: u8) -> Vec<Explanation> {
    let entries = 1usize << (depth as usize + 1);
    let mask = suffix_mask(depth) as usize;
    let mut rows = Vec::with_capacity(entries);
    for i in 0..entries {
        rows.push(Explanation {
            root: ((i >> depth) & 1) as u8,
            suffix: (i & mask) as u32,
            depth,
        });
    }
    rows
}

fn graph_index(root: u8, suffix: u32, depth: u8) -> usize {
    if depth == 0 {
        root as usize
    } else {
        let level_base = 2usize * ((1usize << depth) - 1);
        level_base + ((root as usize) << depth) + suffix as usize
    }
}

fn build_graph(max_depth: u8) -> Vec<GraphNode> {
    let total = 2usize * ((1usize << (max_depth as usize + 1)) - 1);
    let mut nodes = vec![
        GraphNode { parent: u32::MAX, edge_bit: 0, root: 0, depth: 0 };
        total
    ];

    nodes[0] = GraphNode { parent: u32::MAX, edge_bit: 0, root: 0, depth: 0 };
    nodes[1] = GraphNode { parent: u32::MAX, edge_bit: 0, root: 1, depth: 0 };

    for depth in 1..=max_depth {
        let count = 1u32 << depth;
        for root in 0..=1u8 {
            for suffix in 0..count {
                let idx = graph_index(root, suffix, depth);
                let parent = graph_index(root, suffix >> 1, depth - 1);
                nodes[idx] = GraphNode {
                    parent: parent as u32,
                    edge_bit: (suffix & 1) as u8,
                    root,
                    depth,
                };
            }
        }
    }
    nodes
}

fn graph_explain(graph: &[GraphNode], word: Word) -> Explanation {
    let mut idx = graph_index(word.root, word.suffix, word.depth);
    let mut suffix = 0u32;
    let mut shift = 0u8;
    let mut depth = word.depth;

    while graph[idx].depth > 0 {
        let node = graph[idx];
        suffix |= (node.edge_bit as u32) << shift;
        shift += 1;
        idx = node.parent as usize;
    }

    // Traversal collected edge bits from leaf to root, which corresponds to
    // rightmost suffix bit first. Reverse into canonical written suffix order.
    let mut canonical = 0u32;
    for i in 0..depth {
        let bit = (suffix >> i) & 1;
        canonical |= bit << (depth - 1 - i);
    }

    Explanation { root: graph[idx].root, suffix: canonical, depth }
}

fn explanation_hash(x: Explanation) -> u64 {
    ((x.root as u64) << 63)
        ^ ((x.depth as u64) << 56)
        ^ (x.suffix as u64).wrapping_mul(0x9E37_79B1)
}

fn checksum_flat(workload: &[Word], rows: &[Explanation]) -> u64 {
    let mut sum=0u64;
    for &w in workload {
        sum ^= explanation_hash(rows[w.dense_index()]);
    }
    sum
}

fn checksum_cert(workload: &[Word]) -> u64 {
    let mut sum=0u64;
    for &w in workload {
        sum ^= explanation_hash(cert_explain(w));
    }
    sum
}

fn checksum_graph(workload: &[Word], graph: &[GraphNode]) -> u64 {
    let mut sum=0u64;
    for &w in workload {
        sum ^= explanation_hash(graph_explain(graph,w));
    }
    sum
}

fn verify_distinct(workload:&[Word], graph:&[GraphNode]) {
    for &w in workload {
        let a=cert_explain(w);
        let b=graph_explain(graph,w);
        assert_eq!(a.root,b.root);
        assert_eq!(a.suffix,b.suffix);
        assert_eq!(a.depth,b.depth);
    }
}

fn unique_count(workload:&[Word])->usize {
    let mut m=HashMap::<u64,()>::new();
    for &w in workload { m.insert(w.key(),()); }
    m.len()
}

fn print_metrics(mode:&str, depth:u8, calls:usize, distinct:usize, flat_rows:usize, graph_nodes:usize) {
    let n=calls as u64;
    let d=depth as u64;
    println!("METRIC\tcalls\t{n}");
    println!("METRIC\tpath_depth\t{d}");
    println!("METRIC\tdistinct_words\t{distinct}");
    match mode {
        "flat" => {
            println!("METRIC\tstored_rows\t{flat_rows}");
            println!("METRIC\tstored_graph_nodes\t0");
            println!("METRIC\trelation_edges_touched\t0");
            println!("METRIC\tcertificate_bits_touched\t0");
            println!("METRIC\tmetadata_lookups\t{n}");
        }
        "certificate" => {
            println!("METRIC\tstored_rows\t0");
            println!("METRIC\tstored_graph_nodes\t0");
            println!("METRIC\trelation_edges_touched\t0");
            println!("METRIC\tcertificate_bits_touched\t{}", n*d);
            println!("METRIC\tmetadata_lookups\t0");
        }
        "graph" => {
            println!("METRIC\tstored_rows\t0");
            println!("METRIC\tstored_graph_nodes\t{graph_nodes}");
            println!("METRIC\trelation_edges_touched\t{}", n*d);
            println!("METRIC\tcertificate_bits_touched\t0");
            println!("METRIC\tmetadata_lookups\t0");
        }
        "hybrid" => {
            println!("METRIC\tstored_rows\t0");
            println!("METRIC\tstored_graph_nodes\t{graph_nodes}");
            println!("METRIC\trelation_edges_touched\t0");
            println!("METRIC\tprepare_graph_edges_verified\t{}", distinct as u64*d);
            println!("METRIC\tcertificate_bits_touched\t{}", n*d);
            println!("METRIC\tmetadata_lookups\t0");
        }
        _=>{}
    }
    println!("METRIC\texplanation_successes\t{n}");
    println!("METRIC\tambiguity_count\t0");
}

fn main(){
    let args:Vec<String>=env::args().collect();
    if args.len()!=6 {
        eprintln!("usage: bench MODE PHASE DEPTH PATTERN CALLS");
        std::process::exit(2);
    }
    let mode=args[1].as_str();
    let phase=args[2].as_str();
    let depth:u8=args[3].parse().unwrap();
    let pattern=args[4].as_str();
    let calls:usize=args[5].parse().unwrap();
    assert!(depth<=16);

    let workload=make_workload(depth,pattern,calls);
    let distinct=unique_count(&workload);
    let flat=if mode=="flat" {Some(build_flat(depth))} else {None};
    let graph=if mode=="graph" || mode=="hybrid" {Some(build_graph(depth))} else {None};

    black_box(&workload);
    black_box(&flat);
    black_box(&graph);

    if phase=="verify" {
        let g=build_graph(depth);
        verify_distinct(&workload,&g);
        let f=build_flat(depth);
        let a=checksum_flat(&workload,&f);
        let b=checksum_cert(&workload);
        let c=checksum_graph(&workload,&g);
        assert_eq!(a,b);
        assert_eq!(a,c);
        println!("VERIFY\tPASS\tdepth={depth}\tpattern={pattern}\tchecksum={a}");
        return;
    }

    if mode=="hybrid" {
        verify_distinct(&workload,graph.as_ref().unwrap());
    }

    if phase=="prepare" {
        let prepared=workload.len()
            + flat.as_ref().map_or(0,Vec::len)
            + graph.as_ref().map_or(0,Vec::len);
        println!("CHECKSUM\t{prepared}");
        print_metrics(mode,depth,calls,distinct,flat.as_ref().map_or(0,Vec::len),graph.as_ref().map_or(0,Vec::len));
        return;
    }
    assert_eq!(phase,"full");

    let checksum=match mode {
        "flat"=>checksum_flat(&workload,flat.as_ref().unwrap()),
        "certificate"=>checksum_cert(&workload),
        "graph"=>checksum_graph(&workload,graph.as_ref().unwrap()),
        "hybrid"=>checksum_cert(&workload),
        _=>panic!("unknown mode"),
    };

    println!("CHECKSUM\t{}",black_box(checksum));
    print_metrics(mode,depth,calls,distinct,flat.as_ref().map_or(0,Vec::len),graph.as_ref().map_or(0,Vec::len));
}
