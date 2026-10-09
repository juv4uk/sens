//! Інтерактивний stdio REPL: історія, interaction-only echo fallback і
//! перемикання програмних поверхонь. `:мова` / `:surface` не є Lisp syntax:
//! це команди оболонки над одним і тим самим семантичним ядром.

mod surface_catalog;

use sens::{
    eval_parsed_expressions_incremental, eval_program, parse, render_error_for_presentation,
    render_value_for_presentation, Environment, ErrorKind, ExprKind, PresentationLanguage, Session,
};
use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use std::env;
use std::path::PathBuf;
use std::process;

const SURFACE_PREREQUISITES: &[(&str, &str)] = &[
    ("unify.lisp", include_str!("../../../lib/unify.lisp")),
    ("reason.lisp", include_str!("../../../lib/reason.lisp")),
    ("forward.lisp", include_str!("../../../lib/forward.lisp")),
    ("knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
    (
        "persistent-map.lisp",
        include_str!("../../../lib/persistent-map.lisp"),
    ),
    (
        "persistent-vector.lisp",
        include_str!("../../../lib/persistent-vector.lisp"),
    ),
    ("time.lisp", include_str!("../../../lib/time.lisp")),
    ("epistemic.lisp", include_str!("../../../lib/epistemic.lisp")),
];
const UK_SURFACE: &str = include_str!("../../../lib/surface/uk.lisp");
const UKR_SURFACE: &str = include_str!("../../../lib/surface/ukr.lisp");
const SA_SURFACE: &str = include_str!("../../../lib/surface/sa.lisp");

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

fn build_surface_layer(base: &Environment, surface: ReplSurface) -> Result<Environment, String> {
    let layer = base.child();
    if matches!(surface, ReplSurface::Ukrainian | ReplSurface::UkrainianFull | ReplSurface::Sanskrit) {
        let mut session = Session {
            environment: layer.clone(),
        };
        for (name, source) in SURFACE_PREREQUISITES {
            eval_program(source, &mut session).map_err(|error| {
                format!("не вдалося завантажити {name}: {}", error.render(source))
            })?;
        }
        let (name, source) = match surface {
            ReplSurface::Ukrainian => ("uk.lisp", UK_SURFACE),
            ReplSurface::UkrainianFull => ("ukr.lisp", UKR_SURFACE),
            ReplSurface::Sanskrit => ("sa.lisp", SA_SURFACE),
            ReplSurface::Core | ReplSurface::English => unreachable!(),
        };
        eval_program(source, &mut session)
            .map_err(|error| format!("не вдалося завантажити {name}: {}", error.render(source)))?;
    }
    Ok(layer)
}

struct ReplState {
    session: Session,
    base_environment: Environment,
    user_environment: Environment,
    surface: ReplSurface,
}

impl ReplState {
    fn new(mut session: Session, surface: ReplSurface) -> Result<Self, String> {
        let base_environment = session.environment.clone();
        let surface_environment = build_surface_layer(&base_environment, surface)?;
        let user_environment = surface_environment.child();
        session.environment = user_environment.clone();
        Ok(Self {
            session,
            base_environment,
            user_environment,
            surface,
        })
    }

    fn switch_surface(&mut self, surface: ReplSurface) -> Result<(), String> {
        if self.surface == surface {
            return Ok(());
        }
        let surface_environment = build_surface_layer(&self.base_environment, surface)?;
        self.user_environment
            .reparent(surface_environment)
            .map_err(str::to_string)?;
        self.surface = surface;
        Ok(())
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

pub(crate) fn run_repl(session: Session, initial_surface: ReplSurface) {
    let mut state = match ReplState::new(session, initial_surface) {
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

    fn core_state() -> ReplState {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("core bootstrap");
        ReplState::new(session, ReplSurface::Core).expect("REPL state")
    }

    fn value(state: &mut ReplState, source: &str) -> String {
        eval_program(source, &mut state.session)
            .unwrap_or_else(|error| panic!("{source}: {}", error.render(source)))
            .value
            .to_string()
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
            surface_catalog::render_name("укр", "порожній-текст?")
                .expect("UKR registry lookup")
                .starts_with("identity: 00111100")
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
        assert!(sa.contains("surface sa:"));
    }

    #[test]
    fn one_name_help_resolves_across_en_uk_sa() {
        for requested in ["map", "відобразити", "āvartana"] {
            let help = render_surface_name(ReplSurface::Ukrainian, requested).expect("name help");
            // One SENS code, every surface; ft/2 carries no per-surface status.
            assert!(help.contains("identity: 00110111"));
            assert!(help.contains("EN: map"));
            assert!(help.contains("UK: відобразити"));
            assert!(help.contains("SA: āvartana"));
        }
    }

    #[test]
    fn trilingual_status_is_measured_not_claimed() {
        let status = render_surface_status().expect("surface status");
        assert!(status.contains("trilingual present: 124/255"));
        assert!(status.contains("release parity: OPEN"));
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
