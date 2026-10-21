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

#[test]
fn sens_trit_eval_executes_physical_t5m_d24_without_the_source_file() {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/приклад.sens");
    let output = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("eval")
        .arg(path)
        .output()
        .expect("run explicit SENS T5M evaluator");
    assert!(output.status.success(), "{}", error(&output));
    assert_eq!(observed(&output).trim(), "3");
}

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


struct SourceTriplet {
    source: PathBuf,
    physical: PathBuf,
    view: PathBuf,
}
impl SourceTriplet {
    fn mint(name: &str) -> Self {
        let source = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .join(format!("tests/semantic/native-t5/{name}.lisp"));
        assert!(source.is_file(), "actual Ukrainian SENS source missing: {name}");
        let id = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let physical = std::env::temp_dir().join(format!(
            "sens-live-ukr-{name}-{}-{id}.sens", std::process::id()
        ));
        let view = physical.with_extension("");
        assert!(!physical.exists() && !view.exists(), "test must not overwrite files");

        // The SENS source reader resolves exact domain words; Zig alone
        // manufactures the physical T5M carrier and its canonical bit view.
        let minted = Command::new(env!("CARGO_BIN_EXE_sens"))
            .args(["--t5m-mint-pair"])
            .arg(&source)
            .arg(&physical)
            .output()
            .expect("execute current SENS/Zig mint");
        assert!(minted.status.success(), "{name}: native SENS mint: {}", error(&minted));
        assert!(physical.is_file() && view.is_file(), "{name}: both physical files");

        let checked = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("verify-view")
            .arg(&physical)
            .output()
            .expect("Zig physically verifies its own bytes and view");
        assert!(checked.status.success(), "{name}: {}", error(&checked));
        let opened = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("open")
            .arg(&physical)
            .output()
            .expect("Zig physical reader");
        assert!(opened.status.success(), "{name}: {}", error(&opened));
        assert_eq!(
            observed(&opened),
            fs::read_to_string(&view).expect("current exact-bit view"),
            "{name}: exact Zig/T5M source -> view inverse",
        );

        // A freshly mintable source is not enough: the checked-in
        // same-stem binary/view must be byte-identical to live Zig output.
        let committed = source.with_extension("sens");
        let committed_view = source.with_extension("");
        assert_eq!(
            fs::read(&committed).expect("committed physical T5M companion"),
            fs::read(&physical).expect("newly minted Zig T5M bytes"),
            "{name}: checked-in .sens is stale relative to executable Ukrainian .lisp",
        );
        assert_eq!(
            fs::read(&committed_view).expect("committed exact-bit companion"),
            fs::read(&view).expect("newly minted exact-bit view"),
            "{name}: checked-in exact-bit view is stale",
        );
        Self { source, physical, view }
    }
    fn run_sens(&self, paired: bool) -> Output {
        let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
        if paired {
            command.arg("--t5m-pair").arg(&self.source);
        }
        command.arg(&self.physical).output().expect("run native SENS")
    }
}
impl Drop for SourceTriplet {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.physical);
        let _ = fs::remove_file(&self.view);
    }
}

#[test]
fn ukrainian_d3_d4_existing_files_mint_verify_and_execute() {
    // Executable Ukrainian D3/D4 .lisp programs; the stable test
    // name is retained for the existing exact-target CI invocation, not
    // static metadata or mock examples; SENS evaluates each physical program.
    let mut first: Option<SourceTriplet> = None;
    for name in [
        "atom-empty",
        "atom-pair",
        "eq-reflexive",
        "eq-distinct",
        "car-cons",
        "cdr-cons",
        "cond-short-circuit",
        "nested-cons-atom",
        "guard-cond-selectors-law",
        "cdr-nested-pair-cond-lazy",
        "car-preserves-nested-pair-cond-lazy",
        "car-after-cdr-nested-list",
        "eq-car-cdr-empty",
        "d1-through-cons-cdr-car",
        "cond-two-false-branches",
        "car-nested-cons-symbol",
        "cdr-car-second-symbol",
        "cdr-twice-car-third-symbol",
        "cdr-after-car-nested-pair",
        "eq-inner-car-cdr-atom",
        "d4-list-one-symbol",
        "d4-append-second-symbol",
        "d4-null-not-cons",
            "cdr-dotted-tail-domain-identity",
        "cons-two-projections-joint-domain-identity",
        "d4-append-empty-left-preserves-head",
        "d4-append-empty-right-preserves-second",
        "d4-caar-nested-list",
        "d4-cdar-pair-tail",
        "d4-cddr-exact-two",
        "d4-cadr-exact-second",
        "d4-not-not-null-empty",
        "d4-append-empty-left",
        "d4-append-empty-left-law",
        "d4-append-three-associative-third-law",
        "d4-append-two-lists-order",        "cdr-cdr-two-element-tail",
        "car-car-nested-pair-atom",
        "cdr-car-inner-tail-eq",
        "cond-two-false-structural-guards",
        "d4-cddr-third-atom",
        "d4-cdar-dotted-tail-atom",
        "d4-append-associative-third",

        "d4-not-atom-cons",
        "d4-double-not-atom-nil",
        "d4-null-after-cdr-one",
        "d4-cddr-third-in-three",
        "d4-caar-two-inner-atoms",
        "d4-cdar-exact-atom-tail",
        "d4-cadr-from-cons-tail",
        "d4-append-three-order",
        "d4-not-eq-distinct-symbols",
        "d4-cdar-cadr-independent-head-tail",
        "d4-null-not-double-inversion",
        "d4-null-cdr-two-preserves-second",        "d4-caar-after-append-nested",
        "d4-cdar-nonempty-structural-tail",
        "d4-cddr-append-third-exact",
        "d4-null-after-cddr-two",

] {
        let triple = SourceTriplet::mint(name);
        let paired = triple.run_sens(true);
        assert!(paired.status.success(), "{name}: paired SENS: {}", error(&paired));
        assert_eq!(observed(&paired).trim(), "1", "{name}: exact D1 witness");

        let standalone = triple.run_sens(false);
        assert!(
            standalone.status.success(),
            "{name}: independent standalone SENS: {}",
            error(&standalone)
        );
        assert_eq!(
            observed(&standalone),
            observed(&paired),
            "{name}: Ukrainian .lisp and physical .sens differ in live execution"
        );

        if name == "atom-empty" {
            first = Some(triple);
        } else if name == "atom-pair" {
            // A perfectly valid T5M carrier for a DIFFERENT current
            // Ukrainian program cannot pass source↔physical admission.
            let other = first.as_ref().expect("first source-minted pair");
            let wrong = Command::new(env!("CARGO_BIN_EXE_sens"))
                .arg("--t5m-pair")
                .arg(&other.source)
                .arg(&triple.physical)
                .output()
                .expect("execute wrong-source negative witness");
            assert!(!wrong.status.success(), "wrong peer must be rejected");
            assert!(
                error(&wrong).contains("T5M_PHYSICAL_PAIR_MISMATCH"),
                "expected exact width/bits mismatch, got: {}",
                error(&wrong)
            );
        }
    }
}
