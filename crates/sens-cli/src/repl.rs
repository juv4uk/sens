//! Інтерактивний stdio REPL: історія, interaction-only echo fallback і
//! перемикання програмних поверхонь. `:мова` / `:surface` не є Lisp syntax:
//! це команди оболонки над одним і тим самим семантичним ядром.

mod surface_catalog;

use sens::{
    eval_parsed_expressions_incremental, eval_program, parse, render_error_for_presentation,
    render_value_for_presentation, Environment, ErrorKind, ExprKind, PresentationLanguage, Session,
    Value,
};
use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use std::env;
use std::path::PathBuf;
use std::process;

// REPL-local FFI: other CLI binaries acquire no extra dead_code warnings.
#[cfg(feature = "zig-transport")]
unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_repl_persistent_vector_bytes_copy(dst: *mut u8, cap: usize) -> isize;
    fn sens_zig_repl_time_bytes_copy(dst: *mut u8, cap: usize) -> isize;
    fn sens_zig_repl_epistemic_bytes_copy(dst: *mut u8, cap: usize) -> isize;
    fn sens_zig_meta_eval_bytes_copy(dst: *mut u8, cap: usize) -> isize;
}
#[cfg(feature = "zig-transport")]
fn repl_zig_source(
    copy: unsafe extern "C" fn(*mut u8, usize) -> isize, label: &str,
) -> Result<String, String> {
    if unsafe { sens_zig_codec_abi_version() } != 2 {
        return Err(format!("{label}: Zig ABI version mismatch"));
    }
    let n = unsafe { copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0) };
    if n <= 0 { return Err(format!("{label}: invalid Zig byte length {n}")); }
    let len = usize::try_from(n).map_err(|_| format!("{label}: Zig length overflow"))?;
    if len > 8 * 1024 * 1024 { return Err(format!("{label}: host byte bound exceeded")); }
    let mut bytes = vec![0u8; len];
    let got = unsafe { copy(bytes.as_mut_ptr(), len) };
    if got != n { return Err(format!("{label}: Zig exact copy rejected {got}")); }
    String::from_utf8(bytes).map_err(|err| format!("{label}: UTF-8 source error {err}"))
}
// No Rust include_str! of SENS project source. Zig owns byte transport.
fn surface_prerequisite_sources() -> Result<Vec<(&'static str, String)>, String> {
    #[cfg(feature = "zig-transport")]
    {
        Ok(vec![
            ("persistent-vector.lisp", repl_zig_source(sens_zig_repl_persistent_vector_bytes_copy, "ZIG_REPL_PERSISTENT_VECTOR")?),
            ("time.lisp", repl_zig_source(sens_zig_repl_time_bytes_copy, "ZIG_REPL_TIME")?),
            ("epistemic.lisp", repl_zig_source(sens_zig_repl_epistemic_bytes_copy, "ZIG_REPL_EPISTEMIC")?),
        ])
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: REPL prerequisites require Zig transport".into())
    }
}

// SENS-owned loop state: the meta-environment pair (середовище . остання-форма),
// owned by lib/repl-core.lisp. The native layer only threads it as one binding;
// it never interprets the pair. This is the `--sens-loop` mode's only state.
const SENS_LOOP_STATE: &str = "--sens-loop-стан--";

fn escape_lisp_string(input: &str) -> String {
    input.replace('\\', "\\\\").replace('"', "\\\"")
}

/// Initialise the SENS loop from `repl-core` (`репл-почати`).
fn init_sens_loop(session: &mut Session) -> Result<(), String> {
    if session.environment.get("репл-крок").is_none() {
        return Err("SENS-цикл недоступний: lib/repl-core.lisp не завантажено".into());
    }
    eval_program(
        &format!("(визначити {SENS_LOOP_STATE} (репл-почати (як-є ())))"),
        session,
    )
    .map(|_| ())
    .map_err(|error| {
        format!(
            "не вдалося ініціалізувати SENS-цикл: {}",
            error.render("(репл-почати (як-є ()))")
        )
    })
}

/// One SENS-owned REPL step: thread the meta-environment through
/// `репл-крок` → `обчислити-верхню-форму`. Returns the SENS value (остання-форма).
fn sens_loop_step(session: &mut Session, line: &str) -> Result<Value, sens::LanguageError> {
    let source = format!(
        "(визначити {SENS_LOOP_STATE} (репл-крок (прочитати \"{}\") {SENS_LOOP_STATE}))",
        escape_lisp_string(line)
    );
    eval_program(&source, session)?;
    Ok(eval_program(&format!("(решта {SENS_LOOP_STATE})"), session)?.value)
}

// The persistent map is a separate host-neutral root Zig byte asset.
fn persistent_map_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::persistent_map_source_bytes()?;
        String::from_utf8(bytes)
            .map_err(|error| format!("ZIG_PERSISTENT_MAP_REPL UTF-8: {error}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: persistent-map.lisp requires Zig; no Rust source fallback".into())
    }
}

// lib/knowledge.lisp is a host-neutral Zig-owned byte asset, never a Rust embed.
fn knowledge_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::knowledge_source_bytes()?;
        String::from_utf8(bytes)
            .map_err(|err| format!("ZIG_KNOWLEDGE_REPL UTF-8: {err}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: knowledge.lisp requires Zig; no Rust source fallback".into())
    }
}

// Джерело уніфікації передається Zig без прямого Rust-завантаження SENS-файлу.
fn unify_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::unify_source_bytes()?;
        String::from_utf8(bytes).map_err(|e| format!("ZIG_UNIFY_CARRIER UTF-8: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: unify.lisp requires Zig; no Rust source fallback".into())
    }
}

// lib/reason.lisp comes from Zig as opaque bytes; SENS alone evaluates it.
// Source-only forward chaining via Zig, never a Rust source embed or rule registry.
fn forward_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::forward_source_bytes()?;
        String::from_utf8(bytes).map_err(|err| format!("ZIG_FORWARD_CARRIER UTF-8: {err}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: forward.lisp requires Zig; no Rust source fallback".into())
    }
}

fn reason_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::reason_source_bytes()?;
        String::from_utf8(bytes)
            .map_err(|e| format!("ZIG_REASON_CARRIER UTF-8: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: reason.lisp requires Zig; no Rust source fallback".into())
    }
}

// The compact Ukrainian surface is original source bytes carried only by Zig.
fn uk_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::uk_surface_bytes()?;
        String::from_utf8(bytes).map_err(|e| format!("ZIG_UK_CARRIER UTF-8: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: Ukrainian compact surface requires Zig; no Rust source fallback".into())
    }
}
// Full Ukrainian source bytes are transported by Zig; SENS owns their meaning.
fn ukr_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::ukr_surface_bytes()?;
        String::from_utf8(bytes)
            .map_err(|e| format!("ZIG_UKR_CARRIER UTF-8 error: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: Ukrainian full surface requires Zig; no Rust source fallback".into())
    }
}
// The original Sanskrit source is Zig-owned opaque bytes, never a Rust embed.
fn sanskrit_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::sanskrit_surface_bytes()?;
        String::from_utf8(bytes)
            .map_err(|e| format!("ZIG_SANSKRIT_CARRIER UTF-8 error: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: Sanskrit surface requires Zig; no Rust source fallback".into())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ReplSurface {
    Core,
    English,
    Ukrainian,
    UkrainianFull,
    Sanskrit,
}

impl ReplSurface {
    pub(crate) fn parse(value: &str) -> Option<Self> {
        match value.trim().to_lowercase().as_str() {
            "core" | "ядро" => Some(Self::Core),
            "en" | "english" | "англійська" => Some(Self::English),
            "ук" | "uk" | "українська" => Some(Self::Ukrainian),
            "укр" | "ukr" | "українська-повна" => Some(Self::UkrainianFull),
            "sa" | "sanskrit" | "санскрит" => Some(Self::Sanskrit),
            _ => None,
        }
    }

    pub(crate) fn code(self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::English => "en",
            Self::Ukrainian => "ук",
            Self::UkrainianFull => "укр",
            Self::Sanskrit => "sa",
        }
    }

    fn title(self) -> &'static str {
        match self {
            Self::Core => "ядро",
            Self::English => "англійська",
            Self::Ukrainian => "українська",
            Self::UkrainianFull => "українська (повна)",
            Self::Sanskrit => "санскрит",
        }
    }

    fn presentation(self) -> PresentationLanguage {
        match self {
            Self::Core => PresentationLanguage::Canonical,
            Self::English => PresentationLanguage::English,
            Self::Ukrainian | Self::UkrainianFull => PresentationLanguage::Ukrainian,
            Self::Sanskrit => PresentationLanguage::Sanskrit,
        }
    }
}

fn render_surface_names(surface: ReplSurface) -> Result<String, String> {
    surface_catalog::render_names(surface.code())
}

fn render_surface_name(surface: ReplSurface, requested: &str) -> Result<String, String> {
    surface_catalog::render_name(surface.code(), requested)
}

fn render_surface_status() -> Result<String, String> {
    surface_catalog::render_status()
}

fn build_surface_layer(base: &Environment, surface: ReplSurface, sens_loop: bool) -> Result<Environment, String> {
    let layer = base.child();
    let needs_surface = matches!(
        surface,
        ReplSurface::Ukrainian | ReplSurface::UkrainianFull | ReplSurface::Sanskrit
    );
    // Meta-eval + repl-core are needed both for surface projection
    // and for the SENS-owned `--sens-loop` mode. They load here once; the
    // surface-specific sources below load only for uk/укр/sa.
    if sens_loop || needs_surface {
        // Used only inside the zig-transport block below; without that feature
        // this binding is unused and need not be mutable.
        #[cfg_attr(not(feature = "zig-transport"), allow(unused_mut, unused_variables))]
        let mut session = Session {
            environment: layer.clone(),
        };
        #[cfg(feature = "zig-transport")]
        {
            let meta_eval = repl_zig_source(sens_zig_meta_eval_bytes_copy, "ZIG_SENS_META_EVAL")?;
            sens::load_meta_evaluator_library_from_source(&mut session, &meta_eval)
                .map_err(|error| {
                    format!(
                        "не вдалося завантажити MetaEval: {}",
                        error.render(&meta_eval)
                    )
                })?;
            let repl_core = crate::zig_transport::repl_core_source_bytes()
                .and_then(|bytes| String::from_utf8(bytes).map_err(|err| format!("ZIG_SENS_REPL UTF-8: {err}")))?;
            sens::parse_mixed_exact_domain(&repl_core)
                .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
                .map_err(|error| {
                    format!("не вдалося завантажити repl-core: {}", error.render(&repl_core))
                })?;
        }
    }
    if needs_surface {
        let mut session = Session {
            environment: layer.clone(),
        };
        let unify_source = unify_surface_source()?;
        let reason_source = reason_surface_source()?;
        let forward_source = forward_surface_source()?;
        let knowledge_source = knowledge_surface_source()?;
        let persistent_map_source = persistent_map_surface_source()?;
        let prerequisite_sources = surface_prerequisite_sources()?;
        let prerequisites = std::iter::once(("unify.lisp", unify_source.as_str()))
            .chain(std::iter::once(("reason.lisp", reason_source.as_str())))
            .chain(std::iter::once(("forward.lisp", forward_source.as_str())))
            .chain(std::iter::once(("knowledge.lisp", knowledge_source.as_str())))
            .chain(std::iter::once(("persistent-map.lisp", persistent_map_source.as_str())))
            .chain(prerequisite_sources.iter().map(|(name, source)| (*name, source.as_str())));
        for (name, source) in prerequisites {
            (if name == "time.lisp" {
                sens::load_time_library_from_source(&mut session, source)
            } else if matches!(name, "unify.lisp" | "reason.lisp" | "forward.lisp" | "knowledge.lisp" | "persistent-map.lisp") {
                sens::eval_pinned_reasoning_source(
                    &format!("lib/{name}"), source, &mut session
                )
            } else if matches!(name, "persistent-vector.lisp" | "epistemic.lisp") {
                sens::parse_mixed_exact_domain(source)
                    .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
            } else {
                eval_program(source, &mut session)
            }).map_err(|error| {
                format!("не вдалося завантажити {name}: {}", error.render(source))
            })?;
        }
        // Keep the same SENS evaluation order; only source transport changes.
        let uk_source = if surface == ReplSurface::Ukrainian {
            Some(uk_surface_source()?)
        } else {
            None
        };
        let ukr_source = if surface == ReplSurface::UkrainianFull {
            Some(ukr_surface_source()?)
        } else {
            None
        };
        let sanskrit_source = if surface == ReplSurface::Sanskrit {
            Some(sanskrit_surface_source()?)
        } else {
            None
        };
        let (name, source) = match surface {
            ReplSurface::Ukrainian => ("uk.lisp", uk_source.as_deref()
                .ok_or("RUST_ZIG_ONLY: missing Zig Ukrainian compact source")?),
            ReplSurface::UkrainianFull => ("ukr.lisp", ukr_source.as_deref()
                .ok_or("RUST_ZIG_ONLY: missing Zig Ukrainian full source")?),
            ReplSurface::Sanskrit => ("sa.lisp", sanskrit_source.as_deref()
                .ok_or("RUST_ZIG_ONLY: missing Zig Sanskrit source")?),
            ReplSurface::Core | ReplSurface::English => unreachable!(),
        };
        sens::parse_mixed_exact_domain(source)
            .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
            .map_err(|error| format!("не вдалося завантажити {name}: {}", error.render(source)))?;
    }
    Ok(layer)
}

struct ReplState {
    session: Session,
    base_environment: Environment,
    user_environment: Environment,
    surface: ReplSurface,
    sens_loop: bool,
}

impl ReplState {
    fn new(mut session: Session, surface: ReplSurface, sens_loop: bool) -> Result<Self, String> {
        let base_environment = session.environment.clone();
        let surface_environment = build_surface_layer(&base_environment, surface, sens_loop)?;
        let user_environment = surface_environment.child();
        session.environment = user_environment.clone();
        if sens_loop {
            init_sens_loop(&mut session)?;
        }
        Ok(Self {
            session,
            base_environment,
            user_environment,
            surface,
            sens_loop,
        })
    }

    fn switch_surface(&mut self, surface: ReplSurface) -> Result<(), String> {
        if self.surface == surface {
            return Ok(());
        }
        let surface_environment = build_surface_layer(&self.base_environment, surface, self.sens_loop)?;
        self.user_environment
            .reparent(surface_environment)
            .map_err(str::to_string)?;
        self.surface = surface;
        Ok(())
    }
}

/// Classic Lisp REPL printer policy: user-entered symbols may be lowercase,
/// while replies print symbol data in uppercase. This is presentation only:
/// runtime values, semantic identities, strings, numbers and machine protocols
/// are unchanged.
fn render_repl_reply(value: &Value, language: PresentationLanguage) -> String {
    match value {
        Value::Symbol(_) => render_value_for_presentation(value, language).to_uppercase(),
        Value::DomainIdentity(sens::DomainIdentity::D1(_)) => {
            render_value_for_presentation(value, language).to_uppercase()
        }
        Value::Pair(_, _) => render_repl_pair(value, language),
        Value::Vector(vector) => {
            let items = vector
                .borrow()
                .iter()
                .map(|item| render_repl_reply(item, language))
                .collect::<Vec<_>>();
            format!("#({})", items.join(" "))
        }
        _ => render_value_for_presentation(value, language),
    }
}

fn render_repl_pair(value: &Value, language: PresentationLanguage) -> String {
    let mut output = String::from("(");
    let mut current = value;
    let mut first = true;

    loop {
        match current {
            Value::Pair(head, tail) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_repl_reply(head, language));
                current = tail;
                first = false;
            }
            Value::Nil => {
                output.push(')');
                return output;
            }
            tail => {
                output.push_str(" . ");
                output.push_str(&render_repl_reply(tail, language));
                output.push(')');
                return output;
            }
        }
    }
}

/// `~/.sens-history`, якщо home directory доступний.
pub(crate) fn history_path() -> Option<PathBuf> {
    let home = env::var_os("HOME").or_else(|| env::var_os("USERPROFILE"))?;
    Some(PathBuf::from(home).join(".sens-history"))
}

fn print_surface_help() {
    println!("Поверхні: :мова ук | укр | en | sa | core");
    println!("Технічний alias: :surface ук | укр | en | sa | core");
    println!("Каталог поточної людської поверхні: :імена / :names");
    println!("Одна semantic identity у всіх людських поверхнях: :ім'я <назва> / :name <name>");
    println!("Стан людських поверхонь: :поверхні / :surfaces");
    println!("Сире лексичне середовище без фільтрації поверхнею: (середовище) / (env)");
    println!("core — канонічний машинний шар, не четверта людська мова.");
    println!("Перемикання змінює лише surface-frame; ваші define/closures лишаються живими.");
}

fn handle_meta_command(line: &str, state: &mut ReplState) -> bool {
    let mut parts = line.split_whitespace();
    let Some(command) = parts.next() else {
        return false;
    };

    match command {
        ":мова" | ":surface" => {
            let Some(requested) = parts.next() else {
                println!(
                    "Поточна поверхня: {} ({})",
                    state.surface.title(),
                    state.surface.code()
                );
                print_surface_help();
                return true;
            };
            if parts.next().is_some() {
                eprintln!("Поверхня приймає рівно одне ім'я.");
                print_surface_help();
                return true;
            }
            let Some(surface) = ReplSurface::parse(requested) else {
                eprintln!("Невідома поверхня: {requested}");
                print_surface_help();
                return true;
            };
            match state.switch_surface(surface) {
                Ok(()) => println!("Поверхня: {} ({})", surface.title(), surface.code()),
                Err(error) => eprintln!("Помилка перемикання поверхні: {error}"),
            }
            true
        }
        ":імена" | ":names" => {
            if parts.next().is_some() {
                eprintln!("Команда :імена не приймає аргументів.");
                return true;
            }
            match render_surface_names(state.surface) {
                Ok(output) => println!("{output}"),
                Err(error) => eprintln!("Помилка каталогу поверхні: {error}"),
            }
            true
        }
        ":ім'я" | ":name" => {
            let Some(requested) = parts.next() else {
                eprintln!("Використання: :ім'я <назва>");
                return true;
            };
            if parts.next().is_some() {
                eprintln!("Команда :ім'я приймає рівно одну назву.");
                return true;
            }
            match render_surface_name(state.surface, requested) {
                Ok(output) => println!("{output}"),
                Err(error) => eprintln!("Помилка каталогу поверхні: {error}"),
            }
            true
        }
        ":поверхні" | ":surfaces" => {
            if parts.next().is_some() {
                eprintln!("Команда :поверхні не приймає аргументів.");
                return true;
            }
            match render_surface_status() {
                Ok(output) => println!("{output}"),
                Err(error) => eprintln!("Помилка стану поверхонь: {error}"),
            }
            true
        }
        ":допомога" | ":help" => {
            print_surface_help();
            true
        }
        _ => false,
    }
}

pub(crate) fn run_repl(session: Session, initial_surface: ReplSurface, sens_loop: bool) {
    let mut state = match ReplState::new(session, initial_surface, sens_loop) {
        Ok(state) => state,
        Err(error) => {
            eprintln!("Error: could not initialize REPL surface: {error}");
            process::exit(1);
        }
    };

    println!("sens REPL v{} (pure Rust)", env!("CARGO_PKG_VERSION"));
    println!(
        "Поверхня: {} ({}) · змінити: :мова ук|укр|en|sa|core · :допомога",
        state.surface.title(),
        state.surface.code()
    );
    if state.sens_loop {
        println!("Режим: SENS-цикл (repl-core · обчислити-верхню-форму), не нативний оцінювач.");
    }
    println!("Символи можна вводити малими літерами; REPL друкує їх ВЕЛИКИМИ.");
    println!("D1 лишається 1/0 у Canon; людські проекції друкуються ВЕЛИКИМИ.");
    println!("Ctrl-C або Ctrl-D — вихід.");

    let mut rl = match DefaultEditor::new() {
        Ok(editor) => editor,
        Err(err) => {
            eprintln!("Error: could not start the REPL line editor: {err}");
            process::exit(1);
        }
    };

    let history_path = history_path();
    if let Some(path) = &history_path {
        let _ = rl.load_history(path);
    }

    loop {
        let prompt = format!("sens[{}]> ", state.surface.code());
        let readline = rl.readline(&prompt);
        match readline {
            Ok(line) => {
                let line = line.trim();
                if line.is_empty() {
                    continue;
                }

                let _ = rl.add_history_entry(line);
                if let Some(path) = &history_path {
                    let _ = rl.append_history(path);
                }

                if handle_meta_command(line, &mut state) {
                    continue;
                }

                if state.sens_loop {
                    match sens_loop_step(&mut state.session, line) {
                        Ok(value) => println!(
                            "{}",
                            render_repl_reply(&value, state.surface.presentation())
                        ),
                        Err(error) => eprintln!(
                            "{}",
                            render_error_for_presentation(
                                &error,
                                line,
                                state.surface.presentation()
                            )
                        ),
                    }
                    continue;
                }

                match parse(line) {
                    Ok(ast) => {
                        match eval_parsed_expressions_incremental(&ast, &mut state.session) {
                            Ok(result) => {
                                for out in result.output {
                                    println!("{out}");
                                }
                                println!(
                                    "{}",
                                    render_repl_reply(
                                        &result.value,
                                        state.surface.presentation(),
                                    )
                                );
                            }
                            Err(e) => {
                                // Це лише interaction policy: невідомий standalone symbol
                                // вітається через `echo`, але всередині справжньої форми
                                // UnknownSymbol лишається звичайною мовною помилкою.
                                if e.kind == ErrorKind::UnknownSymbol
                                    && ast.len() == 1
                                    && matches!(ast[0].kind, ExprKind::Symbol(_))
                                {
                                    println!("echo {line}");
                                } else {
                                    eprintln!(
                                        "{}",
                                        render_error_for_presentation(
                                            &e,
                                            line,
                                            state.surface.presentation(),
                                        )
                                    );
                                }
                            }
                        }
                    }
                    Err(e) => eprintln!(
                        "{}",
                        render_error_for_presentation(&e, line, state.surface.presentation(),)
                    ),
                }
            }
            Err(ReadlineError::Interrupted | ReadlineError::Eof) => break,
            Err(err) => {
                eprintln!("Error: {err:?}");
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn core_state() -> ReplState {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("core bootstrap");
        ReplState::new(session, ReplSurface::Core, false).expect("REPL state")
    }

    fn value(state: &mut ReplState, source: &str) -> String {
        eval_program(source, &mut state.session)
            .unwrap_or_else(|error| panic!("{source}: {}", error.render(source)))
            .value
            .to_string()
    }

    #[test]
    fn classic_repl_reply_uppercases_symbols_but_preserves_strings_and_numbers() {
        let value = Value::list([
            Value::Symbol("car".into()),
            Value::list([
                Value::Symbol("cons".into()),
                Value::String("Keep Mixed Case".into()),
                Value::Number(42.0, sens::Exactness::Exact),
            ]),
        ]);

        assert_eq!(
            render_repl_reply(&value, PresentationLanguage::Canonical),
            "(CAR (CONS \"Keep Mixed Case\" 42))"
        );
        // Presentation is one-way only: the runtime symbol identity is untouched.
        let Value::Pair(head, _) = &value else {
            panic!("list");
        };
        assert_eq!(head.as_ref(), &Value::Symbol("car".into()));
    }

    #[test]
    fn classic_repl_reply_uppercases_d1_human_projection_but_not_machine_bits() {
        let no = Value::DomainIdentity(sens::DomainIdentity::D1(
            sens::PredicateBit::from_word(sens::Bit1::new(0).unwrap()),
        ));
        let yes = Value::DomainIdentity(sens::DomainIdentity::D1(
            sens::PredicateBit::from_word(sens::Bit1::new(1).unwrap()),
        ));

        assert_eq!(render_repl_reply(&no, PresentationLanguage::Canonical), "0");
        assert_eq!(render_repl_reply(&yes, PresentationLanguage::Canonical), "1");
        assert_eq!(render_repl_reply(&no, PresentationLanguage::English), "0");
        assert_eq!(render_repl_reply(&yes, PresentationLanguage::English), "1");
        assert_eq!(render_repl_reply(&no, PresentationLanguage::Ukrainian), "НІ");
        assert_eq!(render_repl_reply(&yes, PresentationLanguage::Ukrainian), "ТАК");
        assert_eq!(render_repl_reply(&no, PresentationLanguage::Sanskrit), "NA");
        assert_eq!(render_repl_reply(&yes, PresentationLanguage::Sanskrit), "ĀM");
    }

    #[test]
    fn classic_repl_reply_accepts_lowercase_source_and_prints_uppercase_symbols() {
        let mut state = core_state();
        let result = eval_program(
            "(quote (car cons \"MiXeD\" 42))",
            &mut state.session,
        )
        .expect("lowercase REPL source should evaluate");

        assert_eq!(
            render_repl_reply(&result.value, PresentationLanguage::Canonical),
            "(CAR CONS \"MiXeD\" 42)"
        );
    }

    #[test]
    fn classic_repl_reply_uppercases_dotted_and_vector_symbol_data() {
        let dotted = Value::Pair(
            std::rc::Rc::new(Value::Symbol("left".into())),
            std::rc::Rc::new(Value::Symbol("right".into())),
        );
        assert_eq!(
            render_repl_reply(&dotted, PresentationLanguage::Canonical),
            "(LEFT . RIGHT)"
        );

        let vector = Value::Vector(std::rc::Rc::new(std::cell::RefCell::new(vec![
            Value::Symbol("alpha".into()),
            Value::String("beta".into()),
        ])));
        assert_eq!(
            render_repl_reply(&vector, PresentationLanguage::Canonical),
            "#(ALPHA \"beta\")"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_persistent_map_repl_exact_bytes() {
        let source = persistent_map_surface_source().expect("persistent map via Zig root");
        let bytes = crate::zig_transport::persistent_map_source_bytes().expect("second Zig byte copy");
        assert!(!source.is_empty());
        assert_eq!(source.as_bytes(), bytes.as_slice(), "ZIG_PERSISTENT_MAP_REPL byte parity");
        println!("ZIG_PERSISTENT_MAP_REPL_PASS test_id=zig-repl-persistent-map layer=transport bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_persistent_map_no_rust_fallback() {
        let err = persistent_map_surface_source().expect_err("must not bypass Zig");
        assert_eq!(err, "RUST_ZIG_ONLY: persistent-map.lisp requires Zig; no Rust source fallback");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_knowledge_repl_preserves_exact_bytes() {
        let source = knowledge_surface_source().expect("knowledge source via Zig C ABI");
        let bytes = crate::zig_transport::knowledge_source_bytes().expect("independent Zig C byte copy");
        assert!(!source.is_empty(), "ZIG_KNOWLEDGE_REPL empty source");
        assert_eq!(source.as_bytes(), bytes.as_slice(), "ZIG_KNOWLEDGE_REPL exact byte parity");
        println!("ZIG_KNOWLEDGE_REPL_PASS test_id=knowledge-repl-zig-only layer=transport bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_knowledge_without_zig_fails_closed() {
        let error = knowledge_surface_source().expect_err("no Rust fallback for knowledge.lisp");
        assert_eq!(error, "RUST_ZIG_ONLY: knowledge.lisp requires Zig; no Rust source fallback");
        println!("ZIG_KNOWLEDGE_NO_FALLBACK_PASS test_id=knowledge-repl-no-rust-source layer=transport");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_forward_source_preserves_every_byte() {
        let source = forward_surface_source().expect("forward source via Zig C ABI");
        let bytes = crate::zig_transport::forward_source_bytes().expect("second Zig C byte copy");
        assert_eq!(source.as_bytes(), bytes.as_slice(), "ZIG_FORWARD_CARRIER exact byte parity");
        assert!(source.starts_with("; Чинний рушій прямого виведення СЕНС:"), "wrong SENS source asset");
        println!("ZIG_FORWARD_CARRIER_PASS test_id=zig-forward-exact-carry layer=transport bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_forward_without_zig_denies_rust_bypass() {
        let error = forward_surface_source().expect_err("only Zig may carry forward.lisp");
        assert!(error.contains("RUST_ZIG_ONLY: forward.lisp requires Zig; no Rust source fallback"), "{error}");
        println!("ZIG_FORWARD_NO_FALLBACK_PASS test_id=zig-forward-no-rust-bypass layer=transport");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_unify_repl_source_matches_opaque_c_abi_bytes() {
        let source = unify_surface_source().expect("Zig exact lib/unify.lisp bytes");
        let copied = crate::zig_transport::unify_source_bytes().expect("Zig copied original source");
        assert_eq!(source.as_bytes(), copied.as_slice(), "ZIG_UNIFY_CARRIER byte parity");
        assert!(source.starts_with("; Уніфікація зіставляє структури"), "wrong unify asset");
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn rust_only_repl_rejects_unify_source_bypass() {
        let error = unify_surface_source().expect_err("no direct Rust SENS source");
        assert!(error.contains("RUST_ZIG_ONLY"), "{error}");
        assert!(error.contains("no Rust source fallback"), "{error}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_uk_surface_preserves_original_bytes() {
        let source = uk_surface_source().expect("root Zig C ABI original Ukrainian surface");
        let bytes = crate::zig_transport::uk_surface_bytes().expect("second Zig ABI copy");
        assert_eq!(source.as_bytes(), bytes.as_slice(), "UK surface exact byte identity");
        assert!(source.starts_with("; Ukrainian surface"), "not canonical source asset");
        assert!(source.contains("одна семантична реалізація"), "truncated or swapped source");
        println!("ZIG_UK_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_uk_surface_rejects_rust_only_loading() {
        let error = uk_surface_source().expect_err("Zigless Rust cannot read the surface");
        assert!(error.contains("RUST_ZIG_ONLY"), "{error}");
        assert!(error.contains("no Rust source fallback"), "{error}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_ukr_surface_preserves_actual_source_bytes() {
        let source = ukr_surface_source().expect("real Zig full Ukrainian bytes");
        let bytes = crate::zig_transport::ukr_surface_bytes().expect("second Zig ABI copy");
        assert_eq!(source.as_bytes(), bytes.as_slice(), "UKR original byte parity");
        assert!(source.starts_with("; Повна українська проєкція"), "wrong source");
        assert!(source.contains("рівноправною мовною поверхнею"), "truncated source");
        println!("ZIG_UKR_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_ukr_surface_denies_rust_only_loading() {
        let err = ukr_surface_source().expect_err("no direct Rust Lisp source");
        assert!(err.contains("RUST_ZIG_ONLY"), "{err}");
        assert!(err.contains("no Rust source fallback"), "{err}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_sanskrit_surface_preserves_actual_source_bytes() {
        let source = sanskrit_surface_source().expect("live root Zig C ABI");
        let bytes = crate::zig_transport::sanskrit_surface_bytes()
            .expect("second Zig ABI byte copy");
        assert_eq!(source.as_bytes(), bytes.as_slice(), "Sanskrit exact-byte replay");
        assert!(source.starts_with("; Sanskrit surface"), "expected tracked source");
        assert!(source.contains("svarūpa"), "source identity/truncation witness");
        println!("ZIG_SANSKRIT_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED", bytes.len());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_sanskrit_surface_denies_rust_only_loading() {
        let err = sanskrit_surface_source().expect_err("no direct Rust source fallback");
        assert!(err.contains("RUST_ZIG_ONLY"), "{err}");
        assert!(err.contains("no Rust source fallback"), "{err}");
    }

    #[test]
    fn ukrainian_surface_adds_derived_vocabulary_but_not_canon_bindings() {
        let mut state = core_state();
        assert!(state.session.environment.get("атом?").is_none());

        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        assert_eq!(value(&mut state, "(атом? 'мама)"), "(1)");
        // Contract 6.0: canonical spelling is resolver-owned, never a mutable
        // surface-frame alias. Derived Ukrainian vocabulary remains a binding.
        assert!(state.session.environment.get("атом?").is_none());
        // `додати` is now a table surface (plus, 00001100) resolved through
        // its code; `вектор-додати` is derived vocabulary bound by uk.lisp.
        assert!(state.session.environment.get("додати").is_none());
        assert!(state.session.environment.get("вектор-додати").is_some());

        state.switch_surface(ReplSurface::Core).expect("core");
        assert!(state.session.environment.get("атом?").is_none());
        assert_eq!(value(&mut state, "(atom? 'мама)"), "(1)");
        // Canon is not a UI layer: registered spellings still denote Canon
        // even when no human surface frame is loaded.
        assert_eq!(value(&mut state, "(атом? 'мама)"), "(1)");
    }

    #[test]
    fn switching_surface_preserves_user_frame_and_closure_view() {
        let mut state = core_state();
        value(&mut state, "(define крок 1)");
        value(&mut state, "(define додай-крок (lambda (x) (+ x крок)))");
        assert_eq!(value(&mut state, "(додай-крок 5)"), "6");

        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        value(&mut state, "(define крок 2)");
        assert_eq!(value(&mut state, "(додай-крок 5)"), "7");

        state.switch_surface(ReplSurface::English).expect("en");
        assert_eq!(value(&mut state, "(додай-крок 5)"), "7");
    }

    #[test]
    fn uk_and_ukr_are_distinct_repl_selectors_over_one_registry() {
        assert_eq!(ReplSurface::parse("ук"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("uk"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("укр"), Some(ReplSurface::UkrainianFull));
        assert_eq!(ReplSurface::parse("ukr"), Some(ReplSurface::UkrainianFull));
        assert_ne!(ReplSurface::Ukrainian.code(), ReplSurface::UkrainianFull.code());
        assert!(
            surface_catalog::render_name("укр", "D6:101000")
                .expect("UKR registry lookup")
                .starts_with("identity: D6:101000")
        );
    }

    #[test]
    fn all_human_surfaces_have_catalogs() {
        let en = render_surface_names(ReplSurface::English).expect("EN catalog");
        let uk = render_surface_names(ReplSurface::Ukrainian).expect("UK catalog");
        let ukr = render_surface_names(ReplSurface::UkrainianFull).expect("UKR catalog");
        let sa = render_surface_names(ReplSurface::Sanskrit).expect("SA catalog");
        assert!(en.contains("surface en:"));
        assert!(uk.contains("surface ук:"));
        assert!(ukr.contains("surface укр:"));
        assert!(sa.contains("surface san:"));
    }

    #[test]
    fn one_name_help_resolves_across_en_uk_sa() {
        let help = render_surface_name(ReplSurface::Ukrainian, "D6:101000").expect("name help");
        assert!(help.contains("identity: D6:101000"));
        assert!(help.contains("EN: map"));
        assert!(help.contains("UK: відобразити"));
        assert!(help.contains("SAN: āvartana"));
        assert!(render_surface_name(ReplSurface::Ukrainian, "map")
            .expect("ambiguous map is described")
            .contains("неоднозначне"));
    }

    #[test]
    fn projection_status_reports_measured_table_coverage() {
        let status = render_surface_status().expect("surface status");
        assert!(status.contains("Проєкції таблиць D1–D11"));
        assert!(status.contains("доменні координати:"));
        assert!(status.contains("rows with all four human projections:"));
    }

    #[test]
    fn raw_environment_distinguishes_bootstrap_bindings_from_canon_resolution() {
        let mut state = core_state();
        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        let snapshot = state.session.environment.snapshot();
        // Since #1477 no function name is bound in the raw environment: the
        // call resolves through the SENS code, in any surface.
        assert!(!snapshot.iter().any(|(name, _)| name.as_ref() == "atom?"));
        assert!(!snapshot.iter().any(|(name, _)| name.as_ref() == "атом?"));
        assert_eq!(value(&mut state, "(атом? 'мама)"), "(1)");
    }
}
