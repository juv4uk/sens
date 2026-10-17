use sens::{
    eval_expr, eval_parsed_expressions, load_core_library, lower_program, parse_mixed_exact_domain,
    Expr, Session, Value,
};
use serde_json::{json, Value as JsonValue};
use std::{env, fs, path::PathBuf, process, time::Instant};

const WARMUPS: usize = 10;
const SAMPLES: usize = 100;

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
}

fn manifest() -> Result<JsonValue, String> {
    let path = root().join("workloads.json");
    let text = fs::read_to_string(&path)
        .map_err(|error| format!("read workload manifest {}: {error}", path.display()))?;
    serde_json::from_str(&text).map_err(|error| format!("parse workload manifest: {error}"))
}

fn workloads(manifest: &JsonValue) -> Result<&[JsonValue], String> {
    manifest
        .get("workloads")
        .and_then(JsonValue::as_array)
        .map(Vec::as_slice)
        .ok_or_else(|| "manifest field workloads must be an array".to_string())
}

fn get_workload<'a>(manifest: &'a JsonValue, id: &str) -> Result<&'a JsonValue, String> {
    workloads(manifest)?
        .iter()
        .find(|workload| workload.get("id").and_then(JsonValue::as_str) == Some(id))
        .ok_or_else(|| format!("unknown workload: {id}"))
}

fn expected_text(expected: &JsonValue) -> Result<String, String> {
    match expected {
        JsonValue::Number(number) => Ok(number.to_string()),
        JsonValue::Array(values) => {
            let values = values
                .iter()
                .map(|value| {
                    value
                        .as_i64()
                        .map(|number| number.to_string())
                        .ok_or_else(|| "expected array must contain only integers".to_string())
                })
                .collect::<Result<Vec<_>, _>>()?;
            Ok(format!("({})", values.join(" ")))
        }
        _ => Err("candidate workload must declare numeric expected output".into()),
    }
}

struct Prepared {
    session: Session,
    call: Expr,
    expected: String,
}

fn source(path: &str) -> Result<String, String> {
    let path = root().join(path);
    fs::read_to_string(&path)
        .map_err(|error| format!("read SENS source {}: {error}", path.display()))
}

fn prepare(workload: &JsonValue) -> Result<Prepared, String> {
    let id = workload
        .get("id")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| "workload has no string id".to_string())?;
    if workload.get("status").and_then(JsonValue::as_str) != Some("candidate") {
        return Err(format!(
            "workload {id} is not runnable (status is not candidate)"
        ));
    }
    let setup_path = workload
        .get("sens_setup")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| format!("workload {id} has no sens_setup"))?;
    let call_path = workload
        .get("sens_call")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| format!("workload {id} has no sens_call"))?;
    let expected = expected_text(
        workload
            .get("expected")
            .ok_or_else(|| format!("workload {id} has no expected value"))?,
    )?;

    let mut session = Session::default();
    load_core_library(&mut session).map_err(|error| format!("load current Core4: {error:?}"))?;

    let setup = source(setup_path)?;
    let setup_forms = parse_mixed_exact_domain(&setup)
        .map_err(|error| format!("parse setup {setup_path}: {error:?}"))?;
    eval_parsed_expressions(&setup_forms, &mut session)
        .map_err(|error| format!("evaluate setup {setup_path}: {error:?}"))?;

    let call_source = source(call_path)?;
    let call_forms = parse_mixed_exact_domain(&call_source)
        .map_err(|error| format!("parse call {call_path}: {error:?}"))?;
    if call_forms.len() != 1 {
        return Err(format!(
            "call source {call_path} must contain exactly one expression"
        ));
    }
    let mut lowered = lower_program(&call_forms);
    let call = lowered
        .pop()
        .ok_or_else(|| format!("call source {call_path} is empty"))?;
    Ok(Prepared {
        session,
        call,
        expected,
    })
}

fn result_text(value: &Value) -> String {
    value.to_string()
}

fn check_one(workload: &JsonValue) -> JsonValue {
    let id = workload
        .get("id")
        .and_then(JsonValue::as_str)
        .unwrap_or("UNKNOWN");
    match prepare(workload) {
        Ok(prepared) => match eval_expr(&prepared.call, &prepared.session.environment) {
            Ok(actual_value) => {
                let actual = result_text(&actual_value);
                let passed = actual == prepared.expected;
                json!({
                    "workload": id,
                    "status": if passed { "PASS" } else { "FAIL" },
                    "expected": prepared.expected,
                    "actual": actual,
                    "parity_gate": "SENS output equals fixed expected value before timing"
                })
            }
            Err(error) => json!({
                "workload": id,
                "status": "FAIL",
                "error": format!("execute SENS call: {error:?}")
            }),
        },
        Err(error) => json!({
            "workload": id,
            "status": "FAIL",
            "error": error
        }),
    }
}

fn check_all(manifest: &JsonValue) -> Result<JsonValue, String> {
    let mut results = Vec::new();
    for workload in workloads(manifest)? {
        let id = workload
            .get("id")
            .and_then(JsonValue::as_str)
            .unwrap_or("UNKNOWN");
        match workload.get("status").and_then(JsonValue::as_str) {
            Some("candidate") => results.push(check_one(workload)),
            Some("blocked") => results.push(json!({
                "workload": id,
                "status": "BLOCKED",
                "reason": workload.get("reason").and_then(JsonValue::as_str).unwrap_or("no reason recorded")
            })),
            _ => results.push(json!({ "workload": id, "status": "SKIPPED" })),
        }
    }
    let pass_count = results
        .iter()
        .filter(|result| result.get("status").and_then(JsonValue::as_str) == Some("PASS"))
        .count();
    let fail_count = results
        .iter()
        .filter(|result| result.get("status").and_then(JsonValue::as_str) == Some("FAIL"))
        .count();
    Ok(json!({
        "schema_version": 1,
        "implementation": "SENS source / current mixed exact-domain reader and evaluator",
        "runtime_metadata": {
            "profile": if cfg!(debug_assertions) { "debug" } else { "release" },
            "os": env::consts::OS,
            "architecture": env::consts::ARCH
        },
        "timing_started": false,
        "passing_workloads": pass_count,
        "minimum_for_overall_conclusion": 3,
        "overall_status": if fail_count > 0 { "FAIL" } else if pass_count >= 3 { "PASS" } else { "PARTIAL" },
        "results": results
    }))
}

fn rss_kib(field: &str) -> Result<u64, String> {
    let status = fs::read_to_string("/proc/self/status")
        .map_err(|error| format!("read /proc/self/status: {error}"))?;
    let line = status
        .lines()
        .find(|line| line.starts_with(&format!("{field}:")))
        .ok_or_else(|| format!("/proc/self/status has no {field}"))?;
    line.split_whitespace()
        .nth(1)
        .ok_or_else(|| format!("malformed /proc/self/status field {field}"))?
        .parse()
        .map_err(|error| format!("parse {field}: {error}"))
}

fn run_one(workload: &JsonValue) -> Result<JsonValue, String> {
    let id = workload
        .get("id")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| "workload has no string id".to_string())?;
    let prepared = prepare(workload)?;
    let parity = eval_expr(&prepared.call, &prepared.session.environment)
        .map_err(|error| format!("pre-timing parity call failed: {error:?}"))?;
    let actual = result_text(&parity);
    if actual != prepared.expected {
        return Err(format!(
            "parity failed for {id}: expected {}, actual {actual}",
            prepared.expected
        ));
    }
    drop(parity);

    for _ in 0..WARMUPS {
        let result = eval_expr(&prepared.call, &prepared.session.environment)
            .map_err(|error| format!("warmup failed for {id}: {error:?}"))?;
        drop(result);
    }
    let rss_baseline_kib = rss_kib("VmRSS")?;

    let mut samples = Vec::with_capacity(SAMPLES);
    for ordinal in 1..=SAMPLES {
        let start = Instant::now();
        let result = eval_expr(&prepared.call, &prepared.session.environment)
            .map_err(|error| format!("measured call failed for {id}: {error:?}"))?;
        let elapsed_ns = start.elapsed().as_nanos();
        let output = result_text(&result);
        drop(result);
        let elapsed_ns =
            u64::try_from(elapsed_ns).map_err(|_| format!("sample duration overflow for {id}"))?;
        samples.push(json!({
            "ordinal": ordinal,
            "elapsed_ns": elapsed_ns,
            "result": output
        }));
    }
    let rss_peak_kib = rss_kib("VmHWM")?;
    let profile = if cfg!(debug_assertions) {
        "debug"
    } else {
        "release"
    };

    Ok(json!({
        "schema_version": 1,
        "workload": id,
        "implementation": "SENS",
        "status": "PASS",
        "parity": "PASS",
        "warmups": WARMUPS,
        "n": samples.len(),
        "samples": samples,
        "output": actual,
        "rss_kib": {
            "baseline_after_warmup": rss_baseline_kib,
            "peak_vmhwm": rss_peak_kib,
            "delta_peak_from_baseline": rss_peak_kib.saturating_sub(rss_baseline_kib)
        },
        "runtime_metadata": {
            "os": env::consts::OS,
            "architecture": env::consts::ARCH,
            "profile": profile
        }
    }))
}

fn execute() -> Result<JsonValue, String> {
    let mut args = env::args().skip(1);
    match args.next().as_deref() {
        Some("check") if args.next().is_none() => check_all(&manifest()?),
        Some("run") => {
            let id = args
                .next()
                .ok_or_else(|| "usage: sens-vs-python-bench run <workload>".to_string())?;
            if args.next().is_some() {
                return Err("run accepts exactly one workload id".into());
            }
            let manifest = manifest()?;
            let workload = get_workload(&manifest, &id)?;
            let result = run_one(workload)?;
            Ok(result)
        }
        _ => Err("usage: sens-vs-python-bench check | run <workload>".into()),
    }
}

fn main() {
    match execute() {
        Ok(output) => println!(
            "{}",
            serde_json::to_string(&output).expect("JSON serializes")
        ),
        Err(error) => {
            println!("{}", json!({ "status": "FAIL", "error": error }));
            process::exit(2);
        }
    }
}
