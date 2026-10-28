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

const SURFACE_PREREQUISITES: &[(&str, Option<u32>)] = &[
    ("unify.lisp", Some(0)),
    ("reason.lisp", Some(1)),
    ("forward.lisp", Some(2)),
    ("knowledge.lisp", Some(3)),
    ("persistent-map.lisp", Some(4)),
    ("persistent-vector.lisp", Some(5)),
    // Єдиний штатний loader: WASM не вбудовує окрему копію time.lisp.
    ("time.lisp", None),
    ("epistemic.lisp", Some(6)),
];

const UK_SURFACE_ASSET: u32 = 7;
const UKR_SURFACE_ASSET: u32 = 8;
const SA_SURFACE_ASSET: u32 = 9;

unsafe extern "C" {
    fn sens_wasm_source_asset_len(asset: u32) -> usize;
    fn sens_wasm_source_asset_copy(asset: u32, destination: *mut u8, capacity: usize) -> isize;
}

fn source_asset(asset: u32) -> Result<String, String> {
    const MAX_SOURCE_BYTES: usize = 16 * 1024 * 1024;

    // Zig transports opaque bytes only. SENS remains responsible for UTF-8
    // validation, parsing, and every interpretation of the source.
    let length = unsafe { sens_wasm_source_asset_len(asset) };
    if length == 0 || length > MAX_SOURCE_BYTES {
        return Err(format!(
            "Неприпустимий розмір джерела Zig asset {asset}: {length}"
        ));
    }

    let mut bytes = vec![0; length];
    let copied = unsafe { sens_wasm_source_asset_copy(asset, bytes.as_mut_ptr(), bytes.len()) };
    if copied < 0 || copied as usize != length {
        return Err(format!(
            "Zig asset {asset} скопійовано не повністю: очікувалося {length}, отримано {copied}"
        ));
    }
    String::from_utf8(bytes).map_err(|error| format!("Zig asset {asset} не є UTF-8: {error}"))
}

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

fn load_surface_prerequisite(
    name: &str,
    source: Option<&str>,
    session: &mut Session,
) -> Result<(), String> {
    let result = match (name, source) {
        ("time.lisp", None) => sens::load_time_library(session),
        (_, Some(source))
            if matches!(
                name,
                "unify.lisp"
                    | "reason.lisp"
                    | "forward.lisp"
                    | "knowledge.lisp"
                    | "persistent-map.lisp"
            ) =>
        {
            sens::eval_pinned_reasoning_source(&format!("lib/{name}"), source, session)
        }
        (_, Some(source)) => eval_program(source, session),
        (_, None) => return Err(format!("Бібліотека {name} не має штатного завантажувача")),
    };
    result.map(|_| ()).map_err(|error| {
        let diagnostic = source
            .map(|source| error.render(source))
            .unwrap_or_else(|| error.to_string());
        format!("Помилка завантаження {name}: {diagnostic}")
    })
}

fn build_surface_layer(base: &Environment, surface: WebSurface) -> Result<Environment, String> {
    let layer = base.child();
    if matches!(
        surface,
        WebSurface::Ukrainian | WebSurface::UkrainianFull | WebSurface::Sanskrit
    ) {
        let mut session = Session {
            environment: layer.clone(),
        };
        for (name, asset) in SURFACE_PREREQUISITES {
            let source = asset.map(source_asset).transpose()?;
            load_surface_prerequisite(name, source.as_deref(), &mut session)?;
        }
        let (name, asset) = match surface {
            WebSurface::Ukrainian => ("uk.lisp", UK_SURFACE_ASSET),
            WebSurface::UkrainianFull => ("ukr.lisp", UKR_SURFACE_ASSET),
            WebSurface::Sanskrit => ("sa.lisp", SA_SURFACE_ASSET),
            WebSurface::Core | WebSurface::English => unreachable!(),
        };
        let source = source_asset(asset)?;
        eval_program(&source, &mut session)
            .map_err(|error| format!("failed to load {name}: {}", error.render(&source)))?;
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
        let surface_environment =
            build_surface_layer(&base_environment, WebSurface::UkrainianFull)?;
        let user_environment = surface_environment.child();
        session.environment = user_environment.clone();
        Ok(Self {
            session,
            base_environment,
            user_environment,
            surface: WebSurface::UkrainianFull,
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

fn remap_literate_error(
    mut error: sens::LanguageError,
    offset_maps: &[(usize, usize, usize)],
) -> sens::LanguageError {
    error.span.start = sens_literate::remap_offset(error.span.start, offset_maps);
    error.span.end = sens_literate::remap_offset(error.span.end, offset_maps);
    error
}

/// Ensures the shared session exists and has core.lisp preloaded.
/// Idempotent — subsequent calls are no-ops.
fn init_if_needed() -> Result<(), String> {
    SESSION.with(|slot| {
        let mut guard = slot.borrow_mut();
        if guard.is_none() {
            *guard = Some(WebSession::new(session_with_core()?)?);
        }
        Ok(())
    })
}

fn session_with_core() -> Result<Session, String> {
    let mut session = Session::default();
    // Той самий bootstrap, що й у native: макроси, перевірка чинності
    // кешу та вибір профілю належать одному loader, а не окремому WASM шляху.
    sens::load_core_library(&mut session)
        .map_err(|error| format!("Помилка штатного завантаження Core4: {error}"))?;
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
        // Ukrainian human source uses decimal integer spellings as a source
        // projection into exact D24+ values. This happens before lowering for
        // both ordinary .lisp and fenced Markdown code, with original spans
        // restored for diagnostics. D1-D10 identities are never promoted.
        let (result, forms) = if matches!(
            state.surface,
            WebSurface::Ukrainian | WebSurface::UkrainianFull
        ) {
            let (code, offset_maps) =
                sens_literate::extract_code(source, source_mode == SourceMode::Literate);
            if source_mode == SourceMode::Literate && offset_maps.is_empty() {
                (
                    sens::EvalResult {
                        value: sens::Value::Nil,
                        output: vec!["No sens code blocks found in markdown document.".to_string()],
                    },
                    vec![],
                )
            } else {
                let parsed = sens::parse(&code).map_err(|error| {
                    let error = remap_literate_error(error, &offset_maps);
                    JsValue::from_str(&render_error_for_presentation(
                        &error,
                        source,
                        state.surface.presentation(),
                    ))
                })?;
                let projected =
                    sens::source_projection::project_ukr_decimal_integer_literals(&parsed, &code)
                        .map_err(|error| {
                        let error = remap_literate_error(error, &offset_maps);
                        JsValue::from_str(&render_error_for_presentation(
                            &error,
                            source,
                            state.surface.presentation(),
                        ))
                    })?;
                sens::load_core_library(&mut state.session).map_err(|error| {
                    let error = remap_literate_error(error, &offset_maps);
                    JsValue::from_str(&render_error_for_presentation(
                        &error,
                        source,
                        state.surface.presentation(),
                    ))
                })?;
                let result = sens::eval_parsed_expressions(&projected, &mut state.session)
                    .map_err(|error| {
                        let error = remap_literate_error(error, &offset_maps);
                        JsValue::from_str(&render_error_for_presentation(
                            &error,
                            source,
                            state.surface.presentation(),
                        ))
                    })?;
                (result, projected)
            }
        } else {
            sens_literate::eval_literate(source, source_mode, &mut state.session).map_err(
                |error| {
                    JsValue::from_str(&render_error_for_presentation(
                        &error,
                        source,
                        state.surface.presentation(),
                    ))
                },
            )?
        };

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



/// Direct JS-callable string-slice: char-indexed substring with clamping.
/// Convenience for browser text processing without full sens evaluation.
#[wasm_bindgen]
pub fn string_slice(s: &str, start: i64, end: i64) -> String {
    let length = s.chars().count() as i64;
    let start = start.max(0).min(length) as usize;
    let end = end.clamp(start as i64, length) as usize;
    sens::string_slice_text(s, start, end)
}
