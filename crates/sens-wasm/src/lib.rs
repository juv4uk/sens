//! WebAssembly bindings exposing the canonical sens engine to the browser.
//! Persistent session with core.lisp preloaded on first call.

use sens::{
    eval_program, present_system_message, render_error_for_presentation,
    render_value_for_presentation, Environment, PresentationLanguage, Session,
};
use sens_literate::SourceMode;
use serde::{Deserialize, Serialize};
use std::cell::RefCell;
use wasm_bindgen::prelude::*;

const CORE_FASL: &[u8] = include_bytes!("../../../lib/core4.lisp.fasl");

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
enum WebSurface {
    Core,
    English,
    Ukrainian,
    UkrainianFull,
    Sanskrit,
}

impl WebSurface {
    fn parse(value: &str) -> Option<Self> {
        match value.trim().to_lowercase().as_str() {
            "core" | "ядро" => Some(Self::Core),
            "en" | "english" | "англійська" => Some(Self::English),
            "ук" | "українська" => Some(Self::Ukrainian),
            "укр" | "ukr" | "українська-повна" => Some(Self::UkrainianFull),
            "sa" | "sanskrit" | "санскрит" => Some(Self::Sanskrit),
            _ => None,
        }
    }

    fn code(self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::English => "en",
            Self::Ukrainian => "ук",
            Self::UkrainianFull => "укр",
            Self::Sanskrit => "sa",
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

fn build_surface_layer(base: &Environment, surface: WebSurface) -> Result<Environment, String> {
    let layer = base.child();
    if matches!(surface, WebSurface::Ukrainian | WebSurface::UkrainianFull | WebSurface::Sanskrit) {
        let mut session = Session {
            environment: layer.clone(),
        };
        for (name, source) in SURFACE_PREREQUISITES {
            eval_program(source, &mut session)
                .map_err(|error| format!("failed to load {name}: {}", error.render(source)))?;
        }
        let (name, source) = match surface {
            WebSurface::Ukrainian => ("uk.lisp", UK_SURFACE),
            WebSurface::UkrainianFull => ("ukr.lisp", UKR_SURFACE),
            WebSurface::Sanskrit => ("sa.lisp", SA_SURFACE),
            WebSurface::Core | WebSurface::English => unreachable!(),
        };
        eval_program(source, &mut session)
            .map_err(|error| format!("failed to load {name}: {}", error.render(source)))?;
    }
    Ok(layer)
}

struct WebSession {
    session: Session,
    base_environment: Environment,
    user_environment: Environment,
    surface: WebSurface,
}

impl WebSession {
    fn new(mut session: Session) -> Result<Self, String> {
        let base_environment = session.environment.clone();
        let surface_environment = build_surface_layer(&base_environment, WebSurface::Core)?;
        let user_environment = surface_environment.child();
        session.environment = user_environment.clone();
        Ok(Self {
            session,
            base_environment,
            user_environment,
            surface: WebSurface::Core,
        })
    }

    fn switch_surface(&mut self, surface: WebSurface) -> Result<(), String> {
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

thread_local! {
    static SESSION: RefCell<Option<WebSession>> = const { RefCell::new(None) };
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Evaluation {
    value: String,
    output: Vec<String>,
    ast: String,
    engine: String,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Diagnostic {
    from: usize,
    to: usize,
    severity: &'static str,
    message: String,
}

/// Ensures the shared session exists and has core.lisp preloaded.
/// Idempotent — subsequent calls are no-ops.
fn init_if_needed() -> Result<(), String> {
    SESSION.with(|slot| {
        let mut guard = slot.borrow_mut();
        if guard.is_none() {
            *guard = Some(WebSession::new(session_with_core_fasl(CORE_FASL)?)?);
        }
        Ok(())
    })
}

fn session_with_core_fasl(fasl_bytes: &[u8]) -> Result<Session, String> {
    let mut session = Session::default();
    let (expressions, _) = sens::fasl_decode_program(fasl_bytes)
        .ok_or_else(|| "failed to decode core4.lisp.fasl (format or hash mismatch)".to_string())?;
    sens::eval_parsed_expressions(&expressions, &mut session)
        .map_err(|error| format!("failed to preload core.lisp: {error}"))?;
    Ok(session)
}

#[wasm_bindgen]
pub fn evaluate(source: &str, mode: JsValue) -> Result<JsValue, JsValue> {
    init_if_needed().map_err(|error| JsValue::from_str(&error))?;

    let mode_str = mode.as_string().unwrap_or_default();
    let source_mode = if mode_str == "markdown" {
        SourceMode::Literate
    } else {
        SourceMode::PureLisp
    };

    SESSION.with(|slot| {
        let mut guard = slot.borrow_mut();
        let state = guard.as_mut().expect("session set by init_if_needed");
        let (result, forms) =
            sens_literate::eval_literate(source, source_mode, &mut state.session).map_err(
                |e| {
                    JsValue::from_str(&render_error_for_presentation(
                        &e,
                        source,
                        state.surface.presentation(),
                    ))
                },
            )?;

        let evaluation = Evaluation {
            value: render_value_for_presentation(&result.value, state.surface.presentation()),
            output: result.output,
            ast: format!("{forms:#?}"),
            engine: "sens · WASM".to_string(),
        };

        serde_wasm_bindgen::to_value(&evaluation).map_err(|e| JsValue::from_str(&e.to_string()))
    })
}

/// Force a fresh session (clears all definitions).
#[wasm_bindgen]
pub fn reset_session() {
    SESSION.with(|slot| {
        *slot.borrow_mut() = None;
    });
}

fn set_surface_impl(name: &str) -> Result<String, String> {
    init_if_needed()?;
    let surface = WebSurface::parse(name)
        .ok_or_else(|| format!("unknown surface: {name}; expected ук|укр|en|sa|core"))?;
    SESSION.with(|slot| {
        let mut guard = slot.borrow_mut();
        let state = guard.as_mut().expect("session set by init_if_needed");
        state.switch_surface(surface)?;
        Ok(state.surface.code().to_string())
    })
}

/// Змінює лише interaction/programming surface поточної browser-сесії.
#[wasm_bindgen]
pub fn set_surface(name: &str) -> Result<String, JsValue> {
    set_surface_impl(name).map_err(|error| JsValue::from_str(&error))
}

#[wasm_bindgen]
pub fn current_surface() -> String {
    if init_if_needed().is_err() {
        return "core".to_string();
    }
    SESSION.with(|slot| {
        slot.borrow()
            .as_ref()
            .map(|state| state.surface.code().to_string())
            .unwrap_or_else(|| "core".to_string())
    })
}

#[wasm_bindgen]
pub fn diagnose(source: &str, mode: JsValue) -> JsValue {
    let mode_str = mode.as_string().unwrap_or_default();
    let is_literate = mode_str == "markdown";
    let presentation = if init_if_needed().is_ok() {
        SESSION.with(|slot| {
            slot.borrow()
                .as_ref()
                .map(|state| state.surface.presentation())
                .unwrap_or(PresentationLanguage::Canonical)
        })
    } else {
        PresentationLanguage::Canonical
    };
    serde_wasm_bindgen::to_value(&diagnose_impl_with_presentation(
        source,
        is_literate,
        presentation,
    ))
    .unwrap_or(JsValue::NULL)
}

/// Non-wasm_bindgen core of diagnose() -- pulled out so native #[test]s
/// can exercise it directly (JsValue isn't constructible from a plain
/// native test without the wasm-bindgen-test harness).
#[cfg(test)]
fn diagnose_impl(source: &str, is_literate: bool) -> Vec<Diagnostic> {
    diagnose_impl_with_presentation(source, is_literate, PresentationLanguage::Canonical)
}

fn diagnose_impl_with_presentation(
    source: &str,
    is_literate: bool,
    presentation: PresentationLanguage,
) -> Vec<Diagnostic> {
    // extract_code/remap_offset are the same functions parse_literate()
    // itself uses internally (sens-literate/src/lib.rs) -- called
    // directly here, instead of going through parse_literate(), so the
    // offset_maps are available afterward to remap arity_diagnostics'
    // spans too, not just a parse error's.
    let (concatenated, offset_maps) = sens_literate::extract_code(source, is_literate);

    let mut diagnostics: Vec<Diagnostic> = Vec::new();

    if is_literate && offset_maps.is_empty() {
        return diagnostics;
    }

    match sens::parse(&concatenated) {
        Err(e) => diagnostics.push(Diagnostic {
            from: sens_literate::remap_offset(e.span.start, &offset_maps),
            to: sens_literate::remap_offset(e.span.end, &offset_maps),
            severity: "error",
            message: present_system_message(&e.message, presentation),
        }),
        // Only meaningful to check arity once the source actually
        // parses -- same order the native LSP server uses
        // (sens-lsp/src/server.rs's publish()), which this reuses
        // rather than reimplementing: canonical language-item arities
        // from sens::language_items(), not a WASM-side guess.
        Ok(_) => {
            if let Ok(arity_diags) = sens_lsp::analysis::arity_diagnostics(&concatenated) {
                for d in arity_diags {
                    diagnostics.push(Diagnostic {
                        from: sens_literate::remap_offset(d.span.start, &offset_maps),
                        to: sens_literate::remap_offset(d.span.end, &offset_maps),
                        severity: "error",
                        message: present_system_message(&d.message, presentation),
                    });
                }
            }
        }
    }

    diagnostics
}

// ── native tests ──

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(target_arch = "wasm32")]
    use wasm_bindgen_test::wasm_bindgen_test;

    #[test]
    fn core_lisp_definitions_available_after_init() {
        init_if_needed().expect("core.lisp preload must succeed");
        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            let (result, _) = sens_literate::eval_literate(
                "(length (quote (a b c)))",
                SourceMode::PureLisp,
                session,
            )
            .expect("length should work after core.lisp preload");
            assert_eq!(result.value.to_string(), "3");
        });
    }

    #[test]
    fn web_surface_switch_is_layered_and_preserves_user_definitions() {
        reset_session();
        init_if_needed().expect("core preload");

        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            eval_program("(define крок 1)", session).expect("user def");
            eval_program("(define додай-крок (lambda (x) (+ x крок)))", session)
                .expect("closure def");
        });

        assert_eq!(set_surface_impl("ук").expect("ук"), "ук");
        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            let uk = eval_program("(атом? 'мама)", session).expect("uk alias");
            assert_eq!(uk.value.to_string(), "(1)");
            // `хибне?` (not?) answers t/(); t is presented in Ukrainian.
            let truth = eval_program("(хибне? '())", session).expect("uk predicate");
            assert_eq!(
                render_value_for_presentation(&truth.value, WebSurface::Ukrainian.presentation()),
                "істина"
            );
            eval_program("(define крок 2)", session).expect("redefine user value");
            let closure = eval_program("(додай-крок 5)", session).expect("closure");
            assert_eq!(closure.value.to_string(), "7");
        });

        assert_eq!(set_surface_impl("core").expect("core"), "core");
        SESSION.with(|slot| {
            let guard = slot.borrow();
            let state = guard.as_ref().unwrap();
            assert!(state.session.environment.get("атом?").is_none());
            assert!(state.session.environment.get("додай-крок").is_some());
        });
    }

    #[test]
    fn ukr_surface_selects_full_ukrainian_namespace() {
        reset_session();
        init_if_needed().expect("core preload");
        assert_eq!(set_surface_impl("ukr").expect("ukr"), "укр");
        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            let full = eval_program("(порожній-текст? \"\")", session)
                .expect("full Ukrainian spelling");
            assert_eq!(full.value.to_string(), "(1)");
        });
    }

    #[test]
    fn broken_core_preload_is_reported_instead_of_installing_partial_session() {
        let error = session_with_core_fasl(b"broken fasl")
            .expect_err("if FASL loading fails, it must propagate rather than swallow the error");
        assert!(
            error.contains("failed to decode") || error.contains("failed to preload"),
            "{error}"
        );
    }

    #[test]
    fn wasm_session_exposes_unicode_string_slice_with_clamped_bounds() {
        reset_session();
        init_if_needed().expect("core.lisp preload must succeed");

        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;

            let (unicode, _) = sens_literate::eval_literate(
                r#"(string-slice "привіт" 1 3)"#,
                SourceMode::PureLisp,
                session,
            )
            .expect("the WASM session must expose the canonical string-slice primitive");
            assert_eq!(unicode.value.to_string(), r#""ри""#);

            let (clamped, _) = sens_literate::eval_literate(
                r#"(string-slice "abc" 2 99)"#,
                SourceMode::PureLisp,
                session,
            )
            .expect("string-slice must preserve its canonical clamping semantics in WASM");
            assert_eq!(clamped.value.to_string(), r#""c""#);
        });
    }

    #[test]
    fn persistent_session_preserves_definitions_across_calls() {
        reset_session();
        init_if_needed().expect("core.lisp preload must succeed");

        // Define foo in one call
        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            let _ = sens_literate::eval_literate(
                "(def foo (lambda (x) (+ x 1)))",
                SourceMode::PureLisp,
                session,
            )
            .expect("def should succeed");
        });

        // Call foo in a separate eval — same session
        SESSION.with(|slot| {
            let mut guard = slot.borrow_mut();
            let session = &mut guard.as_mut().unwrap().session;
            let (result, _) =
                sens_literate::eval_literate("(foo 5)", SourceMode::PureLisp, session)
                    .expect("foo should be visible from previous eval");
            assert_eq!(result.value.to_string(), "6");
        });
    }

    // wasm32-only: exercises the public wasm_bindgen `evaluate()` path (the actual
    // JS-callable entry the browser REPL uses) across two separate invocations with
    // no in-between state passing — the session persists in the wasm module itself.
    // Native persistence is covered separately by
    // persistent_session_preserves_definitions_across_calls above (wasm-bindgen's
    // JsValue is a stub on non-wasm32, so this tests the real boundary only on wasm32).
    #[cfg(target_arch = "wasm32")]
    #[wasm_bindgen_test]
    fn wasm32_evaluate_keeps_definitions_across_calls() {
        reset_session();
        init_if_needed().expect("core.lisp preload must succeed");

        let mode = JsValue::from_str("sens");
        evaluate("(def foo (lambda (x) (+ x 1)))", mode.clone()).expect("def should succeed");
        let second: Evaluation = serde_wasm_bindgen::from_value(
            evaluate("(foo 5)", mode).expect("second call should see foo from the first"),
        )
        .expect("decode second evaluation");
        assert_eq!(second.value, "6");
    }

    #[test]
    fn diagnose_reports_arity_mismatch_in_pure_lisp() {
        // Same example sens-lsp/tests/e2e.rs's
        // t15_arity_diagnostics_are_conservative_and_shadow_aware uses
        // for the native LSP -- confirms the WASM side now reports the
        // same canonical diagnostic, not just parse errors.
        let diagnostics = diagnose_impl("(car 1 2)", false);
        assert_eq!(diagnostics.len(), 1);
        assert!(
            diagnostics[0]
                .message
                .contains("arity: car expects 1, received 2"),
            "expected canonical arity message, got: {}",
            diagnostics[0].message
        );
        assert_eq!(diagnostics[0].severity, "error");
    }

    #[test]
    fn diagnose_reports_no_arity_diagnostic_for_valid_call() {
        let diagnostics = diagnose_impl("(car (quote (1 2)))", false);
        assert!(
            diagnostics.is_empty(),
            "valid call must not be flagged: {diagnostics:?}"
        );
    }

    #[test]
    fn diagnose_remaps_arity_span_correctly_in_literate_mode() {
        // The bad call sits inside a fenced ```sens block, offset
        // from the start of the document by the markdown prose before
        // it -- this is exactly the case extract_code's offset_maps
        // exist for. If remapping were wrong (e.g. reporting the
        // position within the *extracted* code instead of the original
        // document), `from`/`to` would point at the wrong characters.
        let source = "# Doc\n\nSome prose.\n\n```sens\n(car 1 2)\n```\n";
        let diagnostics = diagnose_impl(source, true);
        assert_eq!(diagnostics.len(), 1);
        let d = &diagnostics[0];
        assert_eq!(
            &source[d.from..d.to],
            "(car 1 2)",
            "remapped span must point at the actual call in the original document, got: {:?}",
            &source[d.from..d.to]
        );
    }

    #[test]
    fn diagnose_reports_exact_parse_error_span_in_pure_lisp() {
        let source = ")";
        let diagnostics = diagnose_impl(source, false);

        assert_eq!(diagnostics.len(), 1);
        let diagnostic = &diagnostics[0];
        assert_eq!(diagnostic.severity, "error");
        assert_eq!((diagnostic.from, diagnostic.to), (0, 1));
        assert_eq!(&source[diagnostic.from..diagnostic.to], ")");
    }

    #[test]
    fn diagnose_remaps_parse_error_span_in_literate_mode() {
        let source = "# Doc\n\nProse before the program.\n\n```sens\n)\n```\n";
        let diagnostics = diagnose_impl(source, true);

        assert_eq!(diagnostics.len(), 1);
        let diagnostic = &diagnostics[0];
        assert_eq!(diagnostic.severity, "error");
        assert_eq!(
            &source[diagnostic.from..diagnostic.to],
            ")",
            "parse-error span must point into the original Markdown source"
        );
    }

    #[test]
    fn diagnose_accepts_empty_source_and_literate_prose_without_code() {
        assert!(diagnose_impl("", false).is_empty());
        assert!(diagnose_impl("", true).is_empty());
        assert!(diagnose_impl("# Notes\n\nNo executable fence here.\n", true).is_empty());
    }
}

/// Direct JS-callable string-slice: char-indexed substring with clamping.
/// Convenience for browser text processing without full sens evaluation.
#[wasm_bindgen]
pub fn string_slice(s: &str, start: i64, end: i64) -> String {
    let length = s.chars().count() as i64;
    let start = start.max(0).min(length) as usize;
    let end = end.clamp(start as i64, length) as usize;
    sens::string_slice_text(s, start, end)
}
