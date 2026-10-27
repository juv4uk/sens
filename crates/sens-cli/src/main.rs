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
#[cfg(test)]
fn parse_human_lisp_file(source: &str) -> Result<Vec<sens::Expr>, sens::LanguageError> {
    let parsed = parse(source)?;
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

#[cfg(test)]
mod core_profile_bootstrap_tests {
    use super::*;

    #[cfg(all(feature = "zig-transport", feature = "benchmark-ast-visits"))]
    #[test]
    fn physical_binary_metrics_come_from_the_sens_evaluator() {
        let (result, ast_nodes, eval_visits) =
            eval_physical_t5_with_benchmark_metrics(&[0x63, 0x89, 0x06, 0xa1])
                .expect("physical T5M enters Zig and executes as binary SENS");
        let _ = result; // Host observes evaluator execution, not SENS value truth.
        assert!(ast_nodes > 0);
        assert!(eval_visits > 0);
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn native_t5m_pair_mint_matches_zig_and_executes_without_python() {
        let source = "(як-є ())";
        let (physical, view) = repl::mint_t5m_source_pair(source)
            .expect("SENS reader + pinned Zig must mint the physical pair");
        let restored = zig_transport::decode_t5m_exact_words(&physical)
            .expect("Zig must decode its own carrier");
        let expected = restored
            .iter()
            .map(|word| {
                word.bits
                    .iter()
                    .map(|bit| if *bit == 0 { '0' } else { '1' })
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join(" ")
            + "\n";
        assert_eq!(view, expected, "view must use exact Zig-returned words");
        repl::eval_t5m_paired_file(source, &physical)
            .expect("real SENS evaluator must execute source-verified bytes");

        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("system time")
            .as_nanos();
        let dir =
            std::env::temp_dir().join(format!("sens-native-pair-{}-{unique}", std::process::id()));
        fs::create_dir(&dir).expect("create isolated output directory");
        let path = dir.join("single.sens");
        let result = write_new_t5m_pair(
            path.to_str().expect("utf8 temporary path"),
            &physical,
            &view,
        );
        assert!(result.is_ok(), "publish exact carrier and view: {result:?}");
        assert_eq!(fs::read(&path).unwrap(), physical);
        assert_eq!(fs::read(path.with_extension("")).unwrap(), view.as_bytes());
        assert!(
            write_new_t5m_pair(path.to_str().unwrap(), &physical, &view,).is_err(),
            "cannot overwrite a committed pair"
        );
        // Дійсне SENS-означення перевіряємо тим самим Zig/T5M.
        let bindings = vec!["(визначити помічник (функція (аргумент) аргумент))".to_owned()];
        let source = "(помічник (як-є ()))";
        let (bound_physical, _) = repl::mint_t5m_source_pair_with_bindings(source, &bindings)
            .expect("SENS must resolve a preload-defined function without Python or JSON");
        repl::eval_t5m_paired_file_with_bindings(source, &bound_physical, &bindings)
            .expect("the physically paired program runs with native SENS definitions");
        assert!(
            repl::eval_t5m_paired_file_with_bindings("(як-є (()))", &bound_physical, &bindings,)
                .is_err(),
            "another source must not reuse the T5M carrier"
        );
        let args = [
            "sens",
            "--t5m-pair",
            "program.lisp",
            "program.sens",
            "--binding-source",
            "helper.lisp",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect::<Vec<_>>();
        assert_eq!(
            t5m_pair_request(&args).unwrap().unwrap().2,
            vec!["helper.lisp"]
        );
        let mut invalid = args.clone();
        invalid[4] = "--python-resolver".into();
        assert!(t5m_pair_request(&invalid).unwrap().is_err());
        fs::remove_dir_all(&dir).expect("clean test fixtures");
    }

    #[test]
    fn file_mode_uses_human_decimal_source_not_legacy_encoded_literals() {
        let parsed = parse_human_lisp_file("(додати -2 5)").expect("підписаний десятковий операнд");
        let sens::ExprKind::List(items) = &parsed[0].kind else {
            panic!("очікувано один виклик D5");
        };
        let digits: Vec<_> = items
            .iter()
            .filter_map(|item| match &item.kind {
                sens::ExprKind::BinaryNumber(number) => Some(number.to_decimal_string()), // projection-human
                _ => None,
            })
            .collect();
        assert_eq!(digits, ["-2", "5"]);
    }

    #[test]
    fn implicit_ukrainian_repl_default_does_not_reject_file_mode() {
        let file_args = vec!["sens".to_owned(), "програма.lisp".to_owned()];
        let (_, default_surface) =
            extract_repl_surface(file_args.clone()).expect("implicit surface default");
        assert_eq!(default_surface, repl::ReplSurface::UkrainianFull);
        assert!(
            !explicit_repl_surface_flag(&file_args),
            "default REPL preference is not a user-requested file flag"
        );

        let explicit = vec![
            "sens".to_owned(),
            "--surface=укр".to_owned(),
            "програма.lisp".to_owned(),
        ];
        assert!(explicit_repl_surface_flag(&explicit));
        assert!(explicit_repl_surface_flag(&[
            "sens".to_owned(),
            "--surface".to_owned(),
            "укр".to_owned(),
            "програма.lisp".to_owned()
        ]));
    }

    #[test]
    fn default_repl_surface_is_full_ukr_and_compact_remains_explicit() {
        let (args, surface) =
            extract_repl_surface(vec!["sens".to_owned()]).expect("default surface");
        assert_eq!(args, vec!["sens".to_owned()]);
        assert_eq!(surface, repl::ReplSurface::UkrainianFull);

        let (_, compact) = extract_repl_surface(vec!["sens".to_owned(), "--surface=ук".to_owned()])
            .expect("explicit compact surface");
        assert_eq!(compact, repl::ReplSurface::Ukrainian);

        let (_, core) = extract_repl_surface(vec!["sens".to_owned(), "--surface=core".to_owned()])
            .expect("explicit core surface");
        assert_eq!(core, repl::ReplSurface::Core);

        let (_, no_args) = extract_repl_surface(Vec::new()).expect("empty arg vector");
        assert_eq!(no_args, repl::ReplSurface::UkrainianFull);
    }

    #[test]
    fn t5m_source_mode_requires_ukrainian_lisp_not_physical_bytes() {
        let admitted = vec![
            "sens".to_owned(),
            "--t5m-file".to_owned(),
            "програма.lisp".to_owned(),
        ];
        assert_eq!(t5m_file_request(&admitted), Some(Ok("програма.lisp")));
        for invalid in ["програма.sens", "програма.lisp.sens", "програма"] {
            let args = vec![
                "sens".to_owned(),
                "--t5m-file".to_owned(),
                invalid.to_owned(),
            ];
            assert!(
                matches!(t5m_file_request(&args), Some(Err(_))),
                "physical/untyped file must not enter textual Lisp parser: {invalid}"
            );
        }
        let incomplete = vec!["sens".to_owned(), "--t5m-file".to_owned()];
        assert!(matches!(t5m_file_request(&incomplete), Some(Err(_))));
    }

    #[test]
    fn t5m_files_mode_accepts_ordered_lisp_sources_only() {
        let valid = vec![
            "sens".to_owned(),
            "--t5m-files".to_owned(),
            "lib/core4-parts/core4-language.lisp".to_owned(),
            "lib/core4-parts/core4-d6.lisp".to_owned(),
        ];
        assert_eq!(t5m_files_request(&valid), Some(Ok(&valid[2..])));

        let invalid = vec![
            "sens".to_owned(),
            "--t5m-files".to_owned(),
            "lib/core4-parts/core4-language.lisp".to_owned(),
            "lib/core4.sens".to_owned(),
        ];
        assert!(matches!(t5m_files_request(&invalid), Some(Err(_))));

        let incomplete = vec!["sens".to_owned(), "--t5m-files".to_owned()];
        assert!(matches!(t5m_files_request(&incomplete), Some(Err(_))));
    }

    #[test]
    fn explicit_physical_t5_is_a_pure_binary_entrypoint_not_an_alias() {
        let arguments = vec!["sens".to_owned(), "program.sens".to_owned()];
        assert_eq!(physical_t5_request(&arguments), Some(Ok("program.sens")));
        let legacy = vec!["sens".to_owned(), "program.lisp".to_owned()];
        assert_eq!(physical_t5_request(&legacy), None);
        let flags = vec![
            "sens".to_owned(),
            "--core=4".to_owned(),
            "program.sens".to_owned(),
        ];
        assert!(matches!(physical_t5_request(&flags), Some(Err(_))));
    }

    #[test]
    fn physical_benchmark_accepts_only_an_explicit_sens_binary() {
        let args = vec![
            "sens".to_owned(),
            "--benchmark-physical".to_owned(),
            "program.sens".to_owned(),
        ];
        assert_eq!(
            physical_t5_benchmark_request(&args),
            Some(Ok(("program.sens", false)))
        );
        let core4 = vec![
            "sens".to_owned(),
            "--benchmark-physical".to_owned(),
            "program.sens".to_owned(),
            "--core4-runtime".to_owned(),
        ];
        assert_eq!(
            physical_t5_benchmark_request(&core4),
            Some(Ok(("program.sens", true)))
        );
        let textual = vec![
            "sens".to_owned(),
            "--benchmark-physical".to_owned(),
            "program.lisp".to_owned(),
        ];
        assert!(matches!(
            physical_t5_benchmark_request(&textual),
            Some(Err(_))
        ));
        let extra = vec![
            "sens".to_owned(),
            "--benchmark-physical".to_owned(),
            "program.sens".to_owned(),
            "--surface=укр".to_owned(),
        ];
        assert!(matches!(
            physical_t5_benchmark_request(&extra),
            Some(Err(_))
        ));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn physical_t5_enters_canonical_binary_reader_not_text_lisp() {
        // SENS owns exact source words and D2 admission. The Zig turnstile,
        // rather than a Rust fixture embed or Rust T5 decoder, mints bytes.
        let source = "10 001 00 000 01";
        let tokens = sens::parse_binary_source_words(source).expect("SENS exact binary source");
        let words: Vec<_> = tokens.into_iter().map(|token| token.word).collect();
        let forms = sens::parse_canonical_word_sequence(&words).expect("SENS canonical D2 program");
        assert!(!forms.is_empty());

        let physical =
            zig_transport::encode_t5m_direct(&words).expect("only Zig may create physical T5M");
        assert_eq!(physical, [0x63, 0x89, 0x06, 0xa1]);
        // The exact-byte checked Zig adapter is used by sens-trit in
        // production. Exercise that same adapter in this sens test binary:
        // it must accept the unchanged carrier and reject one flipped bit.
        let checked = zig_transport::verify_t5m_encoding(&words, &physical)
            .expect("Zig physical carrier matches the admitted exact words");
        assert_eq!(checked, physical);
        let mut one_bit_mutant = physical.clone();
        one_bit_mutant[0] ^= 0b0000_0001;
        let error = zig_transport::verify_t5m_encoding(&words, &one_bit_mutant)
            .expect_err("mutated physical T5M may not match the original words");
        assert!(
            error.contains("physical byte"),
            "unexpected mismatch: {error}"
        );
        let restored =
            decode_physical_t5m_words(&physical).expect("physical T5M re-enters through Zig ABI");
        let expected: Vec<_> = words
            .iter()
            .map(|word| (word.width(), word.packed_bits()))
            .collect();
        let observed: Vec<_> = restored
            .iter()
            .map(|word| match word {
                sens::ExactDomainWord::Identity(identity) => {
                    (identity.width(), identity.packed_bits())
                }
                sens::ExactDomainWord::Number(number) => {
                    let bits = number.exact_numeric_domain_bits().expect("qualified D24+");
                    let payload = bits
                        .iter()
                        .fold(0u16, |value, &bit| (value << 1) | u16::from(bit));
                    (bits.len(), payload)
                }
            })
            .collect();
        assert_eq!(
            observed, expected,
            "exact-width domain identities survive Zig"
        );
        assert!(sens::PhysicalT5Program::from_exact_domain_words(&restored).is_ok());
        // A malformed physical carrier is rejected before SENS D2 evaluation.
        assert!(decode_physical_t5m_words(&[0xf3]).is_err());
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn physical_main_binary_passes_through_zig_abi_v2_before_sens_admission() {
        // This canonical T5M carrier holds five exact D2/D3 words.
        // Zig transports [width, MSB, LSB]; SENS alone judges D2 and eval.
        let physical = [0x63, 0x89, 0x06, 0xa1];
        let words = decode_physical_t5m_words(&physical).expect("Zig ABI v2 ingress");
        let widths: Vec<_> = words
            .iter()
            .map(|word| match word {
                sens::ExactDomainWord::Identity(identity) => identity.width(),
                sens::ExactDomainWord::Number(number) => number.numeric_domain_width().unwrap(),
            })
            .collect();
        let bits: Vec<_> = words
            .iter()
            .map(|word| match word {
                sens::ExactDomainWord::Identity(identity) => identity.packed_bits(),
                sens::ExactDomainWord::Number(number) => number
                    .exact_numeric_domain_bits()
                    .unwrap()
                    .iter()
                    .fold(0u16, |value, &bit| (value << 1) | u16::from(bit)),
            })
            .collect();
        assert_eq!(widths, [2, 3, 2, 3, 2]);
        assert_eq!(bits, [2, 1, 0, 0, 1]);
        assert!(sens::PhysicalT5Program::from_exact_domain_words(&words).is_ok());
        // Не обмежуємося успіхом декодера: саме фізичні байти мають
        // пройти SENS D2 reader та справжнє виконання D3 QUOTE.
        let executed = eval_physical_t5(&physical)
            .expect("physical .sens must execute through the SENS reader/evaluator");
        let _ = executed; // SENS owns the semantic verdict.
        // Malformed physical data must fail before even attempting D2 admission.
        // Two zero physical bytes are a valid all-zero T5M stream, not a
        // malformed carrier. Empty input is the actual third invalid case.
        for invalid in [&[0xf3][..], &[0xf2][..], &[][..]] {
            assert!(
                decode_physical_t5m_words(invalid).is_err(),
                "invalid {invalid:?}"
            );
            assert!(
                eval_physical_t5(invalid).is_err(),
                "invalid carrier executed: {invalid:?}"
            );
        }
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn physical_main_refuses_to_bypass_unavailable_zig_transport() {
        let physical = [0x63, 0x89, 0x06, 0xa1];
        let error =
            decode_physical_t5m_words(&physical).expect_err("no Zig means no .sens ingress");
        assert!(error.contains("no Rust fallback"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_transports_only_physical_t5m() {
        let raw = linter_t5m_asset_zig_only().expect("live Zig C ABI must carry linter T5M");
        let words = zig_transport::decode_t5m_exact_words(&raw)
            .expect("physical T5M decodes to exact SENS words");
        assert!(!raw.is_empty());
        assert!(!words.is_empty());
        println!(
            "ZIG_LINTER_T5M_CARRIER_PASS bytes={} words={} semantic_admission=CLI_TESTED",
            raw.len(),
            words.len()
        );
        let rust_main = include_str!("main.rs");
        assert!(!rust_main.contains("include_str!(\"../../../lib/linter.lisp\")"));
        assert!(!rust_main.contains("include_bytes!(\"../../../lib/linter.sens\")"));
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_refuses_absent_transport() {
        let error = linter_t5m_asset_zig_only().expect_err("Zig-less Rust must not load linter T5M");
        assert!(error.contains("RUST_ZIG_ONLY"));
        assert!(error.contains("no Rust fallback"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_contract_carrier_preserves_real_original_bytes() {
        let text = contract_source_zig_only().expect("live Zig ABI");
        let bytes = zig_transport::contract_source_bytes().expect("second Zig ABI copy");
        assert_eq!(text.as_bytes(), bytes.as_slice(), "exact contract bytes");
        assert!(
            text.starts_with("; language-contract.lisp"),
            "unexpected asset"
        );
        println!(
            "ZIG_CONTRACT_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_contract_carrier_denies_rust_only_host() {
        let err = contract_source_zig_only().expect_err("no Rust fallback");
        assert!(err.contains("RUST_ZIG_ONLY"));
    }

    #[test]
    fn cli_core_selector_defaults_to_core4_and_accepts_only_3_or_4() {
        let (args, core) = extract_cli_core(vec!["sens".to_string()]).expect("default selector");
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

    #[test]
    fn cli_time_library_bootstraps_from_exact_t5m_words() {
        let mut session = Session {
            environment: Environment::root(),
        };
        bootstrap_core(&mut session, CliCore::Core4).expect("CLI Core4 bootstrap must succeed");

        sens::load_time_library(&mut session)
            .expect("SENS restores and loads the exact T5M time words");
    }
}
