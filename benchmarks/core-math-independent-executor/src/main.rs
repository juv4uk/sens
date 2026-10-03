use serde_json::{json, Value};
use sha2::{Digest, Sha256};
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
    let mut hasher = Sha256::new();
    hasher.update(s.as_bytes());
    format!("{:x}", hasher.finalize())
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
