use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Q {
    n: i128,
    d: i128,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Eval {
    Q(Q),
    Undefined,
}

fn gcd(mut a: i128, mut b: i128) -> i128 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    if a == 0 { 1 } else { a }
}

impl Q {
    fn new(mut n: i128, mut d: i128) -> Self {
        assert!(d != 0);
        if d < 0 {
            n = -n;
            d = -d;
        }
        let g = gcd(n, d);
        Self { n: n / g, d: d / g }
    }

    fn parse(s: &str) -> Self {
        let (n, d) = s.split_once('/').expect("neutral rational must be n/d");
        Self::new(n.parse().unwrap(), d.parse().unwrap())
    }

    fn render(self) -> String {
        format!("{}/{}", self.n, self.d)
    }

    fn add(self, other: Self) -> Self {
        Self::new(self.n * other.d + other.n * self.d, self.d * other.d)
    }

    fn mul(self, other: Self) -> Self {
        Self::new(self.n * other.n, self.d * other.d)
    }

    fn recip(self) -> Eval {
        if self.n == 0 {
            Eval::Undefined
        } else {
            Eval::Q(Self::new(self.d, self.n))
        }
    }
}

fn repo_root() -> PathBuf {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest.parent().unwrap().parent().unwrap().to_path_buf()
}

fn load_json(path: &Path) -> Value {
    serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap()
}

fn expr_calls(node: &Value, out: &mut BTreeSet<String>) {
    if let Some(call) = node.get("call").and_then(Value::as_str) {
        out.insert(call.to_string());
        for arg in node["args"].as_array().unwrap() {
            expr_calls(arg, out);
        }
    }
}

fn eval_expr(
    node: &Value,
    env: &BTreeMap<String, Q>,
    constants: &BTreeMap<String, Q>,
    operations: &BTreeMap<String, Value>,
) -> Eval {
    if let Some(var) = node.get("var").and_then(Value::as_str) {
        return Eval::Q(*env.get(var).expect("unknown variable"));
    }
    if let Some(c) = node.get("const").and_then(Value::as_str) {
        return Eval::Q(*constants.get(c).expect("unknown constant"));
    }

    let call = node["call"].as_str().unwrap();
    let args = node["args"].as_array().unwrap();
    let mut values = Vec::with_capacity(args.len());
    for arg in args {
        match eval_expr(arg, env, constants, operations) {
            Eval::Q(q) => values.push(q),
            Eval::Undefined => return Eval::Undefined,
        }
    }

    match call {
        "add" => Eval::Q(values[0].add(values[1])),
        "mul" => Eval::Q(values[0].mul(values[1])),
        "recip" => values[0].recip(),
        generated => {
            let rule = operations.get(generated).expect("unknown generated operation");
            let inputs = rule["inputs"].as_array().unwrap();
            assert_eq!(inputs.len(), values.len());
            let nested_env: BTreeMap<String, Q> = inputs.iter()
                .zip(values)
                .map(|(name, value)| (name.as_str().unwrap().to_string(), value))
                .collect();
            eval_expr(&rule["expression"], &nested_env, constants, operations)
        }
    }
}

fn topological_generated(spec: &Value) -> Vec<String> {
    let basis: BTreeSet<String> = spec["basis_operations"].as_array().unwrap()
        .iter().map(|v| v["id"].as_str().unwrap().to_string()).collect();
    let rules: BTreeMap<String, Value> = spec["generation_rules"].as_array().unwrap()
        .iter().map(|v| (v["id"].as_str().unwrap().to_string(), v.clone())).collect();

    let mut available = basis;
    let mut remaining = rules.clone();
    let mut order = Vec::new();

    while !remaining.is_empty() {
        let mut progress = false;
        let names: Vec<String> = remaining.keys().cloned().collect();
        for name in names {
            let rule = remaining.get(&name).unwrap();
            let mut calls = BTreeSet::new();
            expr_calls(&rule["expression"], &mut calls);
            if calls.is_subset(&available) {
                available.insert(name.clone());
                order.push(name.clone());
                remaining.remove(&name);
                progress = true;
            }
        }
        assert!(progress, "dependency cycle or unknown operation in neutral IR");
    }
    order
}

fn render_eval(value: Eval) -> String {
    match value {
        Eval::Q(q) => q.render(),
        Eval::Undefined => "UNDEFINED".to_string(),
    }
}

fn semantic_payload(
    op: &str,
    rule: &Value,
    constants: &BTreeMap<String, Q>,
    operations: &BTreeMap<String, Value>,
    corpus: &[String],
) -> (Value, usize) {
    let inputs = rule["inputs"].as_array().unwrap();
    let arity = inputs.len();
    let mut cases: Vec<Vec<String>> = Vec::new();
    let mut outputs: Vec<String> = Vec::new();
    let mut undefined = 0usize;

    fn recurse(
        depth: usize,
        arity: usize,
        corpus: &[String],
        current: &mut Vec<String>,
        out: &mut Vec<Vec<String>>,
    ) {
        if depth == arity {
            out.push(current.clone());
            return;
        }
        for value in corpus {
            current.push(value.clone());
            recurse(depth + 1, arity, corpus, current, out);
            current.pop();
        }
    }

    recurse(0, arity, corpus, &mut Vec::new(), &mut cases);

    for case in &cases {
        let env: BTreeMap<String, Q> = inputs.iter()
            .zip(case.iter())
            .map(|(name, value)| (
                name.as_str().unwrap().to_string(),
                Q::parse(value),
            ))
            .collect();
        let result = eval_expr(&rule["expression"], &env, constants, operations);
        let rendered = render_eval(result);
        if rendered == "UNDEFINED" {
            undefined += 1;
        }
        outputs.push(rendered);
    }

    (
        json!({
            "inputs": cases,
            "operation": op,
            "outputs": outputs,
        }),
        undefined,
    )
}

fn canonical_json(value: &Value) -> String {
    // serde_json::Map is key-sorted in this build's preserve_order-disabled default.
    serde_json::to_string(value).unwrap()
}

fn sha256_hex(s: &str) -> String {
    const K: [u32; 64] = [
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
    ];
    let mut h: [u32; 8] = [
        0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19,
    ];

    let mut msg = s.as_bytes().to_vec();
    let bit_len = (msg.len() as u64) * 8;
    msg.push(0x80);
    while (msg.len() % 64) != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());

    for chunk in msg.chunks_exact(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            let j = i * 4;
            w[i] = u32::from_be_bytes([chunk[j],chunk[j+1],chunk[j+2],chunk[j+3]]);
        }
        for i in 16..64 {
            let s0 = w[i-15].rotate_right(7) ^ w[i-15].rotate_right(18) ^ (w[i-15] >> 3);
            let s1 = w[i-2].rotate_right(17) ^ w[i-2].rotate_right(19) ^ (w[i-2] >> 10);
            w[i] = w[i-16].wrapping_add(s0).wrapping_add(w[i-7]).wrapping_add(s1);
        }

        let mut a=h[0]; let mut b=h[1]; let mut c=h[2]; let mut d=h[3];
        let mut e=h[4]; let mut f=h[5]; let mut g=h[6]; let mut hh=h[7];

        for i in 0..64 {
            let s1=e.rotate_right(6)^e.rotate_right(11)^e.rotate_right(25);
            let ch=(e & f)^((!e)&g);
            let temp1=hh.wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);
            let s0=a.rotate_right(2)^a.rotate_right(13)^a.rotate_right(22);
            let maj=(a & b)^(a & c)^(b & c);
            let temp2=s0.wrapping_add(maj);
            hh=g; g=f; f=e; e=d.wrapping_add(temp1);
            d=c; c=b; b=a; a=temp1.wrapping_add(temp2);
        }

        h[0]=h[0].wrapping_add(a); h[1]=h[1].wrapping_add(b);
        h[2]=h[2].wrapping_add(c); h[3]=h[3].wrapping_add(d);
        h[4]=h[4].wrapping_add(e); h[5]=h[5].wrapping_add(f);
        h[6]=h[6].wrapping_add(g); h[7]=h[7].wrapping_add(hh);
    }

    h.iter().map(|x| format!("{:08x}", x)).collect::<String>()
}

fn expected_cert<'a>(certs: &'a Value, op: &str) -> &'a Value {
    certs["certificates"].as_array().unwrap()
        .iter().find(|c| c["operation"].as_str() == Some(op)).unwrap()
}

fn minimal_mutant_divergence(
    sub_rule: &Value,
    constants: &BTreeMap<String, Q>,
    operations: &BTreeMap<String, Value>,
    corpus: &[String],
) -> (Vec<String>, String, String) {
    let mut mutant = sub_rule.clone();
    mutant["expression"] = json!({
        "call": "add",
        "args": [{"var":"x"},{"var":"y"}]
    });

    for x in corpus {
        for y in corpus {
            let env = BTreeMap::from([
                ("x".to_string(), Q::parse(x)),
                ("y".to_string(), Q::parse(y)),
            ]);
            let good = render_eval(eval_expr(
                &sub_rule["expression"], &env, constants, operations
            ));
            let bad = render_eval(eval_expr(
                &mutant["expression"], &env, constants, operations
            ));
            if good != bad {
                return (vec![x.clone(), y.clone()], good, bad);
            }
        }
    }
    panic!("mutated SUB unexpectedly matched full corpus")
}

fn main() {
    let root = repo_root();
    let spec = load_json(&root.join("docs/research/2433-core-math-neutral-v1.json"));
    let certs = load_json(&root.join("docs/research/2433-core-math-generation-certificates.json"));

    assert_eq!(spec["schema"], "core-math-neutral/v1");
    assert_eq!(spec["status"], "research-only");

    let constants: BTreeMap<String, Q> = spec["constants"].as_array().unwrap()
        .iter().map(|v| (
            v["id"].as_str().unwrap().to_string(),
            Q::parse(v["value"].as_str().unwrap()),
        )).collect();

    let operations: BTreeMap<String, Value> = spec["generation_rules"].as_array().unwrap()
        .iter().map(|v| (v["id"].as_str().unwrap().to_string(), v.clone())).collect();

    let order = topological_generated(&spec);
    assert!(order.iter().position(|x| x == "neg").unwrap()
        < order.iter().position(|x| x == "sub").unwrap());

    let corpus: Vec<String> = certs["corpus"].as_array().unwrap()
        .iter().map(|v| v.as_str().unwrap().to_string()).collect();

    let mut checked = 0usize;
    for op in &order {
        let rule = operations.get(op).unwrap();
        let (payload, undefined) = semantic_payload(
            op, rule, &constants, &operations, &corpus
        );
        let digest = sha256_hex(&canonical_json(&payload));
        let expected = expected_cert(&certs, op);
        assert_eq!(digest, expected["semantic_signature_sha256"].as_str().unwrap());
        assert_eq!(undefined.to_string(), expected["undefined_cases"].as_str().unwrap());
        checked += 1;
        println!(
            "CERT op={} sha256={} undefined={}",
            op, digest, undefined
        );
    }

    // Explicit zero partiality from the independently executed neutral rule.
    let div = operations.get("div").unwrap();
    let env = BTreeMap::from([
        ("x".to_string(), Q::new(1, 1)),
        ("y".to_string(), Q::new(0, 1)),
    ]);
    assert_eq!(
        eval_expr(&div["expression"], &env, &constants, &operations),
        Eval::Undefined
    );

    // Minimal divergence control: corrupt SUB and emit first differing corpus case.
    let sub = operations.get("sub").unwrap();
    let (input, good, bad) = minimal_mutant_divergence(
        sub, &constants, &operations, &corpus
    );

    println!("EXECUTOR=standalone-rust");
    println!("INTERNAL-Q=i128-pair-gcd-normalized");
    println!("GENERATED-ORDER={}", order.join(","));
    println!("CERTIFICATES-MATCHED={}", checked);
    println!("ZERO-DIVISION-PARTIALITY=PASS");
    println!("SENS-EVALUATOR-CALLS=0");
    println!("CORE-LISP-READS=0");
    println!("COPIED-CLOSURE-ROWS=0");
    println!(
        "MUTANT-DIVERGENCE op=sub input={} expected={} mutant={}",
        input.join(","), good, bad
    );
    println!("MINIMAL-DIVERGENCE-REPORT=PASS");
    println!("STATUS=PASS-INDEPENDENT-RUST-EXECUTOR");
    println!("AUTHORITY=RESEARCH-ONLY");
}
