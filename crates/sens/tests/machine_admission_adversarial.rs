use sens::{
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
        .unwrap_or_else(|error| panic!("{} must load as ordinary sens: {error}", path.display()));
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
fn exhausted_instruction_patterns_return_exact_d1_no_not_structural_empty() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("ратифіковане ядро");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    // Порожній перелік шаблонів — це предикат D1:0, а не структурне D3:000.
    for source in [
        "(x86-admitted-instruction-against? (00000001 ()) (00000001 ud2))",
        "(x86-admitted-instruction-against? (00000001 ()) (00000001 ()))",
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(false),
            "неприпустима інструкція не може повертати структурне ()"
        );
    }
}

#[test]
fn x86_pattern_mismatches_are_exact_d1_no_not_empty() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("ратифіковане ядро");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);

    // Структура не є D1:0. Невідповідна інструкція має повертати
    // саме негативний предикат, який можна передати у суворий D3 COND.
    for source in [
        "(x86-admission-pattern-match? (00000001 (ret)) (00000001 (ud2)))",
        "(x86-admission-pattern-match? (00000001 (ret)) (00000001 ret))",
        "(x86-admission-pattern-match? (00000001 (ret)) (00000001 (ret extra)))",
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(false),
            "незбіг шаблону не може повертати структурне () або Number: {source}"
        );
    }

    let allowed = "(x86-admission-pattern-match? (00000001 (ret)) (00000001 (ret)))";
    let result = eval_program(allowed, &mut session)
        .unwrap_or_else(|error| panic!("{allowed}: {error}"));
    assert_eq!(
        result.value.as_predicate_bit(),
        Some(true),
        "точний збіг має повертати D1:1, а не історичне t"
    );
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
            // #176 generalized mov-r64-imm64 admission to all 16 GPRs
            // (previously rax/rcx only), so a made-up register name is now
            // the register slot's negative witness instead of a real GPR.
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 notareg 1))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-imm64 notareg 1))",
        ),
        (
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-imm64 rax))",
        ),
        (
            // `register` is an operand-slot wildcard admitting only the 16
            // real GPR names; a made-up symbol must still fail closed, not
            // be silently accepted because *some* atom sits in that slot.
            "(x86-call-admitted-u64 (quote ((add-r64-r64 rax notareg))) 0)",
            "(rejected unadmitted-machine-form (add-r64-r64 rax notareg))",
        ),
        (
            // #176's generalized mov-mem-disp8 admission: 128 is one past
            // the signed disp8 maximum (127) and must fail closed, not be
            // silently truncated or wrapped into something encodable.
            "(x86-call-admitted-u64 (quote ((mov-r64-mem-disp8 rax rdi 128))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-mem-disp8 rax rdi 128))",
        ),
        (
            // -129 is one past the signed disp8 minimum (-128).
            "(x86-call-admitted-u64 (quote ((mov-mem-disp8-r64 rdi -129 rax))) 0)",
            "(rejected unadmitted-machine-form (mov-mem-disp8-r64 rdi -129 rax))",
        ),
        (
            // The `disp8` wildcard must fail closed on a non-numeric atom
            // rather than erroring out of the comparison operators that
            // would otherwise be applied to it.
            "(x86-call-admitted-u64 (quote ((mov-mem-disp8-r64 rdi notanumber rax))) 0)",
            "(rejected unadmitted-machine-form (mov-mem-disp8-r64 rdi notanumber rax))",
        ),
        (
            // A made-up base register in the mem-disp8 form must fail
            // closed the same way an invalid register does elsewhere.
            "(x86-call-admitted-u64 (quote ((mov-r64-mem-disp8 rax notareg 0))) 0)",
            "(rejected unadmitted-machine-form (mov-r64-mem-disp8 rax notareg 0))",
        ),
        (
            // Jcc rel8's disp8 slot fails closed the same way MOV's does:
            // one past the signed max.
            "(x86-call-admitted-u64 (quote ((jz-rel8 128))) 0)",
            "(rejected unadmitted-machine-form (jz-rel8 128))",
        ),
        (
            // A made-up condition mnemonic must fail closed, not be
            // silently confused with a real one.
            "(x86-call-admitted-u64 (quote ((jzzz-rel8 0))) 0)",
            "(rejected unadmitted-machine-form (jzzz-rel8 0))",
        ),
        (
            // JMP rel8's disp8 slot fails closed the same way Jcc's does:
            // one past the signed min.
            "(x86-call-admitted-u64 (quote ((jmp-rel8 -129))) 0)",
            "(rejected unadmitted-machine-form (jmp-rel8 -129))",
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
