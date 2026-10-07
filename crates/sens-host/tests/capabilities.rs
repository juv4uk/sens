//! Capability-surface tests for sens-host. Moved verbatim from
//! crates/sens/tests/mccarthy.rs during the core/host split (2026-08-22):
//! host forms are installed by this crate and verified against an installed
//! registry. Public `process-run` is now a Lisp wrapper over `process-run-raw`.

use sens::{
    eval_program, load_core_library, load_fs_library, load_process_library, Environment,
    ErrorKind, Exactness, Session, Value,
};
use sens_host::install;

fn capability_session() -> Session {
    install();
    let mut session = Session::default();
    // `read-file`/`write-file` are language-owned (lib/fs.lisp) over the
    // host's `read-file-bytes`/`write-file-bytes`; load core (for the
    // macro substrate lib/fs.lisp's `let`/`cond` need) and fs.lisp so the two
    // public names resolve instead of raising UnknownSymbol.
    load_core_library(&mut session).unwrap();
    load_fs_library(&mut session).unwrap();
    session
}

fn process_session(environment: Environment) -> Session {
    install();
    let mut session = Session { environment };
    load_core_library(&mut session).unwrap();
    load_process_library(&mut session).unwrap();
    session
}

fn eval_cap_error(source: &str) -> sens::LanguageError {
    let mut session = capability_session();
    eval_program(source, &mut session).unwrap_err()
}

/// The conformance fixture's tcp-connect type-check entry, verified on the
/// installed side: with the host layer active it must fail Type (arity/
/// argument check), matching tests/fixtures/conformance.lisp's expectation.
#[test]
fn conformance_tcp_connect_type_error_holds_with_host_installed() {
    let error = eval_cap_error("(tcp-connect 42 8099)");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_then_read_file_round_trips_the_same_content() {
    let path = std::env::temp_dir().join("sens-write-file-round-trip.txt");
    // Forward slashes only: sens's string reader treats an unrecognized
    // backslash escape as "drop the backslash, keep the character" (only
    // \n/\t/\"/\\ are special — see parser.rs's `string` method), so a raw
    // Windows path like `C:\Users\...` embedded in a double-quoted literal
    // would silently lose every backslash instead of erroring.
    let path_str = path
        .to_str()
        .expect("temp path should be valid UTF-8")
        .replace('\\', "/");
    let source = format!(r#"(write-file "{path_str}" "hello from sens")"#);
    let mut session = capability_session();
    let result = eval_program(&source, &mut session).expect("write-file should succeed");
    assert_eq!(result.value, Value::String("hello from sens".into()));

    let read_back = eval_program(&format!(r#"(read-file "{path_str}")"#), &mut session)
        .expect("read-file should read back what write-file wrote");
    assert_eq!(read_back.value, Value::String("hello from sens".into()));

    std::fs::remove_file(&path).ok();
}

#[test]
fn write_file_overwrites_rather_than_appends() {
    let path = std::env::temp_dir().join("sens-write-file-overwrite.txt");
    let path_str = path
        .to_str()
        .expect("temp path should be valid UTF-8")
        .replace('\\', "/");
    let mut session = capability_session();
    eval_program(
        &format!(r#"(write-file "{path_str}" "first")"#),
        &mut session,
    )
    .expect("first write-file should succeed");
    eval_program(
        &format!(r#"(write-file "{path_str}" "second")"#),
        &mut session,
    )
    .expect("second write-file should succeed");
    let read_back = eval_program(&format!(r#"(read-file "{path_str}")"#), &mut session)
        .expect("read-file should see only the second write");
    assert_eq!(read_back.value, Value::String("second".into()));

    std::fs::remove_file(&path).ok();
}

#[test]
fn write_file_rejects_a_non_string_path() {
    let error = eval_program(r#"(write-file 42 "x")"#, &mut capability_session())
        .expect_err("a non-string path must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_rejects_a_non_string_content_argument() {
    let error = eval_program(
        r#"(write-file "path-does-not-matter-here.txt" 42)"#,
        &mut capability_session(),
    )
    .expect_err("a non-string content argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_wrong_arity_is_an_arity_error() {
    let error = eval_program(r#"(write-file "only-a-path.txt")"#, &mut capability_session())
        .expect_err("write-file with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn read_dir_lists_the_files_it_wrote() {
    let dir = std::env::temp_dir().join("sens-read-dir-test");
    std::fs::create_dir_all(&dir).expect("temp dir should be creatable");
    let a = dir.join("alpha.yaml");
    let b = dir.join("beta.yaml");
    std::fs::write(&a, "canonical: alpha\n").ok();
    std::fs::write(&b, "canonical: beta\n").ok();

    let dir_str = dir
        .to_str()
        .expect("temp path should be valid UTF-8")
        .replace('\\', "/");
    let mut session = capability_session();
    let result = eval_program(&format!(r#"(read-dir "{dir_str}")"#), &mut session)
        .expect("read-dir should list the directory");
    let names = result.value.to_string().replace(['(', ')'], "");
    assert!(
        names.contains("alpha.yaml"),
        "alpha.yaml should be listed, got {names}"
    );
    assert!(
        names.contains("beta.yaml"),
        "beta.yaml should be listed, got {names}"
    );

    std::fs::remove_dir_all(&dir).ok();
}

#[test]
fn read_dir_rejects_a_missing_directory() {
    let error = eval_program(
        r#"(read-dir "/definitely/not/a/real/sens-dir")"#,
        &mut Session::default(),
    )
    .expect_err("read-dir on a missing directory must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn read_dir_rejects_a_non_string_path() {
    let error = eval_program(r#"(read-dir 42)"#, &mut Session::default())
        .expect_err("read-dir with a non-string path must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_bytes_then_read_file_bytes_round_trips_non_utf8_bytes() {
    let path = std::env::temp_dir().join("sens-write-file-bytes-round-trip.bin");
    let path_str = path
        .to_str()
        .expect("temp path should be valid UTF-8")
        .replace('\\', "/");
    let source = format!(r#"(write-file-bytes "{path_str}" (quote (0 1 2 255 65 254)))"#);
    let mut session = capability_session();
    let result = eval_program(&source, &mut session).expect("write-file-bytes should succeed");
    assert_eq!(
        result.value,
        Value::list([0, 1, 2, 255, 65, 254].map(|n| Value::Number(n as f64, Exactness::Exact)))
    );

    let raw = std::fs::read(&path).expect("the file should exist with raw bytes");
    assert_eq!(raw, vec![0u8, 1, 2, 255, 65, 254]);

    let read_back = eval_program(&format!(r#"(read-file-bytes "{path_str}")"#), &mut session)
        .expect("read-file-bytes should read back what write-file-bytes wrote");
    assert_eq!(
        read_back.value,
        Value::list([0, 1, 2, 255, 65, 254].map(|n| Value::Number(n as f64, Exactness::Exact)))
    );

    std::fs::remove_file(&path).ok();
}

#[test]
fn write_file_bytes_rejects_a_non_string_path() {
    let error = eval_program(
        r#"(write-file-bytes 42 (quote (1 2 3)))"#,
        &mut Session::default(),
    )
    .expect_err("a non-string path must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_bytes_rejects_a_non_list_second_argument() {
    let error = eval_program(
        r#"(write-file-bytes "path-does-not-matter.bin" 42)"#,
        &mut Session::default(),
    )
    .expect_err("a non-list second argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_bytes_rejects_an_out_of_range_element() {
    let error = eval_program(
        r#"(write-file-bytes "path-does-not-matter.bin" (quote (1 256 3)))"#,
        &mut Session::default(),
    )
    .expect_err("an element above 255 must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_bytes_rejects_a_negative_element() {
    let error = eval_program(
        r#"(write-file-bytes "path-does-not-matter.bin" (quote (1 -1 3)))"#,
        &mut Session::default(),
    )
    .expect_err("a negative element must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn read_file_bytes_rejects_a_non_string_path() {
    let error = eval_program(r#"(read-file-bytes 42)"#, &mut Session::default())
        .expect_err("a non-string path must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn write_file_bytes_wrong_arity_is_an_arity_error() {
    let error = eval_program(
        r#"(write-file-bytes "only-a-path.bin")"#,
        &mut Session::default(),
    )
    .expect_err("write-file-bytes with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn read_file_bytes_wrong_arity_is_an_arity_error() {
    let error = eval_program(r#"(read-file-bytes)"#, &mut Session::default())
        .expect_err("read-file-bytes with no arguments must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn process_run_is_unrestricted_in_a_native_root_session() {
    let mut session = process_session(Environment::root());
    let result = eval_program(
        r#"(process-run "git" (quote ("--version")))"#,
        &mut session,
    )
    .expect("the trusted native root session should run a named program");
    let Value::Pair(ref exit_code, ref rest) = result.value else {
        panic!("process-run should return a 3-element list");
    };
    assert_eq!(**exit_code, Value::Number(0.0, Exactness::Exact));
    let Value::Pair(ref stdout, _) = **rest else {
        panic!("process-run should return a 3-element list");
    };
    let Value::String(ref stdout) = **stdout else {
        panic!("stdout should be a string");
    };
    assert!(stdout.contains("git version"));
}

#[test]
fn process_run_succeeds_for_an_explicitly_allowed_program() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let source = r#"(process-run "git" (quote ("--version")))"#;
    let result =
        eval_program(source, &mut session).expect("an explicitly allowed program should run");
    let Value::Pair(ref exit_code, ref rest) = result.value else {
        panic!("process-run should return a 3-element list");
    };
    assert_eq!(**exit_code, Value::Number(0.0, Exactness::Exact));
    let Value::Pair(ref stdout, _) = **rest else {
        panic!("process-run should return a 3-element list");
    };
    let Value::String(ref stdout) = **stdout else {
        panic!("stdout should be a string");
    };
    assert!(stdout.contains("git version"));
}

#[test]
fn process_run_is_deny_all_for_an_explicit_empty_allowlist() {
    let mut session = process_session(Environment::root().with_process_allowlist(Vec::new()));
    let error = eval_program(r#"(process-run "git" (quote ("--version")))"#, &mut session)
        .expect_err("an explicit empty embedding allowlist must remain deny-all");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn process_run_rejects_a_program_not_on_the_allowlist() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let error = eval_program(
        r#"(process-run "cmd" (quote ("/C" "echo" "hi")))"#,
        &mut session,
    )
    .expect_err("a program not on the allowlist must fail named, not run");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn process_run_rejects_a_non_string_program() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let error = eval_program("(process-run 42 (list \"x\"))", &mut session)
        .expect_err("a non-string program name must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn process_run_rejects_a_non_list_args_argument() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let error = eval_program(r#"(process-run "git" "not-a-list")"#, &mut session)
        .expect_err("a non-list args argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn process_run_rejects_a_non_string_element_in_args() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let error = eval_program("(process-run \"git\" (quote (42)))", &mut session)
        .expect_err("a non-string element in args must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn process_run_wrong_arity_is_an_arity_error() {
    let mut session = process_session(
        Environment::root().with_process_allowlist(vec!["git".to_string()]),
    );
    let error = eval_program(r#"(process-run "git")"#, &mut session)
        .expect_err("process-run with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn load_evaluates_every_form_in_a_file_and_returns_the_last_value() {
    let path = std::env::temp_dir().join("sens-load-round-trip.lisp");
    let path_str = path.to_str().unwrap().replace('\\', "/");
    std::fs::write(&path, "(def x 1) (def y 2) (+ x y)").unwrap();

    let result = eval_program(&format!(r#"(load "{path_str}")"#), &mut Session::default())
        .expect("load should evaluate the file and return the last form's value");
    assert_eq!(result.value, Value::Number(3.0, Exactness::Exact));

    std::fs::remove_file(&path).ok();
}

#[test]
fn load_uses_the_same_surface_lowering_as_eval_program() {
    let path = std::env::temp_dir().join("sens-load-lowering-parity.lisp");
    let path_str = path.to_str().unwrap().replace('\\', "/");
    std::fs::write(&path, "(додати 20 22)").unwrap();

    let direct = eval_program("(додати 20 22)", &mut capability_session())
        .expect("direct program should lower the human function surface");
    let loaded = eval_program(
        &format!(r#"(load "{path_str}")"#),
        &mut capability_session(),
    )
    .expect("load should use the same lowering path as eval_program");

    assert_eq!(loaded.value, direct.value);
    assert_eq!(loaded.value, Value::Number(42.0, Exactness::Exact));

    std::fs::remove_file(&path).ok();
}

#[test]
fn load_definitions_are_visible_in_the_calling_environment() {
    let path = std::env::temp_dir().join("sens-load-definitions.lisp");
    let path_str = path.to_str().unwrap().replace('\\', "/");
    std::fs::write(&path, "(def loaded-value 99)").unwrap();

    let mut session = capability_session();
    eval_program(&format!(r#"(load "{path_str}")"#), &mut session).expect("load should succeed");
    let result = eval_program("loaded-value", &mut session)
        .expect("a definition made by load should be visible afterward");
    assert_eq!(result.value, Value::Number(99.0, Exactness::Exact));

    std::fs::remove_file(&path).ok();
}

#[test]
fn load_rejects_a_non_string_path() {
    let error = eval_program("(load 42)", &mut Session::default())
        .expect_err("a non-string path must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn load_wrong_arity_is_an_arity_error() {
    let error = eval_program("(load)", &mut Session::default())
        .expect_err("load with no arguments must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn load_a_missing_file_fails_named_not_panics() {
    let error = eval_program(
        r#"(load "sens-load-does-not-exist-anywhere.lisp")"#,
        &mut capability_session(),
    )
    .expect_err("loading a nonexistent file must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn car_on_a_non_pair_fails_named_not_panics() {
    let error = eval_program("(car 42)", &mut Session::default())
        .expect_err("car on a non-pair must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn car_on_the_empty_list_fails_named_not_panics() {
    let error = eval_program("(car (quote ()))", &mut Session::default())
        .expect_err("car on the empty list must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn cdr_on_a_non_pair_fails_named_not_panics() {
    let error = eval_program("(cdr 42)", &mut Session::default())
        .expect_err("cdr on a non-pair must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn car_wrong_arity_is_an_arity_error() {
    let error = eval_program("(car 1 2)", &mut Session::default())
        .expect_err("car with two arguments must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn cons_wrong_arity_is_an_arity_error() {
    let error = eval_program("(cons 1)", &mut Session::default())
        .expect_err("cons with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

#[test]
fn eq_rejects_non_atom_arguments() {
    let error = eval_program("(eq? (quote (1 2)) (quote (1 2)))", &mut Session::default())
        .expect_err("eq on two non-atom lists must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn cond_rejects_a_clause_that_is_not_a_list() {
    let error = eval_program("(cond 42)", &mut Session::default())
        .expect_err("a non-list cond clause must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn cond_rejects_a_clause_with_the_wrong_number_of_parts() {
    // Since #1495 a clause is canonical `(query expected-result expression)`
    // or migration-only `(test expression)`; one part or four are malformed.
    for source in ["(00000111 (t))", "(00000111 (t t 1 2))"] {
        let error = eval_program(source, &mut Session::default())
            .expect_err("a malformed cond clause must fail named, not panic");
        assert_eq!(error.kind, ErrorKind::InvalidForm, "{source}");
    }
}

#[test]
fn def_rejects_a_non_symbol_name() {
    let error = eval_program("(def 42 1)", &mut Session::default())
        .expect_err("def with a non-symbol name must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn defmacro_wrong_arity_is_an_arity_error() {
    let error = eval_program("(defmacro only-a-name)", &mut Session::default())
        .expect_err("defmacro with only a name must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}