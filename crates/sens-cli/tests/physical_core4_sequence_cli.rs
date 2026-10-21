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
        let relative = if name.starts_with("lib/") {
            format!("{name}.lisp")
        } else {
            format!("tests/semantic/native-t5/{name}.lisp")
        };
        let source = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .join(relative);
        assert!(source.is_file(), "actual Ukrainian SENS source missing: {name}");
        let id = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let physical = std::env::temp_dir().join(format!(
            "sens-live-ukr-{}-{}-{id}.sens", name.replace('/', "-"), std::process::id()
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


// Перевіряємо реальне виконання ще не опублікованих фізичних трійок.
// Український Lisp є джерелом; exact-слова читає SENS, T5M пакує Zig.
fn verify_unpaired_ukrainian_libs_natively() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let mut independently_executed = std::collections::BTreeSet::new();
    for stem in [
        "d1-direct-values",
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
        "list-reverse-four",
        "list-halfturn-four",
        "list-halfturn-six",
        "list-reverse-general",
        "list-drop-last-general",
        "list-append-general",
        "list-collapse-adjacent",
        "list-unique-stable",
        "розділити-до-першого-входження",
        "list-interleave-two-pairs",


        "list-zip-general",
        "pair-zip-unzip-three",

        "виключне-або-д1",
            "поміняти-кожну-пару",
            "вилучити-перше-входження",
    ] {
        let source = root.join("lib").join(format!("{stem}.lisp"));
        assert!(source.is_file(), "{stem}: українське джерело відсутнє");
        let sequence = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let scratch = std::env::temp_dir().join(format!(
            "sens-native-unpaired-{}-{sequence}", std::process::id()
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
            "test_id=ukr-lib-mint source={stem} stderr={}", error(&minted)
        );
        assert!(physical.is_file() && view.is_file(), "{stem}: створено фізичну пару");
        // Оборотні трійки нових прикладів мають бути тотожні байт-в-байт
        // реальному пакуванню Zig, а не лише текстовому звіту.
        if matches!(
            stem,
            "вилучити-середнє-з-трійки"
                | "вставити-посеред-пари"
                | "розділити-четвірку-на-пари"
                | "list-swap-ends-five"
                | "list-swap-inner-five"
                | "rotate-four-left"
                | "rotate-four-right"
                | "list-delete-second"
                | "list-insert-second"
                | "list-reverse-four"
                | "list-halfturn-four"
                | "list-halfturn-six"
                | "list-zip-general"
                | "list-drop-last-general"
                | "list-append-general"
                | "list-collapse-adjacent"
                | "розділити-до-першого-входження"
                | "list-unique-stable"
                | "замінити-третій-в-четвірці"
        ) {
            let committed_physical = root.join("lib").join(format!("{stem}.sens"));
            let committed_view = root.join("lib").join(stem);
            assert_eq!(
                fs::read(&physical).expect("згенеровані T5M байти"),
                fs::read(&committed_physical).expect("збережені T5M байти"),
                "test_id=ukr-lib-physical-parity source={stem}"
            );
            assert_eq!(
                fs::read(&view).expect("згенеровані точні слова"),
                fs::read(&committed_view).expect("збережені точні слова"),
                "test_id=ukr-lib-exact-parity source={stem}"
            );
        }
        let verify = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg("verify-view")
            .arg(&physical)
            .output()
            .expect("Zig verify-view");
        assert!(
            verify.status.success(),
            "test_id=ukr-lib-inverse source={stem} stderr={}", error(&verify)
        );
        let pair = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg("--t5m-pair")
            .arg(&source)
            .arg(&physical)
            .output()
            .expect("реальне парне виконання SENS");
        assert!(
            pair.status.success(),
            "test_id=ukr-lib-pair source={stem} stderr={}", error(&pair)
        );
        assert_eq!(
            observed(&pair).trim(), "1",
            "test_id=ukr-lib-d1 source={stem}: правильний виконуваний закон"
        );
        let bare = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&physical)
            .output()
            .expect("самостійне виконання фізичного SENS");
        assert!(
            bare.status.success(),
            "test_id=ukr-lib-bare source={stem} stderr={}", error(&bare)
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
            !mismatch.status.success() &&
                error(&mismatch).contains("T5M_PHYSICAL_PAIR_MISMATCH"),
            "test_id=ukr-lib-mutant source={stem} actual={}",
            error(&mismatch)
        );
        fs::remove_dir_all(&scratch).expect("прибрати лише власні тимчасові файли");
        independently_executed.insert(stem);
        println!("SENS_UKR_EXECUTABLE_PASS file=lib/{stem}.lisp exact=Zig/T5M d1=1");
    }
    println!(
        "SENS_UKR_EXECUTABLE_TOTAL scope=cli-native-subset unique_files={} native=SENS/Zig/T5M",
        independently_executed.len()
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
        "lib/list-append-general",
        "lib/list-collapse-adjacent",
        "lib/pair-zip-unzip-two",
        "lib/list-zip-general",
        "lib/list-chunk-pairs-general",
        "lib/list-interpose-general",
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
        assert!(paired.status.success(), "{name}: paired SENS: {}", error(&paired));
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
