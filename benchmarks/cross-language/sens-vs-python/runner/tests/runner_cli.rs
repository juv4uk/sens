use serde_json::Value;
use std::process::Command;

fn runner(args: &[&str]) -> (i32, Value) {
    let output = Command::new(env!("CARGO_BIN_EXE_sens-vs-python-bench"))
        .args(args)
        .output()
        .expect("runner starts");
    let status = output.status.code().expect("runner exits with a code");
    let value = serde_json::from_slice(&output.stdout).expect("runner prints JSON");
    (status, value)
}

#[test]
fn check_requires_three_parity_passes_and_reports_json_blocker_without_timing() {
    let (status, report) = runner(&["check"]);
    assert_eq!(status, 0, "{report}");
    assert_eq!(report["overall_status"], "PASS");
    assert_eq!(report["passing_workloads"], 3);
    assert_eq!(report["timing_started"], false);
    let results = report["results"].as_array().expect("results array");
    assert_eq!(
        results.iter().filter(|row| row["status"] == "PASS").count(),
        3
    );
    assert!(results
        .iter()
        .any(|row| { row["workload"] == "json-parse-serialize" && row["status"] == "BLOCKED" }));
}

#[test]
fn run_fib_emits_ten_warmups_one_hundred_raw_samples_and_rss() {
    let (status, report) = runner(&["run", "fib"]);
    assert_eq!(status, 0, "{report}");
    assert_eq!(report["status"], "PASS");
    assert_eq!(report["warmups"], 10);
    assert_eq!(report["n"], 100);
    let samples = report["samples"].as_array().expect("raw samples");
    assert_eq!(samples.len(), 100);
    assert_eq!(samples[0]["ordinal"], 1);
    assert!(samples[0]["elapsed_ns"].as_u64().is_some());
    assert!(report["rss_kib"]["baseline_after_warmup"]
        .as_u64()
        .is_some());
    assert!(report["rss_kib"]["peak_vmhwm"].as_u64().is_some());
}

#[test]
fn blocked_json_cannot_be_timed() {
    let (status, report) = runner(&["run", "json-parse-serialize"]);
    assert_eq!(status, 2);
    assert_eq!(report["status"], "FAIL");
    assert!(report["error"].as_str().unwrap().contains("not runnable"));
    assert!(report.get("samples").is_none());
}
