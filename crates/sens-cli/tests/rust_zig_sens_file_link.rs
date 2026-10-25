//! Executable Rust host -> Zig ABI -> binary SENS file boundary (#5777).
//! A real Rust CLI process moves exact typed words through Zig. Only SENS
//! executes the D2 program; this test does not implement or infer its law.
#![cfg(feature = "zig-transport")]

use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Pair {
    dir: PathBuf,
    source: PathBuf,
    physical: PathBuf,
}

impl Pair {
    fn new(source: &str) -> Self {
        let suffix = NEXT.fetch_add(1, Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!(
            "sens-rust-zig-file-link-{}-{suffix}",
            std::process::id()
        ));
        fs::create_dir(&dir).expect("unique temporary directory");
        let source_path = dir.join("program.lisp");
        let physical = dir.join("program.sens");
        fs::write(&source_path, source).expect("write exact binary SENS source");
        Self {
            dir,
            source: source_path,
            physical,
        }
    }

    fn trit(&self, command: &str) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg(command)
            .arg(self.path_for(command))
            .output()
            .expect("run real Zig-backed Rust SENS CLI")
    }

    fn path_for(&self, command: &str) -> &Path {
        if command == "encode" || command == "verify" {
            &self.source
        } else {
            &self.physical
        }
    }
}

impl Drop for Pair {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.dir).expect("remove only our temporary fixture");
    }
}

fn run(binary: &str, args: &[&str]) -> Output {
    Command::new(binary)
        .args(args)
        .output()
        .expect("run real Rust-hosted SENS CLI")
}

fn command(binary: &str, args: &[&Path]) -> Output {
    Command::new(binary)
        .args(args)
        .output()
        .expect("run real SENS file process")
}

fn must_pass(output: Output, label: &str) -> Output {
    assert!(
        output.status.success(),
        "{label} failed: exit={:?} stdout={:?} stderr={:?}",
        output.status.code(),
        output.stdout,
        output.stderr
    );
    output
}

#[test]
fn rust_zig_d3_selftest_and_one_bit_mutant_are_executed_only_via_zig() {
    // A real compiled CLI runs the SAME SENS-owned source fixtures. Rust
    // neither embeds these files nor interprets their domain values.
    let repo = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let fixture = repo.join("tests/fixtures/semantic");
    let backend = must_pass(
        run(env!("CARGO_BIN_EXE_sens-trit"), &["backend"]),
        "Zig transport backend",
    );
    assert_eq!(
        backend.stdout,
        b"transport=zig codec=T5M abi=2 semantic_authority=SENS\n"
    );

    let positive = fixture.join("exact-d3-logic-selftest.sens");
    let negative = fixture.join("exact-d3-logic-mutant.sens");
    let opening = |file: &Path| {
        must_pass(
            Command::new(env!("CARGO_BIN_EXE_sens-trit"))
                .arg("open")
                .arg(file)
                .output()
                .expect("real Zig T5 open process"),
            "Zig T5 physical words",
        )
    };
    let executing = |file: &Path| {
        must_pass(
            Command::new(env!("CARGO_BIN_EXE_sens-trit"))
                .arg("eval")
                .arg(file)
                .output()
                .expect("real Zig -> SENS execution"),
            "SENS-owned binary self-verdict",
        )
    };
    let law_words = String::from_utf8(opening(&positive).stdout).expect("exact binary source");
    let mutant_words = String::from_utf8(opening(&negative).stdout).expect("exact binary mutant");
    let law = law_words.split_whitespace().collect::<Vec<_>>();
    let mutant = mutant_words.split_whitespace().collect::<Vec<_>>();
    assert_eq!(law.len(), mutant.len(), "mutant must preserve exact words");
    let changed = law
        .iter()
        .zip(mutant.iter())
        .map(|(a, b)| {
            assert_eq!(
                a.len(),
                b.len(),
                "a one-bit mutant cannot alter domain width"
            );
            assert!(a.bytes().chain(b.bytes()).all(|x| x == b'0' || x == b'1'));
            a.bytes().zip(b.bytes()).filter(|(x, y)| x != y).count()
        })
        .sum::<usize>();
    assert_eq!(changed, 1, "one SENS D1 bit changes; no domain-width alias");

    let good = executing(&positive);
    let bad = executing(&negative);
    assert!(!good.stdout.is_empty() && !bad.stdout.is_empty());
    assert_ne!(
        good.stdout, bad.stdout,
        "native SENS self-verdict must falsify mutant"
    );
    assert!(good.stderr.is_empty() && bad.stderr.is_empty());
}

#[test]
fn rust_zig_sens_real_file_link_exact_bytes_and_fail_closed() {
    let repo = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    // This extensionless fixture is the canonical binary projection; the
    // historic quote-legacy.lisp is NOT the language source for this test.
    let source =
        fs::read_to_string(repo.join("tests/fixtures/migration-quote-cohort-main/quote-legacy"))
            .expect("ratified binary projection");
    assert!(!source.trim().is_empty(), "nonempty exact binary program");
    assert!(source
        .split_whitespace()
        .all(|w| w.bytes().all(|b| b == b'0' || b == b'1')));
    let golden =
        fs::read(repo.join("tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"))
            .expect("committed physical SENS fixture");

    // Required: this Rust process MUST be backed by Zig, never Rust's T5 codec.
    let backend = must_pass(
        run(env!("CARGO_BIN_EXE_sens-trit"), &["backend"]),
        "Zig backend",
    );
    assert_eq!(
        backend.stdout,
        b"transport=zig codec=T5M abi=2 semantic_authority=SENS\n"
    );

    let pair = Pair::new(&source);
    must_pass(pair.trit("encode"), "Rust CLI -> Zig T5 physical encode");
    let observed = fs::read(&pair.physical).expect("physical .sens bytes created");
    assert_eq!(
        observed, golden,
        "exact file bytes differ from pinned physical SENS"
    );
    must_pass(
        pair.trit("verify"),
        "Zig byte-level .lisp/.sens verification",
    );
    let opened = must_pass(pair.trit("open"), "Zig T5 ingress to typed SENS words");
    assert_eq!(
        String::from_utf8(opened.stdout).expect("binary projection is ASCII"),
        format!("{}\n", source.trim()),
        "all binary words and widths must survive the corridor"
    );

    // Different CLI programs execute the SAME physical file. Both success
    // and stdout/stderr are process observations, not a host truth table.
    let host_eval = must_pass(pair.trit("eval"), "Rust-hosted Zig -> SENS evaluation");
    let native = must_pass(
        command(env!("CARGO_BIN_EXE_sens"), &[&pair.physical]),
        "native physical SENS execution",
    );
    assert_eq!(
        host_eval.stdout, native.stdout,
        "two physical entry points disagree"
    );
    assert_eq!(
        host_eval.stderr, native.stderr,
        "unexpected diagnostic drift"
    );
    assert!(
        !native.stdout.is_empty(),
        "SENS must emit a visible self-verdict"
    );
    assert_eq!(
        fs::read(&pair.physical).unwrap(),
        golden,
        "execution changed the binary"
    );

    // A distinct exact-width word must NOT be reinterpreted as the original
    // file merely because some numeric host value could alias its payload.
    let changed_width = source.replacen("001", "0001", 1);
    assert_ne!(changed_width, source);
    fs::write(&pair.source, changed_width).expect("write alternate exact-domain source");
    let mismatch = pair.trit("verify");
    assert!(
        !mismatch.status.success(),
        "changed domain width must fail verification"
    );
    assert!(
        String::from_utf8_lossy(&mismatch.stderr)
            .contains("paired .lisp/.sens differs in exact domain words"),
        "wrong reason for changed-width refusal: {:?}",
        mismatch.stderr
    );

    // A non-ternary transport byte may never be consumed as SENS.
    let corrupt = pair.dir.join("corrupt.sens");
    let mut malformed = golden.clone();
    malformed.push(0xf3);
    fs::write(&corrupt, malformed).expect("isolated transport mutant");
    let invalid = command(
        env!("CARGO_BIN_EXE_sens-trit"),
        &[Path::new("open"), &corrupt],
    );
    assert!(
        !invalid.status.success(),
        "invalid T5 byte passed Zig ingress"
    );
    assert!(
        invalid.stdout.is_empty(),
        "invalid carrier emitted SENS words"
    );

    println!(
        "RUST_ZIG_SENS_FILE_LINK_PASS layer=transport source=.lisp physical=.sens \
         golden_bytes={} exact_words={} width_mutant=REJECTED \
         malformed_t5=REJECTED semantic_authority=SENS",
        golden.len(),
        source.split_whitespace().count()
    );
}
