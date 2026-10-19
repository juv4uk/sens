//! CLI-level physical T5M execution of already Lisp-owned D4 mechanisms.
//!
//! Zig owns T5M packing; sens-trit is the only encoder used here. SENS remains
//! the evaluator. No replacement Rust LIST/APPEND primitive or new resident.
use std::{
    fs,
    io::Write,
    path::PathBuf,
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};
static UNIQUE: AtomicU64 = AtomicU64::new(0);

struct PhysicalT5m {
    source: PathBuf,
    path: PathBuf,
    projection: String,
    bytes: Vec<u8>,
}
impl PhysicalT5m {
    fn from_exact(words: &str) -> Self {
        let suffix = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let stem = format!("sens-d4-sequence-{}-{suffix}", std::process::id());
        // `sens-trit encode` currently accepts exact-width machine words via a
        // `.lisp`-suffixed input. This is a T5M transport witness, not a test of
        // Ukrainian source parsing or source-to-domain lowering.
        let source = std::env::temp_dir().join(format!("{stem}.lisp"));
        let path = std::env::temp_dir().join(format!("{stem}.sens"));
        assert!(!source.exists(), "must never overwrite another test source");
        assert!(!path.exists(), "must never overwrite another physical file");
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&source)
            .expect("create a new exact-word projection test source")
            .write_all(format!("{words}\n").as_bytes())
            .expect("write exact-word projection test source");

        let backend = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("backend")
            .output()
            .expect("query the configured physical codec");
        assert!(backend.status.success(), "{}", error(&backend));
        assert_eq!(
            observed(&backend).trim(),
            "transport=zig codec=T5M abi=2 semantic_authority=SENS",
            "the physical test must use the current Zig-owned T5M route"
        );

        let encoded = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("encode")
            .arg(&source)
            .output()
            .expect("run the public Zig-backed T5M encoder");
        assert!(
            encoded.status.success(),
            "T5M encode failed: stdout={} stderr={}",
            observed(&encoded),
            error(&encoded)
        );
        assert!(path.is_file(), "T5M encoder must create its .sens output");
        let bytes = fs::read(&path).expect("physical T5M test file");

        let opened = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("open")
            .arg(&path)
            .output()
            .expect("open physical T5M through the public CLI");
        assert!(opened.status.success(), "{}", error(&opened));
        assert_eq!(observed(&opened).trim(), words);

        Self {
            source,
            path,
            projection: format!("{words}\n"),
            bytes,
        }
    }
    fn cli(&self, mode: &str) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg(mode)
            .arg(&self.path)
            .output()
            .expect("spawn public SENS T5 CLI")
    }

    fn native_sens(&self) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&self.path)
            .output()
            .expect("spawn sterile native SENS on physical T5M")
    }
}
impl Drop for PhysicalT5m {
    fn drop(&mut self) {
        let current = fs::read(&self.path).expect("test T5 still exists");
        assert_eq!(
            current, self.bytes,
            "CLI must not mutate physical T5M source"
        );
        assert_eq!(fs::read_to_string(&self.source).unwrap(), self.projection);
        fs::remove_file(&self.path).expect("remove test-owned physical T5M input");
        fs::remove_file(&self.source).expect("remove test-owned projection input");
    }
}
fn observed(output: &Output) -> String {
    String::from_utf8(output.stdout.clone()).expect("UTF-8 CLI stdout")
}
fn error(output: &Output) -> String {
    String::from_utf8(output.stderr.clone()).expect("UTF-8 CLI stderr")
}

#[test]
fn physical_t5m_d4_list_executes_in_sterile_native_sens() {
    // D4:1110 LIST(D3:001 QUOTE(D3:000 EMPTY)).
    let physical = PhysicalT5m::from_exact("10 1110 00 10 001 00 000 01 01");
    let opened = physical.cli("open");
    assert!(opened.status.success(), "{}", error(&opened));
    assert_eq!(observed(&opened).trim(), "10 1110 00 10 001 00 000 01 01");

    let native = physical.native_sens();
    assert!(native.status.success(), "{}", error(&native));
    assert_eq!(observed(&native).trim(), "(())");

    let explicit = physical.cli("eval");
    assert!(explicit.status.success(), "{}", error(&explicit));
    assert_eq!(
        observed(&explicit).trim(),
        observed(&native).trim(),
        "sens-trit eval and sterile sens must agree on this physical D4 witness"
    );
}

#[test]
fn physical_t5m_d4_append_executes_in_sterile_native_sens() {
    // APPEND (LIST (QUOTE ())) (LIST (QUOTE ()))
    let exact = "10 1111 00 10 1110 00 10 001 00 000 01 01 00 10 1110 00 10 001 00 000 01 01 01";
    let physical = PhysicalT5m::from_exact(exact);
    let native = physical.native_sens();
    assert!(native.status.success(), "{}", error(&native));
    assert_eq!(observed(&native).trim(), "(() ())");
    let explicit = physical.cli("eval");
    assert!(explicit.status.success(), "{}", error(&explicit));
    assert_eq!(observed(&explicit).trim(), observed(&native).trim());

    let id =
        PhysicalT5m::from_exact("10 1111 00 10 001 00 000 01 00 10 1110 00 10 001 00 000 01 01 01");
    let native = id.native_sens();
    assert!(native.status.success(), "{}", error(&native));
    assert_eq!(observed(&native).trim(), "(())");
    let explicit = id.cli("eval");
    assert!(explicit.status.success(), "{}", error(&explicit));
    assert_eq!(observed(&explicit).trim(), observed(&native).trim());
}

#[test]
fn corrupt_physical_t5m_is_rejected_before_sens_evaluation() {
    let suffix = UNIQUE.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!(
        "sens-invalid-d4-{}-{suffix}.sens",
        std::process::id(),
    ));
    assert!(!path.exists());
    fs::write(&path, [0xf3u8]).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("eval")
        .arg(&path)
        .output()
        .unwrap();
    fs::remove_file(&path).unwrap();
    assert!(
        !output.status.success(),
        "corrupt T5M cannot reach SENS evaluation"
    );
}
