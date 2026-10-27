//! Integration tests for the `sens` CLI binary.
//! Intehratsiini testy dlia CLI-binarnyka `sens`.
//! Integrationstests für die `sens`-CLI-Binärdatei.
//!
//! These exercise the compiled binary as a black box (argv in, stdout/stderr/exit
//! code out) instead of calling internal functions directly, since main.rs itself
//! has no unit-testable functions — the behavior lives in argument handling and I/O.
//! Vony pereviriaiut skompilovanyi binarnyk yak chornu skrynku (argv na vkhodi,
//! stdout/stderr/kod vykhodu na vykhodi), a ne vyklykaiut vnutrishni funktsii napriamu,
//! bo main.rs ne maie vlasnykh funktsii dlia unit-testiv — povedinka zhyve v obrobtsi
//! arhumentiv ta I/O.
//! Sie prüfen die kompilierte Binärdatei als Black Box (argv als Eingabe,
//! stdout/stderr/Exit-Code als Ausgabe) statt interne Funktionen direkt aufzurufen,
//! da main.rs selbst keine unit-testbaren Funktionen besitzt — das Verhalten steckt
//! in der Argumentverarbeitung und E/A.

use std::process::Command;

/// Every test here spawns the compiled binary with the sens repo root as
/// its working directory, matching how the `sens` binary is invoked in
/// practice (and specifically required by `--oracle-help`, which reads
/// `knowledge/guard-reference.lisp` relative to the caller's cwd so new
/// reference entries take effect without a rebuild).
fn sens() -> Command {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    command.current_dir(repo_root);
    command
}

#[test]
fn version_flag_prints_the_crate_version() {
    let output = sens().arg("--version").output().expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), format!("sens {}", env!("CARGO_PKG_VERSION")));
}

#[test]
fn short_version_flags_match_the_long_form() {
    for flag in ["-V", "-v"] {
        let output = sens().arg(flag).output().expect("binary should run");
        assert!(output.status.success());
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert_eq!(stdout.trim(), format!("sens {}", env!("CARGO_PKG_VERSION")));
    }
}

#[test]
fn help_flag_prints_usage() {
    let output = sens().arg("--help").output().expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Usage: sens [file]"));
    assert!(stdout.contains(".lisp"));
    assert!(stdout.contains(".sens"));
    assert!(stdout.contains("physical .sens is packed T5M"));
    assert!(stdout.contains("--t5m-file"));
    assert!(stdout.contains("--oracle-check <file|->"));
    assert!(stdout.contains("--core=3|4"));
}

#[test]
fn oracle_check_file_is_agent_friendly_and_side_effect_free() {
    let path = std::env::temp_dir().join("sens-oracle-check-unclosed.lisp");
    std::fs::write(&path, "(def answer (+ 40 2)").expect("should write fixture");

    let output = sens()
        .args(["--oracle-check", path.to_str().expect("UTF-8 temp path")])
        .output()
        .expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert_eq!(output.status.code(), Some(2));
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("(code unclosed-list)"), "{stdout}");
    assert!(stdout.contains("(action insert)"), "{stdout}");
    assert!(stdout.contains("(text \")\")"), "{stdout}");
}

#[test]
fn oracle_check_valid_file_returns_zero_without_evaluating_it() {
    // Agent syntax preflight is a textual-compatibility tool, not a .sens/T5 reader.
    let path = std::env::temp_dir().join("sens-oracle-check-valid.lisp");
    // Unknown symbol would fail evaluation, but syntax-only preflight must
    // accept it. This proves the command does not silently become eval.
    std::fs::write(&path, "(not-defined-here 1)").expect("should write fixture");

    let output = sens()
        .args(["--oracle-check", path.to_str().expect("UTF-8 temp path")])
        .output()
        .expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("(outcome valid)"), "{stdout}");
    assert!(stdout.contains("(forms 1)"), "{stdout}");
}

#[test]
fn oracle_help_lists_curated_agent_tools_from_wsm() {
    let output = sens()
        .arg("--oracle-help")
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("oracle-check"), "{stdout}");
    assert!(stdout.contains("agent-send"), "{stdout}");
    assert!(stdout.contains("bilingual-docs-check"), "{stdout}");
}

#[test]
fn oracle_help_explains_one_tool_with_invocation_and_verification() {
    let output = sens()
        .args(["--oracle-help", "agent-send"])
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("../ecosystem/scripts/agent-send"),
        "{stdout}"
    );
    assert!(
        stdout.contains("/home/agents/ecosystem/scripts/agent-send send"),
        "{stdout}"
    );
    assert!(
        stdout.contains("(risk writes-coordination-log)"),
        "{stdout}"
    );
    assert!(
        stdout.contains("(verify (admitted inbox-id wakeup-result))"),
        "{stdout}"
    );
    assert!(stdout.contains("(type tool)"), "{stdout}");
}

#[test]
fn oracle_help_explains_a_reference_topic_that_is_not_a_tool() {
    let output = sens()
        .args(["--oracle-help", "lsp-server"])
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("(type reference-topic)"), "{stdout}");
    assert!(
        stdout.contains("(source knowledge/guard-reference.lisp)"),
        "{stdout}"
    );
    assert!(stdout.contains("docs/lsp-m0.md"), "{stdout}");
}

#[test]
fn oracle_help_flags_a_name_present_in_both_directories_as_ambiguous() {
    // resource-preflight is a real, currently-existing name collision: both
    // a curated tool (guard-script-directory) and a reference topic
    // (guard-reference-directory) use it. This proves guard-ask never
    // silently prefers one -- the caller decides.
    let output = sens()
        .args(["--oracle-help", "resource-preflight"])
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.starts_with("(ambiguous"), "{stdout}");
    assert!(
        stdout.contains("(tool (tool (name resource-preflight)"),
        "{stdout}"
    );
    assert!(
        stdout.contains("(reference-topic (reference (topic resource-preflight)"),
        "{stdout}"
    );
}

#[test]
fn oracle_help_reports_not_found_when_absent_from_both_directories() {
    let output = sens()
        .args(["--oracle-help", "definitely-not-a-real-guard-name"])
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.starts_with("(not-found"), "{stdout}");
    assert!(stdout.contains("(decision unknown)"), "{stdout}");
    assert!(stdout.contains("unknown-routes"), "{stdout}");
}

#[test]
fn textual_compatibility_extensions_do_not_claim_sens_binary_identity() {
    let dir = std::env::temp_dir();
    let code = "(як-є сенс)";

    for ext in [".wsm", ".my", ".lisp", ".сенс"] {
        let path = dir.join(format!("sens-cli-test-ext{ext}"));
        std::fs::write(&path, code).expect("should write compatibility source");

        let output = sens().arg(&path).output().expect("binary should run");
        let _ = std::fs::remove_file(&path);

        assert!(
            output.status.success(),
            "{ext}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert_eq!(
            String::from_utf8_lossy(&output.stdout).trim(),
            "сенс",
            "{ext}"
        );
    }
}

/// The active CLI consumes real physical T5 bytes, not a Lisp UTF-8 file
/// renamed to .sens. Both routes are checked through the compiled CLI.
#[test]
fn sens_binary_executes_physical_t5_without_a_human_name_parser() {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
    );
    let bytes = std::fs::read(path).expect("committed physical T5 fixture");
    assert!(!bytes.is_empty());
    // The physical carrier is a sequence of packed bytes, never the
    // displayed zero/one source with spaces.
    assert_ne!(bytes.as_slice(), &b"10 001 00 10 01 01"[..]);

    let output = sens().arg(path).output().expect("canonical SENS CLI");
    assert!(
        output.status.success(),
        "physical T5 rejected: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        !String::from_utf8_lossy(&output.stdout).trim().is_empty(),
        "physical T5 produced no CLI result"
    );

    // No hidden Core4/human-compatibility interpretation is allowed for T5.
    let flagged = sens()
        .arg("--core=4")
        .arg(path)
        .output()
        .expect("physical T5 request with a flag");
    assert!(!flagged.status.success());
}

#[test]
fn sens_binary_rejects_text_disguised_as_physical_t5() {
    let path = std::env::temp_dir().join("sens-cli-physical-no-text-alias.sens");
    std::fs::write(&path, b"(quote ())").expect("write deliberate textual counterfeit");
    let output = sens().arg(&path).output().expect("canonical SENS CLI");
    let _ = std::fs::remove_file(&path);
    assert!(
        !output.status.success(),
        "textual .sens was executed as Lisp"
    );
    let diagnostic = String::from_utf8_lossy(&output.stderr);
    assert!(
        diagnostic.contains("physical T5")
            || diagnostic.contains("exact binary reader")
            || diagnostic.contains("current SENS execution"),
        "missing physical-binary rejection diagnostic: {diagnostic}"
    );
}

#[test]
fn t5m_file_mode_does_not_reinterpret_physical_sens_as_textual_lisp() {
    // Якщо фізичний .sens містить випадково читабельний текст, він все одно
    // мусить пройти лише двійковий reader, а не --t5m-file.
    let path = std::env::temp_dir().join(format!(
        "sens-cli-t5m-no-text-fallback-{}.sens",
        std::process::id()
    ));
    std::fs::write(&path, "(додати 20 22)\n").expect("write disguised physical fixture");
    let output = sens()
        .args(["--t5m-file", path.to_str().expect("UTF-8 temp path")])
        .output()
        .expect("T5M CLI must reject disguised physical source");
    let _ = std::fs::remove_file(&path);

    assert!(
        !output.status.success(),
        "physical .sens bypassed its binary reader"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("--t5m-file accepts only .lisp sources"),
        "{stderr}"
    );
    assert!(!String::from_utf8_lossy(&output.stdout).contains("42"));
}

#[test]
fn t5m_file_mode_rejects_malformed_ukrainian_source() {
    let path = std::env::temp_dir().join(format!(
        "sens-cli-t5m-malformed-{}.lisp",
        std::process::id()
    ));
    std::fs::write(&path, "(додати 20 22").expect("write incomplete source");
    let output = sens()
        .args(["--t5m-file", path.to_str().expect("UTF-8 temp path")])
        .output()
        .expect("T5M CLI must report malformed source");
    let _ = std::fs::remove_file(&path);

    assert!(!output.status.success(), "malformed source was admitted");
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("T5M file execution failed"), "{stderr}");
}

#[test]
fn running_a_file_with_a_parse_error_exits_nonzero() {
    let dir = std::env::temp_dir();
    let path = dir.join("sens-cli-test-parse-error.lisp");
    std::fs::write(&path, "(1 2").expect("should write temp file");

    let output = sens().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.starts_with("Parse error:"));
}

#[test]
fn running_a_missing_file_reports_a_read_error() {
    let output = sens()
        .arg("this-file-does-not-exist-sens-cli.lisp")
        .output()
        .expect("binary should run");

    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.starts_with("Error reading file"));
}

#[test]
fn repl_history_persists_across_separate_sessions() {
    // Isolate HOME/USERPROFILE per test run so this doesn't read or write the
    // real user's ~/.sens-history, and so parallel test runs don't collide.
    // Izoliuiemo HOME/USERPROFILE dlia kozhnoho zapusku testu, shchob ne chytaty y ne
    // pysaty v realnyi ~/.sens-history korystuvacha, i shchob paralelni
    // zapusky testiv ne konfliktuvaly.
    // Isoliert HOME/USERPROFILE pro Testlauf, damit weder das echte
    // ~/.sens-history des Nutzers gelesen/geschrieben wird noch parallele
    // Testläufe kollidieren.
    let dir = std::env::temp_dir().join(format!("sens-cli-test-history-{}", std::process::id()));
    std::fs::create_dir_all(&dir).expect("should create temp home dir");

    let run = |input: &str| {
        use std::io::Write;
        use std::process::Stdio;
        let mut child = sens()
            .env("HOME", &dir)
            .env("USERPROFILE", &dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("binary should spawn");
        child
            .stdin
            .take()
            .expect("stdin should be piped")
            .write_all(input.as_bytes())
            .expect("should write to stdin");
        child.wait_with_output().expect("binary should run")
    };

    run("(додати 1 2)\n");
    run("(додати 3 4)\n");

    let history = std::fs::read_to_string(dir.join(".sens-history"))
        .expect("second session should find history left by the first");
    let _ = std::fs::remove_dir_all(&dir);

    assert!(history.contains("(додати 1 2)"));
    assert!(history.contains("(додати 3 4)"));
}

#[test]
fn default_ukrainian_repl_localizes_errors_and_help_prose() {
    use std::io::Write;
    use std::process::Stdio;

    let home =
        std::env::temp_dir().join(format!("sens-cli-repl-ukr-errors-{}", std::process::id()));
    std::fs::create_dir_all(&home).expect("should create isolated REPL home");
    let mut child = sens()
        .env("HOME", &home)
        .env("USERPROFILE", &home)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("REPL should start");
    child
        .stdin
        .take()
        .expect("stdin should be piped")
        .write_all(":допомога\n)\n".as_bytes())
        .expect("should request help and send invalid syntax");
    let output = child.wait_with_output().expect("REPL should finish at EOF");
    let _ = std::fs::remove_dir_all(&home);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stdout.contains("SENS REPL версії"), "{stdout}");
    assert!(!stdout.contains("Rust mechanisms"), "{stdout}");
    assert!(stdout.contains("Додаткова команда:"), "{stdout}");
    assert!(stdout.contains("тотожність"), "{stdout}");
    assert!(stdout.contains("визначення й замикання"), "{stdout}");
    assert!(!stdout.contains("semantic identity"), "{stdout}");
    assert!(!stdout.contains("define/closures"), "{stdout}");
    assert!(stderr.contains("Помилка REPL/T5M:"), "{stderr}");
    assert!(
        stderr.contains("Синтаксична помилка: неочікувана закривна дужка"),
        "{stderr}"
    );
    assert!(stderr.contains("рядок 1, стовпець 1"), "{stderr}");
    assert!(
        !stderr.contains("unexpected closing parenthesis"),
        "{stderr}"
    );
    assert!(!stderr.contains("line/riadok/Zeile"), "{stderr}");
}

/// The banner line proves `bind` succeeded, but the very first connection
/// against a just-spawned dev binary on this machine has been observed to
/// have its handshake accepted by the OS and then reset before a full
/// request/response round-trip completes — a real, reproducible flake
/// here (plausibly local AV/firewall inspecting a newly-listening
/// unsigned binary), not a bug in the request-handling loop itself, which
/// a manual, unhurried connection to the same binary always answers
/// correctly. Retrying the whole round-trip, not just `connect`, is what
/// actually absorbs it — a version that only retried `connect` still saw
/// the reset on the subsequent read.
fn request_with_retry(port: u16, request: &str) -> String {
    use std::io::{BufRead, Write};
    use std::net::TcpStream;
    use std::time::Duration;

    let mut last_err = None;
    for _ in 0..100 {
        let attempt = (|| -> std::io::Result<String> {
            let mut stream = TcpStream::connect(("127.0.0.1", port))?;
            writeln!(stream, "{request}")?;
            let mut response = String::new();
            std::io::BufReader::new(&stream).read_line(&mut response)?;
            Ok(response)
        })();
        match attempt {
            Ok(response) if !response.trim().is_empty() => return response,
            Ok(_) => last_err = None,
            Err(err) => last_err = Some(err),
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    panic!("should get a non-empty response after retrying: {last_err:?}");
}

/// `--tcp=0` binds an OS-assigned ephemeral port instead of a fixed one —
/// keeps this test from colliding with a real `--tcp=9999` instance
/// already running on the machine, and from leaking a fixed port if the
/// test process is killed uncleanly.
fn spawn_sexpr_server() -> (std::process::Child, u16) {
    use std::io::BufRead;
    use std::process::Stdio;

    let mut child = sens()
        .args(["--tcp=0", "--protocol=sexpr"])
        .stderr(Stdio::piped())
        .stdout(Stdio::null())
        .spawn()
        .expect("binary should start");

    let stderr = child.stderr.take().expect("stderr should be piped");
    let mut reader = std::io::BufReader::new(stderr);
    let mut banner = String::new();
    reader
        .read_line(&mut banner)
        .expect("banner line should be read before the port is needed");
    let port: u16 = banner
        .trim()
        .rsplit(':')
        .next()
        .expect("banner should end in :PORT")
        .parse()
        .expect("banner port should be numeric");

    // Keep the child's stderr pipe alive and drain it after consuming the
    // banner. The server logs connection/request diagnostics; dropping this
    // reader makes those writes hit EPIPE and abort the child connection
    // thread, which masked protocol responses as ECONNRESET.
    std::thread::spawn(move || {
        let mut reader = reader;
        let _ = std::io::copy(&mut reader, &mut std::io::sink());
    });

    (child, port)
}

#[test]
fn sexpr_protocol_rejects_missing_or_nil_id_without_fake_response() {
    let (mut child, port) = spawn_sexpr_server();
    let missing = request_with_retry(port, r#"(request (op eval) (source "(+ 1 2)"))"#);
    let explicit_nil =
        request_with_retry(port, r#"(request (id ()) (op eval) (source "(+ 1 2)"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        missing.contains("(protocol-error") && missing.contains("(kind missing-id)"),
        "{missing}"
    );
    assert!(
        explicit_nil.contains("(protocol-error") && explicit_nil.contains("(kind missing-id)"),
        "{explicit_nil}"
    );
    assert!(!missing.contains("(status ok)"), "{missing}");
    assert!(!explicit_nil.contains("(status ok)"), "{explicit_nil}");
}

#[test]
fn sexpr_protocol_parse_returns_canonical_structure_not_debug_format() {
    let (mut child, port) = spawn_sexpr_server();
    let response = request_with_retry(port, r#"(request (id 3) (op parse) (source "(+ 1 2)"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        response.contains("(value (+ 1 2))"),
        "expected canonical SENS syntax, not a Rust Debug string: {response}"
    );
}

// #1675: run the canonical active-lib migration completion gate in the
// focused CI target (`cargo test -p sens-cli --test cli`).
#[path = "active_lib_sens_completion.rs"]
mod active_lib_sens_completion;


#[test]
fn cli_lint_runs_a_simple_ukrainian_file_through_t5m() {
    let path = std::env::temp_dir().join(format!(
        "sens-cli-lint-t5m-{}.lisp",
        std::process::id(),
    ));
    std::fs::write(
        &path,
        "(визначити перевірка (функція (дерево) (за-умовою ((атом? дерево) так) (так (аналіз-розмір дерево)))))\n",
    )
    .expect("виконуваний український файл для лінтера");

    let output = sens()
        .arg("--lint")
        .arg(&path)
        .output()
        .expect("запуск SENS --lint");
    let _ = std::fs::remove_file(&path);

    assert!(
        output.status.success(),
        "--lint має виконати лінтер через поточний SENS/T5M шлях: stderr={} stdout={}",
        String::from_utf8_lossy(&output.stderr),
        String::from_utf8_lossy(&output.stdout),
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("Linter passed:"));
}

#[cfg(feature = "zig-transport")]
#[test]
fn t5m_physical_pair_repair_uses_sens_mint_and_executes_real_pair() {
    use std::{fs, path::Path};
    let repo = Path::new(concat!(env!("CARGO_MANIFEST_DIR"), "/../.."));
    let dir = std::env::temp_dir().join(format!(
        "sens-real-t5m-repair-{}-{}",
        std::process::id(),
        line!()
    ));
    fs::create_dir_all(&dir).expect("ізольоване джерело");
    let src = dir.join("обертання.lisp");
    let physical = dir.join("обертання.sens");
    let view = dir.join("обертання");
    let script = repo.join("scripts/refresh-verified-t5m-pair.sh");
    let run = || {
        Command::new("bash")
            .arg(&script)
            .arg(&src)
            .arg(env!("CARGO_BIN_EXE_sens"))
            .arg(env!("CARGO_BIN_EXE_sens-trit"))
            .current_dir(repo)
            .output()
            .expect("запуск справжнього SENS/Zig мігратора")
    };

    fs::write(&src, "(як-є ())\n").expect("вихідна D3 програма");
    let first = run();
    assert!(
        first.status.success(),
        "test_id=t5m-repair-first layer=SENS/Zig stderr={} stdout={}",
        String::from_utf8_lossy(&first.stderr),
        String::from_utf8_lossy(&first.stdout)
    );
    assert!(String::from_utf8_lossy(&first.stdout).contains("T5M_REPAIR_OK"));
    let original = fs::read(&physical).expect("справжні T5M байти");
    assert!(!original.is_empty());
    assert!(!fs::read_to_string(&view).unwrap().trim().is_empty());
    // Перевірка реального mint/eval через SENS, але з примусовою
    // невідомою аварією лише standalone-виконання фізичного носія.
    // Такий дефект не може перезаписати вже робочу пару як успіх.
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let proxy = dir.join("sens-standalone-failure.sh");
        let real_sens = format!("{:?}", env!("CARGO_BIN_EXE_sens"));
        fs::write(&proxy, format!(
            "#!/bin/sh\ncase \"$1\" in\n  --t5m-mint|--t5m-pair) exec {real_sens} \"$@\" ;;\n  *) echo 'unexpected standalone failure' >&2; exit 23 ;;\nesac\n"
        )).expect("обгортка фізичного виконання");
        let mut perms = fs::metadata(&proxy).unwrap().permissions();
        perms.set_mode(0o700);
        fs::set_permissions(&proxy, perms).unwrap();
        let unexpected = Command::new("bash")
            .arg(&script)
            .arg(&src)
            .arg(&proxy)
            .arg(env!("CARGO_BIN_EXE_sens-trit"))
            .current_dir(repo)
            .output()
            .expect("ремонт із невідомою standalone-аварією");
        assert!(
            !unexpected.status.success(),
            "test_id=t5m-repair-standalone-red layer=SENS/Zig stdout={}",
            String::from_utf8_lossy(&unexpected.stdout)
        );
        assert!(
            String::from_utf8_lossy(&unexpected.stderr)
                .contains("T5M_REPAIR_STANDALONE_UNEXPECTED_FAIL"),
            "test_id=t5m-repair-standalone-red layer=SENS/Zig stderr={}",
            String::from_utf8_lossy(&unexpected.stderr)
        );
        assert_eq!(
            fs::read(&physical).unwrap(),
            original,
            "невідома standalone-аварія не має переписувати вже перевірені байти"
        );
        let _ = fs::remove_file(proxy);
    }
    let paired = sens()
        .args([
            "--t5m-pair",
            src.to_str().unwrap(),
            physical.to_str().unwrap(),
        ])
        .output()
        .expect("SENS eval");
    assert!(
        paired.status.success(),
        "SENS paired stderr={}",
        String::from_utf8_lossy(&paired.stderr)
    );

    // Заміна власне Lisp змінює фізичну пару; стара не залишається
    // формально допущеною, навіть якщо попередній CI був зелений.
    fs::write(&src, "(як-є (()))\n").expect("новий Lisp");
    let refreshed = run();
    assert!(
        refreshed.status.success(),
        "test_id=t5m-repair-refresh layer=SENS/Zig stderr={}",
        String::from_utf8_lossy(&refreshed.stderr)
    );
    let new_physical = fs::read(&physical).expect("оновлена пара");
    assert_ne!(
        original, new_physical,
        "пара повинна оновитися разом з Lisp"
    );

    // Негативна перевірка: пошкоджений SENS source → точна відмова,
    // і раніше перевірений .sens не переписується через невдалий ремонт.
    fs::write(&src, "(невідома-недопущена-функція (як-є ()))\n").expect("неприпустима програма");
    let refused = run();
    assert!(
        !refused.status.success(),
        "невідома викличність не може пройти"
    );
    assert_eq!(
        fs::read(&physical).unwrap(),
        new_physical,
        "помилка не має псувати попередню фізичну пару"
    );

    // Дві українські програми: залежність DEFINE і її реальний SENS-споживач.
    let helper = dir.join("допоміжний.lisp");
    fs::write(
        &helper,
        "(визначити локальний-помічник (функція (значення) значення))\n",
    )
    .expect("потрібне українське визначення");
    fs::write(&src, "(локальний-помічник (як-є ()))\n").expect("користувач DEFINE");
    let missing_binding = run();
    assert!(
        !missing_binding.status.success(),
        "невідомий виклик не можна вважати виконаним"
    );
    assert_eq!(
        fs::read(&physical).unwrap(),
        new_physical,
        "невдала пара не повинна псувати попередню T5M"
    );
    let repaired_binding = Command::new("bash")
        .arg(&script)
        .arg(&src)
        .arg(env!("CARGO_BIN_EXE_sens"))
        .arg(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("--binding-source")
        .arg(&helper)
        .current_dir(repo)
        .output()
        .expect("SENS/Zig виконання реальної DEFINE-залежності");
    assert!(
        repaired_binding.status.success(),
        "test_id=t5m-repair-binding-source layer=SENS/Zig stderr={} stdout={}",
        String::from_utf8_lossy(&repaired_binding.stderr),
        String::from_utf8_lossy(&repaired_binding.stdout)
    );
    assert!(String::from_utf8_lossy(&repaired_binding.stdout).contains("T5M_REPAIR_OK"));
    assert!(
        String::from_utf8_lossy(&repaired_binding.stdout)
            .contains("mode=paired-and-dependency-complete"),
        "test_id=t5m-repair-dependency-complete layer=SENS/Zig expected=paired-and-dependency-complete stdout={} stderr={}",
        String::from_utf8_lossy(&repaired_binding.stdout),
        String::from_utf8_lossy(&repaired_binding.stderr)
    );
    let paired_with_binding = sens()
        .arg("--t5m-pair")
        .arg(&src)
        .arg(&physical)
        .arg("--binding-source")
        .arg(&helper)
        .output()
        .expect("живе SENS виконання фізичної пари з DEFINE");
    assert!(
        paired_with_binding.status.success(),
        "test_id=t5m-repair-binding-execute layer=SENS stderr={}",
        String::from_utf8_lossy(&paired_with_binding.stderr)
    );
    assert_eq!(
        String::from_utf8_lossy(&paired_with_binding.stdout).trim(),
        "()"
    );

    let _ = fs::remove_dir_all(&dir);
}
