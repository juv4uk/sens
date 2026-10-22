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
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../tests/fixtures/приклад.sens");
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
        let relative = if name.starts_with("lib/") {
            format!("{name}.lisp")
        } else {
            format!("tests/semantic/native-t5/{name}.lisp")
        };
        let source = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .join(relative);
        assert!(
            source.is_file(),
            "actual Ukrainian SENS source missing: {name}"
        );
        let id = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let physical = std::env::temp_dir().join(format!(
            "sens-live-ukr-{}-{}-{id}.sens",
            name.replace('/', "-"),
            std::process::id()
        ));
        let view = physical.with_extension("");
        assert!(
            !physical.exists() && !view.exists(),
            "test must not overwrite files"
        );

        // The SENS source reader resolves exact domain words; Zig alone
        // manufactures the physical T5M carrier and its canonical bit view.
        let minted = Command::new(env!("CARGO_BIN_EXE_sens"))
            .args(["--t5m-mint-pair"])
            .arg(&source)
            .arg(&physical)
            .output()
            .expect("execute current SENS/Zig mint");
        assert!(
            minted.status.success(),
            "{name}: native SENS mint: {}",
            error(&minted)
        );
        assert!(
            physical.is_file() && view.is_file(),
            "{name}: both physical files"
        );

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
        Self {
            source,
            physical,
            view,
        }
    }
    fn run_sens(&self, paired: bool) -> Output {
        let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
        if paired {
            command.arg("--t5m-pair").arg(&self.source);
        }
        command
            .arg(&self.physical)
            .output()
            .expect("run native SENS")
    }
}
impl Drop for SourceTriplet {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.physical);
        let _ = fs::remove_file(&self.view);
    }
}

// Перевіряємо реальне виконання ще не опублікованих фізичних трійок.
// Український Lisp є джерелом; exact-слова читає SENS, T5M пакує Zig.
// Адресна діагностика: перший реальний розбіжний байт без дампу всієї програми.
fn same_bytes_with_diagnostic(
    actual_path: &std::path::Path,
    committed_path: &std::path::Path,
    stem: &str,
    test_id: &str,
) -> bool {
    let actual = fs::read(actual_path).expect("згенеровані Zig/T5M байти");
    let expected = fs::read(committed_path).expect("закомічена фізична пара");
    if actual != expected {
        let offset = actual
            .iter()
            .zip(&expected)
            .position(|(a, b)| a != b)
            .unwrap_or(actual.len().min(expected.len()));
        println!(
            "test_id={test_id} source={stem} first_diff_byte={offset} minted={:?} committed={:?} minted_len={} committed_len={}",
            actual.get(offset), expected.get(offset), actual.len(), expected.len()
        );
        return false;
    }
    true
}

fn verify_unpaired_ukrainian_libs_natively() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let mut independently_executed = std::collections::BTreeSet::new();
    let mut physical_drifted = std::collections::BTreeSet::new();
    for stem in [
        "d1-direct-values",
        "axioms-d1-principle-five",
        "d3-pair-laws",
        "d4-second-two-tails-law",
        "pair-replace-first",
        "pair-replace-rest",
        "поміняти-перші-два",
        "вилучити-середнє-з-трійки",
        "вставити-посеред-пари",
        "розділити-четвірку-на-пари",
        "pair-zip-unzip-two",
        "list-delete-second",
        "list-insert-second",
        "rotate-four-left",
        "rotate-four-right",
        "list-swap-neighbors-four",
        "list-swap-middle-four",
        "list-replace-fourth",
        "list-swap-ends-five",
        "поміняти-другий-і-третій",
        "list-swap-inner-five",
        "reverse-three",
        "list-reverse-four",
        "list-halfturn-four",
        "list-halfturn-six",
        "list-reverse-general",
        "list-interleave-two-general",
        "list-reverse-tail-general",
        "list-last-adjacent-equal-atom-suffix-general",
        "list-first-adjacent-equal-atom-suffix-general",
        "list-every-fifth-linear-general",
        "list-every-fourth-linear-general",
        "list-every-second-general",
        "list-every-third-linear-general",
        "list-drop-three-zero-copy-general",
        "list-drop-two-zero-copy-general",
        "list-drop-last-general",
        "list-append-general",
        "list-collapse-adjacent",
        "list-collapse-adjacent-atoms",
        "list-common-prefix-general",
        "list-common-prefix-three-atoms-general",
        "list-unique-stable",
        "розділити-до-першого-входження",
        "list-interleave-two-pairs",
        "list-zip-general",
        "pair-zip-unzip-three",
        "виключне-або-д1",
        "поміняти-кожну-пару",
        "вилучити-перше-входження",
        "взяти-через-один",
        "list-subsequence-atoms-general",
        "list-rotate-inverse-general",
        "list-middle-even",
        "list-middle-suffix-two-pointers-zero-copy-general",
        "list-common-suffix-general",
        "list-chunk-triplets-general",
        "list-stable-difference-general",
        "list-unzip-pairs-general",
        "list-palindrome-atoms-general",
        "list-palindrome-linear-atoms-general",
        "list-trailing-compound-run-zero-copy-general",
        "list-trailing-equal-atomic-run-general",
        "list-multiset-difference-general",
        "list-stable-union-general",
        "list-cartesian-product-general",
        "list-neighbor-windows-general",
        "list-remove-all-atoms-general",
        "list-stable-intersection-general",
        "list-atom-sequence-equal-general",
        "list-split-last-occurrence-general",
        "list-swap-adjacent-pairs",
        "list-contiguous-sublist-atoms-general",
        "list-duplicate-reversible",
        "list-duplicate-atoms-preserve-compounds-general",
        "list-has-adjacent-equal-atoms",
        "list-rotate-five-by-two",
        "list-tree-mirror-general",
        "list-unique-last-stable",
        "list-replace-last-occurrence-general",
        "list-drop-while-atom-general",
        "list-take-while-atom-general",
        "list-interpose-general",
        "list-last-occurrence-suffix",
        "list-suffix-after-last-atom-match-zero-copy-general",
        "list-split-first-occurrence-general",
        "list-deduplicate-neighbors",
        "list-alternating-split-four",
        "list-remove-first-atom",
        "list-prefix-atoms-general",
        "list-flatten-nested-general",
        "list-flatten-stack-linear-general",
        "list-all-suffixes-general",
        "list-all-prefixes-general",
        "list-all-distinct-atoms-general",
        "list-first-adjacent-repeat-atom-general",
        "tree-leaf-tally-unary",
        "list-keep-all-matching-atoms-general",
        "list-overlapping-triplets-general",
        "list-overlapping-quadruples-general",
        "list-replace-first-atom-general",
        "list-remove-interior-matching-atoms-general",
        "list-multiset-intersection-general",
        "list-zip-with-tails-general",
        "list-three-lanes-general",
        "list-adjacent-runs-general",
        "list-collapse-adjacent-runs-general",
        "list-all-slices-ends-general",
        "list-rotation-inverse-general",
        "list-trim-edges-atom-general",
        "list-trim-ends-atom-general",
        "list-alternating-split-general",
        "list-chunk-pairs-general",
        "list-remove-last-atom",
        "list-stable-symmetric-difference-general",
        "list-suffix-atoms-general",
        "list-split-at-first-atom-general",
        "list-stable-bipartition-general",
        "вилучити-всі-входження",
        "замінити-всі-входження",
        "list-all-cuts-general",
        "list-strip-prefix-atoms-general",
        "list-first-globally-unique-atom-general",
        "list-prefix-before-repeat-general",
        "list-split-before-every-atom-general",
        "list-remove-last-matching-atom-general",
        "list-run-length-unary-general",
        "tree-contains-atom-general",
        "list-count-matching-atoms-unary",
        "list-first-position-unary-general",
        "tree-replace-atom-general",
        "list-first-repeated-atom-general",
        "list-last-repeated-atom-by-final-occurrence-general",
        "list-last-globally-unique-atom-general",
        "tree-prune-matching-leaves-general",
        "list-keep-last-unique-atoms-general",
        "list-keep-repeated-atoms-once-general",
        "list-move-first-match-to-front-general",
        "list-all-unordered-position-pairs-general",
        "list-distinct-unordered-atom-pairs-general",
        "list-first-divergence-suffix-general",
        "list-interleave-three-general",
        "list-interleave-three-rotation-general",
        "list-drop-every-third-compact-general",
        "list-drop-every-third-general",
        "list-drop-leading-compounds-zero-copy-general",
        "list-drop-leading-equal-atoms-zero-copy-general",
        "list-tail-after-first-atom-zero-copy-general",
        "list-drop-through-last-atom-zero-copy-general",
        "list-select-longer-zero-copy-general",
        "list-split-atomic-prefix-general",
        "list-first-compound-zero-copy-general",
        "list-first-compound-general",
        "list-last-compound-suffix-general",
        "list-last-atom-suffix-general",
        "tree-pair-tally-unary-general",
        "list-all-subsets-by-position-general",
        "list-all-matching-positions-unary-general",
        "list-partition-atomic-compound-general",
        "list-count-consecutive-atomic-runs-unary-general",
        "list-leading-compound-run-length-unary-general",
        "list-leading-atom-run-length-unary-general",
        "list-drop-last-two-linear",
        "list-last-n-unary-zero-copy-general",
        "list-last-two-zero-copy-general",
        "list-tail-after-first-compound-zero-copy-general",
        "list-tail-after-second-compound-zero-copy-general",
        "list-remove-first-compound-general",
        "list-suffix-after-first-atomic-triple-zero-copy-general",
        "list-suffix-after-last-atomic-triple-zero-copy-general",
        "list-suffix-after-last-atomic-pair-zero-copy-general",
        "list-suffix-from-last-compound-zero-copy-general",
        "list-tail-after-second-atom-zero-copy-general",
        "list-suffix-after-last-compound-zero-copy-general",
        "interleave-pairs",
        "pair-associativity-law",
        "pair-swap",
        "rotate-left",
        "rotate-three-right",
        "замінити-третій-в-четвірці",
        "list-prefix-through-last-compound-general",
        "list-last-element-zero-copy-general",
        "list-last-three-zero-copy-general",
        "list-tail-after-fourth-compound-zero-copy-general",
        "list-tail-after-third-compound-zero-copy-general",
        "list-penultimate-element-zero-copy-general",
        "list-suffix-after-first-compound-atom-zero-copy-general",
        "list-suffix-after-first-adjacent-compound-pair-zero-copy-general",
        "list-suffix-after-first-adjacent-compounds-zero-copy-general",
        "list-suffix-after-first-adjacent-atom-pair-zero-copy-general",
        "list-unique-stable-fast-general",
        "list-every-sixth-linear-general",
        "list-maximum-fold-general",
        "list-tail-after-third-atom-zero-copy-general",
        "залишити-точні-числа",
    ] {
        let source = root.join("lib").join(format!("{stem}.lisp"));
        assert!(source.is_file(), "{stem}: українське джерело відсутнє");
        let sequence = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let scratch = std::env::temp_dir().join(format!(
            "sens-native-unpaired-{}-{sequence}",
            std::process::id()
        ));
        fs::create_dir(&scratch).expect("створити ізольоване місце SENS-програми");
        let physical = scratch.join("програма.sens");
        let view = scratch.join("програма");
        let minted = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg("--t5m-mint-pair")
            .arg(&source)
            .arg(&physical)
            .output()
            .expect("SENS reader -> Zig/T5M");
        assert!(
            minted.status.success(),
            "test_id=ukr-lib-mint source={stem} stderr={}",
            error(&minted)
        );
        assert!(
            physical.is_file() && view.is_file(),
            "{stem}: створено фізичну пару"
        );
        // Оборотні трійки нових прикладів мають бути тотожні байт-в-байт
        // реальному пакуванню Zig, а не лише текстовому звіту.
        if matches!(
            stem,
            "axioms-d1-principle-five"
                | "d3-pair-laws"
                | "d4-second-two-tails-law"
                | "вилучити-середнє-з-трійки"
                | "вставити-посеред-пари"
                | "розділити-четвірку-на-пари"
                | "list-swap-ends-five"
                | "list-swap-inner-five"
                | "rotate-four-left"
                | "rotate-four-right"
                | "list-delete-second"
                | "list-insert-second"
                | "reverse-three"
                | "list-reverse-four"
                | "list-halfturn-four"
                | "list-halfturn-six"
                | "list-zip-general"
                | "list-drop-three-zero-copy-general"
                | "list-drop-two-zero-copy-general"
                | "list-drop-last-general"
                | "list-append-general"
                | "list-collapse-adjacent"
                | "list-collapse-adjacent-atoms"
                | "list-common-prefix-general"
                | "list-common-prefix-three-atoms-general"
                | "list-chunk-triplets-general"
                | "list-common-suffix-general"
                | "list-middle-even"
                | "list-rotate-inverse-general"
                | "list-subsequence-atoms-general"
                | "розділити-до-першого-входження"
                | "взяти-через-один"
                | "вилучити-перше-входження"
                | "list-unique-stable"
                | "list-stable-difference-general"
                | "list-unzip-pairs-general"
                | "list-palindrome-atoms-general"
                | "list-palindrome-linear-atoms-general"
                | "list-trailing-compound-run-zero-copy-general"
                | "list-trailing-equal-atomic-run-general"
                | "list-multiset-difference-general"
                | "list-stable-union-general"
                | "list-cartesian-product-general"
                | "list-neighbor-windows-general"
                | "list-remove-all-atoms-general"
                | "list-stable-intersection-general"
                | "list-atom-sequence-equal-general"
                | "list-split-last-occurrence-general"
                | "list-swap-adjacent-pairs"
                | "list-contiguous-sublist-atoms-general"
                | "list-replace-last-occurrence-general"
                | "list-duplicate-reversible"
                | "list-duplicate-atoms-preserve-compounds-general"
                | "list-has-adjacent-equal-atoms"
                | "list-rotate-five-by-two"
                | "list-tree-mirror-general"
                | "list-unique-last-stable"
                | "list-drop-while-atom-general"
                | "list-take-while-atom-general"
                | "list-interpose-general"
                | "list-last-occurrence-suffix"
                | "list-suffix-after-last-atom-match-zero-copy-general"
                | "list-tail-after-first-atom-zero-copy-general"
                | "list-drop-through-last-atom-zero-copy-general"
                | "list-select-longer-zero-copy-general"
                | "list-split-first-occurrence-general"
                | "list-all-distinct-atoms-general"
                | "list-keep-all-matching-atoms-general"
                | "list-overlapping-triplets-general"
                | "list-overlapping-quadruples-general"
                | "list-replace-first-atom-general"
                | "list-remove-interior-matching-atoms-general"
                | "list-multiset-intersection-general"
                | "list-zip-with-tails-general"
                | "list-three-lanes-general"
                | "list-adjacent-runs-general"
                | "list-collapse-adjacent-runs-general"
                | "list-all-slices-ends-general"
                | "list-rotation-inverse-general"
                | "list-trim-edges-atom-general"
                | "list-trim-ends-atom-general"
                | "list-alternating-split-general"
                | "list-chunk-pairs-general"
                | "list-remove-last-atom"
                | "list-stable-symmetric-difference-general"
                | "list-suffix-atoms-general"
                | "list-split-at-first-atom-general"
                | "list-stable-bipartition-general"
                | "вилучити-всі-входження"
                | "замінити-всі-входження"
                | "list-deduplicate-neighbors"
                | "list-first-compound-zero-copy-general"
                | "list-first-adjacent-repeat-atom-general"
                | "tree-leaf-tally-unary"
                | "list-alternating-split-four"
                | "list-remove-first-atom"
                | "list-prefix-atoms-general"
                | "list-flatten-nested-general"
                | "list-flatten-stack-linear-general"
                | "list-all-suffixes-general"
                | "list-all-prefixes-general"
                | "замінити-третій-в-четвірці"
                | "list-all-cuts-general"
                | "list-strip-prefix-atoms-general"
                | "list-first-globally-unique-atom-general"
                | "list-prefix-before-repeat-general"
                | "list-split-before-every-atom-general"
                | "list-run-length-unary-general"
                | "list-count-consecutive-atomic-runs-unary-general"
                | "tree-contains-atom-general"
                | "list-count-matching-atoms-unary"
                | "list-first-position-unary-general"
                | "tree-replace-atom-general"
                | "list-first-repeated-atom-general"
                | "list-last-repeated-atom-by-final-occurrence-general"
                | "list-last-globally-unique-atom-general"
                | "tree-prune-matching-leaves-general"
                | "list-keep-last-unique-atoms-general"
                | "list-keep-repeated-atoms-once-general"
                | "list-move-first-match-to-front-general"
                | "list-all-unordered-position-pairs-general"
                | "list-distinct-unordered-atom-pairs-general"
                | "list-first-divergence-suffix-general"
                | "list-interleave-two-general"
                | "list-reverse-tail-general"
                | "list-last-adjacent-equal-atom-suffix-general"
                | "list-first-adjacent-equal-atom-suffix-general"
                | "list-every-fifth-linear-general"
                | "list-every-fourth-linear-general"
                | "list-every-second-general"
                | "list-every-third-linear-general"
                | "list-interleave-three-general"
                | "list-interleave-three-rotation-general"
                | "list-drop-every-third-compact-general"
                | "list-drop-every-third-general"
                | "list-last-compound-suffix-general"
                | "list-last-atom-suffix-general"
                | "list-all-subsets-by-position-general"
                | "tree-pair-tally-unary-general"
                | "list-drop-last-two-linear"
                | "list-last-n-unary-zero-copy-general"
                | "list-last-two-zero-copy-general"
                | "list-tail-after-first-compound-zero-copy-general"
                | "list-tail-after-second-compound-zero-copy-general"
                | "list-remove-first-compound-general"
                | "list-suffix-after-first-atomic-triple-zero-copy-general"
                | "list-suffix-from-last-compound-zero-copy-general"
                | "list-tail-after-second-atom-zero-copy-general"
                | "interleave-pairs"
                | "pair-associativity-law"
                | "pair-swap"
                | "rotate-left"
                | "rotate-three-right"
                | "list-tail-after-fourth-compound-zero-copy-general"
                | "list-prefix-through-last-compound-general"
                | "list-last-element-zero-copy-general"
                | "list-last-three-zero-copy-general"
                | "list-tail-after-third-compound-zero-copy-general"
                | "list-leading-compound-run-length-unary-general"
                | "list-leading-atom-run-length-unary-general"
                | "list-partition-atomic-compound-general"
                | "list-penultimate-element-zero-copy-general"
                | "list-suffix-after-first-compound-atom-zero-copy-general"
                | "list-suffix-after-first-adjacent-compound-pair-zero-copy-general"
                | "list-suffix-after-first-adjacent-compounds-zero-copy-general"
                | "list-suffix-after-first-adjacent-atom-pair-zero-copy-general"
                | "list-unique-stable-fast-general"
                | "list-every-sixth-linear-general"
                | "list-maximum-fold-general"
                | "list-tail-after-third-atom-zero-copy-general"
                | "залишити-точні-числа"
        ) {
            let committed_physical = root.join("lib").join(format!("{stem}.sens"));
            let committed_view = root.join("lib").join(stem);
            // Дрейф однієї трійки не зупиняє виконання інших програм.
            // Але підсумок CI залишається RED, доки байти не виправлені.
            let bytes_equal = same_bytes_with_diagnostic(
                &physical,
                &committed_physical,
                stem,
                "ukr-lib-physical-parity",
            );
            let view_equal = same_bytes_with_diagnostic(
                &view,
                &committed_view,
                stem,
                "ukr-lib-exact-parity",
            );
            if !bytes_equal || !view_equal {
                physical_drifted.insert(stem);
            }
        }
        let verify = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("verify-view")
            .arg(&physical)
            .output()
            .expect("Zig verify-view");
        assert!(
            verify.status.success(),
            "test_id=ukr-lib-inverse source={stem} stderr={}",
            error(&verify)
        );
        let pair = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg("--t5m-pair")
            .arg(&source)
            .arg(&physical)
            .output()
            .expect("реальне парне виконання SENS");
        assert!(
            pair.status.success(),
            "test_id=ukr-lib-pair source={stem} stderr={}",
            error(&pair)
        );
        assert_eq!(
            observed(&pair).trim(),
            "1",
            "test_id=ukr-lib-d1 source={stem}: правильний виконуваний закон"
        );
        let bare = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&physical)
            .output()
            .expect("самостійне виконання фізичного SENS");
        assert!(
            bare.status.success(),
            "test_id=ukr-lib-bare source={stem} stderr={}",
            error(&bare)
        );
        assert_eq!(
            bare.stdout, pair.stdout,
            "test_id=ukr-lib-parity source={stem}: обидва шляхи мають однаковий D1 результат"
        );
        let mutant = scratch.join("змінене-джерело.lisp");
        let mut source_bytes = fs::read(&source).expect("зчитати чинний Lisp");
        source_bytes.extend_from_slice("\n(як-є ())\n".as_bytes());
        fs::write(&mutant, source_bytes).expect("зберегти лише тестовий мутант");
        let mismatch = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg("--t5m-pair")
            .arg(&mutant)
            .arg(&physical)
            .output()
            .expect("негативний SENS-мутант");
        assert!(
            !mismatch.status.success() && error(&mismatch).contains("T5M_PHYSICAL_PAIR_MISMATCH"),
            "test_id=ukr-lib-mutant source={stem} actual={}",
            error(&mismatch)
        );
        // Не зараховувати за сам факт наявності однойменної трійки:
        // її реальні байти мусять збігатися зі щойно виконаним SENS mint
        // та бітовим виглядом Zig. Дрейф позначається адресно без HOLD
        // для інших незалежних українських програм.
        let committed_physical = root.join("lib").join(format!("{stem}.sens"));
        let committed_view = root.join("lib").join(stem);
        let has_pair = committed_physical.is_file() && committed_view.is_file();
        let exact_pair = has_pair
            && fs::read(&physical).expect("нативний T5M")
                == fs::read(&committed_physical).expect("наявний T5M")
            && fs::read(&view).expect("нативний точний вигляд")
                == fs::read(&committed_view).expect("наявний точний вигляд");
        fs::remove_dir_all(&scratch).expect("прибрати лише власні тимчасові файли");
        if exact_pair {
            independently_executed.insert(stem);
            println!("SENS_UKR_EXECUTABLE_PASS file=lib/{stem}.lisp exact=Zig/T5M d1=1");
        } else if has_pair {
            println!("SENS_UKR_EXECUTABLE_DRIFT file=lib/{stem}.lisp reason=MINT_OR_VIEW_MISMATCH native=SENS/Zig/T5M");
        } else {
            println!("SENS_UKR_EXECUTABLE_PENDING file=lib/{stem}.lisp reason=NO_COMMITTED_T5M_TRIPLE");
        }
    }
    println!(
        "SENS_UKR_EXECUTABLE_TOTAL scope=cli-native-subset unique_files={} native=SENS/Zig/T5M",
        independently_executed.len()
    );
    assert!(
        physical_drifted.is_empty(),
        "test_id=ukr-lib-committed-parity-drift source_files={physical_drifted:?} action=refresh-via-SENS-Zig"
    );
}

#[test]
fn d11_selector_suffix_law_runs_in_native_sens() {
    // D11 candidate words are not called: the owner-ratified D3 selectors
    // compose in SENS. One asymmetric positive and two negative mutations.
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let fixture = root.join("tests/fixtures/d11-selector-law-witness.lisp");
    let original = fs::read_to_string(&fixture).expect("D11 SENS law witness source");
    let execution = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&fixture)
        .output()
        .expect("run D11 selector law in native SENS");
    assert!(
        execution.status.success(),
        "test_id=d11-selector-live layer=SENS stderr={}",
        error(&execution)
    );
    assert_eq!(
        observed(&execution).trim(),
        "1",
        "test_id=d11-selector-parent-child expected=D1:1 actual={} stderr={}",
        observed(&execution),
        error(&execution)
    );

    let mutations = [
        (
            "wrong-parent-suffix",
            "(батько (перше вхід))",
            "(батько (решта вхід))",
        ),
        (
            "indistinguishable-branches",
            "(селектор-зразок (як-є правильно) (як-є неправильно))",
            "(селектор-зразок (як-є правильно) (як-є правильно))",
        ),
    ];
    for (label, original_part, changed_part) in mutations {
        assert!(
            original.contains(original_part),
            "test_id=d11-selector-mutation-anchor fixture={} case={label}",
            fixture.display()
        );
        let replaced = original.replacen(original_part, changed_part, 1);
        let serial = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let mutant = std::env::temp_dir().join(format!(
            "sens-d11-selector-mutant-{}-{serial}.lisp",
            std::process::id()
        ));
        fs::write(&mutant, replaced).expect("write temporary D11 law mutant");
        let negative = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&mutant)
            .output()
            .expect("run negative D11 selector witness in SENS");
        fs::remove_file(&mutant).expect("delete only owned D11 mutation");
        assert!(
            negative.status.success(),
            "test_id=d11-selector-{label} layer=SENS stderr={}",
            error(&negative)
        );
        assert_eq!(
            observed(&negative).trim(),
            "0",
            "test_id=d11-selector-{label} expected=D1:0 actual={} stderr={}",
            observed(&negative),
            error(&negative)
        );
    }
}

#[test]
fn ukrainian_d3_d4_existing_files_mint_verify_and_execute() {
    verify_unpaired_ukrainian_libs_natively();
    // Executable Ukrainian D3/D4 .lisp programs; the stable test
    // name is retained for the existing exact-target CI invocation, not
    // static metadata or mock examples; SENS evaluates each physical program.
    let mut first: Option<SourceTriplet> = None;
    for name in [
        "atom-empty",
        "d3-cond-false-branch-skips-car",
        "d3-nested-tail-head-identity-lazy",
        "d3-false-tail-atom-skips-unsafe-head",
        "d3-cond-short-circuit-unsafe-car",
        "d3-empty-data-distinct-from-d1-no",
        "d4-fourth-after-two-list-append",
        "d4-cdar-first-pair-after-append",
        "d4-not-null-nonempty-cddr",
        "d4-cadr-nested-dotted-second-tail",
        "d4-append-right-associated-third",
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
        "d4-append-empty-right-exact-length",
        "d4-caar-nested-list",
        "d4-cdar-pair-tail",
        "d4-cddr-exact-two",
        "d4-cadr-exact-second",
        "d4-not-not-null-empty",
        "d4-append-empty-left",
        "d4-append-empty-left-law",
        "d4-append-three-associative-third-law",
        "d4-append-two-lists-order",
        "cdr-cdr-two-element-tail",
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
        "d4-null-cdr-two-preserves-second",
        "d4-caar-after-append-nested",
        "d4-cdar-nonempty-structural-tail",
        "d4-cddr-append-third-exact",
        "d4-null-after-cddr-two",
        "d4-append-nested-pair-preserved",
        "lib/d3-pair-laws",
        "lib/pair-associativity-law",
        "lib/поміняти-кожну-пару",
        "lib/rotate-left",
        "lib/pair-swap",
        "lib/поміняти-перші-два",
        "lib/pair-replace-first",
        "lib/pair-replace-rest",
        "lib/d4-second-two-tails-law",
        "lib/rotate-three-right",
        "lib/rotate-four-left",
        "lib/rotate-four-right",
        "lib/list-reverse-general",
        "lib/list-duplicate-atoms-preserve-compounds-general",
        "lib/list-interleave-two-general",
        "lib/list-reverse-tail-general",
        "lib/list-last-adjacent-equal-atom-suffix-general",
        "lib/list-append-general",
        "lib/list-collapse-adjacent",
        "lib/list-collapse-adjacent-atoms",
        "lib/list-adjacent-runs-general",
        "lib/list-collapse-adjacent-runs-general",
        "lib/list-neighbor-windows-general",
        "lib/list-common-prefix-general",
        "lib/list-common-prefix-three-atoms-general",
        "lib/list-common-suffix-general",
        "lib/list-subsequence-atoms-general",
        "lib/list-rotate-inverse-general",
        "lib/list-middle-even",
        "lib/list-split-first-occurrence-general",
        "lib/list-split-last-occurrence-general",
        "lib/list-flatten-nested-general",
        "lib/list-cartesian-product-general",
        "lib/list-stable-intersection-general",
        "lib/list-prefix-atoms-general",
        "lib/list-strip-prefix-atoms-general",
        "lib/tree-contains-atom-general",
        "lib/list-split-before-every-atom-general",
        "lib/list-first-globally-unique-atom-general",
        "lib/list-prefix-before-repeat-general",
        "lib/list-trim-edges-atom-general",
        "lib/list-all-distinct-atoms-general",
        "lib/list-keep-all-matching-atoms-general",
        "lib/list-overlapping-triplets-general",
        "lib/list-replace-first-atom-general",
        "lib/list-remove-interior-matching-atoms-general",
        "lib/list-run-length-unary-general",
        "lib/list-count-consecutive-atomic-runs-unary-general",
        "lib/list-multiset-intersection-general",
        "lib/list-zip-with-tails-general",
        "lib/list-three-lanes-general",
        "lib/list-suffix-atoms-general",
        "lib/list-split-at-first-atom-general",
        "lib/list-stable-bipartition-general",
        "lib/вилучити-всі-входження",
        "lib/замінити-всі-входження",
        "lib/list-stable-symmetric-difference-general",
        "lib/list-drop-while-atom-general",
        "lib/list-take-while-atom-general",
        "lib/list-remove-first-atom",
        "lib/list-remove-all-atoms-general",
        "lib/list-remove-last-atom",
        "lib/list-last-occurrence-suffix",
        "lib/pair-zip-unzip-two",
        "lib/pair-zip-unzip-three",
        "lib/list-zip-general",
        "lib/list-chunk-pairs-general",
        "lib/list-chunk-triplets-general",
        "lib/list-interpose-general",
        "lib/list-all-unordered-position-pairs-general",
        "lib/list-distinct-unordered-atom-pairs-general",
        "lib/list-first-divergence-suffix-general",
        "lib/list-interleave-three-general",
        "lib/list-interleave-three-rotation-general",
        "lib/list-drop-every-third-compact-general",
        "lib/list-drop-every-third-general",
        "lib/list-keep-repeated-atoms-once-general",
        "lib/list-last-repeated-atom-by-final-occurrence-general",
        "lib/list-last-compound-suffix-general",
        "lib/list-last-atom-suffix-general",
        "lib/list-all-subsets-by-position-general",
        "lib/list-palindrome-linear-atoms-general",
        "lib/list-trailing-equal-atomic-run-general",
        "lib/list-all-slices-ends-general",
        "lib/list-atom-sequence-equal-general",
        "lib/list-rotation-inverse-general",
        "lib/list-alternating-split-four",
        "lib/list-alternating-split-general",
        "lib/list-replace-fourth",
        "lib/list-swap-middle-four",
        "lib/list-swap-neighbors-four",
        "lib/list-swap-ends-five",
        "lib/reverse-three",
        "lib/interleave-pairs",
        "lib/list-insert-second",
        "lib/list-delete-second",
        "lib/list-halfturn-six",
        "lib/list-unique-stable",
        "lib/замінити-третій-в-четвірці",
        "lib/поміняти-другий-і-третій",
        "lib/виключне-або-д1",
        // Реальні українські DEFINE/LAMBDA: дві взаємодоповнювальні
        // рекурсивні функції над вкладеними NIL/CONS, без Text7 EQ.
        "d5-ukr-drop-until-recursive-program",
        "d5-ukr-take-before-recursive-program",
    ] {
        let triple = SourceTriplet::mint(name);
        let paired = triple.run_sens(true);
        assert!(
            paired.status.success(),
            "{name}: paired SENS: {}",
            error(&paired)
        );
        let expected = match name {
            "d5-ukr-drop-until-recursive-program" => "(((()) ()) ((()) ()) () ())",
            "d5-ukr-take-before-recursive-program" => "(() (()) (() () ()) ())",
            _ => "1",
        };
        assert_eq!(
            observed(&paired).trim(),
            expected,
            "{name}: exact SENS result (language evaluator, not host semantics)",
        );

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

#[test]
fn ukr_cond_skips_unsafe_branch_and_preserves_exact_t5m_triplet() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let stem = root.join("examples/migrated/коротке-замикання");
    let source = stem.with_extension("lisp");
    let physical = stem.with_extension("sens");
    let view = fs::read_to_string(&stem).expect("точний бітовий перегляд");
    assert_eq!(view, format!("{}\n", view.trim_end()), "канонічний LF");

    let opened = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("open").arg(&physical).output().expect("Zig/T5M open");
    assert!(opened.status.success(), "{}", error(&opened));
    assert_eq!(opened.stdout, view.as_bytes(), "точне обернене представлення");

    let paired = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-pair").arg(&source).arg(&physical).output()
        .expect("SENS: українська проєкція ↔ фізична програма");
    assert!(paired.status.success(), "{}", error(&paired));
    assert_eq!(observed(&paired).trim(), "1", "D1:1 без виконання хибної гілки");

    let direct = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&physical).output().expect("нативне виконання SENS");
    assert!(direct.status.success(), "{}", error(&direct));
    assert_eq!(direct.stdout, paired.stdout, "носій не змінює SENS семантики");
}


#[test]
fn contest_uk_all_physical_programs_have_native_execution_and_peers() {
    // Лічимо тільки фізичні .sens, які справді виконав SENS через Zig/T5M.
    // Жодних ручних списків категорій або Python/JSON-оракулів.
    use std::collections::BTreeSet;

    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    // Конкурс друкує абсолютний canonical source; PathBuf із ../.. у
    // CARGO_MANIFEST_DIR не є лексичним префіксом цього самого шляху.
    // Нормалізуємо директорію, а не послаблюємо перевірку source-only.
    let dir = root.join("benchmarks/contest-uk")
        .canonicalize()
        .expect("чинна тека нативного конкурсу");
    let output = Command::new("bash")
        .arg(dir.join("run-native.sh"))
        .env("SENS_BINARY", env!("CARGO_BIN_EXE_sens"))
        .env("SENS_TRIT_BINARY", env!("CARGO_BIN_EXE_sens-trit"))
        .env("SENS_CONTEST_REPEATS", "1")
        .output()
        .expect("виконати нативний конкурс");
    // У черзі нативного remint можуть перебувати нові українські .lisp,
    // для яких фізичні .sens/view ще НЕ опубліковані. Вони не є
    // виконуваними конкурсантами й не повинні робити чужу SENS CI-дію RED.
    // Але неповна фізична пара або будь-яка невдала вже фізична програма
    // лишається справжньою помилкою, а не "пропуском".
    let report = observed(&output);
    let mut pending: BTreeSet<String> = BTreeSet::new();
    let mut executed: BTreeSet<String> = BTreeSet::new();
    let mut unexpected: Vec<String> = Vec::new();
    for line in report.lines().skip(1) {
        let columns: Vec<&str> = line.split('\t').collect();
        if columns.len() != 5 {
            unexpected.push(line.to_owned());
            continue;
        }
        let name = columns[0];
        match columns[4] {
            "ПІДТВЕРДЖЕНО" => {
                assert!(executed.insert(name.to_owned()), "дубль результату: {name}");
            }
            "НЕМАЄ_ОБЕРНЕНОЇ_ПАРИ" => {
                let source = dir.join(format!("{name}.lisp"));
                let physical = dir.join(format!("{name}.sens"));
                let view = dir.join(name);
                assert!(
                    source.is_file() && !source.is_symlink()
                        && !physical.exists() && !physical.is_symlink()
                        && !view.exists() && !view.is_symlink(),
                    "не завершений remint або зламана напівпара: {name}"
                );
                assert!(pending.insert(name.to_owned()), "дубль очікування: {name}");
            }
            _ => unexpected.push(line.to_owned()),
        }
    }
    assert!(
        unexpected.is_empty(),
        "SENS конкурс має справжню помилку: {unexpected:?}; stdout={report} stderr={}",
        error(&output)
    );
    // Source-only учасники законно очікують нативний remint у stderr,
    // але сам скрипт має завершуватися GREEN, коли всі фізичні програми
    // реально виконалися. Попереднє порівняння з pending.is_empty()
    // перетворювало чесне очікування на штучний CI RED.
    for line in error(&output).lines() {
        if let Some(rest) = line.strip_prefix("CONTEST_PENDING_NATIVE_PAIR source=") {
            let source_path = rest
                .strip_suffix(" status=NOT_EXECUTED")
                .expect("точний стан непарного джерела");
            let source = PathBuf::from(source_path);
            // Bash pwd та Rust canonicalize можуть розходитись лексично
            // через шлях checkout. Звіряти фізичну теку, не текст префікса:
            // усі вимоги до справжнього файла та відсутності пари збережено.
            assert!(
                source.is_file() && !source.is_symlink(),
                "неправильне джерело у stderr: {source_path}"
            );
            let resolved = source.canonicalize()
                .expect("чинне джерело кандидата SENS");
            assert_eq!(
                resolved.parent(), Some(dir.as_path()),
                "джерело поза реальною текою конкурсу: {source_path}"
            );
            let name = source.file_stem()
                .and_then(|stem| stem.to_str())
                .expect("українська назва source-only Lisp");
            assert!(
                !source.with_extension("sens").exists()
                    && !source.with_extension("").exists(),
                "source-only не може мати напівпари: {source_path}"
            );
            assert!(pending.insert(name.to_owned()), "дубль pending: {name}");
        } else if !line.is_empty() {
            unexpected.push(format!("stderr: {line}"));
        }
    }
    assert!(
        unexpected.is_empty(),
        "нативний конкурс приховав помилку: {unexpected:?}; stdout={report} stderr={}",
        error(&output)
    );
    assert!(
        output.status.success(),
        "жодне pending джерело не скасовує RED справжньої фізичної програми: {report}; stderr={}",
        error(&output)
    );

    let mut tracked: BTreeSet<String> = BTreeSet::new();
    for entry in fs::read_dir(&dir).expect("прочитати конкурсні програми") {
        let path = entry.expect("прочитати файл").path();
        if path.extension().is_none_or(|ext| ext != "sens") {
            continue;
        }
        assert!(path.is_file() && !path.is_symlink(), "неправильний фізичний носій: {path:?}");
        let name = path.file_stem()
            .and_then(|stem| stem.to_str())
            .expect("українська назва фізичного файла")
            .to_owned();
        assert!(tracked.insert(name), "дубль фізичної конкурсної програми");
    }
    assert!(!tracked.is_empty(), "немає жодної фізичної конкурсної програми");

    assert_eq!(
        executed, tracked,
        "Кожна чинна .sens мусить бути обернена й справді виконана SENS: {report}"
    );
    println!(
        "SENS_UKR_EXECUTABLE_PASS count={} pending_unpaired={} corpus=contest-uk native=SENS_ZIG_T5M release=NOT_CERTIFIED",
        tracked.len(), pending.len()
    );
}

#[test]
fn d9_native_witness_executes_current_lisp_with_zig_t5m() {
    // SENS вирішує семантику, Zig — фізичну оберненість.
    // Не підтверджувати старий SYMBOL? статичним порівнянням із Core4:
    // Text7 не є Value::Symbol і не допускає SYMBOL->STRING.
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let source = root.join("tests/semantic/d9-four-uk-projections-laws.lisp");
    let id = UNIQUE.fetch_add(1, Ordering::Relaxed);
    let stem = format!("sens-d9-{}-{id}", std::process::id());
    let physical = std::env::temp_dir().join(format!("{stem}.sens"));
    let view = physical.with_extension("");
    let altered = std::env::temp_dir().join(format!("{stem}.lisp"));
    assert!(!physical.exists() && !view.exists() && !altered.exists(), "конфлікт тимчасового SENS-носія");

    let mint = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-mint").arg(&source).arg(&physical)
        .output().expect("нативний SENS mint Д9");
    assert!(mint.status.success(), "SENS mint: {}", error(&mint));
    assert!(physical.is_file(), "SENS mint не створив T5M");

    let opened = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("open").arg(&physical).output()
        .expect("Zig T5M open");
    assert!(opened.status.success(), "Zig open: {}", error(&opened));
    assert!(!opened.stdout.is_empty(), "Zig повернув порожню фізичну проєкцію");
    fs::write(&view, &opened.stdout).expect("зафіксувати точне Zig-бітове вигляд");
    let verified = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("verify-view").arg(&physical).output()
        .expect("Zig verify-view");
    assert!(verified.status.success(), "Zig verify-view: {}", error(&verified));

    let paired = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-pair").arg(&source).arg(&physical).output()
        .expect("виконання живого Д9 Lisp із парою");
    assert!(paired.status.success(), "SENS paired: {}", error(&paired));
    let standalone = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&physical).output()
        .expect("незалежне фізичне виконання Д9");
    assert!(standalone.status.success(), "SENS standalone: {}", error(&standalone));
    assert_eq!(paired.stdout, standalone.stdout, "виконання джерела та T5M не збігається");

    // Змінене джерело мусить отримати справжнє T5M_PHYSICAL_PAIR_MISMATCH.
    let original = fs::read_to_string(&source).expect("український свідок Д9");
    fs::write(&altered, format!("{original}\n(як-є ())\n"))
        .expect("підмінене джерело для негативного свідка");
    let mismatch = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-pair").arg(&altered).arg(&physical).output()
        .expect("негативний T5M виклик");
    assert!(!mismatch.status.success(), "змінений Lisp помилково прийнято як T5M");
    assert!(
        error(&mismatch).contains("T5M_PHYSICAL_PAIR_MISMATCH"),
        "неправильна причина відхилення: {}", error(&mismatch)
    );

    fs::remove_file(&altered).expect("прибрати негативний Lisp");
    fs::remove_file(&physical).expect("прибрати тимчасовий T5M");
    fs::remove_file(&view).expect("прибрати точний Zig-вигляд");
}
