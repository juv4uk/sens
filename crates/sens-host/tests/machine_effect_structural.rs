#![cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]

use sens::{
    eval_program, load_core_library, register_capability, Environment, ErrorKind, Exactness, Expr,
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
    TEST_LOCK.lock().unwrap_or_else(|poisoned| poisoned.into_inner())
}

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary sens: {error}", path.display()));
}

fn machine_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/effects/u64.lisp", &mut session);
    load_lisp_file("lib/machine/effects/structural.lisp", &mut session);
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/atoms/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/projection/x86-64.lisp", &mut session);
    session
}

fn spy_executor(
    _arguments: &[Expr],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    EXECUTOR_CALLS.fetch_add(1, Ordering::SeqCst);
    Ok(Value::Number(4242.0, Exactness::Exact))
}

#[test]
fn structural_effect_seam_executes_car_cons_vertical_day_on_host_boundary() {
    let _serial = test_lock();
    install();
    let mut session = machine_session();

    let reference = eval_program("(перше (сполучити 2 3))", &mut session)
        .expect("interpreter structural reference");
    assert_eq!(reference.value.to_string(), "2");

    let native = eval_program(
        "(x86-call-semantic-car-effect-u64 (сполучити 2 3))",
        &mut session,
    )
    .expect("structural effect seam must execute through admitted host gateway");

    assert_eq!(native.value, reference.value);
}

#[test]
fn invalid_car_input_fails_before_structural_effect_reaches_host() {
    let _serial = test_lock();
    let mut session = machine_session();

    register_capability("native-call-u64-raw", spy_executor);
    let _restore = RestoreHostCapabilities;

    for source in ["5", "(quote ())"] {
        let reference = eval_program(&format!("(перше {source})"), &mut session)
            .expect_err("canonical CAR must reject invalid input");
        assert_eq!(reference.kind, ErrorKind::Type);

        EXECUTOR_CALLS.store(0, Ordering::SeqCst);
        let machine = eval_program(
            &format!("(x86-call-semantic-car-effect-u64 {source})"),
            &mut session,
        )
        .expect_err("machine wrapper must preserve canonical Type before host");

        assert_eq!(machine.kind, reference.kind);
        assert_eq!(EXECUTOR_CALLS.load(Ordering::SeqCst), 0);
    }
}
