use std::fs;
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_RUN_ID: AtomicU64 = AtomicU64::new(0);

fn run_source(source: &str, core3: bool) -> (bool, String) {
    let run_id = NEXT_RUN_ID.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!(
        "sens-decimal-head-{}-{run_id}.lisp",
        std::process::id()
    ));
    fs::write(&path, source).expect("source");

    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    if core3 {
        command.arg("--core=3");
    }
    let output = command.arg(&path).output().expect("canonical sens binary");

    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let _ = fs::remove_file(&path);
    (output.status.success(), stderr)
}

#[test]
fn decimal_number_spelling_never_acts_as_an_invoke_opcode() {
    // This decimal source is numeric data, not the historical eight-bit
    // identity. Neither a Core profile nor a mechanism string can make it a
    // callable resident; host-kernel behavior has its own direct tests.
    for core3 in [false, true] {
        for mechanism in ["common-lisp", "prolog", "clips", "datalog"] {
            let source = format!("(10101000 \"{mechanism}\" \"payload\")");
            let (ok, stderr) = run_source(&source, core3);
            assert!(!ok, "numeric source unexpectedly invoked {mechanism}");
            assert!(
                stderr.contains("expression is not callable"),
                "{mechanism}, core3={core3}: {stderr}"
            );
            assert!(
                stderr.contains("двійкове число"),
                "{mechanism}, core3={core3}: {stderr}"
            );
            assert!(
                !stderr.contains("unsupported raw island mechanism"),
                "numeric data reached the obsolete invoke dispatcher: {stderr}"
            );
        }
    }
}
