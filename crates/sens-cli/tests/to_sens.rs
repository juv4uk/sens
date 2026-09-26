use sens::{eval_program, load_core_library, load_macro_library, Session, CORE_LIBRARY_SOURCE};
use std::process::Command;

fn tool() -> Command {
    Command::new(env!("CARGO_BIN_EXE_sens-to-sens"))
}

fn temp_file(name: &str, source: &str) -> std::path::PathBuf {
    let path = std::env::temp_dir().join(format!(
        "sens-to-sens-{}-{}-{name}.lisp",
        std::process::id(),
        std::thread::current().name().unwrap_or("test")
    ));
    std::fs::write(&path, source).expect("write temp source");
    path
}

fn eval_core(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn check_reports_without_writing_then_apply_preserves_formatting() {
    let source =
        "; comment keeps (+ 9 9)\n(define f\n  (lambda (x)\n    (+ x 2)))\n(quote (+ 3 4))\n";
    let path = temp_file("format", source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    assert_eq!(check.status.code(), Some(1));
    assert_eq!(std::fs::read_to_string(&path).expect("read unchanged"), source);
    let check_out = String::from_utf8_lossy(&check.stdout);
    assert!(check_out.contains("convertible=4"), "{check_out}");

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );

    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);
    assert_eq!(
        rewritten,
        "; comment keeps (+ 9 9)\n(00001001 f\n  (00001000 (x)\n    (00001100 x 2)))\n(00000001 (+ 3 4))\n"
    );
}

#[test]
fn derived_functions_and_macros_keep_runtime_result_after_rewrite() {
    let source =
        "(let* ((xs (list 1 2 3)) (n (length xs))) (and (member? 2 xs) (or () (+ n 39))))";
    let path = temp_file("derived-parity", source);

    let original = eval_core(source);
    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );

    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);

    assert!(rewritten.contains("(10011101 "));
    assert!(rewritten.contains("(00100111 1 2 3)"));
    assert!(rewritten.contains("(00101000 xs)"));
    assert!(rewritten.contains("(00101100 2 xs)"));
    assert!(rewritten.contains("(10011010 "));
    assert!(rewritten.contains("(10011011 "));
    assert_eq!(eval_core(&rewritten), original);
}

#[test]
fn defmacro_rewrites_to_exact_00001010_and_preserves_raw_syntax() {
    let source =
        "(defmacro twice (x) (list (quote list) x x))\n(twice 7)\n";
    let path = temp_file("defmacro-exact", source);
    let expected = eval_core(source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    assert_eq!(check.status.code(), Some(1));
    let stdout = String::from_utf8_lossy(&check.stdout);
    assert!(stdout.contains("convertible=2"), "{stdout}");
    assert!(!stdout.contains("blocked-defmacro"), "{stdout}");

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );
    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);

    assert!(rewritten.starts_with("(00001010 twice "));
    assert!(rewritten.contains("(00100111 (00000001 list) x x)"));
    assert_eq!(eval_core(&rewritten), expected);
}

#[test]
fn defmacro_target_shadowing_is_preserved_after_migration() {
    let source =
        "(defmacro list args (car args))\n(list (quote shadowed))\n";
    let path = temp_file("defmacro-shadow", source);
    let expected = eval_core(source);
    assert_eq!(expected, "shadowed");

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );
    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);

    assert_eq!(
        rewritten,
        "(00001010 list args (00000101 args))\n(list (00000001 shadowed))\n"
    );
    assert_eq!(eval_core(&rewritten), expected);
}

#[test]
fn check_is_clean_after_all_currently_convertible_heads_are_migrated() {
    let source = "(00001001 f (00001000 (x) (00100111 x)))\n";
    let path = temp_file("clean", source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    let _ = std::fs::remove_file(&path);

    assert!(check.status.success());
    let stdout = String::from_utf8_lossy(&check.stdout);
    assert!(stdout.contains("convertible=0"), "{stdout}");
}


#[test]
fn rewritten_current_core_library_preserves_representative_behavior() {
    let path = temp_file("core-library", CORE_LIBRARY_SOURCE);

    let apply = tool().arg(&path).output().expect("run core migration");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );
    let rewritten = std::fs::read_to_string(&path).expect("read rewritten core");
    let _ = std::fs::remove_file(&path);

    assert_ne!(rewritten, CORE_LIBRARY_SOURCE, "M0 must actually migrate current core call heads");
    assert!(
        rewritten.contains("(00100111 "),
        "current core rewrite should contain exact SENS list calls"
    );
    assert!(
        rewritten.contains("(10011100 "),
        "current core rewrite should contain exact SENS let calls"
    );

    let mut baseline = Session::default();
    load_core_library(&mut baseline).expect("baseline core loads");

    let mut migrated = Session::default();
    load_macro_library(&mut migrated).expect("macro bootstrap loads");
    eval_program(&rewritten, &mut migrated).expect("rewritten core loads");

    for source in [
        "(list 1 2 3)",
        "(member? 2 (quote (1 2 3)))",
        "(append (quote (1 2)) (quote (3 4)))",
        "(quotient 17 5)",
        "(let* ((x 3) (y (+ x 4))) y)",
        "(and (member? 2 (quote (1 2 3))) (or () 9))",
    ] {
        let expected = eval_program(source, &mut baseline)
            .unwrap_or_else(|error| panic!("baseline {source}: {error:?}"))
            .value
            .to_string();
        let actual = eval_program(source, &mut migrated)
            .unwrap_or_else(|error| panic!("migrated {source}: {error:?}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "{source}");
    }
}


#[test]
fn top_level_surface_redefinition_has_identical_result_after_migration() {
    let source =
        "(define list (lambda args (quote shadowed)))\n(list 1 2)\n";
    let path = temp_file("top-level-shadow", source);

    let mut baseline = Session::default();
    load_core_library(&mut baseline).expect("baseline core loads");
    let expected = eval_program(source, &mut baseline)
        .expect("baseline surface shadow program")
        .value
        .to_string();
    assert_eq!(expected, "shadowed");

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );
    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);

    assert_eq!(
        rewritten,
        "(00001001 list (00001000 args (00000001 shadowed)))\n(list 1 2)\n"
    );

    let mut migrated = Session::default();
    load_core_library(&mut migrated).expect("migrated baseline core loads");
    let actual = eval_program(&rewritten, &mut migrated)
        .expect("migrated surface shadow program")
        .value
        .to_string();
    assert_eq!(actual, expected);
}
