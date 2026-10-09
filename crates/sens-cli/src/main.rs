use sens::{eval_parsed_expressions, parse, Environment, Session, Value};
use std::env;
use std::fs;
use std::io::Read;
use std::process;
use std::rc::Rc;
mod lsp_entry;
mod island_invoke;
mod islands;
mod repl;
mod swarm;
mod tcp_repl;
use swarm::{dotted_alist_lookup, oracle_check, oracle_help, run_client, run_tcp_repl_sexpr};
use tcp_repl::run_tcp_repl;

/// `--allow-process=git,cargo` restricts process execution for the
/// unauthenticated TCP/oracle entry point. The trusted local CLI/REPL is the
/// Lisp-machine profile and does not require per-program grants.
fn allowed_processes(args: &[String]) -> Vec<String> {
    args.iter()
        .find_map(|arg| arg.strip_prefix("--allow-process="))
        .map(|list| list.split(',').map(str::to_string).collect())
        .unwrap_or_default()
}

fn extract_repl_surface(args: Vec<String>) -> Result<(Vec<String>, repl::ReplSurface), String> {
    let mut output = Vec::with_capacity(args.len());
    let mut input = args.into_iter();
    let Some(program) = input.next() else {
        return Ok((output, repl::ReplSurface::Core));
    };
    output.push(program);
    let mut input = input.peekable();
    let mut surface = repl::ReplSurface::Core;
    let mut seen = false;

    while let Some(arg) = input.next() {
        let surface_value = if arg == "--surface" {
            Some(
                input
                    .next()
                    .ok_or_else(|| "--surface requires uk|en|sa|core".to_string())?,
            )
        } else {
            arg.strip_prefix("--surface=").map(str::to_string)
        };

        if let Some(value) = surface_value {
            if seen {
                return Err("--surface may be specified only once".to_string());
            }
            surface = repl::ReplSurface::parse(&value)
                .ok_or_else(|| format!("unknown REPL surface: {value}"))?;
            seen = true;
        } else {
            output.push(arg);
        }
    }
    Ok((output, surface))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum CliCore {
    Core3,
    Core4,
}

fn extract_cli_core(args: Vec<String>) -> Result<(Vec<String>, CliCore), String> {
    let mut output = Vec::with_capacity(args.len());
    let mut input = args.into_iter();
    let Some(program) = input.next() else {
        return Ok((output, CliCore::Core4));
    };
    output.push(program);
    let mut input = input.peekable();
    let mut core = CliCore::Core4;
    let mut seen = false;

    while let Some(arg) = input.next() {
        let core_value = if arg == "--core" {
            Some(
                input
                    .next()
                    .ok_or_else(|| "--core requires 3|4".to_string())?,
            )
        } else {
            arg.strip_prefix("--core=").map(str::to_string)
        };

        if let Some(value) = core_value {
            if seen {
                return Err("--core may be specified only once".to_string());
            }
            core = match value.as_str() {
                "3" => CliCore::Core3,
                "4" => CliCore::Core4,
                _ => return Err(format!("unknown Core profile: {value}; expected 3|4")),
            };
            seen = true;
        } else {
            output.push(arg);
        }
    }

    Ok((output, core))
}

fn bootstrap_core(
    session: &mut Session,
    core: CliCore,
) -> Result<sens::EvalResult, sens::LanguageError> {
    match core {
        CliCore::Core3 => sens::load_core3_library(session),
        CliCore::Core4 => sens::load_core_library(session),
    }
}

/// Identify an explicitly invoked physical binary program before loading any
/// Lisp libraries or installing host capabilities. A .sens file is bytes,
/// NEVER legacy textual Lisp or a source string with a new extension.
fn physical_t5_request(args: &[String]) -> Option<Result<&str, &'static str>> {
    let (position, path) = args
        .iter()
        .enumerate()
        .skip(1)
        .find(|(_, argument)| {
            std::path::Path::new(argument).extension().and_then(|ext| ext.to_str()) == Some("sens")
        })?;
    if position != 1 || args.len() != 2 {
        return Some(Err(
            "physical .sens accepts exactly one file argument; use sens-trit for explicit Core4 evaluation",
        ));
    }
    Some(Ok(path.as_str()))
}

/// One pure T5 -> canonical binary D2 -> current evaluator route.
/// Neither human spellings nor an eight-bit compatibility reader participate.
/// An explicit binary file never gains ambient host capabilities or Core4.
fn eval_physical_t5(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    let binary = sens::open_ternary_program(bytes)
        .map_err(|err| format!("physical T5/D2 rejected: {err:?}"))?;
    let forms = sens::parse_canonical_binary(&binary)
        .map_err(|err| format!("exact binary reader rejected: {}", err.render(&binary)))?;
    let mut pure = Session::default();
    eval_parsed_expressions(&forms, &mut pure)
        .map_err(|err| format!("current SENS execution rejected: {}", err.render(&binary)))
}

fn main() {
    // Physical .sens is the exact binary entrypoint and needs no legacy
    // bootstrap or ambient host capabilities. Reject extra flags instead of
    // silently interpreting its bytes as textual Lisp.
    let raw_args: Vec<String> = env::args().collect();
    if let Some(request) = physical_t5_request(&raw_args) {
        let result = match request {
            Ok(filename) => fs::read(filename)
                .map_err(|err| format!("read physical .sens: {err}"))
                .and_then(|bytes| eval_physical_t5(&bytes)),
            Err(message) => Err(message.to_owned()),
        };
        match result {
            Ok(result) => {
                for output in result.output {
                    println!("{output}");
                }
                println!("{}", result.value);
            }
            Err(err) => {
                eprintln!("sens: {err}");
                process::exit(1);
            }
        }
        return;
    }

    // The CLI is a trusted local Lisp-machine surface: install the OS
    // capability layer (filesystem, process execution, TCP). The semantic
    // core itself ships none.
    sens_host::install();
    // Availability only; Core3×10101000 admission remains SENS-owned.
    island_invoke::install();
    let args: Vec<String> = env::args().collect();
    let allowed = allowed_processes(&args);
    let sexpr_protocol = args.iter().any(|a| a == "--protocol=sexpr");
    let args: Vec<String> = args
        .into_iter()
        .filter(|arg| !arg.starts_with("--allow-process=") && arg != "--protocol=sexpr")
        .collect();
    let (args, cli_core) = match extract_cli_core(args) {
        Ok(parsed) => parsed,
        Err(error) => {
            eprintln!("sens: {error}");
            process::exit(2);
        }
    };
    let (args, repl_surface) = match extract_repl_surface(args) {
        Ok(parsed) => parsed,
        Err(error) => {
            eprintln!("sens: {error}");
            process::exit(2);
        }
    };
    let allowed_for_tcp = allowed.clone();
    // Plain `f64`s, not a `Value` — `run_tcp_repl_sexpr` spawns one thread
    // per connection, and `Value`'s `Rc`-based sharing isn't `Send`; each
    // connection rebuilds its own `contract_version` `Value` locally from
    // these two numbers instead of cloning a shared one across threads.
    let (contract_major, contract_minor) = {
        let contract_source = include_str!("../../../language-contract.lisp");
        let mut throwaway = Session {
            environment: Environment::root(),
        };
        let quoted = format!("(quote {contract_source})");
        parse(&quoted)
            .ok()
            .and_then(|ast| eval_parsed_expressions(&ast, &mut throwaway).ok())
            .map(|r| r.value)
            .and_then(|v| {
                let major = dotted_alist_lookup(&v, "major")?;
                let minor = dotted_alist_lookup(&v, "minor")?;
                let Value::Number(major, _) = major else {
                    return None;
                };
                let Value::Number(minor, _) = minor else {
                    return None;
                };
                Some((major, minor))
            })
            .unwrap_or((0.0, 0.0))
    };
    let mut session = Session {
        environment: Environment::root(),
    };

    // Канонічний Core4 bootstrap і FASL fallback належать одному loader-у:
    // CLI не повинен виконувати Core4 в обхід loader-owned selected profile.
    const CORE_SRC: &str = sens::CORE_LIBRARY_SOURCE;
    // The loader already validates the embedded FASL hash and falls back to
    // CORE_LIBRARY_SOURCE when stale. Normal program stderr must stay reserved
    // for program/CLI diagnostics; FASL freshness is available through the
    // explicit core_library_fasl_is_current() diagnostic API.
    if let Err(e) = bootstrap_core(&mut session, cli_core) {
        let label = match cli_core {
            CliCore::Core3 => "Core3",
            CliCore::Core4 => "Core4",
        };
        eprintln!("Error loading bootstrap {label}: {}", e.render(CORE_SRC));
        process::exit(1);
    }

    // Time is a language-owned semantic layer, not part of the closed core.
    // Load it explicitly after core so local CLI/REPL sessions keep `utc-now`
    // even after the old Rust calendar builtin is removed.
    if let Err(e) = sens::load_time_library(&mut session) {
        eprintln!(
            "Error loading time.lisp: {}",
            e.render(sens::TIME_LIBRARY_SOURCE)
        );
        process::exit(1);
    }

    // Process execution remains a host capability only at the raw byte
    // boundary. Decode/result policy is language-owned and must be present in
    // every local CLI/REPL session before the legacy host `process-run` can be
    // removed safely.
    if let Err(e) = sens::load_process_library(&mut session) {
        eprintln!(
            "Error loading process.lisp: {}",
            e.render(sens::PROCESS_LIBRARY_SOURCE)
        );
        process::exit(1);
    }

    // File text policy is language-owned the same way: the host now exposes
    // only `read-file-bytes`/`write-file-bytes`, deletion-audit follow-up
    // 2026-09-12 (FS-CAPABILITY-UTF8-POLICY-MIGRATION).
    if let Err(e) = sens::load_fs_library(&mut session) {
        eprintln!(
            "Error loading fs.lisp: {}",
            e.render(sens::FS_LIBRARY_SOURCE)
        );
        process::exit(1);
    }

    // Text form stays in scope for downstream consumers (tcp repl seed,
    // --lint path) without re-reading the file.
    #[allow(unused_variables)]
    let core_lib = CORE_SRC;

    // The sexpr/oracle server creates a fresh custom Environment per connection.
    // Its handler now establishes the macro substrate explicitly before this
    // remaining language-owned seed is evaluated, so macro.lisp need not be
    // duplicated into the seed string.
    static SEXPR_BOOTSTRAP: std::sync::OnceLock<String> = std::sync::OnceLock::new();
    let sexpr_bootstrap_lib: &'static str = SEXPR_BOOTSTRAP
        .get_or_init(|| {
            format!(
                "{}\n{}\n{}\n{}\n{}",
                CORE_SRC,
                sens::TIME_LIBRARY_SOURCE,
                sens::UTF8_LIBRARY_SOURCE,
                sens::PROCESS_LIBRARY_SOURCE,
                sens::FS_LIBRARY_SOURCE
            )
        })
        .as_str();

    if args.len() > 1 {
        let arg = &args[1];

        if arg == "islands" {
            match islands::run(&args[2..]) {
                Ok(output) => println!("{output}"),
                Err(error) => {
                    eprintln!("sens islands: {error}");
                    process::exit(2);
                }
            }
            return;
        }

        if arg == "install" {
            let mut island_args = vec!["install".to_string()];
            island_args.extend_from_slice(&args[2..]);
            match islands::run(&island_args) {
                Ok(output) => println!("{output}"),
                Err(error) => {
                    eprintln!("sens islands: {error}");
                    process::exit(2);
                }
            }
            return;
        }

        // LSP mode: forwards to the sens-lsp crate's stdio entrypoint.
        if arg == "lsp" {
            lsp_entry::run();
            return;
        }

        if arg == "--version" || arg == "-V" || arg == "-v" {
            println!("sens {}", env!("CARGO_PKG_VERSION"));
            return;
        }

        if arg == "--help" || arg == "-h" {
            println!("Usage: sens [file]");
            println!("If no file is provided, starts the REPL.");
            println!("Textual compatibility source: .lisp and historical aliases; physical .sens is packed T5, not UTF-8 Lisp.");
            println!("  sens program.sens            Run exact physical T5 with pure SENS (no implicit Core4/host effects)");
            println!("  sens-trit open program.sens  Display exact binary words without running");
            println!("\nOptions:");
            println!("  lsp                          Run the Language Server (LSP over stdio)");
            println!("  install [--profile four-kernel]  Automatically bootstrap the execution-island runtimes for the current host");
            println!("  islands plan|install|status      Inspect, install, or observe execution islands without semantic admission");
            println!("  -V, --version               Print version information");
            println!("  -h, --help                  Print help information");
            println!("  --surface=uk|en|sa|core      Start the interactive REPL with this programming surface");
            println!("  --core=3|4                    Explicitly select Core3 laboratory or default Core4 before evaluation");
            println!(
                "  --allow-process=a,b,c        TCP/oracle only: allow exactly these process names"
            );
            println!("  --lint                        Run the linter on the provided file and exit with non-zero if thresholds are exceeded");
            println!("  --oracle-check <file|->       Parse-only agent preflight; '-' reads stdin and emits oracle-result/1");
            println!("  --oracle-help [tool]          List common agent tools or explain one from the WSM Guard directory");
            println!("  --tcp[=PORT]                 Serve the REPL over TCP on 127.0.0.1 (default port 9999) instead of stdio");
            println!("  --protocol=sexpr              With --tcp: strict (request (id) (op) (source)) / (response ...) envelope, no banner/prompt");
            println!("  --connect=HOST:PORT            P2P client: forward one sexpr request from stdin to a peer's TCP REPL, print the response");
            return;
        }

        if arg == "--tcp" || arg.starts_with("--tcp=") {
            let port = arg
                .strip_prefix("--tcp=")
                .and_then(|p| p.parse::<u16>().ok())
                .unwrap_or(9999);
            if sexpr_protocol {
                run_tcp_repl_sexpr(
                    port,
                    sexpr_bootstrap_lib,
                    allowed_for_tcp,
                    contract_major,
                    contract_minor,
                );
            } else {
                run_tcp_repl(port, core_lib, &allowed_for_tcp);
            }
            return;
        }

        if arg.starts_with("--connect=") {
            let address = arg.strip_prefix("--connect=").unwrap_or_default();
            if address.is_empty() {
                eprintln!("sens: --connect requires HOST:PORT");
                process::exit(1);
            }
            run_client(address);
            return;
        }

        if arg == "--oracle-check" {
            if args.len() < 3 {
                eprintln!("Usage: sens --oracle-check <file|->");
                process::exit(1);
            }
            let source = if args[2] == "-" {
                let mut source = String::new();
                if let Err(error) = std::io::stdin().read_to_string(&mut source) {
                    eprintln!("sens: failed to read source from stdin: {error}");
                    process::exit(1);
                }
                source
            } else {
                match fs::read_to_string(&args[2]) {
                    Ok(source) => source,
                    Err(error) => {
                        eprintln!("sens: failed to read {}: {error}", args[2]);
                        process::exit(1);
                    }
                }
            };
            let contract_version = Value::list([
                Value::Number(contract_major, sens::Exactness::Exact),
                Value::Number(contract_minor, sens::Exactness::Exact),
            ]);
            let (result, valid) = oracle_check(&source, &contract_version);
            println!("{result}");
            if !valid {
                process::exit(2);
            }
            return;
        }

        if arg == "--oracle-help" {
            match oracle_help(&mut session, args.get(2).map(String::as_str)) {
                Ok(reference) => println!("{reference}"),
                Err(error) => {
                    eprintln!("sens: {error}");
                    process::exit(2);
                }
            }
            return;
        }

        if arg == "--lint" {
            if args.len() < 3 {
                eprintln!("Usage: sens --lint <file>");
                process::exit(1);
            }
            let filename = &args[2];

            // Load linter
            let linter_lib = include_str!("../../../lib/linter.lisp");
            if let Ok(linter_ast) = parse(linter_lib) {
                if let Err(e) = eval_parsed_expressions(&linter_ast, &mut session) {
                    eprintln!("Error loading linter: {}", e.render(linter_lib));
                    process::exit(1);
                }
            } else {
                eprintln!("Failed to parse linter.lisp");
                process::exit(1);
            }

            match fs::read_to_string(filename) {
                Ok(source) => {
                    let quoted_src = format!("(quote (begin {}\n))", source);
                    match parse(&quoted_src) {
                        Ok(q_ast) => {
                            let target_ast = match eval_parsed_expressions(&q_ast, &mut session) {
                                Ok(r) => r.value,
                                Err(e) => {
                                    eprintln!(
                                        "Error evaluating quoted source: {}",
                                        e.render(&quoted_src)
                                    );
                                    process::exit(1);
                                }
                            };
                            session.environment.define("*lint-target*", target_ast);

                            let lint_call_src = "(lint-check *lint-target* (quote ((max-size . 5000) (max-nesting . 50) (max-complexity . 100) (max-globals . 500) (max-effects . 10))))";
                            match parse(lint_call_src) {
                                Ok(lint_ast) => {
                                    match eval_parsed_expressions(&lint_ast, &mut session) {
                                        Ok(result) => {
                                            if let Value::Nil = result.value {
                                                println!("Linter passed: {}", filename);
                                                return;
                                            } else {
                                                eprintln!(
                                                    "Linter violations found in {}:",
                                                    filename
                                                );
                                                eprintln!("{}", result.value);
                                                process::exit(1);
                                            }
                                        }
                                        Err(e) => {
                                            eprintln!(
                                                "Error running linter: {}",
                                                e.render(lint_call_src)
                                            );
                                            process::exit(1);
                                        }
                                    }
                                }
                                Err(e) => {
                                    eprintln!(
                                        "Parse error creating lint call: {}",
                                        e.render(lint_call_src)
                                    );
                                    process::exit(1);
                                }
                            }
                        }
                        Err(e) => {
                            eprintln!("Parse error in {}: {}", filename, e.render(&source));
                            process::exit(1);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error reading file {}: {}", filename, e);
                    process::exit(1);
                }
            }
        }

        // `--surface` належить інтерактивному REPL, а не semantics/file execution.
        if repl_surface != repl::ReplSurface::Core {
            eprintln!("sens: --surface is available only when starting the interactive REPL");
            process::exit(2);
        }

        // Run file
        let filename = arg;

        // `*argv*` (PLAN.md item 21's follow-up, for scripts/release.lisp
        // taking a version on the command line) — everything after the
        // filename, as a sens list of strings, defined before the
        // script runs. Empty when nothing follows the filename, not an
        // error — a script that wants an argument checks for that itself
        // (`(atom *argv*)`), the same way any other missing-input case in
        // this language is handled, not a special CLI-only mechanism.
        // `*argv*` (продовження PLAN.md, пункту 21, для scripts/release.lisp,
        // яка бере версію з командного рядка) — усе після імені файлу, як
        // sens-список рядків, визначений до запуску скрипта. Порожній,
        // якщо нічого не йде після імені файлу, не помилка — скрипт, якому
        // потрібен аргумент, сам перевіряє це (`(atom *argv*)`), так само
        // як будь-який інший випадок відсутнього вводу в цій мові, не
        // окремий CLI-специфічний механізм.
        let argv = Value::list(
            args[2..]
                .iter()
                .map(|arg| Value::String(Rc::from(arg.as_str()))),
        );
        session.environment.define("*argv*", argv);

        match fs::read_to_string(filename) {
            Ok(source) => match parse(&source) {
                Ok(ast) => match eval_parsed_expressions(&ast, &mut session) {
                    Ok(result) => {
                        for out in result.output {
                            println!("{}", out);
                        }
                        println!("{}", result.value);
                    }
                    Err(e) => {
                        // Вивід, накопичений до помилки (наприклад, «FAIL: ...» від
                        // скрипта перевірок), не губиться: друкуємо його перед помилкою.
                        for out in session.environment.output_take_new() {
                            println!("{}", out);
                        }
                        eprintln!("Error: {}", e.render(&source));
                        process::exit(1);
                    }
                },
                Err(e) => {
                    eprintln!("Parse error: {}", e.render(&source));
                    process::exit(1);
                }
            },
            Err(e) => {
                eprintln!("Error reading file {}: {}", filename, e);
                process::exit(1);
            }
        }
    } else {
        // REPL mode
        repl::run_repl(session, repl_surface);
    }
}


#[cfg(test)]
mod core_profile_bootstrap_tests {
    use super::*;

    #[test]
    fn explicit_physical_t5_is_a_pure_binary_entrypoint_not_an_alias() {
        let arguments = vec!["sens".to_owned(), "program.sens".to_owned()];
        assert_eq!(physical_t5_request(&arguments), Some(Ok("program.sens")));
        let legacy = vec!["sens".to_owned(), "program.lisp".to_owned()];
        assert_eq!(physical_t5_request(&legacy), None);
        let flags = vec![
            "sens".to_owned(), "--core=4".to_owned(), "program.sens".to_owned(),
        ];
        assert!(matches!(physical_t5_request(&flags), Some(Err(_))));
    }

    #[test]
    fn physical_t5_enters_canonical_binary_reader_not_text_lisp() {
        let bytes = include_bytes!(
            "../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        );
        let source = sens::open_ternary_program(bytes).expect("admitted physical bytes");
        let forms = sens::parse_canonical_binary(&source).expect("canonical D2 program");
        assert!(!forms.is_empty());
        assert!(!source.contains("QUOTE"));
        assert!(!source.contains("(quote"));
        // Broken physical/truncated structural programs fail before evaluation.
        assert!(sens::open_ternary_program(&[0xf3]).is_err());
    }

    #[test]
    fn cli_core_selector_defaults_to_core4_and_accepts_only_3_or_4() {
        let (args, core) =
            extract_cli_core(vec!["sens".to_string()]).expect("default selector");
        assert_eq!(args, vec!["sens"]);
        assert_eq!(core, CliCore::Core4);

        let (args, core) = extract_cli_core(vec![
            "sens".to_string(),
            "--core=3".to_string(),
            "program.lisp".to_string(),
        ])
        .expect("explicit Core3 selector");
        assert_eq!(args, vec!["sens", "program.lisp"]);
        assert_eq!(core, CliCore::Core3);

        assert!(extract_cli_core(vec!["sens".to_string(), "--core=2".to_string()]).is_err());
        assert!(extract_cli_core(vec![
            "sens".to_string(),
            "--core=3".to_string(),
            "--core=4".to_string(),
        ])
        .is_err());
    }

    #[test]
    fn cli_core_bootstrap_uses_only_canonical_profile_loaders() {
        let mut core4 = Session {
            environment: Environment::root(),
        };
        bootstrap_core(&mut core4, CliCore::Core4).expect("CLI Core4 bootstrap must succeed");
        assert_eq!(
            core4.environment.selected_core_profile(),
            Some(sens::CoreProfile::Core4)
        );

        let mut core3 = Session {
            environment: Environment::root(),
        };
        bootstrap_core(&mut core3, CliCore::Core3).expect("CLI Core3 bootstrap must succeed");
        assert_eq!(
            core3.environment.selected_core_profile(),
            Some(sens::CoreProfile::Core3)
        );
    }
}
