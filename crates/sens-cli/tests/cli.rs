//! Integration tests for the `my-lisp` CLI binary.
//! Intehratsiini testy dlia CLI-binarnyka `my-lisp`.
//! Integrationstests für die `my-lisp`-CLI-Binärdatei.
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
/// its working directory, matching how the legacy `my-lisp` binary is actually invoked in
/// practice (and specifically required by `--oracle-help`, which reads
/// `knowledge/guard-reference.lisp` relative to the caller's cwd so new
/// reference entries take effect without a rebuild).
fn legacy_bin() -> Command {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let mut command = Command::new(env!("CARGO_BIN_EXE_my-lisp"));
    command.current_dir(repo_root);
    command
}

fn sens() -> Command {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    command.current_dir(repo_root);
    command
}

#[test]
fn version_flag_prints_the_crate_version() {
    let output = legacy_bin()
        .arg("--version")
        .output()
        .expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(
        stdout.trim(),
        format!("sens {}", env!("CARGO_PKG_VERSION"))
    );
}

#[test]
fn sens_and_my_lisp_binaries_execute_the_same_direct_8_bit_program() {
    let path = std::env::temp_dir().join("sens-cli-parity-direct-8-bit.lisp");
    std::fs::write(&path, "(00000001 42)").expect("should write parity fixture");

    let legacy = legacy_bin()
        .arg(&path)
        .output()
        .expect("my-lisp binary should run");
    let canonical = sens()
        .arg(&path)
        .output()
        .expect("sens binary should run");
    let _ = std::fs::remove_file(&path);

    assert_eq!(canonical.status.code(), legacy.status.code());
    assert_eq!(canonical.stdout, legacy.stdout);
    assert_eq!(canonical.stderr, legacy.stderr);
    assert!(canonical.status.success());
    assert_eq!(String::from_utf8_lossy(&canonical.stdout).trim(), "42");
}

#[test]
fn short_version_flags_match_the_long_form() {
    for flag in ["-V", "-v"] {
        let output = legacy_bin().arg(flag).output().expect("binary should run");
        assert!(output.status.success());
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert_eq!(
            stdout.trim(),
            format!("sens {}", env!("CARGO_PKG_VERSION"))
        );
    }
}

#[test]
fn help_flag_prints_usage() {
    let output = legacy_bin().arg("--help").output().expect("binary should run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Usage: sens [file]"));
    assert!(stdout.contains(".wsm"));
    assert!(stdout.contains(".my"));
    assert!(stdout.contains(".lisp"));
    assert!(stdout.contains(".sens"));
    assert!(stdout.contains(".сенс"));
    assert!(stdout.contains("--oracle-check <file|->"));
    assert!(stdout.contains("--core=3|4"));
}

#[test]
fn explicit_core3_flag_selects_core3_before_file_evaluation() {
    let path = std::env::temp_dir().join("sens-cli-core3-profile-1429.lisp");
    std::fs::write(&path, "(10101000)").expect("should write Core3 probe");

    let default = sens()
        .arg(&path)
        .output()
        .expect("default Core4 CLI should run");
    let core3 = sens()
        .args(["--core=3", path.to_str().expect("UTF-8 temp path")])
        .output()
        .expect("explicit Core3 CLI should run");
    let _ = std::fs::remove_file(&path);

    assert_eq!(default.status.code(), Some(1));
    assert!(
        String::from_utf8_lossy(&default.stderr)
            .contains("SENS function has no admitted callable mechanism: 10101000"),
        "{:?}",
        String::from_utf8_lossy(&default.stderr)
    );

    assert_eq!(core3.status.code(), Some(1));
    assert!(
        String::from_utf8_lossy(&core3.stderr)
            .contains("10101000: expected 2 arguments, received 0"),
        "{:?}",
        String::from_utf8_lossy(&core3.stderr)
    );
}

#[test]
fn oracle_check_file_is_agent_friendly_and_side_effect_free() {
    let path = std::env::temp_dir().join("my-lisp-oracle-check-unclosed.lisp");
    std::fs::write(&path, "(def answer (+ 40 2)").expect("should write fixture");

    let output = legacy_bin()
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

    let output = legacy_bin()
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
    let output = legacy_bin()
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
    let output = legacy_bin()
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
    let output = legacy_bin()
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
    let output = legacy_bin()
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
    let output = legacy_bin()
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
fn running_a_source_file_prints_its_result() {
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-ok.lisp");
    std::fs::write(&path, "(+ 1 2)").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), "3");
}

/// Historical human-source extensions remain compatibility inputs only.
/// A physical .sens file must never be a textual alias of these extensions.
#[test]
fn textual_compatibility_extensions_do_not_claim_sens_binary_identity() {
    let dir = std::env::temp_dir();
    let code = "(+ 1 2)";

    for ext in [".wsm", ".my", ".lisp", ".сенс"] {
        let path = dir.join(format!("my-lisp-cli-test-ext{ext}"));
        std::fs::write(&path, code).expect("should write compatibility source");

        let output = legacy_bin().arg(&path).output().expect("binary should run");
        let _ = std::fs::remove_file(&path);

        assert!(
            output.status.success(),
            "{ext}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "3", "{ext}");
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
    assert_ne!(bytes, b"10 001 00 10 01 01");

    let output = sens().arg(path).output().expect("canonical SENS CLI");
    assert!(
        output.status.success(),
        "physical T5 rejected: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "()");

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
    assert!(!output.status.success(), "textual .sens was executed as Lisp");
    let diagnostic = String::from_utf8_lossy(&output.stderr);
    assert!(
        diagnostic.contains("physical T5")
            || diagnostic.contains("exact binary reader")
            || diagnostic.contains("current SENS execution"),
        "missing physical-binary rejection diagnostic: {diagnostic}"
    );
}

#[test]
fn running_a_file_with_an_evaluation_error_exits_nonzero() {
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-eval-error.lisp");
    std::fs::write(&path, "(car (quote ()))").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.starts_with("Error:"));
}

#[test]
fn running_a_file_with_a_parse_error_exits_nonzero() {
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-parse-error.lisp");
    std::fs::write(&path, "(1 2").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.starts_with("Parse error:"));
}

#[test]
fn running_a_missing_file_reports_a_read_error() {
    let output = legacy_bin()
        .arg("this-file-does-not-exist-my-lisp-cli.lisp")
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
    let dir = std::env::temp_dir().join(format!("my-lisp-cli-test-history-{}", std::process::id()));
    std::fs::create_dir_all(&dir).expect("should create temp home dir");

    let run = |input: &str| {
        use std::io::Write;
        use std::process::Stdio;
        let mut child = legacy_bin()
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

    run("(+ 1 2)\n");
    run("(+ 3 4)\n");

    let history = std::fs::read_to_string(dir.join(".sens-history"))
        .expect("second session should find history left by the first");
    let _ = std::fs::remove_dir_all(&dir);

    assert!(history.contains("(+ 1 2)"));
    assert!(history.contains("(+ 3 4)"));
}

#[test]
fn repl_echoes_a_lone_unknown_symbol_as_a_greeting_not_an_error() {
    // Isolated HOME, like repl_history_persists_across_separate_sessions.
    use std::io::Write;
    use std::process::Stdio;

    let dir = std::env::temp_dir().join(format!("my-lisp-cli-test-echo-{}", std::process::id()));
    std::fs::create_dir_all(&dir).expect("should create temp home dir");

    let mut child = legacy_bin()
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
        .write_all("мама\nhello\nсонце\n(+ мама 1)\n(car мама)\n(quote мама)\n".as_bytes())
        .expect("should write to stdin");
    let output = child.wait_with_output().expect("binary should run");
    let _ = std::fs::remove_dir_all(&dir);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Lone unknown symbols greet instead of erroring...
    assert!(stdout.contains("echo мама"), "stdout was: {stdout:?}");
    assert!(stdout.contains("echo hello"), "stdout was: {stdout:?}");
    assert!(stdout.contains("echo сонце"), "stdout was: {stdout:?}");
    // ...but the same unknown symbol inside a real form is still a named
    // failure — the echo is an interaction policy, not a language change.
    assert!(stderr.contains("unknown symbol"), "stderr was: {stderr:?}");
    // A quoted symbol evaluates fine and prints itself, no echo involved.
    assert!(stdout.contains("мама"), "stdout was: {stdout:?}");
}

/// The echo fallback must not leak into non-interactive execution: running a
/// file whose whole content is a lone unknown symbol still fails named.
/// Echo-fallback ne povynen proshkodzhuvaty v neinteraktyvne vykonannia:
/// fail, чиє vsi vmist — odyn nevidomyi symvol, i dalі provaliuietsia nazvano.
#[test]
fn file_mode_still_errors_on_a_lone_unknown_symbol() {
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-lone-symbol.lisp");
    std::fs::write(&path, "мама").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("unknown symbol"), "stderr was: {stderr:?}");
}

#[test]
fn read_with_no_arguments_reads_one_line_from_real_stdin() {
    // Reliable in file mode, where the CLI's own stdin isn't also owned by
    // rustyline's line editor (see the caveat on read_stdin_line in
    // crates/my-lisp/src/eval/special_forms.rs for the interactive-REPL case).
    use std::io::Write;
    use std::process::Stdio;

    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-read-stdin.lisp");
    std::fs::write(&path, "(eval (read))").expect("should write temp file");

    let mut child = legacy_bin()
        .arg(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("binary should spawn");
    child
        .stdin
        .take()
        .expect("stdin should be piped")
        .write_all(b"(+ 1 2)\n")
        .expect("should write to stdin");
    let output = child.wait_with_output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), "3");
}

#[test]
fn core_lib_is_preloaded_before_running_a_file() {
    // lib/core.my defines `identity`; if the CLI stopped injecting core.my this
    // would fail with an "unknown symbol" evaluation error instead of returning 5.
    // lib/core.my vyznachaie `identity`; yakby CLI perestav vstavliaty core.my, tse b
    // provalylos pomylkoiu "unknown symbol" zamist povernennia 5.
    // lib/core.my definiert `identity`; würde die CLI core.my nicht mehr einspeisen,
    // schlüge dies mit einem "unknown symbol"-Fehler fehl statt 5 zurückzugeben.
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-core-lib.lisp");
    std::fs::write(&path, "(identity 5)").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), "5");
}

#[test]
fn argv_carries_everything_after_the_filename() {
    // *argv* (PLAN.md item 21's follow-up, for scripts/release.my taking a
    // version on the command line) is whatever follows the filename, as a
    // my-lisp list of strings — not parsed as code, just passed through.
    // *argv* (prodovzhennia PLAN.md, punktu 21, dlia scripts/release.my, yaka
    // bere versiiu z komandnoho riadka) — use, shcho yde pislia imeni failu, yak
    // my-lisp-spysok riadkiv — ne parsytsia yak kod, lyshe peredaietsia yak ye.
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-argv.lisp");
    std::fs::write(&path, "*argv*").expect("should write temp file");

    let output = legacy_bin()
        .arg(&path)
        .arg("0.4.4")
        .arg("extra")
        .output()
        .expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), "(\"0.4.4\" \"extra\")");
}

#[test]
fn argv_is_empty_when_nothing_follows_the_filename() {
    let dir = std::env::temp_dir();
    let path = dir.join("my-lisp-cli-test-argv-empty.lisp");
    std::fs::write(&path, "*argv*").expect("should write temp file");

    let output = legacy_bin().arg(&path).output().expect("binary should run");
    let _ = std::fs::remove_file(&path);

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.trim(), "()");
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

    let mut child = legacy_bin()
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
fn sexpr_protocol_eval_returns_structured_response() {
    let (mut child, port) = spawn_sexpr_server();
    let response = request_with_retry(port, r#"(request (id 1) (op eval) (source "(+ 1 2)"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        response.contains("(status ok)"),
        "unexpected response: {response}"
    );
    assert!(
        response.contains("(value 3)"),
        "unexpected response: {response}"
    );
    assert!(
        response.contains("(output ())"),
        "unexpected response: {response}"
    );
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
fn sexpr_protocol_diagnose_returns_structured_error() {
    let (mut child, port) = spawn_sexpr_server();
    let response = request_with_retry(port, r#"(request (id 2) (op diagnose) (source "(car 1)"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        response.contains("(status error)"),
        "unexpected response: {response}"
    );
    assert!(
        response.contains("(kind type-error)"),
        "unexpected response: {response}"
    );
}

#[test]
fn sexpr_protocol_parse_returns_canonical_structure_not_debug_format() {
    let (mut child, port) = spawn_sexpr_server();
    let response = request_with_retry(port, r#"(request (id 3) (op parse) (source "(+ 1 2)"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        response.contains("(value (+ 1 2))"),
        "expected canonical my-lisp syntax, not a Rust Debug string: {response}"
    );
}

#[test]
fn sexpr_protocol_connections_do_not_share_state() {
    let (mut child, port) = spawn_sexpr_server();

    let _ = request_with_retry(
        port,
        r#"(request (id 1) (op eval) (source "(def leaked 999)"))"#,
    );
    let second_response =
        request_with_retry(port, r#"(request (id 2) (op eval) (source "leaked"))"#);
    child.kill().expect("should be able to stop the server");

    assert!(
        second_response.contains("(status error)") && second_response.contains("unknown-symbol"),
        "a def on one connection leaked into another: {second_response}"
    );
}

// #1675: run the canonical active-lib migration completion gate in the
// focused CI target (`cargo test -p sens-cli --test cli`).
#[path = "active_lib_sens_completion.rs"]
mod active_lib_sens_completion;

// #1006: exact 10101000 remains denied in Core4 and admitted only via explicit Core3.
#[path = "raw_invoke_sens_1006.rs"]
mod raw_invoke_sens_1006;
