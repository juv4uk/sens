use sens::{eval_parsed_expressions, parse, Environment, Session, Value};
use std::env;
use std::fs;
use std::io::{Read, Write};
use std::process;
use std::rc::Rc;
mod island_invoke;
mod islands;
mod lsp_entry;
mod repl;
mod swarm;
mod tcp_repl;
#[cfg(feature = "zig-transport")]
use sens_cli::zig_transport;
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
        return Ok((output, repl::ReplSurface::UkrainianFull));
    };
    output.push(program);
    let mut input = input.peekable();
    let mut surface = repl::ReplSurface::UkrainianFull;
    let mut seen = false;

    while let Some(arg) = input.next() {
        let surface_value = if arg == "--surface" {
            Some(
                input
                    .next()
                    .ok_or_else(|| "--surface requires ук|укр|en|sa|core".to_string())?,
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

/// Separate mode: evaluate interactive input through the SENS-owned loop
/// (`lib/repl-core.lisp`: `репл-почати`/`репл-крок` → `обчислити-верхню-форму`)
/// instead of the native Rust evaluator. This is an additional, opt-in mode;
/// the default REPL keeps the native evaluator until parity is proven.
fn extract_sens_loop(args: Vec<String>) -> (Vec<String>, bool) {
    let mut sens_loop = false;
    let output = args
        .into_iter()
        .filter(|arg| {
            if arg == "--sens-loop" {
                sens_loop = true;
                false
            } else {
                true
            }
        })
        .collect();
    (output, sens_loop)
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

/// Людська українська .lisp-проєкція належить SENS, а не GUI/TUI.
/// Звичайні десяткові операнди набувають точного домену D24+ перед
/// обчисленням. Фізичний .sens іде окремим T5M шляхом, без цього reader.
    sens::source_projection::project_ukr_decimal_integer_literals(&parsed, source)
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
    let (position, path) = args.iter().enumerate().skip(1).find(|(_, argument)| {
        std::path::Path::new(argument)
            .extension()
            .and_then(|ext| ext.to_str())
            == Some("sens")
    })?;
    if position != 1 || args.len() != 2 {
        return Some(Err(
            "physical .sens accepts exactly one file argument; use sens-trit for explicit Core4 evaluation",
        ));
    }
    Some(Ok(path.as_str()))
}

/// Explicit instrumentation mode: its only input is the physical binary.
fn physical_t5_benchmark_request(
    args: &[String],
) -> Option<Result<(&str, bool), &'static str>> {
    let position = args
        .iter()
        .position(|argument| argument == "--benchmark-physical")?;
    let load_core4 = args.len() == 4 && args[3] == "--core4-runtime";
    if position != 1 || !(args.len() == 3 || load_core4) {
        return Some(Err(
            "usage: sens --benchmark-physical <program.sens> [--core4-runtime]",
        ));
    }
    if std::path::Path::new(&args[2])
        .extension()
        .and_then(|ext| ext.to_str())
        != Some("sens")
    {
        return Some(Err(
            "--benchmark-physical accepts only a physical .sens binary",
        ));
    }
    Some(Ok((args[2].as_str(), load_core4)))
}

/// Явно обраний людський .lisp → українська проєкція → Zig T5M →
/// двійковий SENS → виконання. Це окремо від історичного `sens file.lisp`.
fn t5m_file_request(args: &[String]) -> Option<Result<&str, &'static str>> {
    let position = args.iter().position(|argument| argument == "--t5m-file")?;
    if position != 1 || args.len() != 3 {
        return Some(Err("usage: sens --t5m-file <ukrainian-source.lisp>"));
    }
    // Фізичні .sens — це байти T5M, не людський Lisp навіть у режимі
    // --t5m-file. Не дозволяємо обійти двійковий reader текстовим шляхом.
    if std::path::Path::new(&args[2])
        .extension()
        .and_then(|ext| ext.to_str())
        != Some("lisp")
    {
        return Some(Err("--t5m-file accepts only .lisp sources; run physical .sens through the binary entry point"));
    }
    Some(Ok(args[2].as_str()))
}

fn t5m_files_request(args: &[String]) -> Option<Result<&[String], &'static str>> {
    let position = args.iter().position(|argument| argument == "--t5m-files")?;
    if position != 1 || args.len() < 3 {
        return Some(Err(
            "usage: sens --t5m-files <source1.lisp> [source2.lisp ...]",
        ));
    }
    if args[2..].iter().any(|path| {
        std::path::Path::new(path)
            .extension()
            .and_then(|ext| ext.to_str())
            != Some("lisp")
    }) {
        return Some(Err("--t5m-files accepts only ordered .lisp sources"));
    }
    Some(Ok(&args[2..]))
}

/// Генерувати фізичні байти SENS за тим самим reader, що --t5m-pair.
/// Zig пакує точні слова T5M; жодного Python-eval чи старого T5.
fn t5m_mint_request(args: &[String]) -> Option<Result<(&str, &str), &'static str>> {
    if !args.iter().skip(1).any(|part| part == "--t5m-mint") {
        return None;
    }
    if args.len() != 4 || args[1] != "--t5m-mint" {
        return Some(Err("usage: sens --t5m-mint <source.lisp> <output.sens>"));
    }
    let source = std::path::Path::new(&args[2]);
    let physical = std::path::Path::new(&args[3]);
    if source.extension().and_then(|ext| ext.to_str()) != Some("lisp")
        || physical.extension().and_then(|ext| ext.to_str()) != Some("sens")
    {
        return Some(Err("--t5m-mint requires .lisp input and .sens output"));
    }
    Some(Ok((&args[2], &args[3])))
}

// Явні Lisp-залежності SENS; жодного Python/JSON resolver.
fn t5m_binding_paths(args: &[String]) -> Result<Vec<&str>, &'static str> {
    if args.len() < 4 || !(args.len() - 4).is_multiple_of(2) {
        return Err("expected zero or more --binding-source <source.lisp> pairs");
    }
    let mut paths = Vec::new();
    for pair in args[4..].as_chunks::<2>().0 {
        if pair[0] != "--binding-source"
            || std::path::Path::new(&pair[1])
                .extension()
                .and_then(|ext| ext.to_str())
                != Some("lisp")
        {
            return Err("only --binding-source <source.lisp> is permitted");
        }
        paths.push(pair[1].as_str());
    }
    Ok(paths)
}

fn read_t5m_binding_sources(paths: &[&str]) -> Result<Vec<String>, String> {
    paths
        .iter()
        .map(|path| {
            fs::read_to_string(path)
                .map_err(|error| format!("read SENS binding source {path}: {error}"))
        })
        .collect()
}

/// Створити фізичний T5M та читабельні біти за одним SENS-reader/Zig
/// roundtrip. Жодних Python-міграторів, JSON-квитанцій чи другого кодека.
type T5mMintPairRequest<'a> = Option<Result<(&'a str, &'a str, Vec<&'a str>), &'static str>>;

fn t5m_mint_pair_request(args: &[String]) -> T5mMintPairRequest<'_> {
    if !args.iter().skip(1).any(|part| part == "--t5m-mint-pair") {
        return None;
    }
    if args.len() < 4 || args[1] != "--t5m-mint-pair" {
        return Some(Err("usage: sens --t5m-mint-pair <source.lisp> <output.sens> [--binding-source <source.lisp> ...]"));
    }
    let source = std::path::Path::new(&args[2]);
    let physical = std::path::Path::new(&args[3]);
    if source.extension().and_then(|ext| ext.to_str()) != Some("lisp")
        || physical.extension().and_then(|ext| ext.to_str()) != Some("sens")
    {
        return Some(Err("--t5m-mint-pair requires .lisp and .sens paths"));
    }
    Some(t5m_binding_paths(args).map(|bindings| (&args[2][..], &args[3][..], bindings)))
}

/// Нові фізичні файли публікуємо разом або відкидаємо створене нами.
/// Публікація в існуючі tracked-файли робиться окремо після SENS-eval.
fn write_new_t5m_pair(path: &str, bytes: &[u8], view: &str) -> Result<(), String> {
    let physical = std::path::Path::new(path);
    let readable = physical.with_extension("");
    let mut binary = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(physical)
        .map_err(|error| format!("T5M_PAIR_CARRIER_CREATE: {error}"))?;
    if let Err(error) = binary.write_all(bytes).and_then(|_| binary.sync_all()) {
        drop(binary);
        let _ = fs::remove_file(physical);
        return Err(format!("T5M_PAIR_CARRIER_WRITE: {error}"));
    }
    drop(binary);
    let mut readable_file = match fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&readable)
    {
        Ok(file) => file,
        Err(error) => {
            let _ = fs::remove_file(physical);
            return Err(format!("T5M_PAIR_VIEW_CREATE: {error}"));
        }
    };
    if let Err(error) = readable_file
        .write_all(view.as_bytes())
        .and_then(|_| readable_file.sync_all())
    {
        drop(readable_file);
        // Видаляємо лише об'єкти, створені цим викликом.
        let _ = fs::remove_file(&readable);
        let _ = fs::remove_file(physical);
        return Err(format!("T5M_PAIR_VIEW_WRITE: {error}"));
    }
    Ok(())
}

type T5mPairRequest<'a> = Option<Result<(&'a str, &'a str, Vec<&'a str>, bool), &'static str>>;

/// Парне виконання дозволяє читати D24+ з реальних байтів Zig T5M,
/// лише якщо український Lisp свідчить ТОЧНО ту саму доменну послідовність.
/// Це не дозвіл трактувати довільний W24 за числову ідентичність.
fn t5m_pair_request(
    args: &[String],
) -> T5mPairRequest<'_> {
    if !args.iter().skip(1).any(|item| item == "--t5m-pair") {
        return None;
    }
    if args.len() < 4 || args[1] != "--t5m-pair" {
        return Some(Err("usage: sens --t5m-pair <ukrainian-source.lisp> <physical.sens> [--binding-source <source.lisp> ...]"));
    }
    let source = std::path::Path::new(&args[2]);
    let physical = std::path::Path::new(&args[3]);
    if source.extension().and_then(|part| part.to_str()) != Some("lisp")
        || physical.extension().and_then(|part| part.to_str()) != Some("sens")
    {
        return Some(Err(
            "--t5m-pair requires .lisp source and physical .sens bytes",
        ));
    }
    let mut bindings = Vec::new();
    let mut load_core4 = false;
    let mut index = 4;
    while index < args.len() {
        match args[index].as_str() {
            "--core4-runtime" => {
                if load_core4 {
                    return Some(Err("--core4-runtime may be specified only once"));
                }
                load_core4 = true;
                index += 1;
            }
            "--binding-source" => {
                let Some(path) = args.get(index + 1) else {
                    return Some(Err("--binding-source requires a .lisp path"));
                };
                if std::path::Path::new(path)
                    .extension()
                    .and_then(|part| part.to_str())
                    != Some("lisp")
                {
                    return Some(Err("only --binding-source <source.lisp> is permitted"));
                }
                bindings.push(path.as_str());
                index += 2;
            }
            _ => return Some(Err("unsupported --t5m-pair option")),
        }
    }
    Some(Ok((&args[2][..], &args[3][..], bindings, load_core4)))
}

/// Фізичний вхід: байти -> стерильний Zig ABI v2 -> точні слова SENS.
/// T5M зберігає ширину слова, доки правила SENS не встановлять D1–D10
/// або числову родину D24+; обмеження BE3/W1–W9 тут немає.
fn decode_physical_t5m_words(bytes: &[u8]) -> Result<Vec<sens::ExactDomainWord>, String> {
    #[cfg(feature = "zig-transport")]
    {
        // Явний `return` — контракт коридору: check_sterile_zig_corridor вимагає
        // саме `return zig_transport::decode_t5m_exact_words(bytes)?`, щоб символ
        // у коментарі не вважався живим перетином Zig. Хвостовий вираз гейт не приймає.
        #[allow(clippy::needless_return)]
        return zig_transport::decode_t5m_exact_words(bytes)?
            .into_iter()
            .map(|word| sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits))
            .collect()
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        Err("physical .sens requires the Zig transport corridor; no Rust fallback".into())
    }
}

/// Єдиний фізичний шлях: T5M -> точні ідентичності SENS -> бінарний evaluator.
/// Тут немає людських назв чи сумісного восьмибітного читача; фізичний файл
/// не отримує неявних host-можливостей або Core4.
fn eval_physical_t5(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    let words = decode_physical_t5m_words(bytes)?;
    let program = sens::PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|err| format!("exact SENS domain reader rejected: {err}"))?;

    // Фізично типізований шлях D1–D10/D24+ не має неявного Lisp macro
    // surface. Session::default() loads lib/macro.lisp on EVERY invocation;
    // that bootstrap dominates tiny admitted binary programs and is neither
    // needed nor authorized for this capability-free physical route.
    // Textual .lisp and the explicit sens-trit eval-core4 remain unchanged.
    let mut pure = Session::bare();
    // D5:00011 MACRO вже має ратифікований вузький механізм SENS.
    // Не завантажуємо жодного текстового Core або host-можливостей.
    sens::install_ratified_d5_macro_mechanism(&pure);
    program
        .execute(&mut pure)
        .map_err(|err| format!("current SENS execution rejected: {err}"))
}

#[cfg(feature = "benchmark-ast-visits")]
fn count_physical_ast_nodes(expression: &sens::Expr) -> usize {
    let children = match &expression.kind {
        sens::ExprKind::List(items)
        | sens::ExprKind::Call(_, items)
        | sens::ExprKind::DomainCall(_, items) => items.iter().map(count_physical_ast_nodes).sum(),
        sens::ExprKind::Pair(head, tail) => {
            count_physical_ast_nodes(head) + count_physical_ast_nodes(tail)
        }
        _ => 0,
    };
    1 + children
}

#[cfg(feature = "benchmark-ast-visits")]
fn eval_physical_t5_with_benchmark_metrics(
    bytes: &[u8],
    load_core4: bool,
) -> Result<(sens::EvalResult, usize, u64), String> {
    let words = decode_physical_t5m_words(bytes)?;
    let program = sens::PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|err| format!("exact SENS domain reader rejected: {err}"))?;
    let ast_nodes = program.forms().iter().map(count_physical_ast_nodes).sum();
    let mut pure = Session::bare();
    if load_core4 {
        bootstrap_core(&mut pure, CliCore::Core4).map_err(|error| error.to_string())?;
    }
    sens::install_ratified_d5_macro_mechanism(&pure);
    let (result, eval_visits) = program
        .execute_with_visit_count(&mut pure)
        .map_err(|err| format!("current SENS execution rejected: {err}"))?;
    Ok((result, ast_nodes, eval_visits))
}

/// CLI receives only the committed physical linter T5M carrier from Zig.
fn linter_t5m_asset_zig_only() -> Result<Vec<u8>, String> {
    #[cfg(feature = "zig-transport")]
    {
        zig_transport::linter_t5m_bytes()
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: linter T5M asset requires Zig; no Rust fallback".into())
    }
}

/// An exact source carrier through Zig. Interpretation stays SENS-owned.
fn contract_source_zig_only() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = zig_transport::contract_source_bytes()?;
        String::from_utf8(bytes).map_err(|e| format!("ZIG_CONTRACT_CARRIER UTF-8 error: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: language contract requires Zig; no Rust source fallback".into())
    }
}

/// Explicit REPL-only switches must not be confused with the implicit
/// Ukrainian REPL default: file execution never requested a surface.
fn explicit_repl_surface_flag(args: &[String]) -> bool {
    args.iter()
        .skip(1)
        .any(|arg| arg == "--surface" || arg.starts_with("--surface="))
}

fn main() {
    // Physical .sens is the exact binary entrypoint and needs no legacy
    // bootstrap or ambient host capabilities. Reject extra flags instead of
    // silently interpreting its bytes as textual Lisp.
    let raw_args: Vec<String> = env::args().collect();
    // Binary identity metadata must not depend on Lisp library bootstrap.
    // This reports the actual Cargo-compiled executable's pinned version.
    if raw_args.len() == 2 && matches!(raw_args[1].as_str(), "--version" | "-V" | "-v") {
        println!("sens {}", env!("CARGO_PKG_VERSION"));
        return;
    }
    if let Some(request) = t5m_files_request(&raw_args) {
        let result = match request {
            Ok(paths) => paths
                .iter()
                .map(|path| {
                    fs::read_to_string(path)
                        .map(|source| (path.as_str(), source))
                        .map_err(|error| format!("read T5M source {path}: {error}"))
                })
                .collect::<Result<Vec<_>, _>>()
                .and_then(|sources| {
                    let borrowed = sources
                        .iter()
                        .map(|(path, source)| (*path, source.as_str()))
                        .collect::<Vec<_>>();
                    #[cfg(feature = "zig-transport")]
                    {
                        repl::eval_t5m_source_files(&borrowed)
                    }
                    #[cfg(not(feature = "zig-transport"))]
                    {
                        let _ = borrowed;
                        Err("--t5m-files requires the Zig T5M transport corridor".into())
                    }
                }),
            Err(message) => Err(message.to_owned()),
        };
        match result {
            Ok(result) => {
                for output in result.output {
                    println!("{output}");
                }
                println!("{}", result.value);
            }
            Err(error) => {
                eprintln!("sens: T5M multi-file execution failed: {error}");
                process::exit(1);
            }
        }
        return;
    }
    if let Some(request) = t5m_file_request(&raw_args) {
        let result = match request {
            Ok(filename) => fs::read_to_string(filename)
                .map_err(|error| format!("read Ukrainian Lisp source: {error}"))
                .and_then(|source| {
                    #[cfg(feature = "zig-transport")]
                    {
                        repl::eval_t5m_source_file(&source)
                    }
                    #[cfg(not(feature = "zig-transport"))]
                    {
                        let _ = source;
                        Err("--t5m-file requires the Zig T5M transport corridor".into())
                    }
                }),
            Err(message) => Err(message.to_owned()),
        };
        match result {
            Ok(result) => {
                for output in result.output {
                    println!("{output}");
                }
                println!("{}", result.value);
            }
            Err(error) => {
                eprintln!("sens: T5M file execution failed: {error}");
                process::exit(1);
            }
        }
        return;
    }
    if let Some(request) = t5m_mint_request(&raw_args) {
        let result = match request {
            Ok((source_path, physical_path)) => fs::read_to_string(source_path)
                .map_err(|error| format!("read Ukrainian Lisp source: {error}"))
                .and_then(|source| {
                    #[cfg(feature = "zig-transport")]
                    {
                        repl::mint_t5m_source_file(&source)
                    }
                    #[cfg(not(feature = "zig-transport"))]
                    {
                        let _ = source;
                        Err("--t5m-mint requires the Zig T5M transport corridor".into())
                    }
                })
                .and_then(|bytes| {
                    fs::write(physical_path, bytes)
                        .map_err(|error| format!("write physical T5M .sens: {error}"))
                }),
            Err(message) => Err(message.to_owned()),
        };
        if let Err(error) = result {
            eprintln!("sens: T5M mint failed: {error}");
            process::exit(1);
        }
        return;
    }
    if let Some(request) = t5m_mint_pair_request(&raw_args) {
        let result = match request {
            Ok((source_path, physical_path, binding_paths)) => fs::read_to_string(source_path)
                .map_err(|error| format!("read Ukrainian Lisp source: {error}"))
                .and_then(|source| {
                    let bindings = read_t5m_binding_sources(&binding_paths)?;
                    #[cfg(feature = "zig-transport")]
                    {
                        repl::mint_t5m_source_pair_with_bindings(&source, &bindings)
                    }
                    #[cfg(not(feature = "zig-transport"))]
                    {
                        let _ = (source, bindings);
                        Err("--t5m-mint-pair requires Zig T5M transport".into())
                    }
                })
                .and_then(|(bytes, view)| write_new_t5m_pair(physical_path, &bytes, &view)),
            Err(message) => Err(message.to_owned()),
        };
        if let Err(error) = result {
            eprintln!("sens: T5M pair mint failed: {error}");
            process::exit(1);
        }
        return;
    }
    if let Some(request) = t5m_pair_request(&raw_args) {
        let result = match request {
            Ok((source_path, physical_path, binding_paths, load_core4)) => fs::read_to_string(source_path)
                .map_err(|error| format!("read Ukrainian Lisp source: {error}"))
                .and_then(|source| {
                    let physical = fs::read(physical_path)
                        .map_err(|error| format!("read physical .sens: {error}"))?;
                    let bindings = read_t5m_binding_sources(&binding_paths)?;
                    #[cfg(feature = "zig-transport")]
                    {
                        if load_core4 {
                            repl::eval_t5m_paired_file_with_core4(&source, &physical, &bindings)
                        } else {
                            repl::eval_t5m_paired_file_with_bindings(&source, &physical, &bindings)
                        }
                    }
                    #[cfg(not(feature = "zig-transport"))]
                    {
                        let _ = (source, physical, bindings);
                        Err("--t5m-pair requires the Zig T5M transport corridor".into())
                    }
                }),
            Err(message) => Err(message.to_owned()),
        };
        match result {
            Ok(result) => {
                for output in result.output {
                    println!("{output}");
                }
                println!("{}", result.value);
            }
            Err(error) => {
                eprintln!("sens: T5M physical pair execution failed: {error}");
                process::exit(1);
            }
        }
        return;
    }
    if let Some(request) = physical_t5_benchmark_request(&raw_args) {
        #[cfg(feature = "benchmark-ast-visits")]
        let result = match request {
            Ok((filename, load_core4)) => fs::read(filename)
                .map_err(|err| format!("read physical .sens: {err}"))
                .and_then(|bytes| eval_physical_t5_with_benchmark_metrics(&bytes, load_core4)),
            Err(message) => Err(message.to_owned()),
        };
        #[cfg(not(feature = "benchmark-ast-visits"))]
        let result: Result<(sens::EvalResult, usize, u64), String> = match request {
            Ok(_) => {
                Err("--benchmark-physical requires the benchmark-ast-visits build feature".into())
            }
            Err(message) => Err(message.to_owned()),
        };
        match result {
            Ok((result, ast_nodes, eval_visits)) => {
                for output in result.output {
                    println!("{output}");
                }
                println!("{}", result.value);
                eprintln!(
                    "SENS_BINARY_BENCH AST_NODES={ast_nodes} EVAL_VISITS={eval_visits} RESULT={}",
                    result.value
                );
            }
            Err(error) => {
                eprintln!("sens: binary benchmark failed: {error}");
                process::exit(1);
            }
        }
        return;
    }
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
    let (args, sens_loop) = extract_sens_loop(args);
    let allowed_for_tcp = allowed.clone();
    // Plain `f64`s, not a `Value` — `run_tcp_repl_sexpr` spawns one thread
    // per connection, and `Value`'s `Rc`-based sharing isn't `Send`; each
    // connection rebuilds its own `contract_version` `Value` locally from
    // these two numbers instead of cloning a shared one across threads.
    let (contract_major, contract_minor) = {
        let contract_source = match contract_source_zig_only() {
            Ok(source) => source,
            Err(error) => {
                eprintln!("sens: {error}");
                process::exit(2);
            }
        };
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

    // Вибір Core3/Core4 і декодування T5M належать завантажувачу SENS.
    // Rust CLI не вбудовує текст Core4 і не відтворює його семантику.
    if let Err(e) = bootstrap_core(&mut session, cli_core) {
        let label = match cli_core {
            CliCore::Core3 => "Core3",
            CliCore::Core4 => "Core4",
        };
        eprintln!(
            "Error loading bootstrap {label}: {}",
            e.render("<SENS core bootstrap>")
        );
        process::exit(1);
    }

    // Time is a language-owned semantic layer, not part of the closed core.
    // Load it explicitly after core so local CLI/REPL sessions keep `utc-now`
    // even after the old Rust calendar builtin is removed.
    if let Err(e) = sens::load_time_library(&mut session) {
        eprintln!(
            "Error loading time bootstrap: {}",
            e.render("<T5M time bootstrap>")
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
            e.render("<T5M process bootstrap>")
        );
        process::exit(1);
    }

    // File text policy is language-owned the same way: the host now exposes
    // only `read-file-bytes`/`write-file-bytes`, deletion-audit follow-up
    // 2026-09-12 (FS-CAPABILITY-UTF8-POLICY-MIGRATION).
    if let Err(e) = sens::load_fs_library(&mut session) {
        eprintln!(
            "Error loading filesystem T5M bootstrap: {}",
            e.render("<T5M filesystem bootstrap>")
        );
        process::exit(1);
    }

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
            println!("Textual compatibility source: .lisp and historical aliases; physical .sens is packed T5M, not UTF-8 Lisp.");
            println!("  sens program.sens            Run exact physical T5M with pure SENS (no implicit Core4/host effects)");
            println!("  sens --t5m-file program.lisp Run Ukrainian Lisp source through Zig T5M and execute its SENS words");
            println!("  sens --t5m-files a.lisp b.lisp Load ordered Lisp parts through T5M in one SENS session");
            println!("  sens --t5m-mint program.lisp program.sens Mint physical Zig/T5M from the same SENS reader as --t5m-pair");
            println!("  sens-trit open program.sens  Display exact binary words without running");
            println!("\nOptions:");
            println!("  lsp                          Run the Language Server (LSP over stdio)");
            println!("  install [--profile four-kernel]  Automatically bootstrap the execution-island runtimes for the current host");
            println!("  islands plan|install|status      Inspect, install, or observe execution islands without semantic admission");
            println!("  -V, --version               Print version information");
            println!("  -h, --help                  Print help information");
            println!("  --surface=uk|en|sa|core      Start the interactive REPL with this programming surface");
            println!("  --sens-loop                  Initialize repl-core state; interactive forms still use Zig T5M → binary SENS");
            println!("  --core=3|4                    Explicitly select Core3 laboratory or default Core4 before evaluation");
            println!(
                "  --allow-process=a,b,c        TCP/oracle only: allow exactly these process names"
            );
            println!("  --lint                        Run the linter on the provided file and exit with non-zero if thresholds are exceeded");
            println!("  --oracle-check <file|->       Parse-only agent preflight; '-' reads stdin and emits oracle-result-1");
            println!("  --oracle-help [tool]          List common agent tools or explain one from the WSM Guard directory");
            println!("  --tcp[=PORT]                 Serve the REPL over TCP on 127.0.0.1 (default port 9999) instead of stdio");
            println!("  --protocol=sexpr              With --tcp: strict (request (id) (op) (source)) / (response ...) envelope, no banner/prompt");
            println!("  --connect=HOST:PORT            P2P client: forward one sexpr request from stdin to a peer's TCP REPL, print the response");
            return;
        }

        if arg == "--tcp" || arg.starts_with("--tcp=") {
            let port = arg
                .strip_prefix("--tcp=")
                .and_then(|p| p.parse::<u16>().ok()) // projection-human: TCP port is human transport configuration, not a SENS domain identity.
                .unwrap_or(9999);
            if sexpr_protocol {
                run_tcp_repl_sexpr(port, allowed_for_tcp, contract_major, contract_minor);
            } else {
                run_tcp_repl(port, &allowed_for_tcp);
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

            // Load only the committed physical T5M library through Zig;
            // SENS decodes and executes it in the existing Core4 session.
            let linter_asset = match linter_t5m_asset_zig_only() {
                Ok(physical) => physical,
                Err(error) => {
                    eprintln!("Error loading linter T5M through Zig: {error}");
                    process::exit(2);
                }
            };
            if let Err(error) =
                repl::execute_zig_t5m_asset(&linter_asset, "SENS linter", &mut session)
            {
                eprintln!("Error executing linter T5M: {error}");
                process::exit(1);
            }

            match fs::read_to_string(filename) {
                Ok(source) => {
                    let lint_call_src = format!(
                        "(аналіз-перевірити (як-є (begin {source}\n)) (як-є ((max-size . 5000) (max-nesting . 50) (max-complexity . 100) (max-globals . 500) (max-effects . 10))))"
                    );
                    match repl::eval_t5m_source_in_session_preserving_result(
                        &lint_call_src,
                        &mut session,
                        repl::ReplSurface::UkrainianFull,
                    ) {
                        Ok(result) => {
                            if let Value::Nil = result.value {
                                println!("Linter passed: {}", filename);
                                return;
                            }
                            eprintln!("Linter violations found in {}:", filename);
                            eprintln!("{}", result.value);
                            process::exit(1);
                        }
                        Err(error) => {
                            eprintln!("Error running linter through T5M for {filename}: {error}");
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

        // Only an EXPLICIT REPL option is invalid in file mode. The
        // UkrainianFull default is a REPL preference, not a file-mode flag.
        if explicit_repl_surface_flag(&raw_args) || sens_loop {
            eprintln!("sens: --surface / --sens-loop are available only when starting the interactive REPL");
            process::exit(2);
        }

        // Run file
        let filename = arg;

        // Аргументи після шляху передаються як список рядків у змінну
        // української поверхні `параметри-командного-рядка`, до виконання.
        let arguments = Value::list(
            args[2..]
                .iter()
                .map(|arg| Value::String(Rc::from(arg.as_str()))),
        );
        session.environment.define("*argv*", arguments.clone());
        session
            .environment
            .define("параметри-командного-рядка", arguments);

        match fs::read_to_string(filename) {
            Ok(source) => {
                #[cfg(feature = "zig-transport")]
                let result = repl::eval_t5m_source_in_session(
                    &source,
                    &mut session,
                    repl::ReplSurface::UkrainianFull,
                );
                #[cfg(not(feature = "zig-transport"))]
                let result: Result<sens::EvalResult, String> = Err(
                    "RUST_ZIG_ONLY: Lisp file execution requires the Zig T5M corridor; no Rust fallback".into(),
                );

                match result {
                    Ok(result) => {
                        for out in result.output {
                            println!("{}", out);
                        }
                        println!("{}", result.value);
                    }
                    Err(error) => {
                        // Вивід до SENS-помилки не губиться.
                        for out in session.environment.output_take_new() {
                            println!("{}", out);
                        }
                        eprintln!("sens: T5M source execution failed: {error}");
                        process::exit(1);
                    }
                }
            }
            Err(e) => {
                eprintln!("Error reading file {}: {}", filename, e);
                process::exit(1);
            }
        }
    } else {
        // REPL mode
        repl::run_repl(session, repl_surface, sens_loop);
    }
}


