//! Real Rust host -> Zig physical E1/T5 -> current binary SENS execution.
#![cfg(feature = "zig-transport")]

use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct PhysicalCase {
    directory: PathBuf,
    t5: PathBuf,
    e1: PathBuf,
    original: Vec<u8>,
}

impl PhysicalCase {
    fn from_tracked(path: &Path, name: &str) -> Self {
        let serial = NEXT.fetch_add(1, Ordering::Relaxed);
        let directory = std::env::temp_dir().join(format!(
            "sens-zig-e1-bridge-{}-{serial}-{name}",
            std::process::id()
        ));
        fs::create_dir(&directory).expect("isolate physical test files");
        let t5 = directory.join("program.sens");
        let e1 = directory.join("program.e1");
        let original = fs::read(path).expect("tracked binary SENS fixture");
        assert!(!original.is_empty(), "cannot attest an empty SENS program");
        fs::write(&t5, &original).expect("copy SENS fixture without reinterpretation");
        Self {
            directory,
            t5,
            e1,
            original,
        }
    }

    fn trit(&self, command: &str, path: &Path) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg(command)
            .arg(path)
            .output()
            .expect("execute actual Rust CLI linked to Zig ABI")
    }

    fn native(&self) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&self.t5)
            .output()
            .expect("execute actual binary SENS")
    }
}

impl Drop for PhysicalCase {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.directory).expect("remove temporary physical witness");
    }
}

fn checked(result: Output, label: &str) -> Output {
    assert!(
        result.status.success(),
        "{label}: exit={:?} stdout={:?} stderr={:?}",
        result.status.code(),
        result.stdout,
        result.stderr
    );
    result
}

#[test]
fn rust_host_zig_e1_preserves_binary_sens_verdict_and_rejects_corruption() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let backend = checked(
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("backend")
            .output()
            .expect("inspect linked Zig backend"),
        "Zig-backed host",
    );
    assert_eq!(
        backend.stdout,
        b"transport=zig codec=T5M abi=2 semantic_authority=SENS\n"
    );

    let mut results = Vec::new();
    let mut exact_words = Vec::new();
    for (name, fixture) in [
        (
            "law",
            "tests/fixtures/semantic/exact-d3-logic-selftest.sens",
        ),
        (
            "one-bit-mutant",
            "tests/fixtures/semantic/exact-d3-logic-mutant.sens",
        ),
    ] {
        let case = PhysicalCase::from_tracked(&root.join(fixture), name);
        let t5_view = checked(case.trit("open", &case.t5), "Zig physical T5 decode");
        let view = String::from_utf8(t5_view.stdout).expect("binary SENS projection");
        assert!(
            !view.trim().is_empty()
                && view
                    .split_whitespace()
                    .all(|w| w.bytes().all(|bit| bit == b'0' || bit == b'1')),
            "{name}: T5 projection must retain only exact binary words"
        );
        exact_words.push(
            view.split_whitespace()
                .map(str::to_owned)
                .collect::<Vec<_>>(),
        );

        let encoded = checked(case.trit("encode-e1", &case.t5), "Zig physical E1 encode");
        assert!(
            String::from_utf8_lossy(&encoded.stdout).contains("E1_PHYSICAL_ENCODED"),
            "{name}: encoder did not attest physical carrier"
        );
        assert!(case.e1.exists(), "{name}: missing actual .e1 file");
        let carrier = fs::read(&case.e1).expect("read resulting E1 physical carrier");
        assert!(!carrier.is_empty(), "{name}: empty E1 physical carrier");

        let t5 = checked(case.trit("eval", &case.t5), "T5 through Zig to SENS");
        let e1 = checked(case.trit("eval-e1", &case.e1), "E1 through Zig to SENS");
        let native = checked(case.native(), "native SENS on the same exact T5");
        assert_eq!(e1.stdout, t5.stdout, "{name}: E1 changed SENS result");
        assert_eq!(
            e1.stdout, native.stdout,
            "{name}: Rust host changed SENS result"
        );
        assert!(!native.stdout.is_empty(), "{name}: no SENS self-verdict");
        assert_eq!(
            fs::read(&case.t5).unwrap(),
            case.original,
            "{name}: carrier conversion modified the canonical T5 input"
        );
        results.push(e1.stdout);

        // The CRC is physical integrity, not a host truth table.
        let mut mutated = carrier;
        *mutated.last_mut().unwrap() ^= 1;
        let damaged = case.directory.join("bad.e1");
        fs::write(&damaged, mutated).expect("write a distinct E1 integrity mutant");
        let rejected = case.trit("eval-e1", &damaged);
        assert!(!rejected.status.success(), "{name}: damaged E1 executed");
        assert!(
            rejected.stdout.is_empty(),
            "{name}: damaged E1 emitted SENS verdict"
        );
        assert!(
            String::from_utf8_lossy(&rejected.stderr).contains("Zig E1 physical decode rejected"),
            "{name}: rejection did not originate at Zig physical ingress: {:?}",
            rejected.stderr
        );
    }

    assert_ne!(
        results[0], results[1],
        "a one-bit SENS mutant must change its own verdict"
    );
    let before = &exact_words[0];
    let after = &exact_words[1];
    assert_eq!(
        before.len(),
        after.len(),
        "mutation must preserve word framing"
    );
    let mut changed_bits = 0usize;
    for (a, b) in before.iter().zip(after.iter()) {
        assert_eq!(
            a.len(),
            b.len(),
            "mutation must preserve exact domain widths"
        );
        changed_bits += a.bytes().zip(b.bytes()).filter(|(x, y)| x != y).count();
    }
    assert_eq!(
        changed_bits, 1,
        "negative SENS witness changes exactly one bit"
    );
    println!(
        "RUST_ZIG_E1_SENS_PASS layer=transport cases=2 carrier=T5,E1 \
         exact_width=YES one_bit_mutant=YES crc=REJECTED semantic_authority=SENS"
    );
}
