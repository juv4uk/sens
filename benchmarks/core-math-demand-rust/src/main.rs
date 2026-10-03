use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

const CORPUS: [&str; 7] = [
    "-2/1", "-1/1", "-1/2", "0/1", "1/2", "1/1", "2/1",
];
const LAWSET_VERSION: &str = "exact-q-equivalence-set/v1";

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

#[derive(Clone, Debug)]
struct Operation {
    identity: String,
    arity: usize,
    depth: usize,
    expr: Value,
    partiality: Value,
    signature_sha256: String,
    undefined_cases: usize,
}

#[derive(Default, Debug)]
struct Counters {
    basis_refs: usize,
    ref_edges: usize,
    constructor_apps: usize,
    generated_materializations: usize,
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

    fn parse(s: &str) -> Result<Self, String> {
        let (n, d) = s
            .split_once('/')
            .ok_or_else(|| format!("rational must be n/d: {s}"))?;
        let n = n.parse::<i128>().map_err(|e| e.to_string())?;
        let d = d.parse::<i128>().map_err(|e| e.to_string())?;
        if d == 0 {
            return Err("zero denominator".to_string());
        }
        Ok(Self::new(n, d))
    }

    fn render(self) -> String {
        format!("{}/{}", self.n, self.d)
    }

    fn add(self, other: Self) -> Self {
        Self::new(
            self.n * other.d + other.n * self.d,
            self.d * other.d,
        )
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

fn load_json(path: &Path) -> Result<Value, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn canonical_json(value: &Value) -> String {
    serde_json::to_string(value).expect("json serialization")
}

fn sha256_hex(text: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn arg(index: usize) -> Value {
    json!({"arg": index})
}

fn constant(name: &str) -> Value {
    json!({"const": name})
}

fn call(name: &str, args: Vec<Value>) -> Value {
    json!({"call": name, "args": args})
}

fn true_cond() -> Value {
    json!({"true": true})
}

fn nonzero(expr: Value) -> Value {
    json!({"nonzero": expr})
}

fn normalize_expr(node: &Value) -> Result<Value, String> {
    if node.get("arg").is_some() || node.get("const").is_some() {
        return Ok(node.clone());
    }

    let op = node
        .get("call")
        .and_then(Value::as_str)
        .ok_or_else(|| format!("unknown expression node: {}", canonical_json(node)))?;
    let raw_args = node
        .get("args")
        .and_then(Value::as_array)
        .ok_or_else(|| "call missing args".to_string())?;

    let mut args: Vec<Value> = raw_args
        .iter()
        .map(normalize_expr)
        .collect::<Result<Vec<_>, _>>()?;

    if op == "add" || op == "mul" {
        let mut flat = Vec::new();
        for child in args {
            if child.get("call").and_then(Value::as_str) == Some(op) {
                let nested = child["args"]
                    .as_array()
                    .ok_or_else(|| "normalized call missing args".to_string())?;
                flat.extend(nested.iter().cloned());
            } else {
                flat.push(child);
            }
        }
        flat.sort_by_key(canonical_json);
        args = flat;
    }

    Ok(call(op, args))
}

fn and_cond(conds: Vec<Value>) -> Result<Value, String> {
    let mut flat = Vec::new();
    for cond in conds {
        if cond.get("true").and_then(Value::as_bool) == Some(true) {
            continue;
        }
        if let Some(items) = cond.get("and").and_then(Value::as_array) {
            flat.extend(items.iter().cloned());
        } else {
            flat.push(cond);
        }
    }
    if flat.is_empty() {
        return Ok(true_cond());
    }

    let mut by_json: BTreeMap<String, Value> = BTreeMap::new();
    for item in flat {
        by_json.insert(canonical_json(&item), item);
    }
    let values: Vec<Value> = by_json.into_values().collect();
    if values.len() == 1 {
        Ok(values[0].clone())
    } else {
        Ok(json!({"and": values}))
    }
}

fn normalize_cond(node: &Value) -> Result<Value, String> {
    if node.get("true").and_then(Value::as_bool) == Some(true) {
        return Ok(true_cond());
    }
    if let Some(expr) = node.get("nonzero") {
        return Ok(nonzero(normalize_expr(expr)?));
    }
    if let Some(items) = node.get("and").and_then(Value::as_array) {
        let normalized = items
            .iter()
            .map(normalize_cond)
            .collect::<Result<Vec<_>, _>>()?;
        return and_cond(normalized);
    }
    Err(format!("unknown partiality node: {}", canonical_json(node)))
}

fn substitute_expr(
    node: &Value,
    mapping: &BTreeMap<usize, Value>,
) -> Result<Value, String> {
    if let Some(i) = node.get("arg").and_then(Value::as_u64) {
        return Ok(mapping
            .get(&(i as usize))
            .cloned()
            .unwrap_or_else(|| node.clone()));
    }
    if node.get("const").is_some() {
        return Ok(node.clone());
    }
    let op = node
        .get("call")
        .and_then(Value::as_str)
        .ok_or_else(|| "substitute: unknown expression".to_string())?;
    let args = node["args"]
        .as_array()
        .ok_or_else(|| "substitute: call missing args".to_string())?
        .iter()
        .map(|x| substitute_expr(x, mapping))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(call(op, args))
}

fn substitute_cond(
    node: &Value,
    mapping: &BTreeMap<usize, Value>,
) -> Result<Value, String> {
    if node.get("true").and_then(Value::as_bool) == Some(true) {
        return Ok(true_cond());
    }
    if let Some(expr) = node.get("nonzero") {
        return Ok(nonzero(substitute_expr(expr, mapping)?));
    }
    if let Some(items) = node.get("and").and_then(Value::as_array) {
        let children = items
            .iter()
            .map(|x| substitute_cond(x, mapping))
            .collect::<Result<Vec<_>, _>>()?;
        return and_cond(children);
    }
    Err("substitute_cond: unknown node".to_string())
}

fn identity_payload(
    arity: usize,
    expr: &Value,
    partiality: &Value,
    laws: &[String],
) -> Result<Value, String> {
    let mut sorted_laws = laws.to_vec();
    sorted_laws.sort();
    Ok(json!({
        "schema": "core-math-autonomous-op-identity/v1",
        "carrier": "Q",
        "arity": arity,
        "lawset_version": LAWSET_VERSION,
        "normalization_laws": sorted_laws,
        "expression": normalize_expr(expr)?,
        "partiality": normalize_cond(partiality)?,
    }))
}

fn generated_identity(
    arity: usize,
    expr: &Value,
    partiality: &Value,
    laws: &[String],
) -> Result<String, String> {
    let payload = identity_payload(arity, expr, partiality, laws)?;
    Ok(sha256_hex(&canonical_json(&payload)))
}

fn render_eval(value: Eval) -> String {
    match value {
        Eval::Q(q) => q.render(),
        Eval::Undefined => "UNDEFINED".to_string(),
    }
}

fn eval_expr(
    node: &Value,
    argv: &[Q],
    constants: &BTreeMap<String, Q>,
) -> Result<Eval, String> {
    if let Some(i) = node.get("arg").and_then(Value::as_u64) {
        return argv
            .get(i as usize)
            .copied()
            .map(Eval::Q)
            .ok_or_else(|| format!("arg index out of range: {i}"));
    }
    if let Some(name) = node.get("const").and_then(Value::as_str) {
        return constants
            .get(name)
            .copied()
            .map(Eval::Q)
            .ok_or_else(|| format!("unknown constant: {name}"));
    }

    let op = node
        .get("call")
        .and_then(Value::as_str)
        .ok_or_else(|| "eval: unknown expression node".to_string())?;
    let raw_args = node["args"]
        .as_array()
        .ok_or_else(|| "eval: call missing args".to_string())?;

    let mut values = Vec::new();
    for child in raw_args {
        match eval_expr(child, argv, constants)? {
            Eval::Q(q) => values.push(q),
            Eval::Undefined => return Ok(Eval::Undefined),
        }
    }

    match op {
        "add" if values.len() == 2 => Ok(Eval::Q(values[0].add(values[1]))),
        "mul" if values.len() == 2 => Ok(Eval::Q(values[0].mul(values[1]))),
        "recip" if values.len() == 1 => Ok(values[0].recip()),
        _ => Err(format!("unknown/invalid basis call: {op}/{}", values.len())),
    }
}

fn cartesian_cases(arity: usize) -> Vec<Vec<String>> {
    fn rec(depth: usize, arity: usize, cur: &mut Vec<String>, out: &mut Vec<Vec<String>>) {
        if depth == arity {
            out.push(cur.clone());
            return;
        }
        for value in CORPUS {
            cur.push(value.to_string());
            rec(depth + 1, arity, cur, out);
            cur.pop();
        }
    }

    let mut out = Vec::new();
    rec(0, arity, &mut Vec::new(), &mut out);
    out
}

fn attach_signature(
    op: &mut Operation,
    constants: &BTreeMap<String, Q>,
) -> Result<(), String> {
    let cases = cartesian_cases(op.arity);
    let mut outputs = Vec::new();
    let mut undefined = 0usize;

    for case in &cases {
        let argv = case
            .iter()
            .map(|x| Q::parse(x))
            .collect::<Result<Vec<_>, _>>()?;
        let rendered = render_eval(eval_expr(&op.expr, &argv, constants)?);
        if rendered == "UNDEFINED" {
            undefined += 1;
        }
        outputs.push(rendered);
    }

    let payload = json!({
        "arity": op.arity,
        "inputs": cases,
        "outputs": outputs,
    });
    op.signature_sha256 = sha256_hex(&canonical_json(&payload));
    op.undefined_cases = undefined;
    Ok(())
}

fn basis_operations(
    spec: &Value,
    laws: &[String],
    constants: &BTreeMap<String, Q>,
) -> Result<BTreeMap<String, Operation>, String> {
    let rows = spec["basis_operations"]
        .as_array()
        .ok_or_else(|| "basis_operations must be array".to_string())?;

    let mut out = BTreeMap::new();
    for row in rows {
        let id = row["id"]
            .as_str()
            .ok_or_else(|| "basis id missing".to_string())?;
        let arity = row["arity"]
            .as_u64()
            .ok_or_else(|| "basis arity missing".to_string())? as usize;
        let expr = call(id, (0..arity).map(arg).collect());
        let partiality = match row["partiality"].as_str() {
            Some("total") => true_cond(),
            Some("undefined-at-zero") if arity == 1 => nonzero(arg(0)),
            Some(other) => return Err(format!("unsupported basis partiality: {other}")),
            None => return Err("basis partiality missing".to_string()),
        };
        let mut op = Operation {
            identity: format!("basis:{id}"),
            arity,
            depth: 0,
            expr,
            partiality,
            signature_sha256: String::new(),
            undefined_cases: 0,
        };
        // Basis identities are named roots; generated identities never use their
        // display strings directly, only the expanded basis expression.
        let _ = laws;
        attach_signature(&mut op, constants)?;
        out.insert(id.to_string(), op);
    }
    Ok(out)
}

fn bind_left(
    binary: &Operation,
    constant_id: &str,
    laws: &[String],
    constants: &BTreeMap<String, Q>,
) -> Result<Operation, String> {
    if binary.arity != 2 {
        return Err("bind-left requires binary operation".to_string());
    }
    if !constants.contains_key(constant_id) {
        return Err(format!("constant unavailable: {constant_id}"));
    }
    let mapping = BTreeMap::from([
        (0usize, constant(constant_id)),
        (1usize, arg(0)),
    ]);
    let expr = substitute_expr(&binary.expr, &mapping)?;
    let partiality = substitute_cond(&binary.partiality, &mapping)?;
    let identity = generated_identity(1, &expr, &partiality, laws)?;
    let mut op = Operation {
        identity,
        arity: 1,
        depth: binary.depth + 1,
        expr,
        partiality,
        signature_sha256: String::new(),
        undefined_cases: 0,
    };
    attach_signature(&mut op, constants)?;
    Ok(op)
}

fn map_right(
    binary: &Operation,
    unary: &Operation,
    laws: &[String],
    constants: &BTreeMap<String, Q>,
) -> Result<Operation, String> {
    if binary.arity != 2 || unary.arity != 1 {
        return Err("map-right requires binary + unary operands".to_string());
    }

    let unary_expr = substitute_expr(
        &unary.expr,
        &BTreeMap::from([(0usize, arg(1))]),
    )?;
    let unary_part = substitute_cond(
        &unary.partiality,
        &BTreeMap::from([(0usize, arg(1))]),
    )?;

    let mapping = BTreeMap::from([
        (0usize, arg(0)),
        (1usize, unary_expr),
    ]);
    let expr = substitute_expr(&binary.expr, &mapping)?;
    let binary_part = substitute_cond(&binary.partiality, &mapping)?;
    let partiality = and_cond(vec![unary_part, binary_part])?;
    let identity = generated_identity(2, &expr, &partiality, laws)?;

    let mut op = Operation {
        identity,
        arity: 2,
        depth: binary.depth.max(unary.depth) + 1,
        expr,
        partiality,
        signature_sha256: String::new(),
        undefined_cases: 0,
    };
    attach_signature(&mut op, constants)?;
    Ok(op)
}

struct Resolver {
    requests: BTreeMap<String, Value>,
    basis: BTreeMap<String, Operation>,
    constants: BTreeMap<String, Q>,
    schemas: BTreeSet<String>,
    laws: Vec<String>,
    memo: BTreeMap<String, Operation>,
    stack: Vec<String>,
    counters: Counters,
}

impl Resolver {
    fn new(spec: &Value, request_doc: &Value) -> Result<Self, String> {
        if request_doc["lawset_version"].as_str() != Some(LAWSET_VERSION) {
            return Err("request lawset version is not admitted".to_string());
        }

        let mut laws = spec["normalization_laws"]
            .as_array()
            .ok_or_else(|| "normalization_laws missing".to_string())?
            .iter()
            .map(|x| x.as_str().unwrap().to_string())
            .collect::<Vec<_>>();
        laws.sort();

        let expected = vec![
            "Q.add.associative/v1".to_string(),
            "Q.add.commutative/v1".to_string(),
            "Q.mul.associative/v1".to_string(),
            "Q.mul.commutative/v1".to_string(),
        ];
        if laws != expected {
            return Err("active normalization law set is not validated v1".to_string());
        }

        let constants = spec["constants"]
            .as_array()
            .ok_or_else(|| "constants missing".to_string())?
            .iter()
            .map(|x| {
                let id = x["id"].as_str().unwrap().to_string();
                let q = Q::parse(x["value"].as_str().unwrap()).unwrap();
                (id, q)
            })
            .collect::<BTreeMap<_, _>>();

        let basis = basis_operations(spec, &laws, &constants)?;

        let schemas = spec["constructor_schemas"]
            .as_array()
            .ok_or_else(|| "constructor_schemas missing".to_string())?
            .iter()
            .map(|x| x["id"].as_str().unwrap().to_string())
            .collect::<BTreeSet<_>>();

        let requests = request_doc["requests"]
            .as_array()
            .ok_or_else(|| "requests missing".to_string())?
            .iter()
            .map(|x| {
                (
                    x["id"].as_str().unwrap().to_string(),
                    x["certificate"].clone(),
                )
            })
            .collect::<BTreeMap<_, _>>();

        Ok(Self {
            requests,
            basis,
            constants,
            schemas,
            laws,
            memo: BTreeMap::new(),
            stack: Vec::new(),
            counters: Counters::default(),
        })
    }

    fn resolve_request(&mut self, request_id: &str) -> Result<Operation, String> {
        if self.stack.iter().any(|x| x == request_id) {
            return Err(format!("cyclic request reference: {request_id}"));
        }
        let cert = self.requests
            .get(request_id)
            .cloned()
            .ok_or_else(|| format!("unknown request: {request_id}"))?;
        self.stack.push(request_id.to_string());
        let result = self.resolve_cert(&cert);
        self.stack.pop();
        result
    }

    fn resolve_cert(&mut self, cert: &Value) -> Result<Operation, String> {
        let key = sha256_hex(&canonical_json(&json!({
            "schema": "core-math-demand-certificate-key/v1",
            "lawset_version": LAWSET_VERSION,
            "certificate": cert,
        })));
        if let Some(op) = self.memo.get(&key) {
            return Ok(op.clone());
        }

        if let Some(name) = cert.get("basis").and_then(Value::as_str) {
            self.counters.basis_refs += 1;
            let op = self.basis
                .get(name)
                .cloned()
                .ok_or_else(|| format!("basis operation unavailable: {name}"))?;
            self.memo.insert(key, op.clone());
            return Ok(op);
        }

        if let Some(request_id) = cert.get("ref").and_then(Value::as_str) {
            self.counters.ref_edges += 1;
            let op = self.resolve_request(request_id)?;
            self.memo.insert(key, op.clone());
            return Ok(op);
        }

        let constructor = cert["constructor"]
            .as_str()
            .ok_or_else(|| "certificate constructor missing".to_string())?;
        if !self.schemas.contains(constructor) {
            return Err(format!("constructor unavailable: {constructor}"));
        }

        let op = match constructor {
            "bind-left-constant" => {
                let binary_cert = cert.get("binary")
                    .ok_or_else(|| "bind-left certificate missing binary operand".to_string())?;
                let constant_id = cert["constant"]
                    .as_str()
                    .ok_or_else(|| "bind-left constant missing".to_string())?;
                let binary = self.resolve_cert(binary_cert)?;
                self.counters.constructor_apps += 1;
                bind_left(&binary, constant_id, &self.laws, &self.constants)?
            }
            "map-right" => {
                let binary_cert = cert.get("binary")
                    .ok_or_else(|| "map-right certificate missing binary operand".to_string())?;
                let unary_cert = cert.get("unary")
                    .ok_or_else(|| "map-right certificate missing unary operand".to_string())?;
                let binary = self.resolve_cert(binary_cert)?;
                let unary = self.resolve_cert(unary_cert)?;
                self.counters.constructor_apps += 1;
                map_right(&binary, &unary, &self.laws, &self.constants)?
            }
            other => return Err(format!("unsupported constructor: {other}")),
        };

        self.counters.generated_materializations += 1;
        self.memo.insert(key, op.clone());
        Ok(op)
    }
}

fn remove_basis(spec: &Value, id: &str) -> Value {
    let mut out = spec.clone();
    let rows = out["basis_operations"].as_array_mut().unwrap();
    rows.retain(|x| x["id"].as_str() != Some(id));
    out
}

fn remove_schema(spec: &Value, id: &str) -> Value {
    let mut out = spec.clone();
    let rows = out["constructor_schemas"].as_array_mut().unwrap();
    rows.retain(|x| x["id"].as_str() != Some(id));
    out
}

fn negative_controls(spec: &Value, requests: &Value) -> Result<(), String> {
    let no_mul = remove_basis(spec, "mul");
    let mut resolver = Resolver::new(&no_mul, requests)?;
    let err = resolver.resolve_request("r1").unwrap_err();
    assert!(err.contains("basis operation unavailable"));

    let no_map = remove_schema(spec, "map-right");
    let mut resolver = Resolver::new(&no_map, requests)?;
    let err = resolver.resolve_request("r2").unwrap_err();
    assert!(err.contains("constructor unavailable"));

    let mut wrong_law = requests.clone();
    wrong_law["lawset_version"] = Value::String("exact-q-equivalence-set/v2".to_string());
    let err = match Resolver::new(spec, &wrong_law) {
        Ok(_) => return Err("wrong lawset unexpectedly admitted".to_string()),
        Err(err) => err,
    };
    assert!(err.contains("lawset version"));

    let mut bad_type = requests.clone();
    bad_type["requests"].as_array_mut().unwrap().push(json!({
        "id": "bad-type",
        "certificate": {
            "constructor": "map-right",
            "binary": {"basis": "recip"},
            "unary": {"basis": "add"}
        }
    }));
    let mut resolver = Resolver::new(spec, &bad_type)?;
    let err = resolver.resolve_request("bad-type").unwrap_err();
    assert!(err.contains("map-right requires binary + unary"));

    Ok(())
}

fn main() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    let out_dir = args
        .windows(2)
        .find(|pair| pair[0] == "--out")
        .map(|pair| PathBuf::from(&pair[1]))
        .ok_or_else(|| "usage: core-math-demand-rust --out DIR".to_string())?;
    fs::create_dir_all(&out_dir).map_err(|e| e.to_string())?;

    let root = repo_root();
    let spec = load_json(&root.join("benchmarks/core-math-autonomous-closure/spec.json"))?;
    let requests = load_json(&root.join("benchmarks/core-math-demand-derivation/requests.json"))?;

    assert!(spec.get("generation_rules").is_none());

    let mut resolver = Resolver::new(&spec, &requests)?;
    let mut rows = Vec::new();

    for request_id in ["r1", "r2", "r3"] {
        let op = resolver.resolve_request(request_id)?;
        rows.push((
            request_id.to_string(),
            op.identity,
            op.depth,
            op.arity,
            op.signature_sha256,
            op.undefined_cases,
        ));
    }

    // The generic request set should materialize exactly r1/r2/r3; r2 reuses r1.
    assert_eq!(resolver.counters.generated_materializations, 3);
    assert_eq!(resolver.counters.constructor_apps, 3);

    negative_controls(&spec, &requests)?;

    let mut tsv = String::from(
        "request_id\tidentity\tdepth\tarity\tsignature_sha256\tundefined_cases\n"
    );
    for (id, identity, depth, arity, sig, undefined) in &rows {
        tsv.push_str(&format!(
            "{id}\t{identity}\t{depth}\t{arity}\t{sig}\t{undefined}\n"
        ));
    }
    fs::write(out_dir.join("rust-results.tsv"), tsv).map_err(|e| e.to_string())?;

    let artifact = json!({
        "schema": "core-math-demand-rust-result/v1",
        "authority": "research-only",
        "executor": "standalone-rust",
        "internal_q": "i128-pair-gcd-normalized",
        "request_count": rows.len(),
        "generated_materializations": resolver.counters.generated_materializations,
        "constructor_apps": resolver.counters.constructor_apps,
        "basis_refs": resolver.counters.basis_refs,
        "ref_edges": resolver.counters.ref_edges,
        "guards": {
            "sens_evaluator_calls": 0,
            "core_lisp_reads": 0,
            "python_subprocess_or_import": 0,
            "copied_closure_rows": 0,
            "copied_generated_identities": 0,
            "per_result_generation_rules": 0,
            "negative_controls": "PASS"
        },
        "rows": rows.iter().map(|(id, identity, depth, arity, sig, undefined)| json!({
            "request_id": id,
            "identity": identity,
            "depth": depth,
            "arity": arity,
            "signature_sha256": sig,
            "undefined_cases": undefined,
        })).collect::<Vec<_>>(),
    });
    fs::write(
        out_dir.join("rust-result.json"),
        serde_json::to_string_pretty(&artifact).unwrap() + "\n",
    ).map_err(|e| e.to_string())?;

    println!("EXECUTOR=standalone-rust-demand");
    println!("REQUESTS=r1,r2,r3");
    println!("GENERATED-MATERIALIZATIONS={}", resolver.counters.generated_materializations);
    println!("CONSTRUCTOR-APPS={}", resolver.counters.constructor_apps);
    println!("SENS-EVALUATOR-CALLS=0");
    println!("CORE-LISP-READS=0");
    println!("PYTHON-SUBPROCESS-OR-IMPORT=0");
    println!("COPIED-CLOSURE-ROWS=0");
    println!("COPIED-GENERATED-IDENTITIES=0");
    println!("PER-RESULT-GENERATION-RULES=0");
    println!("NEGATIVE-CONTROLS=PASS");
    for (id, identity, depth, arity, sig, undefined) in rows {
        println!(
            "REQUEST id={id} identity={identity} depth={depth} arity={arity} signature={sig} undefined={undefined}"
        );
    }
    println!("STATUS=PASS-INDEPENDENT-RUST-DEMAND-REPLAY");
    println!("AUTHORITY=RESEARCH-ONLY");

    Ok(())
}
