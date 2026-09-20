//! Інтерактивний stdio REPL: історія, interaction-only echo fallback і
//! вибір namespace для назв/подання. `:мова` / `:surface` не є Lisp syntax:
//! вони не змінюють середовище виконання — усі admitted spellings ідуть
//! semantic registry → SID → одна семантика.

mod surface_catalog;

use my_lisp::{
    eval_parsed_expressions_incremental, parse, render_error_for_presentation,
    render_value_for_presentation, ErrorKind, ExprKind, PresentationLanguage, Session,
};
use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use std::env;
use std::path::PathBuf;
use std::process;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ReplSurface {
    Core,
    English,
    Ukrainian,
    Sanskrit,
}

impl ReplSurface {
    pub(crate) fn parse(value: &str) -> Option<Self> {
        match value.trim().to_lowercase().as_str() {
            "core" | "ядро" => Some(Self::Core),
            "en" | "english" | "англійська" => Some(Self::English),
            "укр" | "ук" | "українська" => Some(Self::Ukrainian),
            "sa" | "sanskrit" | "санскрит" => Some(Self::Sanskrit),
            _ => None,
        }
    }

    pub(crate) fn code(self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::English => "en",
            Self::Ukrainian => "укр",
            Self::Sanskrit => "sa",
        }
    }

    fn title(self) -> &'static str {
        match self {
            Self::Core => "ядро",
            Self::English => "англійська",
            Self::Ukrainian => "українська",
            Self::Sanskrit => "санскрит",
        }
    }

    fn presentation(self) -> PresentationLanguage {
        match self {
            Self::Core => PresentationLanguage::Canonical,
            Self::English => PresentationLanguage::English,
            Self::Ukrainian => PresentationLanguage::Ukrainian,
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

struct ReplState {
    session: Session,
    surface: ReplSurface,
}

impl ReplState {
    fn new(session: Session, surface: ReplSurface) -> Self {
        Self { session, surface }
    }

    fn switch_surface(&mut self, surface: ReplSurface) {
        self.surface = surface;
    }
}

/// `~/.my-lisp-history`, якщо home directory доступний.
pub(crate) fn history_path() -> Option<PathBuf> {
    let home = env::var_os("HOME").or_else(|| env::var_os("USERPROFILE"))?;
    Some(PathBuf::from(home).join(".my-lisp-history"))
}

fn print_surface_help() {
    println!("Мови назв: :мова укр | en | sa | core");
    println!("Compatibility selector: :мова ук також обирає укр.");
    println!("Технічний alias: :surface укр | en | sa | core");
    println!("Каталог поточного namespace: :імена / :names");
    println!("Одна semantic identity у всіх namespace: :ім'я <назва> / :name <name>");
    println!("Стан таблиці назв: :поверхні / :surfaces");
    println!("Сире лексичне середовище: (середовище) / (env)");
    println!("core — канонічні SID; укр/en/sa лише вибирають назви й подання.");
    println!("Перемикання :мова не завантажує бібліотеки й не змінює Environment.");
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
                    "Поточна мова назв: {} ({})",
                    state.surface.title(),
                    state.surface.code()
                );
                print_surface_help();
                return true;
            };
            if parts.next().is_some() {
                eprintln!(":мова приймає рівно один namespace.");
                print_surface_help();
                return true;
            }
            let Some(surface) = ReplSurface::parse(requested) else {
                eprintln!("Невідома мова назв: {requested}");
                print_surface_help();
                return true;
            };
            state.switch_surface(surface);
            println!("Мова назв: {} ({})", surface.title(), surface.code());
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

pub(crate) fn run_repl(session: Session, initial_surface: ReplSurface) {
    let mut state = ReplState::new(session, initial_surface);

    println!("my-lisp REPL v{} (pure Rust)", env!("CARGO_PKG_VERSION"));
    println!(
        "Мова назв: {} ({}) · змінити: :мова укр|en|sa|core · :допомога",
        state.surface.title(),
        state.surface.code()
    );
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
        let prompt = format!("my-lisp[{}]> ", state.surface.code());
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

                match parse(line) {
                    Ok(ast) => {
                        match eval_parsed_expressions_incremental(&ast, &mut state.session) {
                            Ok(result) => {
                                for out in result.output {
                                    println!("{out}");
                                }
                                println!(
                                    "{}",
                                    render_value_for_presentation(
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
    use my_lisp::eval_program;

    fn core_state() -> ReplState {
        let mut session = Session::default();
        my_lisp::load_core_library(&mut session).expect("core bootstrap");
        ReplState::new(session, ReplSurface::Core)
    }

    fn value(state: &mut ReplState, source: &str) -> String {
        eval_program(source, &mut state.session)
            .unwrap_or_else(|error| panic!("{source}: {}", error.render(source)))
            .value
            .to_string()
    }

    fn environment_names(state: &ReplState) -> Vec<String> {
        let mut names: Vec<String> = state
            .session
            .environment
            .snapshot()
            .into_iter()
            .map(|(name, _)| name.to_string())
            .collect();
        names.sort();
        names
    }

    #[test]
    fn ukr_registry_name_executes_without_runtime_surface_layer() {
        let mut state = core_state();

        assert!(
            state.session.environment.get("порожній-текст?").is_none(),
            "registry spelling must not need a mutable alias binding"
        );
        assert_eq!(value(&mut state, "(порожній-текст? \"\")"), "t");

        let before = environment_names(&state);
        state.switch_surface(ReplSurface::Ukrainian);
        let after = environment_names(&state);

        assert_eq!(state.surface.code(), "укр");
        assert_eq!(before, after, ":мова must not mutate/reparent Environment");

        let truth = eval_program("(порожній-текст? \"\")", &mut state.session)
            .expect("ukr registry spelling")
            .value;
        assert_eq!(
            render_value_for_presentation(&truth, state.surface.presentation()),
            "істина"
        );
    }

    #[test]
    fn switching_name_namespace_preserves_user_frame_and_closure_view() {
        let mut state = core_state();
        value(&mut state, "(define крок 1)");
        value(&mut state, "(define додай-крок (lambda (x) (+ x крок)))");
        assert_eq!(value(&mut state, "(додай-крок 5)"), "6");

        let before = environment_names(&state);
        state.switch_surface(ReplSurface::Ukrainian);
        assert_eq!(before, environment_names(&state));

        value(&mut state, "(define крок 2)");
        assert_eq!(value(&mut state, "(додай-крок 5)"), "7");

        state.switch_surface(ReplSurface::English);
        assert_eq!(value(&mut state, "(додай-крок 5)"), "7");
    }

    #[test]
    fn human_name_namespaces_have_registry_catalogs() {
        let en = render_surface_names(ReplSurface::English).expect("EN catalog");
        let ukr = render_surface_names(ReplSurface::Ukrainian).expect("UKR catalog");
        let sa = render_surface_names(ReplSurface::Sanskrit).expect("SA catalog");
        assert!(en.contains("namespace en:"));
        assert!(ukr.contains("namespace укр:"));
        assert!(sa.contains("namespace sa:"));
    }

    #[test]
    fn one_name_help_exposes_same_sid_across_namespaces() {
        for requested in ["map", "відобразити", "āvartana"] {
            let help = render_surface_name(ReplSurface::Ukrainian, requested).expect("name help");
            assert!(help.contains("identity: 00110111"));
            assert!(help.contains("УКР: відобразити"));
            assert!(help.contains("EN: map"));
            assert!(help.contains("SA: āvartana"));
        }
    }

    #[test]
    fn table_status_is_measured_not_claimed() {
        let status = render_surface_status().expect("name table status");
        assert!(status.contains("УКР  present"));
        assert!(status.contains("release parity:"));
    }

    #[test]
    fn language_selector_does_not_install_surface_vocabulary() {
        let mut state = core_state();
        let before = environment_names(&state);

        state.switch_surface(ReplSurface::Ukrainian);

        assert_eq!(before, environment_names(&state));
        assert!(
            state.session.environment.get("порожній-текст?").is_none(),
            "Canon name must remain resolver-owned, not a mutable REPL alias"
        );
        assert_eq!(value(&mut state, "(порожній-текст? \"\")"), "t");
    }

    #[test]
    fn compact_uk_selector_is_only_a_compatibility_name_for_ukr() {
        assert_eq!(ReplSurface::parse("ук"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("укр"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("ук").unwrap().code(), "укр");
    }
}
