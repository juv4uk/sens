use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::env;
use std::fs;

const DEFAULT_SPEC: &str = "docs/research/2433-core-math-neutral-v1.json";
const DEFAULT_CERTS: &str = "docs/research/2433-core-math-generation-certificates.json";

#[derive(Clone, Debug, Deserialize)]
struct Spec {
    schema: String,
    status: String,
    carrier: Carrier,
    constants: Vec<Constant>,
    basis_operations: Vec<Operation>,
    generation_rules: Vec<Rule>,
}

#[derive(Clone, Debug, Deserialize)]
struct Carrier {
    id: String,
    kind: String,
    normalization: String,
    partiality: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Constant {
    id: String,
    carrier: String,
    value: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Operation {
    id: String,
    inputs: Vec<String>,
    output: String,
    partiality: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Rule {
    id: String,
    inputs: Vec<String>,
    output: String,
    partiality: String,
    expression: Expr,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum Expr {
    Var { var: String },
    Const {
        #[serde(rename = "const")]
        constant: String,
    },
    Call { call: String, args: Vec<Expr> },
}

#[derive(Clone, Debug, Deserialize)]
struct CertificateArtifact {
    certificates: Vec<ExpectedCertificate>,
    corpus: Vec<String>,
    schema: String,
    authority: String,
}

#[derive(Clone, Debug, Deserialize)]
struct ExpectedCertificate {
    operation: String,
    dependencies: Vec<String>,
    cases: String,
    undefined_cases: String,
    semantic_signature_sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct Q {
    negative: bool,
    numerator: u128,
    denominator: u128,
}

impl Q {
    fn new(negative: bool, numerator: u128, denominator: u128) -> Result<Self, String> {
        if denominator == 0 {
            return Err("zero denominator".into());
        }
        if numerator == 0 {
            return Ok(Self {
                negative: false,
                numerator: 0,
                denominator: 1,
            });
        }
        let g = gcd(numerator, denominator);
        Ok(Self {
            negative,
            numerator: numerator / g,
            denominator: denominator / g,
        })
    }

    fn parse(text: &str) -> Result<Self, String> {
        let (n, d) = text
            .split_once('/')
            .ok_or_else(|| format!("not a rational: {text}"))?;
        let n: i128 = n.parse().map_err(|_| format!("bad numerator: {text}"))?;
        let d: i128 = d.parse().map_err(|_| format!("bad denominator: {text}"))?;
        if d == 0 {
            return Err("zero denominator".into());
        }
        let negative = (n < 0) ^ (d < 0);
        Self::new(negative, n.unsigned_abs(), d.unsigned_abs())
    }

    fn signed_numerator(&self) -> Result<i128, String> {
        let n = i128::try_from(self.numerator).map_err(|_| "numerator overflow")?;
        Ok(if self.negative { -n } else { n })
    }

    fn signed_denominator(&self) -> Result<i128, String> {
        i128::try_from(self.denominator).map_err(|_| "denominator overflow".into())
    }

    fn add(&self, rhs: &Self) -> Result<Self, String> {
        let an = self.signed_numerator()?;
        let ad = self.signed_denominator()?;
        let bn = rhs.signed_numerator()?;
        let bd = rhs.signed_denominator()?;
        let n = an
            .checked_mul(bd)
            .and_then(|x| bn.checked_mul(ad).and_then(|y| x.checked_add(y)))
            .ok_or_else(|| "add overflow".to_string())?;
        let d = ad.checked_mul(bd).ok_or_else(|| "add denominator overflow".to_string())?;
        Self::from_signed(n, d)
    }

    fn mul(&self, rhs: &Self) -> Result<Self, String> {
        let an = self.signed_numerator()?;
        let ad = self.signed_denominator()?;
        let bn = rhs.signed_numerator()?;
        let bd = rhs.signed_denominator()?;
        let n = an.checked_mul(bn).ok_or_else(|| "mul overflow".to_string())?;
        let d = ad.checked_mul(bd).ok_or_else(|| "mul denominator overflow".to_string())?;
        Self::from_signed(n, d)
    }

    fn recip(&self) -> Result<Option<Self>, String> {
        if self.numerator == 0 {
            return Ok(None);
        }
        Ok(Some(Self::new(
            self.negative,
            self.denominator,
            self.numerator,
        )?))
    }

    fn from_signed(n: i128, d: i128) -> Result<Self, String> {
        if d == 0 {
            return Err("zero denominator".into());
        }
        Self::new((n < 0) ^ (d < 0), n.unsigned_abs(), d.unsigned_abs())
    }

    fn render(&self) -> String {
        let prefix = if self.negative { "-" } else { "" };
        format!("{prefix}{}/{}", self.numerator, self.denominator)
    }
}

fn gcd(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    if a == 0 { 1 } else { a }
}

fn sha256_hex(data: &[u8]) -> String {
    const H0: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ];
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ];

    let bit_len = (data.len() as u64).wrapping_mul(8);
    let mut msg = data.to_vec();
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());

    let mut h = H0;
    for chunk in msg.chunks_exact(64) {
        let mut w = [0u32; 64];
        for (i, word) in w[..16].iter_mut().enumerate() {
            let j = i * 4;
            *word = u32::from_be_bytes([
                chunk[j],
                chunk[j + 1],
                chunk[j + 2],
                chunk[j + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7)
                ^ w[i - 15].rotate_right(18)
                ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17)
                ^ w[i - 2].rotate_right(19)
                ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }

        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = h;
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    h.iter().map(|word| format!("{word:08x}")).collect()
}

#[derive(Debug, Serialize)]
struct SignaturePayload {
    inputs: Vec<Vec<String>>,
    operation: String,
    outputs: Vec<String>,
}

#[derive(Clone, Debug)]
struct Evidence {
    operation: String,
    dependencies: Vec<String>,
    inputs: Vec<Vec<String>>,
    outputs: Vec<String>,
    undefined: usize,
    sha256: String,
}

fn load_json<T: for<'de> Deserialize<'de>>(path: &str) -> Result<T, String> {
    let bytes = fs::read(path).map_err(|e| format!("{path}: {e}"))?;
    serde_json::from_slice(&bytes).map_err(|e| format!("{path}: {e}"))
}

fn called_operations(expr: &Expr, out: &mut BTreeSet<String>) {
    if let Expr::Call { call, args } = expr {
        out.insert(call.clone());
        for arg in args {
            called_operations(arg, out);
        }
    }
}

fn topo_order(spec: &Spec) -> Result<Vec<String>, String> {
    let basis: BTreeSet<_> = spec.basis_operations.iter().map(|x| x.id.clone()).collect();
    let rules: BTreeMap<_, _> = spec
        .generation_rules
        .iter()
        .map(|r| (r.id.clone(), r))
        .collect();
    let generated: BTreeSet<_> = rules.keys().cloned().collect();
    let mut available = basis;
    let mut remaining: Vec<_> = spec.generation_rules.iter().map(|r| r.id.clone()).collect();
    let mut order = Vec::new();

    while !remaining.is_empty() {
        let mut next = Vec::new();
        let mut progress = false;
        for id in remaining {
            let rule = rules[&id];
            let mut deps = BTreeSet::new();
            called_operations(&rule.expression, &mut deps);
            if deps.iter().all(|d| available.contains(d)) {
                available.insert(id.clone());
                order.push(id);
                progress = true;
            } else {
                next.push(id);
            }
        }
        if !progress {
            return Err(format!(
                "unresolved generation rules: {:?}; generated={:?}",
                next, generated
            ));
        }
        remaining = next;
    }
    Ok(order)
}

fn eval_operation(
    name: &str,
    args: &[Q],
    spec: &Spec,
    constants: &HashMap<String, Q>,
    rules: &HashMap<String, Rule>,
    stack: &mut Vec<String>,
) -> Result<Option<Q>, String> {
    let basis = spec
        .basis_operations
        .iter()
        .find(|op| op.id == name);

    if let Some(op) = basis {
        if args.len() != op.inputs.len() {
            return Err(format!("arity mismatch for {name}"));
        }
        return match name {
            "add" => Ok(Some(args[0].add(&args[1])?)),
            "mul" => Ok(Some(args[0].mul(&args[1])?)),
            "recip" => args[0].recip(),
            _ => Err(format!("independent executor has no basis mechanism for {name}")),
        };
    }

    let rule = rules
        .get(name)
        .ok_or_else(|| format!("unknown operation: {name}"))?;
    if args.len() != rule.inputs.len() {
        return Err(format!("arity mismatch for generated operation {name}"));
    }
    if stack.iter().any(|x| x == name) {
        return Err(format!("generation cycle while evaluating {name}"));
    }

    stack.push(name.to_string());
    let env: HashMap<String, Q> = rule
        .inputs
        .iter()
        .cloned()
        .zip(args.iter().cloned())
        .collect();
    let result = eval_expr(&rule.expression, &env, spec, constants, rules, stack);
    stack.pop();
    result
}

fn eval_expr(
    expr: &Expr,
    env: &HashMap<String, Q>,
    spec: &Spec,
    constants: &HashMap<String, Q>,
    rules: &HashMap<String, Rule>,
    stack: &mut Vec<String>,
) -> Result<Option<Q>, String> {
    match expr {
        Expr::Var { var } => env
            .get(var)
            .cloned()
            .map(Some)
            .ok_or_else(|| format!("unknown variable: {var}")),
        Expr::Const { constant } => constants
            .get(constant)
            .cloned()
            .map(Some)
            .ok_or_else(|| format!("unknown constant: {constant}")),
        Expr::Call { call, args } => {
            let mut values = Vec::with_capacity(args.len());
            for arg in args {
                match eval_expr(arg, env, spec, constants, rules, stack)? {
                    Some(value) => values.push(value),
                    None => return Ok(None),
                }
            }
            eval_operation(call, &values, spec, constants, rules, stack)
        }
    }
}

fn cartesian(corpus: &[Q], arity: usize) -> Vec<Vec<Q>> {
    fn rec(corpus: &[Q], arity: usize, prefix: &mut Vec<Q>, out: &mut Vec<Vec<Q>>) {
        if prefix.len() == arity {
            out.push(prefix.clone());
            return;
        }
        for value in corpus {
            prefix.push(value.clone());
            rec(corpus, arity, prefix, out);
            prefix.pop();
        }
    }
    let mut out = Vec::new();
    rec(corpus, arity, &mut Vec::new(), &mut out);
    out
}

fn evidence_for(
    rule: &Rule,
    spec: &Spec,
    corpus_text: &[String],
    constants: &HashMap<String, Q>,
    rules: &HashMap<String, Rule>,
) -> Result<Evidence, String> {
    let corpus: Vec<Q> = corpus_text
        .iter()
        .map(|x| Q::parse(x))
        .collect::<Result<_, _>>()?;

    let combos = cartesian(&corpus, rule.inputs.len());
    let mut inputs = Vec::with_capacity(combos.len());
    let mut outputs = Vec::with_capacity(combos.len());
    let mut undefined = 0usize;

    for combo in combos {
        let rendered_inputs: Vec<_> = combo.iter().map(Q::render).collect();
        let mut stack = Vec::new();
        let value = eval_operation(&rule.id, &combo, spec, constants, rules, &mut stack)?;
        let rendered = match value {
            Some(q) => q.render(),
            None => {
                undefined += 1;
                "UNDEFINED".to_string()
            }
        };
        inputs.push(rendered_inputs);
        outputs.push(rendered);
    }

    let payload = SignaturePayload {
        inputs: inputs.clone(),
        operation: rule.id.clone(),
        outputs: outputs.clone(),
    };
    let encoded = serde_json::to_vec(&payload).map_err(|e| e.to_string())?;
    let sha256 = sha256_hex(&encoded);

    let mut deps = BTreeSet::new();
    called_operations(&rule.expression, &mut deps);

    Ok(Evidence {
        operation: rule.id.clone(),
        dependencies: deps.into_iter().collect(),
        inputs,
        outputs,
        undefined,
        sha256,
    })
}

fn build_evidence(
    spec: &Spec,
    certs: &CertificateArtifact,
) -> Result<Vec<Evidence>, String> {
    let constants: HashMap<String, Q> = spec
        .constants
        .iter()
        .map(|c| Ok((c.id.clone(), Q::parse(&c.value)?)))
        .collect::<Result<_, String>>()?;
    let rules: HashMap<String, Rule> = spec
        .generation_rules
        .iter()
        .cloned()
        .map(|r| (r.id.clone(), r))
        .collect();

    let order = topo_order(spec)?;
    order
        .iter()
        .map(|id| evidence_for(&rules[id], spec, &certs.corpus, &constants, &rules))
        .collect()
}

fn verify_structure(spec: &Spec, certs: &CertificateArtifact) -> Result<(), String> {
    if spec.schema != "core-math-neutral/v1" || spec.status != "research-only" {
        return Err("unexpected neutral spec metadata".into());
    }
    if spec.carrier.id != "Q"
        || spec.carrier.kind != "exact-rational"
        || spec.carrier.normalization != "canonical-reduced"
        || spec.carrier.partiality != "explicit"
    {
        return Err("unsupported carrier contract".into());
    }
    if certs.schema != "core-math-generation-certificates/v1"
        || certs.authority != "research-only"
    {
        return Err("unexpected certificate metadata".into());
    }
    for c in &spec.constants {
        if c.carrier != spec.carrier.id {
            return Err(format!("constant carrier mismatch: {}", c.id));
        }
    }
    for op in &spec.basis_operations {
        if op.inputs.iter().any(|x| x != &spec.carrier.id) || op.output != spec.carrier.id {
            return Err(format!("basis carrier mismatch: {}", op.id));
        }
        if !matches!(op.partiality.as_str(), "total" | "undefined-at-zero") {
            return Err(format!("unsupported basis partiality: {}", op.partiality));
        }
    }
    for rule in &spec.generation_rules {
        if rule.output != spec.carrier.id {
            return Err(format!("generated carrier mismatch: {}", rule.id));
        }
        if !matches!(
            rule.partiality.as_str(),
            "total" | "undefined-at-zero" | "undefined-when-y-zero"
        ) {
            return Err(format!("unsupported generated partiality: {}", rule.partiality));
        }
    }
    Ok(())
}

fn compare_certificates(
    actual: &[Evidence],
    expected: &CertificateArtifact,
) -> Result<(), String> {
    let by_id: HashMap<_, _> = expected
        .certificates
        .iter()
        .map(|c| (c.operation.as_str(), c))
        .collect();

    if actual.len() != by_id.len() {
        return Err("certificate count mismatch".into());
    }

    for item in actual {
        let expected = by_id
            .get(item.operation.as_str())
            .ok_or_else(|| format!("missing committed certificate for {}", item.operation))?;
        if item.dependencies != expected.dependencies {
            return Err(format!("dependency mismatch for {}", item.operation));
        }
        if item.inputs.len().to_string() != expected.cases {
            return Err(format!("case count mismatch for {}", item.operation));
        }
        if item.undefined.to_string() != expected.undefined_cases {
            return Err(format!("undefined count mismatch for {}", item.operation));
        }
        if item.sha256 != expected.semantic_signature_sha256 {
            return Err(format!(
                "semantic signature mismatch for {}: {} != {}",
                item.operation, item.sha256, expected.semantic_signature_sha256
            ));
        }
    }
    Ok(())
}

fn mutation_divergence(
    spec: &Spec,
    certs: &CertificateArtifact,
    baseline: &[Evidence],
) -> Result<(String, usize, Vec<String>, String, String), String> {
    let mut mutated = spec.clone();
    let first = mutated
        .constants
        .first_mut()
        .ok_or_else(|| "no constant available for mutation".to_string())?;
    let original = first.value.clone();
    first.value = if original == "1/1" {
        "-1/1".to_string()
    } else {
        "1/1".to_string()
    };

    let changed = build_evidence(&mutated, certs)?;
    let base: HashMap<_, _> = baseline.iter().map(|x| (x.operation.as_str(), x)).collect();

    let mut depths: HashMap<String, usize> = HashMap::new();
    let rule_ids: BTreeSet<_> = spec.generation_rules.iter().map(|r| r.id.clone()).collect();
    for id in topo_order(spec)? {
        let rule = spec
            .generation_rules
            .iter()
            .find(|r| r.id == id)
            .ok_or_else(|| "topology/rule mismatch".to_string())?;
        let mut deps = BTreeSet::new();
        called_operations(&rule.expression, &mut deps);
        let parent_depth = deps
            .iter()
            .filter(|d| rule_ids.contains(*d))
            .map(|d| *depths.get(d).unwrap_or(&0))
            .max()
            .unwrap_or(0);
        depths.insert(id, parent_depth + 1);
    }

    let mut candidates: Vec<_> = changed
        .iter()
        .filter(|item| {
            base.get(item.operation.as_str())
                .map(|b| b.outputs != item.outputs)
                .unwrap_or(false)
        })
        .collect();
    candidates.sort_by_key(|x| (depths.get(&x.operation).copied().unwrap_or(usize::MAX), x.operation.clone()));

    let first_changed = candidates
        .first()
        .ok_or_else(|| "mutation produced no semantic divergence".to_string())?;
    let baseline_item = base[first_changed.operation.as_str()];
    let row = baseline_item
        .outputs
        .iter()
        .zip(first_changed.outputs.iter())
        .position(|(a, b)| a != b)
        .ok_or_else(|| "changed operation has no differing row".to_string())?;

    Ok((
        first_changed.operation.clone(),
        depths[&first_changed.operation],
        first_changed.inputs[row].clone(),
        baseline_item.outputs[row].clone(),
        first_changed.outputs[row].clone(),
    ))
}

fn main() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    let spec_path = args.get(1).map(String::as_str).unwrap_or(DEFAULT_SPEC);
    let cert_path = args.get(2).map(String::as_str).unwrap_or(DEFAULT_CERTS);

    let spec: Spec = load_json(spec_path)?;
    let certs: CertificateArtifact = load_json(cert_path)?;
    verify_structure(&spec, &certs)?;

    let actual = build_evidence(&spec, &certs)?;
    compare_certificates(&actual, &certs)?;

    let zero = Q::parse("0/1")?;
    if zero.recip()?.is_some() {
        return Err("reciprocal zero lost partiality".into());
    }

    let order = topo_order(&spec)?;
    let (op, depth, input, before, after) = mutation_divergence(&spec, &certs, &actual)?;

    println!("EXECUTOR=standalone-rust-sign-magnitude-Q");
    println!("SENS-CRATE-DEPENDENCY=0");
    println!("PYTHON-ORACLE-CALLS=0");
    println!("NEUTRAL-SPEC={spec_path}");
    println!("GENERATED-ORDER={}", order.join(","));
    println!("CERTIFICATE-PARITY=PASS");
    println!("PARTIALITY-PARITY=PASS");
    println!("MODEL-INTERNAL-REPRESENTATION=sign-magnitude-u128-rational");
    println!("MUTATION-DIVERGENCE-OP={op}");
    println!("MUTATION-DIVERGENCE-DEPTH={depth}");
    println!("MUTATION-DIVERGENCE-INPUT={}", input.join(","));
    println!("MUTATION-BASELINE-OUTPUT={before}");
    println!("MUTATION-CHANGED-OUTPUT={after}");
    println!("MINIMAL-DIVERGENCE=PASS");
    println!("STATUS=PASS-CORE-MATH-INDEPENDENT-RUST-EXECUTOR");
    println!("AUTHORITY=RESEARCH-ONLY");

    for item in actual {
        println!(
            "CERT {} cases={} undefined={} sha256={}",
            item.operation,
            item.inputs.len(),
            item.undefined,
            item.sha256
        );
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::Q;

    #[test]
    fn sign_magnitude_normalizes() {
        assert_eq!(Q::parse("-2/-4").unwrap().render(), "1/2");
        assert_eq!(Q::parse("2/-4").unwrap().render(), "-1/2");
        assert_eq!(Q::parse("0/-7").unwrap().render(), "0/1");
    }

    #[test]
    fn sha256_known_vector() {
        assert_eq!(
            super::sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn exact_q_arithmetic_and_partiality() {
        let half = Q::parse("1/2").unwrap();
        let third = Q::parse("1/3").unwrap();
        assert_eq!(half.add(&third).unwrap().render(), "5/6");
        assert_eq!(half.mul(&third).unwrap().render(), "1/6");
        assert_eq!(half.recip().unwrap().unwrap().render(), "2/1");
        assert!(Q::parse("0/1").unwrap().recip().unwrap().is_none());
    }
}
