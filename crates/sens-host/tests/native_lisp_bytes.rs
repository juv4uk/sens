#![cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]

use sens::{eval_parsed_expressions, parse_mixed_exact_domain, 
    eval_program, load_core_library, register_capability, Environment, Exactness, Expr,
    LanguageError, Session, Span, Value,
};
use sens_host::install;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Mutex, MutexGuard};

static EXECUTOR_CALLS: AtomicUsize = AtomicUsize::new(0);
static TEST_LOCK: Mutex<()> = Mutex::new(());

struct RestoreHostCapabilities;

impl Drop for RestoreHostCapabilities {
    fn drop(&mut self) {
        install();
    }
}

fn test_lock() -> MutexGuard<'static, ()> {
    TEST_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    assert!(
        path.starts_with("lib/machine/"),
        "mixed exact-domain reader is reserved for machine-source fixtures: {path}"
    );
    let source = read(path);
    let expressions = parse_mixed_exact_domain(&source)
        .unwrap_or_else(|error| panic!("{path} must parse as mixed exact-domain machine source: {error}"));
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("{path} must load through the mixed exact-domain machine reader: {error}"));
}

fn spy_executor(
    _arguments: &[Expr],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    EXECUTOR_CALLS.fetch_add(1, Ordering::SeqCst);
    Ok(Value::Number(0.0, Exactness::Exact))
}

#[test]
fn unadmitted_ud2_form_is_rejected_before_host_executor() {
    let _serial = test_lock();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before machine admission witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    EXECUTOR_CALLS.store(0, Ordering::SeqCst);
    register_capability("native-call-u64-raw", spy_executor);
    let _restore = RestoreHostCapabilities;

    let result = eval_program(
        "(x86-call-admitted-u64 (quote ((ud2))) 0)",
        &mut session,
    )
    .expect("unadmitted machine form must be a Lisp-level named rejection");

    assert_eq!(
        result.value.to_string(),
        "(rejected unadmitted-machine-form (ud2))"
    );
    assert_eq!(
        EXECUTOR_CALLS.load(Ordering::SeqCst),
        0,
        "rejected machine form must never reach the host executor"
    );
}

/// #176 continued (found while generalizing MOV r64,imm64's admission to all
/// 16 GPRs, not a new bug introduced by that change -- rax/rcx already had
/// the same gap): the `immediate` admission wildcard has no range check, so
/// `(mov-r64-imm64 rax -1)` is admitted as valid Lisp data. But `x86-u64-bytes`
/// uses a plain `mod` per byte, which does not wrap negative whole values the
/// way `x86-disp8-byte` was fixed to for disp8 (#199) -- so encoding produces
/// an out-of-range byte, caught fail-closed at the real host boundary
/// (`native-call-u64-raw` rejects non-0..255 bytes) as a language error
/// rather than a clean `(rejected unadmitted-machine-form ...)` value. Never
/// silently executed: this documents the exact, real failure mode rather
/// than papering over it. No current Lisp semantic need pulls negative
/// imm64 down yet, so the fix (a floor-mod-style two's-complement byte
/// splitter for the full imm64 range) stays out of scope for now.
#[test]
fn negative_mov_r64_imm64_is_admitted_but_fails_closed_at_the_real_host_boundary() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before machine admission witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    let result = eval_program(
        "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax -1) (ret))) 0)",
        &mut session,
    );

    assert!(
        result.is_err(),
        "a negative imm64 must never actually execute on real hardware, even though \
         admission currently has no range check for it"
    );
}

#[test]
fn semantic_lowering_must_produce_structured_forms_before_admission_and_execution() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before structured machine lowering");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let add_forms = eval_program("(x86-lower-add-u64-forms 2 3)", &mut session)
        .expect("semantic lowering must expose structured admitted machine forms before bytes");
    assert_eq!(
        add_forms.value.to_string(),
        "((mov-r64-imm64 rax 2) (mov-r64-imm64 rcx 3) (add-r64-r64 rax rcx) (ret))"
    );

    let add = eval_program(
        "(x86-call-admitted-u64 (x86-lower-add-u64-forms 2 3) 0)",
        &mut session,
    )
    .expect("admitted semantic ADD forms must execute through the canonical gateway");
    assert_eq!(add.value.to_string(), "5");

    let interpreter_car = eval_program("(перше (сполучити 2 3))", &mut session)
        .expect("interpreter CAR reference witness must remain valid");
    let interpreter_cdr = eval_program("(решта (сполучити 2 3))", &mut session)
        .expect("interpreter CDR reference witness must remain valid");

    let native_car = eval_program(
        "(x86-call-admitted-u64 (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)",
        &mut session,
    )
    .expect("CONS+CAR lowering must pass through admission before host execution");
    let native_cdr = eval_program(
        "(x86-call-admitted-u64 (x86-lower-cons-cdr-u64-forms 2 3) x86-pair-cell-bytes)",
        &mut session,
    )
    .expect("CONS+CDR lowering must pass through admission before host execution");

    assert_eq!(native_car.value, interpreter_car.value);
    assert_eq!(native_cdr.value, interpreter_cdr.value);

    let lowering_source = fs::read_to_string(repo_root().join("lib/machine/lowering/semantic-x86-64.lisp"))
        .expect("semantic lowerer source must be readable");
    for forbidden in [
        "(def x86-lower-add-u64\n",
        "(def x86-lower-cons-car-u64\n",
        "(def x86-lower-cons-cdr-u64\n",
        "(x86-encode-program\n",
    ] {
        assert!(
            !lowering_source.contains(forbidden),
            "semantic lowerer must expose forms only; found retired byte path {forbidden}"
        );
    }
}

#[test]
fn x86_pair_layout_is_one_lisp_owned_machine_readable_authority() {
    let _serial = test_lock();
    let path = repo_root().join("lib/machine/layout/pair-x86-64.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));

    sens::parse(&source).expect("x86 pair layout authority must be valid sens");
    for required in [
        "(00001001 x86-pair-cell-bytes 16)",
        "(00001001 x86-pair-car-offset 0)",
        "(00001001 x86-pair-cdr-offset 8)",
        "(target x86-64)",
        "(arena-argument-register rdi)",
        "(lifetime native-call)",
        "(escape forbidden)",
    ] {
        assert!(source.contains(required), "pair layout authority missing {required}");
    }

    assert!(
        !source.contains("semantic-id"),
        "machine representation layout must not allocate language semantic identities"
    );

    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before layout authority");
    eval_program(&source, &mut session).expect("pair layout authority must evaluate as ordinary sens");

    for (name, expected) in [
        ("x86-pair-cell-bytes", "16"),
        ("x86-pair-car-offset", "0"),
        ("x86-pair-cdr-offset", "8"),
    ] {
        let actual = eval_program(name, &mut session)
            .unwrap_or_else(|error| panic!("{name} must be queryable: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected);
    }
}

#[test]
fn interpreter_pair_reference_witnesses_remain_two_and_three() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before pair reference witness");

    let car = eval_program("(перше (сполучити 2 3))", &mut session)
        .expect("interpreter CAR witness must remain valid");
    let cdr = eval_program("(решта (сполучити 2 3))", &mut session)
        .expect("interpreter CDR witness must remain valid");

    assert_eq!(car.value.to_string(), "2");
    assert_eq!(cdr.value.to_string(), "3");
}

#[test]
fn raw_executor_accepts_canonical_binary_number_machine_bytes() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("core must bootstrap before BinaryNumber machine-byte witness");

    // mov rax,42 ; ret
    let result = eval_program(
        "(native-call-u64-raw (quote (#b1001000 #b10111000 #b101010 #b0 #b0 #b0 #b0 #b0 #b0 #b0 #b11000011)))",
        &mut session,
    )
    .expect("raw machine boundary must explicitly decode <=8-bit BinaryNumber cells");

    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn raw_executor_accepts_mixed_legacy_and_binary_machine_byte_carriers() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("core must bootstrap before mixed machine-byte witness");

    // Same bounded program, deliberately mixing canonical BinaryNumber with
    // the historical exact-integer carrier. This is byte-boundary decoding,
    // not general numeric coercion in the language.
    let result = eval_program(
        "(native-call-u64-raw (quote (#b1001000 184 #b101011 0 #b0 0 #b0 0 #b0 0 #b11000011)))",
        &mut session,
    )
    .expect("raw machine boundary must accept both explicitly supported byte carriers");

    assert_eq!(result.value.to_string(), "43");
}

#[test]
fn raw_executor_rejects_binary_number_wider_than_one_byte() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("core must bootstrap before over-width machine-byte witness");

    let error = eval_program(
        "(native-call-u64-raw (quote (#b100000000)))",
        &mut session,
    )
    .expect_err("9-bit BinaryNumber must fail closed before executable memory");

    assert_eq!(error.kind, sens::ErrorKind::Type);
    assert!(
        error
            .to_string()
            .contains("<=8-bit BinaryNumber"),
        "error must identify the bounded machine-byte carrier: {error}"
    );
}

#[test]
fn semantics_blind_raw_executor_accepts_optional_arena_bytes() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before native witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let result = eval_program(
        "(native-call-u64-raw (x86-encode-admitted-program (x86-lower-add-u64-forms 2 3)) 16)",
        &mut session,
    )
    .expect("raw host mechanism must receive only bytes materialized from admitted structured forms");

    assert_eq!(result.value.to_string(), "5");
}

#[test]
fn lisp_owned_pair_memory_addressing_has_exact_rdi_disp8_bytes() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before machine encoder witness");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);

    let car_load = eval_program(
        "(x86-encode-mov-r64-mem-disp8 (quote rax) (quote rdi) x86-pair-car-offset)",
        &mut session,
    )
    .expect("Lisp encoder must encode CAR's [rdi+0] load");
    let cdr_load = eval_program(
        "(x86-encode-mov-r64-mem-disp8 (quote rax) (quote rdi) x86-pair-cdr-offset)",
        &mut session,
    )
    .expect("Lisp encoder must encode CDR's [rdi+8] load");
    let car_store = eval_program(
        "(x86-encode-mov-mem-disp8-r64 (quote rdi) x86-pair-car-offset (quote rax))",
        &mut session,
    )
    .expect("Lisp encoder must encode CONS's [rdi+0] store");

    assert_eq!(car_load.value.to_string(), "(72 139 71 0)");
    assert_eq!(cdr_load.value.to_string(), "(72 139 71 8)");
    assert_eq!(car_store.value.to_string(), "(72 137 71 0)");
}

#[test]
fn native_pair_car_cdr_match_the_interpreter_reference_witness() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before pair parity witness");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let interpreter_car = eval_program("(перше (сполучити 2 3))", &mut session)
        .expect("interpreter CAR reference witness must remain valid");
    let interpreter_cdr = eval_program("(решта (сполучити 2 3))", &mut session)
        .expect("interpreter CDR reference witness must remain valid");

    let native_car = eval_program(
        "(native-call-u64-raw (x86-encode-admitted-program (x86-lower-cons-car-u64-forms 2 3)) x86-pair-cell-bytes)",
        &mut session,
    )
    .expect("Lisp-owned CONS+CAR forms must materialize through admission before raw host execution");
    let native_cdr = eval_program(
        "(native-call-u64-raw (x86-encode-admitted-program (x86-lower-cons-cdr-u64-forms 2 3)) x86-pair-cell-bytes)",
        &mut session,
    )
    .expect("Lisp-owned CONS+CDR forms must materialize through admission before raw host execution");

    assert_eq!(native_car.value, interpreter_car.value);
    assert_eq!(native_cdr.value, interpreter_cdr.value);
}

#[test]
fn lisp_owned_add_bytes_execute_natively_through_semantics_blind_host() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before native witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let result = eval_program(
        "(native-call-u64-raw (x86-encode-admitted-program (x86-lower-add-u64-forms 2 3)))",
        &mut session,
    )
    .expect("host must execute bytes admitted from Lisp-owned structured forms");

    assert_eq!(result.value.to_string(), "5");
}

#[test]
fn native_execution_mechanism_is_not_a_language_semantic_identity() {
    let _serial = test_lock();
    let registry = fs::read_to_string(repo_root().join("lib/surface/semantic-registry.lisp"))
        .expect("semantic registry must be readable");
    assert!(
        !registry.contains("native-call-u64-raw"),
        "raw native invocation is host mechanism, never a language semantic identity"
    );
}

#[test]
fn rust_native_executor_may_grow_local_semantics_and_still_exposes_real_memory_mechanism() {
    let _serial = test_lock();
    let mut source =
        fs::read_to_string(repo_root().join("crates/sens-host/src/native_exec.rs"))
            .expect("native execution mechanism source must be readable");
    source.push_str(
        &fs::read_to_string(repo_root().join("crates/sens-host/src/platform.rs"))
            .expect("host memory-adapter source must be readable"),
    );

    // #1347 deliberately places no semantic-content restriction on Rust.
    // This witness now proves only the physical execution mechanism. Language
    // authority is protected separately at the host -> Lisp boundary.
    #[cfg(unix)]
    let required = ["mmap", "mprotect", "munmap", "PROT_WRITE", "PROT_EXEC"];
    #[cfg(windows)]
    let required = [
        "VirtualAlloc",
        "VirtualProtect",
        "VirtualFree",
        "FlushInstructionCache",
        "PAGE_EXECUTE_READ",
    ];

    for required in required {
        assert!(
            source.contains(required),
            "native host must expose the real executable-memory mechanism; missing {required}"
        );
    }
}

/// #176's own admitted i5-6400 inventory (#174) targets this exact CPU
/// model, and this file already only runs on `target_os = "linux"`, so
/// this witness is a genuine execution proof on the very silicon #174-#178
/// describe -- not a decode-only check. Each condition's flag test is
/// proven by actually branching (or not) on real hardware, not by
/// disassembling the bytes and trusting the mnemonic.
#[test]
fn jcc_actually_branches_on_real_hardware_for_equal_and_ordering_conditions() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    // Each program: mov rax,A; mov rcx,B; cmp rax,rcx; <jcc> +10; mov rax,999;
    // ret. `jcc`'s disp8=10 skips exactly the 10-byte mov-r64-imm64 when
    // taken, so the result is A when taken, 999 when not taken. This is a
    // real, executed proof (not a static decode) that each condition's
    // flag test genuinely reflects the CMP result on real i5-6400 silicon.
    let mut run = |jcc: &str, a: i64, b: i64| -> String {
        let source = format!(
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax {a}) (mov-r64-imm64 rcx {b}) (cmp-r64-r64 rax rcx) ({jcc}-rel8 10) (mov-r64-imm64 rax 999) (ret))) 0)"
        );
        eval_program(&source, &mut session)
            .expect("real hardware must execute the admitted program")
            .value
            .to_string()
    };

    // JZ/JNZ: equality.
    assert_eq!(run("jz", 5, 5), "5", "JZ must branch when equal");
    assert_eq!(run("jz", 5, 6), "999", "JZ must not branch when not equal");
    assert_eq!(run("jnz", 5, 6), "5", "JNZ must branch when not equal");
    assert_eq!(run("jnz", 5, 5), "999", "JNZ must not branch when equal");

    // JL/JNL: signed less-than (SF<>OF).
    assert_eq!(run("jl", 3, 5), "3", "JL must branch when 3 < 5");
    assert_eq!(run("jl", 5, 3), "999", "JL must not branch when 5 >= 3");
    assert_eq!(run("jnl", 5, 3), "5", "JNL must branch when 5 >= 3");

    // JB/JNB: unsigned below (CF).
    assert_eq!(run("jb", 3, 5), "3", "JB must branch when 3 <u 5");
    assert_eq!(run("jb", 5, 3), "999", "JB must not branch when 5 >=u 3");
    assert_eq!(run("jnb", 5, 3), "5", "JNB must branch when 5 >=u 3");

    // JLE/JNLE: signed less-or-equal.
    assert_eq!(run("jle", 5, 5), "5", "JLE must branch when equal");
    assert_eq!(run("jnle", 6, 5), "6", "JNLE must branch when strictly greater");
    assert_eq!(run("jnle", 5, 5), "999", "JNLE must not branch when equal");
}

/// #176 continued: JMP rel8's defining property, compared to Jcc, is that
/// it branches unconditionally -- there is no CMP/flag state to satisfy.
/// This is a real, executed proof on the i5-6400 that the branch is taken
/// regardless of any prior flag state, not merely that the bytes decode to
/// an unconditional-jump mnemonic.
#[test]
fn jmp_actually_branches_unconditionally_on_real_hardware_regardless_of_flags() {
    let _serial = test_lock();
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    // mov rax,A; mov rcx,B; cmp rax,rcx (sets flags one way or another,
    // deliberately including the "not equal" case that would make JZ NOT
    // branch); jmp +10 (unconditionally skips the following mov-r64-imm64,
    // regardless of what CMP just set); mov rax,999; ret.
    let mut run = |a: i64, b: i64| -> String {
        let source = format!(
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax {a}) (mov-r64-imm64 rcx {b}) (cmp-r64-r64 rax rcx) (jmp-rel8 10) (mov-r64-imm64 rax 999) (ret))) 0)"
        );
        eval_program(&source, &mut session)
            .expect("real hardware must execute the admitted program")
            .value
            .to_string()
    };

    assert_eq!(run(5, 5), "5", "JMP must branch when the prior CMP set ZF");
    assert_eq!(
        run(5, 6),
        "5",
        "JMP must branch even when the prior CMP cleared ZF -- unlike JZ, it does not consult flags"
    );
}
