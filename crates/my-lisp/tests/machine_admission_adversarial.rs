use my_lisp::{
    eval_program, load_core_library, register_capability, Environment, Exactness, Expr,
    LanguageError, Session, Span, Value,
};
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};

static EXECUTOR_CALLS: AtomicUsize = AtomicUsize::new(0);

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary my-lisp: {error}", path.display()));
}

fn spy_executor(
    _arguments: &[Expr],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    EXECUTOR_CALLS.fetch_add(1, Ordering::SeqCst);
    Ok(Value::Number(999.0, Exactness::Exact))
}

#[test]
fn canonical_machine_gateway_rejects_raw_bytes_register_bypass_and_truncation_before_host() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before admission adversaries");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    register_capability("native-call-u64-raw", spy_executor);

    for (request, expected) in [
        (
            "(x86-call-admitted-u64 (quote (15 11)) 0)",
            "(rejected unadmitted-machine-form 15)",
        ),
        (
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rbx 1))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-imm64 rbx 1))",
        ),
        (
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-imm64 rax))",
        ),
    ] {
        EXECUTOR_CALLS.store(0, Ordering::SeqCst);
        let result = eval_program(request, &mut session)
            .expect("unadmitted machine data must be rejected as Lisp data, not host failure");
        assert_eq!(result.value.to_string(), expected);
        assert_eq!(
            EXECUTOR_CALLS.load(Ordering::SeqCst),
            0,
            "rejected raw/malformed machine data must never reach the host executor: {request}"
        );
    }
}
