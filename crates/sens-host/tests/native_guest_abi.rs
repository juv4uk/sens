#![cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]

use sens::{eval_program, load_core_library, Session};
use sens_host::install;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

const CHILD_REGISTER_ENV: &str = "MY_LISP_HOST_ABI_CHILD_REGISTER";
const CHILD_ARENA_REGISTER_ENV: &str = "MY_LISP_HOST_ABI_CHILD_ARENA_REGISTER";
const TEST_NAME: &str = "guest_clobber_of_sysv64_callee_saved_gpr_does_not_corrupt_host";
const ARENA_TEST_NAME: &str = "arena_rdi_survives_sysv64_callee_saved_guest_clobber";

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
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before host ABI witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    session
}

fn execute_clobbering_guest(register: &str) {
    let mut session = machine_session();

    let source = format!(
        "(x86-call-admitted-u64 (quote ((mov-r64-imm64 {register} 42) (mov-r64-imm64 rax 7) (ret))) 0)"
    );
    let result = eval_program(&source, &mut session)
        .unwrap_or_else(|error| panic!("admitted guest clobbering {register} must return safely: {error}"));

    assert_eq!(
        result.value.to_string(),
        "7",
        "guest result in RAX must survive host ABI isolation when {register} is clobbered"
    );
}

fn execute_arena_guest_clobbering(register: &str) {
    let mut session = machine_session();

    // Prove both parts of the arena entry contract in the same guest:
    // RDI must still point at the host-provided arena, while a write to a
    // SysV64 nonvolatile register must not corrupt the host caller. Store 11
    // through RDI, clobber the selected register, load the stored value back
    // through RDI into RAX, then return it.
    let source = format!(
        "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 11) (mov-mem-disp8-r64 rdi 0 rax) (mov-r64-imm64 {register} 42) (mov-r64-mem-disp8 rax rdi 0) (ret))) 16)"
    );
    let result = eval_program(&source, &mut session).unwrap_or_else(|error| {
        panic!("arena guest clobbering {register} must preserve RDI arena entry: {error}")
    });

    assert_eq!(
        result.value.to_string(),
        "11",
        "arena pointer in RDI and guest result in RAX must survive host ABI isolation when {register} is clobbered"
    );
}

#[test]
fn raw_executor_has_explicit_sysv64_nonvolatile_isolation_boundary() {
    let path = repo_root().join("crates/sens-host/src/native_exec.rs");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must be readable: {error}", path.display()));

    assert!(
        source.contains("naked_asm!"),
        "raw guest execution needs an explicit ABI-isolation trampoline; a direct extern sysv64 function-pointer call silently assumes the guest preserves host nonvolatile registers"
    );
    for register in ["rbx", "rbp", "r12", "r13", "r14", "r15"] {
        assert!(
            source.contains(&format!("push {register}"))
                && source.contains(&format!("pop {register}")),
            "host ABI-isolation trampoline must save and restore SysV64 callee-saved {register}"
        );
    }
    assert!(
        !source.contains("let function: GuestNoArena")
            && !source.contains("let function: GuestWithArena"),
        "raw executor must not call arbitrary guest bytes directly through an extern sysv64 function pointer"
    );
}

#[test]
fn guest_clobber_of_sysv64_callee_saved_gpr_does_not_corrupt_host() {
    if let Ok(register) = std::env::var(CHILD_REGISTER_ENV) {
        execute_clobbering_guest(&register);
        return;
    }

    let current_exe = std::env::current_exe().expect("test executable path must be available");
    for register in ["rbx", "rbp", "r12", "r13", "r14", "r15"] {
        let status = Command::new(&current_exe)
            .args(["--exact", TEST_NAME, "--nocapture"])
            .env(CHILD_REGISTER_ENV, register)
            .status()
            .unwrap_or_else(|error| panic!("must spawn isolated {register} ABI witness: {error}"));

        assert!(
            status.success(),
            "guest clobbering SysV64 callee-saved {register} corrupted/crashed the host; child status: {status}"
        );
    }
}

#[test]
fn arena_rdi_survives_sysv64_callee_saved_guest_clobber() {
    if let Ok(register) = std::env::var(CHILD_ARENA_REGISTER_ENV) {
        execute_arena_guest_clobbering(&register);
        return;
    }

    let current_exe = std::env::current_exe().expect("test executable path must be available");
    for register in ["rbx", "rbp", "r12", "r13", "r14", "r15"] {
        let status = Command::new(&current_exe)
            .args(["--exact", ARENA_TEST_NAME, "--nocapture"])
            .env(CHILD_ARENA_REGISTER_ENV, register)
            .status()
            .unwrap_or_else(|error| panic!("must spawn isolated arena/{register} ABI witness: {error}"));

        assert!(
            status.success(),
            "arena guest clobbering SysV64 callee-saved {register} corrupted/crashed the host or lost RDI; child status: {status}"
        );
    }
}
