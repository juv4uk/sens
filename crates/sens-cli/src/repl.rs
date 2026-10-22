//! Інтерактивний stdio REPL: історія, interaction-only echo fallback і
//! перемикання програмних поверхонь. `:мова` / `:surface` не є Lisp syntax:
//! це команди оболонки над одним і тим самим семантичним ядром.

mod surface_catalog;

use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use sens::{
    eval_program, render_value_for_presentation, BinaryNumber, CoreDomainIdentity, DomainIdentity,
    Environment, ExactDomainWord, Expr, ExprKind, PhysicalT5Program, PresentationLanguage, Session,
    Value,
};
use std::env;
use std::path::PathBuf;
use std::process;

// REPL-local FFI: other CLI binaries acquire no extra dead_code warnings.
#[cfg(feature = "zig-transport")]
unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_repl_persistent_vector_bytes_copy(dst: *mut u8, cap: usize) -> isize;
    fn sens_zig_repl_epistemic_bytes_copy(dst: *mut u8, cap: usize) -> isize;
    fn sens_zig_meta_eval_bytes_copy(dst: *mut u8, cap: usize) -> isize;
}
#[cfg(feature = "zig-transport")]
fn repl_zig_source(
    copy: unsafe extern "C" fn(*mut u8, usize) -> isize,
    label: &str,
) -> Result<String, String> {
    if unsafe { sens_zig_codec_abi_version() } != 2 {
        return Err(format!("{label}: Zig ABI version mismatch"));
    }
    let n = unsafe { copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0) };
    if n <= 0 {
        return Err(format!("{label}: invalid Zig byte length {n}"));
    }
    let len = usize::try_from(n).map_err(|_| format!("{label}: Zig length overflow"))?;
    if len > 8 * 1024 * 1024 {
        return Err(format!("{label}: host byte bound exceeded"));
    }
    let mut bytes = vec![0u8; len];
    let got = unsafe { copy(bytes.as_mut_ptr(), len) };
    if got != n {
        return Err(format!("{label}: Zig exact copy rejected {got}"));
    }
    String::from_utf8(bytes).map_err(|err| format!("{label}: UTF-8 source error {err}"))
}
// No Rust include_str! of SENS project source. Zig owns byte transport.
fn surface_prerequisite_sources() -> Result<Vec<(&'static str, String)>, String> {
    #[cfg(feature = "zig-transport")]
    {
        Ok(vec![
            (
                "persistent-vector.lisp",
                repl_zig_source(
                    sens_zig_repl_persistent_vector_bytes_copy,
                    "ZIG_REPL_PERSISTENT_VECTOR",
                )?,
            ),
            ("time.lisp", crate::time_library_source_zig_only()?),
            (
                "epistemic.lisp",
                repl_zig_source(sens_zig_repl_epistemic_bytes_copy, "ZIG_REPL_EPISTEMIC")?,
            ),
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

fn t5m_domain_identity(width: usize, bits: u16) -> Result<DomainIdentity, String> {
    let width = u8::try_from(width).map_err(|_| "T5M domain width exceeds u8")?;
    let coordinate = sens::domain_ladder::DomainCoordinate::new(width, bits)
        .ok_or_else(|| format!("invalid exact D{width} coordinate {bits}"))?;
    Ok(DomainIdentity::from_coordinate(coordinate))
}

fn t5m_surface_layout(surface: ReplSurface) -> sens::Text7Layout {
    match surface {
        ReplSurface::Core | ReplSurface::English => sens::Text7Layout::En,
        ReplSurface::Ukrainian | ReplSurface::UkrainianFull => sens::Text7Layout::Uk,
        ReplSurface::Sanskrit => sens::Text7Layout::SaDeva,
        ReplSurface::Lisp => sens::Text7Layout::En,
    }
}

fn append_t5m_expression(
    expression: &Expr,
    layout: sens::Text7Layout,
    words: &mut Vec<ExactDomainWord>,
    depth: usize,
) -> Result<(), String> {
    append_t5m_expression_context(expression, layout, words, depth, false)
}

/// Цитовані протокольні символи — дані, не українські викличні імена.
/// Їхні W7 glyph-и мають точний ASCII/en маршрут, а D2 списки мають
/// канонічні 00-роздільники. Викличні імена надалі лишаються укр.
fn append_t5m_expression_context(
    expression: &Expr,
    layout: sens::Text7Layout,
    words: &mut Vec<ExactDomainWord>,
    depth: usize,
    quoted_data: bool,
) -> Result<(), String> {
    if depth > 768 {
        return Err("T5M source AST exceeds the SENS nesting limit".into());
    }
    let control = |bits| t5m_domain_identity(2, bits).map(ExactDomainWord::Identity);
    match &expression.kind {
        ExprKind::DomainCall(identity, arguments) => {
            words.push(control(0b10)?);
            words.push(ExactDomainWord::Identity(DomainIdentity::from(*identity)));
            for argument in arguments.iter() {
                words.push(control(0b00)?);
                append_t5m_expression_context(
                    argument,
                    layout,
                    words,
                    depth + 1,
                    quoted_data || (identity.width() == 3 && identity.packed_bits() == 0b001),
                )?;
            }
            words.push(control(0b01)?);
        }
        ExprKind::DomainIdentity(identity) => {
            if matches!(identity, DomainIdentity::D2(_)) {
                return Err(
                    "D2 identity is structural and cannot be a standalone T5M value".into(),
                );
            }
            words.push(ExactDomainWord::Identity(*identity));
        }
        ExprKind::BinaryNumber(number) => {
            words.push(ExactDomainWord::number(number.clone()).map_err(str::to_owned)?);
        }
        ExprKind::List(items) if items.is_empty() => {
            words.push(ExactDomainWord::Identity(t5m_domain_identity(3, 0)?));
        }
        ExprKind::List(items) => {
            // Поточний Lisp QUOTE задає D3:001, не W7 напис «як-є».
            // Нормалізація відбувається лише в коді; вкладені цитовані
            // списки залишаються незмінними даними.
            let quoted_head = !quoted_data
                && matches!(
                    items.first().map(|item| &item.kind),
                    Some(ExprKind::DomainIdentity(identity))
                        if identity.width() == 3 && identity.packed_bits() == 0b001
                )
                || !quoted_data
                    && matches!(
                        items.first().map(|item| &item.kind),
                        Some(ExprKind::Symbol(name)) if name.as_ref() == "як-є"
                    );
            words.push(control(0b10)?);
            if quoted_head {
                words.push(ExactDomainWord::Identity(t5m_domain_identity(3, 0b001)?));
                for item in items.iter().skip(1) {
                    words.push(control(0b00)?);
                    append_t5m_expression_context(item, layout, words, depth + 1, true)?;
                }
            } else {
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        words.push(control(0b00)?);
                    }
                    append_t5m_expression_context(item, layout, words, depth + 1, quoted_data)?;
                }
            }
            words.push(control(0b01)?);
        }
        ExprKind::Pair(head, tail) => {
            // D7-символ із кількох glyph-ів нині має D2-рамку списку.
            // У *хвості* крапкової пари це робить improper пару
            // правильним списком без жодної помилки. Не проголошуємо
            // таку зміну структури оборотною: атомний текстовий носій
            // мусить бути доведений окремо, а не вигаданий у Rust.
            if let ExprKind::Symbol(name) = &tail.kind {
                // Цитата не змінює структури: W7/D7 glyph-list не є
                // атомом хвоста ані в даних, ані в звичайній формі.
                if sens::semantic_registry_export::admitted_core_domain_for_surface(name).is_none()
                {
                    return Err(format!(
                        "T5M_DOTTED_TEXT_TAIL_NOT_ATOMIC symbol={name:?}: D7 glyph-list cannot replace a dotted-pair atom"
                    ));
                }
            }
            words.push(control(0b10)?);
            append_t5m_expression_context(head, layout, words, depth + 1, quoted_data)?;
            words.push(control(0b11)?);
            append_t5m_expression_context(tail, layout, words, depth + 1, quoted_data)?;
            words.push(control(0b01)?);
        }
        ExprKind::Symbol(name) => {
            // У цитаті ратифікована тотожність має пріоритет над текстом.
            // Нова викличність з одного лише збігу напису не виникає.
            if quoted_data {
                if let Some(identity) =
                    sens::semantic_registry_export::admitted_core_domain_for_surface(name)
                {
                    words.push(ExactDomainWord::Identity(DomainIdentity::from(identity)));
                    return Ok(());
                }
            }
            // Англійські мітки зовнішнього протоколу (world/tell/...)
            // лишаються цитованими даними. Нецитована укр-проєкція
            // НІКОЛИ не переходить до англійського fallback.
            let symbol_layout = if quoted_data && name.is_ascii() {
                sens::Text7Layout::En
            } else {
                layout
            };
            let text = sens::encode_text7(name, symbol_layout).map_err(|error| {
                format!(
                    "T5M identifier projection: symbol={name:?} source_byte={}: {error}",
                    expression.span.start
                )
            })?;
            words.push(control(0b10)?);
            for (index, cell) in text.cells().iter().enumerate() {
                if index > 0 {
                    words.push(control(0b00)?);
                }
                words.push(ExactDomainWord::Identity(t5m_domain_identity(
                    7,
                    u16::from(*cell),
                )?));
            }
            words.push(control(0b01)?);
        }
        ExprKind::Number(value, _exactness) => {
            // Усередині QUOTE числовий вузол може залишитися у людському AST.
            // Точне зниження до D24+ вже існує для звичайних числових джерел;
            // використовуємо його ж, без текстового W7 або host-арифметики.
            let exact = exact_integer_source_word(&value.to_string())?;
            append_t5m_expression_context(&exact, layout, words, depth + 1, quoted_data)?;
        }
        ExprKind::Rational(value) => {
            let spelling = value.to_string();
            let (numerator, denominator) = spelling
                .split_once('/')
                .map_or((spelling.as_str(), "1"), |parts| parts);
            let numerator = exact_integer_source_word(numerator)?;
            let denominator = exact_integer_source_word(denominator)?;
            let quotient = exact_d5_surface("частка")?;
            let ratio = Expr {
                kind: ExprKind::DomainCall(quotient, vec![numerator, denominator].into()),
                span: expression.span,
            };
            append_t5m_expression_context(&ratio, layout, words, depth + 1, quoted_data)?;
        }
        ExprKind::String(..) => {
            return Err(
                "T5M string values have no admitted exact D7 projection in this REPL path".into(),
            );
        }
        ExprKind::NumericBuffer(..) => {
            return Err("T5M REPL has no admitted NumericBuffer source form".into());
        }
        ExprKind::Call(..) | ExprKind::Sid(..) => {
            return Err("T5M rejects historical SID8/SENS8 call nodes".into());
        }
        ExprKind::Local { .. } => {
            return Err("T5M REPL cannot transport an unresolved lexical slot".into());
        }
    }
    Ok(())
}

fn exact_integer_source_word(source: &str) -> Result<Expr, String> {
    let forms = sens::parse_mixed_exact_domain(source).map_err(|error| error.render(source))?;
    match forms.as_slice() {
        [expression @ Expr {
            kind: ExprKind::BinaryNumber(_),
            ..
        }] => Ok(expression.clone()),
        _ => Err(format!(
            "T5M exact ratio component did not lower to D24+: {source}"
        )),
    }
}

fn catalog_domain_identity(identity: &str) -> Result<Option<DomainIdentity>, String> {
    let Some((domain, bits)) = identity.split_once(':') else {
        return Err(format!(
            "projection catalog identity is malformed: {identity}"
        ));
    };
    let width = domain
        .strip_prefix('D')
        .and_then(|value| value.parse::<usize>().ok())
        .ok_or_else(|| format!("projection catalog domain is malformed: {identity}"))?;
    if bits.len() != width || !bits.bytes().all(|bit| matches!(bit, b'0' | b'1')) {
        return Err(format!(
            "projection catalog word is not exact-width: {identity}"
        ));
    }
    let packed = u16::from_str_radix(bits, 2)
        .map_err(|_| format!("projection catalog word is out of range: {identity}"))?;
    t5m_domain_identity(width, packed).map(Some)
}

/// Non-Ukrainian REPL spellings are accepted only when the selected table
/// column maps to the same callable identity already admitted by the full
/// Ukrainian source-head projection. This adds a surface route, not callability.
fn selected_surface_callable(
    surface: ReplSurface,
    name: &str,
) -> Result<Option<sens::CoreDomainIdentity>, String> {
    let projected_name = match surface {
        // The projection is displayed in its canonical uppercase spelling,
        // while the interactive reader accepts the same Lisp name lowercase.
        ReplSurface::Lisp => name.to_uppercase(),
        _ => name.to_owned(),
    };
    let Some(identity_text) =
        surface_catalog::identity_for_surface_name(surface.code(), &projected_name)?
    else {
        return Ok(None);
    };
    let Some(identity) = catalog_domain_identity(&identity_text)? else {
        return Ok(None);
    };
    let Some(ukr_name) = surface_catalog::ukr_name_for_identity(&identity_text)? else {
        return Ok(None);
    };
    // D3–D6 and proved selectors keep their exact source authority.
    let admitted = sens::semantic_registry_export::exact_uk_callable_for_source_head(&ukr_name)
        .filter(|admitted| *admitted == identity)
        .and_then(DomainIdentity::core_operation);
    if admitted.is_some() {
        return Ok(admitted);
    }

    // The D8 table is a distinct, owner-ratified ladder, not historical W8.
    // The source catalog has already proved the full Ukrainian spelling and
    // exact D8 coordinate. DomainIdentity::core_operation admits only real
    // resident mechanisms (currently CHAR-CODE, READ and three text I/O ops).
    // Do not turn other D8 residents, D7 keyboard text, or English aliases
    // into callable SENS just because a spelling exists in a table.
    if identity.width() == 8
        && projected_name == ukr_name
        && matches!(surface, ReplSurface::UkrainianFull | ReplSurface::Ukrainian)
    {
        return Ok(identity.core_operation());
    }
    Ok(None)
}

fn project_repl_surface_expression(
    expression: &Expr,
    session: &Session,
    surface: ReplSurface,
    depth: usize,
) -> Result<Expr, String> {
    project_repl_surface_expression_in_scope(expression, session, surface, depth, &[])
}

fn project_repl_surface_expression_in_scope(
    expression: &Expr,
    session: &Session,
    surface: ReplSurface,
    depth: usize,
    bound: &[std::rc::Rc<str>],
) -> Result<Expr, String> {
    if depth > 768 {
        return Err("REPL projection lowering exceeds the SENS nesting limit".into());
    }
    let ExprKind::Symbol(name) = &expression.kind else {
        if let ExprKind::List(items) = &expression.kind {
            if items.is_empty() {
                return Ok(expression.clone());
            }
            if matches!(
                &items[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 3 && identity.packed_bits() == 0b001
            ) || matches!(&items[0].kind, ExprKind::Symbol(name) if matches!(name.as_ref(), "quote" | "як-є" | "'"))
            {
                return Ok(expression.clone());
            }

            // A projection spelling is only a lookup route. In value position
            // it lowers to the same exact identity as in call-head position.
            // Lexical binders and persistent REPL bindings keep their Text7 name.
            let mut lambda_identity = None;
            if let ExprKind::Symbol(head) = &items[0].kind {
                if session.environment.get(head).is_none() {
                    lambda_identity =
                        selected_surface_callable(surface, head)?.filter(|identity| {
                            matches!(
                                identity,
                                CoreDomainIdentity::D4(word)
                                    if word.word().packed_bits() == 0b0010
                            )
                        });
                }
            }
            if let Some(identity) = lambda_identity {
                let mut lambda_bound = bound.to_vec();
                if let Some(parameters) = items.get(1) {
                    collect_repl_binders(parameters, &mut lambda_bound);
                }
                let mut projected = Vec::with_capacity(items.len());
                projected.push(Expr {
                    kind: ExprKind::DomainIdentity(DomainIdentity::from(identity)),
                    span: items[0].span,
                });
                if let Some(parameters) = items.get(1) {
                    projected.push(parameters.clone());
                }
                projected.extend(
                    items
                        .iter()
                        .skip(2)
                        .map(|item| {
                            project_repl_surface_expression_in_scope(
                                item,
                                session,
                                surface,
                                depth + 1,
                                &lambda_bound,
                            )
                        })
                        .collect::<Result<Vec<_>, _>>()?,
                );
                return Ok(Expr {
                    kind: ExprKind::List(projected.into()),
                    span: expression.span,
                });
            }

            let mut projected = items
                .iter()
                .map(|item| {
                    project_repl_surface_expression_in_scope(
                        item,
                        session,
                        surface,
                        depth + 1,
                        bound,
                    )
                })
                .collect::<Result<Vec<_>, _>>()?;
            if let ExprKind::Symbol(head) = &items[0].kind {
                // A user binding in the persistent REPL frame shadows a projection
                // alias, preserving ordinary interactive rebinding behavior.
                if session.environment.get(head).is_none() {
                    if let Some(identity) = selected_surface_callable(surface, head)? {
                        let arguments = projected.drain(1..).collect::<Vec<_>>();
                        return Ok(Expr {
                            kind: ExprKind::DomainCall(identity, arguments.into()),
                            span: expression.span,
                        });
                    }
                }
            }
            return Ok(Expr {
                kind: ExprKind::List(projected.into()),
                span: expression.span,
            });
        }
        return Ok(expression.clone());
    };
    if !bound
        .iter()
        .any(|candidate| candidate.as_ref() == name.as_ref())
        && session.environment.get(name).is_none()
    {
        if let Some(identity) = selected_surface_callable(surface, name)? {
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(DomainIdentity::from(identity)),
                span: expression.span,
            });
        }
    }
    Ok(expression.clone())
}

fn collect_repl_binders(expression: &Expr, names: &mut Vec<std::rc::Rc<str>>) {
    match &expression.kind {
        ExprKind::Symbol(name) => names.push(name.clone()),
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_repl_binders(item, names);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_repl_binders(head, names);
            collect_repl_binders(tail, names);
        }
        _ => {}
    }
}

fn exact_t5m_carrier_words(
    words: &[ExactDomainWord],
) -> Result<Vec<crate::zig_transport::ExactT5MWord>, String> {
    words
        .iter()
        .map(|word| match word {
            ExactDomainWord::Identity(identity) => {
                let width = identity.width();
                let bits = (0..width)
                    .rev()
                    .map(|shift| ((identity.packed_bits() >> shift) & 1) as u8)
                    .collect();
                crate::zig_transport::ExactT5MWord::new(width, bits)
            }
            ExactDomainWord::Number(number) => {
                let width = number
                    .numeric_domain_width()
                    .ok_or("T5M number lost its D24+ identity")?;
                crate::zig_transport::ExactT5MWord::new(
                    width,
                    number
                        .exact_numeric_domain_bits()
                        .ok_or("T5M number has no exact bits")?,
                )
            }
        })
        .collect()
}

fn restore_t5m_words(
    expected: &[ExactDomainWord],
    restored: &[crate::zig_transport::ExactT5MWord],
) -> Result<Vec<ExactDomainWord>, String> {
    if expected.len() != restored.len() {
        // Замість двох лічильників показуємо перше точне слово, на якому
        // Zig T5M втратив, вставив або змінив координату. Це діагностика
        // реального RED, не новий релізний бар'єр і не fallback.
        let carrier = exact_t5m_carrier_words(expected)?;
        let first_mismatch_index = carrier
            .iter()
            .zip(restored)
            .position(|(left, right)| left.width != right.width || left.bits != right.bits)
            .unwrap_or_else(|| expected.len().min(restored.len()));
        return Err(format!(
            "T5M_WORD_MISMATCH expected={} restored={} first_mismatch_index={first_mismatch_index}",
            expected.len(),
            restored.len()
        ));
    }
    expected
        .iter()
        .zip(restored)
        .enumerate()
        .map(|(index, (expected, actual))| {
            let (width, bits) = match expected {
                ExactDomainWord::Identity(identity) => {
                    let width = identity.width();
                    let bits = (0..width)
                        .rev()
                        .map(|shift| ((identity.packed_bits() >> shift) & 1) as u8)
                        .collect::<Vec<_>>();
                    (width, bits)
                }
                ExactDomainWord::Number(number) => (
                    number
                        .numeric_domain_width()
                        .ok_or("T5M number lost its D24+ identity")?,
                    number
                        .exact_numeric_domain_bits()
                        .ok_or("T5M number has no exact bits")?,
                ),
            };
            if actual.width != width || actual.bits != bits {
                return Err(format!(
                    "T5M_WORD_MISMATCH index={index} expected_width={width} actual_width={}",
                    actual.width
                ));
            }
            match expected {
                ExactDomainWord::Identity(identity) => Ok(ExactDomainWord::Identity(*identity)),
                ExactDomainWord::Number(_) => Ok(ExactDomainWord::Number(
                    BinaryNumber::from_numeric_domain_bits(width, &actual.bits).ok_or_else(
                        || format!("T5M returned invalid D{width}+ numeric bits at word {index}"),
                    )?,
                )),
            }
        })
        .collect()
}

#[cfg(feature = "zig-transport")]
fn t5m_roundtrip_words(words: &[ExactDomainWord]) -> Result<Vec<ExactDomainWord>, String> {
    let carrier = exact_t5m_carrier_words(words)?;
    let physical = crate::zig_transport::encode_t5m_exact_words(&carrier)?;
    let decoded = crate::zig_transport::decode_t5m_exact_words(&physical)?;
    restore_t5m_words(words, &decoded)
}

#[cfg(not(feature = "zig-transport"))]
fn t5m_roundtrip_words(_words: &[ExactDomainWord]) -> Result<Vec<ExactDomainWord>, String> {
    Err("RUST_ZIG_ONLY: REPL requires the Zig T5M transport; no Rust fallback".into())
}

// Вихідні D3 пари є даними SENS. Будуємо точний AST, не відновлюємо
// семантику через display-рядок і не приймаємо host-об'єкти за дані.
// D2 крапкова пара зберігає як правильні, так і неправильні списки.
fn exact_t5m_result_data(value: &Value, depth: usize) -> Result<Expr, String> {
    if depth > 768 {
        return Err("T5M_RESULT_DEPTH: D3 pair exceeds exact reader limit".into());
    }
    let kind = match value {
        Value::Nil => ExprKind::List(Vec::new().into()),
        Value::Symbol(symbol) => ExprKind::Symbol(symbol.clone()),
        Value::Pair(head, tail) => ExprKind::Pair(
            std::rc::Rc::new(exact_t5m_result_data(head, depth + 1)?),
            std::rc::Rc::new(exact_t5m_result_data(tail, depth + 1)?),
        ),
        Value::BinaryNumber(number) => ExprKind::BinaryNumber(number.clone()),
        Value::DomainIdentity(identity) if !matches!(identity, DomainIdentity::D2(_)) => {
            ExprKind::DomainIdentity(*identity)
        }
        other => {
            return Err(format!(
                "T5M_RESULT_DATA_UNSUPPORTED value={other}: no exact quoted D3 projection"
            ));
        }
    };
    Ok(Expr {
        kind,
        span: Default::default(),
    })
}

fn result_t5m_words(value: &Value) -> Result<Vec<ExactDomainWord>, String> {
    match value {
        Value::Nil => Ok(vec![ExactDomainWord::Identity(t5m_domain_identity(3, 0)?)]),
        Value::DomainIdentity(identity) if !matches!(identity, DomainIdentity::D2(_)) => {
            Ok(vec![ExactDomainWord::Identity(*identity)])
        }
        Value::BinaryNumber(number) => Ok(vec![
            ExactDomainWord::number(number.clone()).map_err(str::to_owned)?
        ]),
        Value::Pair(..) => {
            // Результат проходить власний Zig T5M roundtrip і D3 QUOTE eval,
            // а не лише перевірку байтів на вході.
            let quote = sens::semantic_registry_export::admitted_core_domain_for_surface("як-є")
                .filter(|identity| identity.width() == 3)
                .ok_or("T5M_RESULT_QUOTE: no admitted D3 QUOTE mechanism")?;
            let quoted_data = exact_t5m_result_data(value, 0)?;
            let expression = Expr {
                kind: ExprKind::DomainCall(quote, vec![quoted_data].into()),
                span: Default::default(),
            };
            let mut words = Vec::new();
            append_t5m_expression(&expression, sens::Text7Layout::Uk, &mut words, 0)?;
            Ok(words)
        }

        Value::NumericComposition(composition) => {
            let (negative, numerator, denominator) = composition.as_parts();
            let quotient = exact_d5_surface("частка")?;
            let difference = exact_d5_surface("відняти")?;
            let mut expression = if let Some(denominator) = denominator {
                Expr {
                    kind: ExprKind::DomainCall(
                        quotient,
                        vec![
                            Expr {
                                kind: ExprKind::BinaryNumber(numerator.clone()),
                                span: Default::default(),
                            },
                            Expr {
                                kind: ExprKind::BinaryNumber(denominator.clone()),
                                span: Default::default(),
                            },
                        ]
                        .into(),
                    ),
                    span: Default::default(),
                }
            } else {
                Expr {
                    kind: ExprKind::BinaryNumber(numerator.clone()),
                    span: Default::default(),
                }
            };
            if negative {
                let zero = BinaryNumber::from_numeric_domain_bits(24, &[0; 24])
                    .ok_or("could not form exact D24+ zero for NEG result")?;
                expression = Expr {
                    kind: ExprKind::DomainCall(
                        difference,
                        vec![
                            Expr {
                                kind: ExprKind::BinaryNumber(zero),
                                span: Default::default(),
                            },
                            expression,
                        ]
                        .into(),
                    ),
                    span: Default::default(),
                };
            }
            let mut words = Vec::new();
            append_t5m_expression(&expression, sens::Text7Layout::Uk, &mut words, 0)?;
            Ok(words)
        }
        other => Err(format!(
            "T5M_RESULT_UNSUPPORTED value={}",
            match other {
                Value::Nil => "Nil",
                Value::Bool(_) => "Bool",
                Value::Number(..) => "Number",
                Value::Rational(_) => "Rational",
                Value::BinaryNumber(_) => "BinaryNumber",
                Value::NumericComposition(_) => "NumericComposition",
                Value::Sid(_) => "legacy SID",
                Value::DomainIdentity(_) => "DomainIdentity",
                Value::String(_) => "String",
                Value::Text7(_) => "Text7",
                Value::Symbol(_) => "Symbol",
                Value::Pair(..) => "Pair",
                Value::Closure(_) => "Closure",
                Value::Macro(_) => "Macro",
                Value::Builtin(_) => "Builtin",
                Value::HostHandle { .. } => "HostHandle",
                Value::Vector(_) => "Vector",
                Value::NumericBuffer(_) => "NumericBuffer",
            }
        )),
    }
}

fn exact_d5_surface(surface: &str) -> Result<CoreDomainIdentity, String> {
    sens::semantic_registry_export::admitted_core_domain_for_surface(surface)
        .filter(|identity| identity.width() == 5)
        .ok_or_else(|| format!("SENS surface {surface} does not resolve to a current D5 mechanism"))
}

fn roundtrip_repl_result(value: Value) -> Result<Value, String> {
    let source_words = result_t5m_words(&value)?;
    let restored_words = t5m_roundtrip_words(&source_words)?;
    let program = PhysicalT5Program::from_exact_domain_words(&restored_words)
        .map_err(|error| format!("SENS result reader: {error:?}"))?;
    let output = program
        .execute(&mut Session::default())
        .map_err(|error| format!("SENS result evaluator: {}", error.render("<T5M result>")))?
        .value;
    if output != value {
        return Err(format!(
            "T5M_RESULT_MISMATCH expected={value} actual={output}"
        ));
    }
    Ok(output)
}

fn prepare_t5m_repl_words(
    line: &str,
    surface: ReplSurface,
    session: &Session,
) -> Result<Vec<ExactDomainWord>, String> {
    let parsed = sens::parse_mixed_exact_domain(line).map_err(|error| error.render(line))?;
    let expressions = parsed
        .iter()
        .map(|expression| project_repl_surface_expression(expression, session, surface, 0))
        .collect::<Result<Vec<_>, _>>()?;
    if expressions.is_empty() {
        return Err("T5M_REPL_EMPTY: no SENS form".into());
    }
    let mut words = Vec::new();
    for (index, expression) in expressions.iter().enumerate() {
        // Поточний мігратор ставить D2:00 між формами одного Lisp-файла.
        // Парний Zig/T5M маршрут мусить відновлювати ТОЧНО ті ж слова,
        // інакше 30 форм дають хибне розходження на 29 роздільників.
        if index > 0 {
            words.push(ExactDomainWord::Identity(t5m_domain_identity(2, 0b00)?));
        }
        append_t5m_expression(expression, t5m_surface_layout(surface), &mut words, 0)?;
    }
    Ok(words)
}

fn prepare_t5m_repl_program(
    line: &str,
    surface: ReplSurface,
    session: &Session,
) -> Result<PhysicalT5Program, String> {
    let words = prepare_t5m_repl_words(line, surface, session)?;
    let restored = t5m_roundtrip_words(&words)?;
    PhysicalT5Program::from_exact_domain_words_owned(restored)
        .map_err(|error| format!("SENS binary reader: {error:?}"))
}

/// SENS визначає точні слова, Zig створює фізичні T5M байти.
/// Це один і той самий reader, що надалі перевіряє --t5m-pair.
/// Механічний roundtrip не підмінює семантичний SENS oracle.
// Визначення з інших Lisp-файлів виконує сам SENS через Zig/T5M.
#[cfg(feature = "zig-transport")]
fn preload_t5m_binding_sources(session: &mut Session, bindings: &[String]) -> Result<(), String> {
    for (index, binding) in bindings.iter().enumerate() {
        let program = prepare_t5m_repl_program(binding, ReplSurface::UkrainianFull, session)
            .map_err(|error| format!("T5M_BINDING_READER index={index}: {error}"))?;
        program.execute(session).map_err(|error| {
            format!("T5M_BINDING_SENS index={index}: {}", error.render(binding))
        })?;
    }
    Ok(())
}

#[cfg(feature = "zig-transport")]
pub(crate) fn mint_t5m_source_pair(source: &str) -> Result<(Vec<u8>, String), String> {
    mint_t5m_source_pair_with_bindings(source, &[])
}

#[cfg(feature = "zig-transport")]
pub(crate) fn mint_t5m_source_pair_with_bindings(
    source: &str,
    bindings: &[String],
) -> Result<(Vec<u8>, String), String> {
    let mut session = Session::default();
    preload_t5m_binding_sources(&mut session, bindings)?;
    let words = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, &session)?;
    let carrier = exact_t5m_carrier_words(&words)?;
    let physical = crate::zig_transport::encode_t5m_exact_words(&carrier)?;
    let restored = crate::zig_transport::decode_t5m_exact_words(&physical)?;
    restore_t5m_words(&words, &restored)?;

    // Читабельний файл не є іншим кодеком: це точні слова, які
    // щойно відновив Zig. Rust тут тільки записує їхні 0/1 і пробіли.
    let mut view = String::new();
    for (index, word) in restored.iter().enumerate() {
        if index != 0 {
            view.push(' ');
        }
        for bit in &word.bits {
            match bit {
                0 => view.push('0'),
                1 => view.push('1'),
                _ => return Err("T5M_VIEW_NONBINARY_WORD".into()),
            }
        }
    }
    view.push('\n');
    Ok((physical, view))
}

#[cfg(feature = "zig-transport")]
pub(crate) fn mint_t5m_source_file(source: &str) -> Result<Vec<u8>, String> {
    mint_t5m_source_pair(source).map(|(physical, _)| physical)
}

/// Явно парний фізичний шлях: .lisp НАДАЄ перевірену доменну ідентичність,
/// Zig відновлює справжні байти .sens. Повний збіг усіх ширин і бітів
/// обов'язковий до SENS D2 та виконання. Однакова ширина НЕ є доказом домену.
/// На відміну від --t5m-file, виконується саме наданий фізичний носій.
#[cfg(feature = "zig-transport")]
#[cfg(test)]
pub(crate) fn eval_t5m_paired_file(
    source: &str,
    physical: &[u8],
) -> Result<sens::EvalResult, String> {
    eval_t5m_paired_file_with_bindings(source, physical, &[])
}

#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_paired_file_with_bindings(
    source: &str,
    physical: &[u8],
    bindings: &[String],
) -> Result<sens::EvalResult, String> {
    let mut session = Session::default();
    preload_t5m_binding_sources(&mut session, bindings)?;
    let expected = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, &session)?;
    let actual = crate::zig_transport::decode_t5m_exact_words(physical)?;
    let restored = restore_t5m_words(&expected, &actual)
        .map_err(|error| format!("T5M_PHYSICAL_PAIR_MISMATCH: {error}"))?;
    // Fail closed on noncanonical physical encoding: no equal-looking alternate
    // byte sequence may be executed as the committed source's transport.
    let encoded = crate::zig_transport::encode_t5m_exact_words(&actual)?;
    if encoded != physical {
        return Err("T5M_PHYSICAL_PAIR_MISMATCH: noncanonical T5M bytes".into());
    }
    let program = PhysicalT5Program::from_exact_domain_words_owned(restored)
        .map_err(|error| format!("SENS paired binary reader: {error:?}"))?;
    // Фізичні вхідні слова вже пройшли точну перевірку Zig/SENS.
    // Не відхиляємо справжні результати SENS (списки, пари) лише
    // через те, що кодер зворотного представлення результатів їх не знає.
    // Це не засвідчує оберненість виходу; release=NOT_CERTIFIED.
    // PhysicalT5Program spans index decoded D2/T5M WORDS, not source UTF-8
    // bytes. Rendering those indices against the original Lisp falsely
    // highlights unrelated text (often the first comment) and misdirects
    // repair. SENS still owns the actual verdict; report exact word offsets.
    program
        .execute(&mut session)
        .map_err(|error| format!(
            "SENS paired evaluator: {} (kind={:?}, physical_word_span={}..{}; source_utf8_span=NOT_ASSERTED)",
            error.message, error.kind, error.span.start, error.span.end,
        ))
}

fn eval_t5m_repl_line(
    line: &str,
    session: &mut Session,
    surface: ReplSurface,
) -> Result<sens::EvalResult, String> {
    let program = prepare_t5m_repl_program(line, surface, session)?;
    let mut result = program
        .execute(session)
        .map_err(|error| format!("SENS binary evaluator: {}", error.render(line)))?;
    // A defined closure is retained in the persistent SENS environment, but
    // it is not itself an exact-domain data word to send back through T5M.
    // Keep the evaluator's opaque runtime result for REPL presentation; all
    // subsequent invocations still cross Zig T5M as exact source words.
    if matches!(&result.value, Value::Closure(_)) {
        return Ok(result);
    }
    result.value = roundtrip_repl_result(result.value)?;
    Ok(result)
}

/// Виконати повний файл української Lisp-проєкції тим самим фізичним
/// шляхом, що й один крок REPL: точні слова → Zig T5M roundtrip → SENS.
/// Сесія навмисно без host-capabilities; цей режим є runtime-свідком, а не
/// способом запускати довільні системні дії з CI.
#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_source_file(source: &str) -> Result<sens::EvalResult, String> {
    let mut session = Session::default();
    eval_t5m_repl_line(source, &mut session, ReplSurface::UkrainianFull)
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

// The persistent map is a separate host-neutral root Zig byte asset.
fn persistent_map_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::persistent_map_source_bytes()?;
        String::from_utf8(bytes).map_err(|error| format!("ZIG_PERSISTENT_MAP_REPL UTF-8: {error}"))
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
        String::from_utf8(bytes).map_err(|err| format!("ZIG_KNOWLEDGE_REPL UTF-8: {err}"))
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
        String::from_utf8(bytes).map_err(|e| format!("ZIG_REASON_CARRIER UTF-8: {e}"))
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
        String::from_utf8(bytes).map_err(|e| format!("ZIG_UKR_CARRIER UTF-8 error: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: Ukrainian full surface requires Zig; no Rust source fallback".into())
    }
}
// The original Sanskrit source is Zig-owned opaque bytes, never a Rust embed.
#[cfg(test)]
fn sanskrit_surface_source() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = super::zig_transport::sanskrit_surface_bytes()?;
        String::from_utf8(bytes).map_err(|e| format!("ZIG_SANSKRIT_CARRIER UTF-8 error: {e}"))
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
    Lisp,
}

impl ReplSurface {
    pub(crate) fn parse(value: &str) -> Option<Self> {
        match value.trim().to_lowercase().as_str() {
            "core" | "ядро" => Some(Self::Core),
            "en" | "english" | "англійська" => Some(Self::English),
            "ук" | "uk" | "українська" => Some(Self::Ukrainian),
            "укр" | "ukr" | "українська-повна" => Some(Self::UkrainianFull),
            "sa" | "sanskrit" | "санскрит" => Some(Self::Sanskrit),
            "lisp" | "лісп" => Some(Self::Lisp),
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
            Self::Lisp => "LISP",
        }
    }

    fn title(self) -> &'static str {
        match self {
            Self::Core => "ядро",
            Self::English => "англійська",
            Self::Ukrainian => "українська",
            Self::UkrainianFull => "українська (повна)",
            Self::Sanskrit => "санскрит",
            Self::Lisp => "ЛІСП",
        }
    }

    fn presentation(self) -> PresentationLanguage {
        match self {
            Self::Core => PresentationLanguage::Canonical,
            Self::English => PresentationLanguage::English,
            Self::Ukrainian | Self::UkrainianFull => PresentationLanguage::Ukrainian,
            Self::Sanskrit => PresentationLanguage::Sanskrit,
            Self::Lisp => PresentationLanguage::English,
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

fn build_surface_layer(
    base: &Environment,
    surface: ReplSurface,
    sens_loop: bool,
) -> Result<Environment, String> {
    let layer = base.child();
    let needs_surface = matches!(
        surface,
        ReplSurface::Ukrainian | ReplSurface::UkrainianFull | ReplSurface::Sanskrit
    );
    // Meta-eval + repl-core are needed both for surface projection
    // and for the SENS-owned `--sens-loop` mode. They load here once. The
    // active human aliases come from selected D1–D11 table columns and are
    // admitted only when they pair with a full-ukr callable identity.
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
            sens::load_meta_evaluator_library_from_source(&mut session, &meta_eval).map_err(
                |error| {
                    format!(
                        "не вдалося завантажити MetaEval: {}",
                        error.render(&meta_eval)
                    )
                },
            )?;
            let repl_core = crate::zig_transport::repl_core_source_bytes().and_then(|bytes| {
                String::from_utf8(bytes).map_err(|err| format!("ZIG_SENS_REPL UTF-8: {err}"))
            })?;
            sens::parse_mixed_exact_domain(&repl_core)
                .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
                .map_err(|error| {
                    format!(
                        "не вдалося завантажити repl-core: {}",
                        error.render(&repl_core)
                    )
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
            .chain(std::iter::once((
                "knowledge.lisp",
                knowledge_source.as_str(),
            )))
            .chain(std::iter::once((
                "persistent-map.lisp",
                persistent_map_source.as_str(),
            )))
            .chain(
                prerequisite_sources
                    .iter()
                    .map(|(name, source)| (*name, source.as_str())),
            );
        for (name, source) in prerequisites {
            (if name == "time.lisp" {
                sens::load_time_library_from_source(&mut session, source)
            } else if matches!(
                name,
                "unify.lisp"
                    | "reason.lisp"
                    | "forward.lisp"
                    | "knowledge.lisp"
                    | "persistent-map.lisp"
            ) {
                sens::eval_pinned_reasoning_source(&format!("lib/{name}"), source, &mut session)
            } else if matches!(name, "persistent-vector.lisp" | "epistemic.lisp") {
                sens::parse_mixed_exact_domain(source)
                    .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
            } else {
                eval_program(source, &mut session)
            })
            .map_err(|error| format!("не вдалося завантажити {name}: {}", error.render(source)))?;
        }
        // Keep the same SENS evaluation order; only source transport changes.
        let selected_source = match surface {
            ReplSurface::Ukrainian => Some(("uk.lisp", uk_surface_source()?)),
            ReplSurface::UkrainianFull => Some(("ukr.lisp", ukr_surface_source()?)),
            // sa.lisp contains candidate/legacy aliases which are not the
            // current domain-table projection. Resolve only current table
            // names through selected_surface_callable instead.
            ReplSurface::Sanskrit
            | ReplSurface::Lisp
            | ReplSurface::Core
            | ReplSurface::English => None,
        };
        if let Some((name, source)) = selected_source {
            sens::parse_mixed_exact_domain(&source)
                .and_then(|forms| sens::eval_parsed_expressions(&forms, &mut session))
                .map_err(|error| {
                    format!("не вдалося завантажити {name}: {}", error.render(&source))
                })?;
        }
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
        let surface_environment =
            build_surface_layer(&self.base_environment, surface, self.sens_loop)?;
        self.user_environment
            .reparent(surface_environment)
            .map_err(str::to_string)?;
        self.surface = surface;
        Ok(())
    }
}

fn eval_repl_step_t5m(state: &mut ReplState, line: &str) -> Result<sens::EvalResult, String> {
    eval_t5m_repl_line(line, &mut state.session, state.surface)
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

fn render_repl_ast(
    source: &str,
    surface: ReplSurface,
    session: &Session,
) -> Result<String, String> {
    let forms = sens::parse_mixed_exact_domain(source).map_err(|error| error.render(source))?;
    if forms.is_empty() {
        return Ok("Порожній ввід — форм для показу немає.".into());
    }

    // Перегляд проходить той самий шлях вибраної поверхні → точних слів →
    // Zig/T5M, що й оцінювання, але зупиняється до допуску та виконання SENS.
    // Початкове дерево показуємо лише після безвтратної перевірки слів.
    let words = prepare_t5m_repl_words(source, surface, session)?;
    let restored = t5m_roundtrip_words(&words)?;
    if restored != words {
        return Err("T5M_REPL_PREVIEW_MISMATCH: restored words differ".into());
    }

    let mut lines = Vec::new();
    lines.push(format!(
        "T5M Zig roundtrip: {} точних слів; виконання не запускалося.",
        restored.len()
    ));
    for (index, form) in forms.iter().enumerate() {
        lines.push(format!("Форма {}", index + 1));
        render_repl_ast_node(source, form, 1, &mut lines);
    }
    Ok(lines.join("\n"))
}

fn render_repl_ast_and_eval(
    source: &str,
    state: &mut ReplState,
) -> Result<(String, Result<sens::EvalResult, String>), String> {
    let preview = render_repl_ast(source, state.surface, &state.session)?;
    let execution = eval_t5m_repl_line(source, &mut state.session, state.surface);
    Ok((preview, execution))
}

fn render_repl_ast_node(source: &str, expression: &Expr, depth: usize, lines: &mut Vec<String>) {
    let indent = "  ".repeat(depth);
    let excerpt = source
        .get(expression.span.start..expression.span.end)
        .unwrap_or("");
    match &expression.kind {
        ExprKind::List(items) => {
            lines.push(format!("{indent}Список ({} елементів)", items.len()));
            for item in items.iter() {
                render_repl_ast_node(source, item, depth + 1, lines);
            }
        }
        ExprKind::Pair(head, tail) => {
            lines.push(format!("{indent}Пара"));
            render_repl_ast_node(source, head, depth + 1, lines);
            render_repl_ast_node(source, tail, depth + 1, lines);
        }
        ExprKind::Call(identity, arguments) => {
            lines.push(format!(
                "{indent}Виклик резидента {identity:?} ({} аргументів)",
                arguments.len()
            ));
            for argument in arguments.iter() {
                render_repl_ast_node(source, argument, depth + 1, lines);
            }
        }
        ExprKind::DomainCall(identity, arguments) => {
            lines.push(format!(
                "{indent}Доменний виклик {identity:?} ({} аргументів)",
                arguments.len()
            ));
            for argument in arguments.iter() {
                render_repl_ast_node(source, argument, depth + 1, lines);
            }
        }
        ExprKind::Number(..) => lines.push(format!("{indent}Число: {excerpt}")),
        ExprKind::Rational(..) => lines.push(format!("{indent}Дріб: {excerpt}")),
        ExprKind::BinaryNumber(..) => lines.push(format!("{indent}Двійкове число: {excerpt}")),
        ExprKind::NumericBuffer(..) => lines.push(format!("{indent}Числовий буфер: {excerpt}")),
        ExprKind::Sid(identity) => {
            lines.push(format!(
                "{indent}Історична identity {identity:?}: {excerpt}"
            ));
        }
        ExprKind::DomainIdentity(identity) => {
            lines.push(format!("{indent}Доменна identity {identity:?}: {excerpt}"));
        }
        ExprKind::String(..) => lines.push(format!("{indent}Рядок: {excerpt}")),
        ExprKind::Symbol(..) => lines.push(format!("{indent}Символ: {excerpt}")),
        ExprKind::Local { depth, index } => {
            lines.push(format!(
                "{indent}Локальний слот: depth={depth}, index={index}"
            ));
        }
    }
}

/// `~/.sens-history`, якщо home directory доступний.
pub(crate) fn history_path() -> Option<PathBuf> {
    let home = env::var_os("HOME").or_else(|| env::var_os("USERPROFILE"))?;
    Some(PathBuf::from(home).join(".sens-history"))
}

fn print_surface_help() {
    println!("Показати дерево розбору без виконання: :розбір <форма>");
    println!("Показати дерево й виконати форму: :розбір-виконати <форма>");
    println!("Поверхні: :мова ук | укр | en | sa | LISP | core");
    println!("Технічний alias: :surface ук | укр | en | sa | LISP | core");
    println!("Каталог поточної людської поверхні: :імена / :names");
    println!("Одна semantic identity у всіх людських поверхнях: :ім'я <назва> / :name <name>");
    println!("Стан людських поверхонь: :поверхні / :surfaces");
    println!("Сире лексичне середовище без фільтрації поверхнею: (середовище) / (env)");
    println!("LISP — окрема проєкція з доменних таблиць; core — канонічний машинний шар.");
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
        ":розбір-виконати" => {
            let source = line
                .trim_start()
                .strip_prefix(command)
                .unwrap_or("")
                .trim_start();
            if source.is_empty() {
                eprintln!("Використання: :розбір-виконати <форма>");
            } else {
                match render_repl_ast_and_eval(source, state) {
                    Ok((preview, execution)) => {
                        println!("{preview}");
                        match execution {
                            Ok(result) => {
                                for out in result.output {
                                    println!("{out}");
                                }
                                println!(
                                    "{}",
                                    render_repl_reply(&result.value, state.surface.presentation())
                                );
                            }
                            Err(error) => eprintln!("Помилка виконання SENS:\n{error}"),
                        }
                    }
                    Err(error) => eprintln!("Помилка перегляду SENS:\n{error}"),
                }
            }
            true
        }
        ":розбір" => {
            let source = line
                .trim_start()
                .strip_prefix(command)
                .unwrap_or("")
                .trim_start();
            if source.is_empty() {
                eprintln!("Використання: :розбір <форма>");
            } else {
                match render_repl_ast(source, state.surface, &state.session) {
                    Ok(output) => println!("{output}"),
                    Err(error) => eprintln!("Помилка розбору SENS:\n{error}"),
                }
            }
            true
        }
        _ => false,
    }
}

fn is_interaction_only_unresolved_name(line: &str, error: &str) -> bool {
    let standalone_name = sens::parse_mixed_exact_domain(line)
        .ok()
        .is_some_and(|forms| {
            forms.len() == 1
                && matches!(
                    forms[0].kind,
                    ExprKind::Symbol(_) | ExprKind::DomainIdentity(DomainIdentity::D7(_))
                )
        });
    let unresolved_name =
        error.contains("unknown symbol") || error.contains("domain identity is not callable");
    standalone_name && unresolved_name
}

pub(crate) fn run_repl(session: Session, initial_surface: ReplSurface, sens_loop: bool) {
    let mut state = match ReplState::new(session, initial_surface, sens_loop) {
        Ok(state) => state,
        Err(error) => {
            eprintln!("Error: could not initialize REPL surface: {error}");
            process::exit(1);
        }
    };

    println!(
        "sens REPL v{} (Zig T5M → binary SENS → Rust mechanisms)",
        env!("CARGO_PKG_VERSION")
    );
    println!(
        "Поверхня: {} ({}) · змінити: :мова ук|укр|en|sa|LISP|core · :допомога",
        state.surface.title(),
        state.surface.code()
    );
    if state.sens_loop {
        println!("Режим: repl-core ініціалізовано; кожна інтерактивна форма проходить Zig T5M.");
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

                match eval_repl_step_t5m(&mut state, line) {
                    Ok(result) => {
                        for out in result.output {
                            println!("{out}");
                        }
                        println!(
                            "{}",
                            render_repl_reply(&result.value, state.surface.presentation())
                        );
                    }
                    Err(error) => {
                        // Зберігаємо interaction policy для окремого невідомого імені;
                        // усі форми оцінюються тільки після Zig T5M roundtrip.
                        if is_interaction_only_unresolved_name(line, &error) {
                            println!("echo {line}");
                        } else {
                            eprintln!("REPL/T5M: {error}");
                        }
                    }
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

    #[test]
    fn standalone_d7_text_identity_uses_repl_echo_without_granting_callability() {
        let error =
            "SENS binary evaluator: domain identity is not callable under its ratified law: D7";
        assert!(is_interaction_only_unresolved_name("мама", error));
        assert!(!is_interaction_only_unresolved_name("(мама)", error));
        assert!(!is_interaction_only_unresolved_name(
            "мама",
            "unrelated error"
        ));
    }

    #[test]
    fn repl_parse_preview_renders_nested_ast_and_source_syntax_errors() {
        let source = "(атом? (як-є ()))";
        let session = Session::default();
        let rendered = render_repl_ast(source, ReplSurface::UkrainianFull, &session)
            .expect("валідна форма має пройти T5M і показати AST");

        assert!(rendered.contains("T5M Zig roundtrip"), "{rendered}");
        assert!(rendered.contains("Форма 1"), "{rendered}");
        assert!(rendered.contains("Список"), "{rendered}");
        assert!(rendered.contains("Доменна identity"), "{rendered}");
        assert!(rendered.contains("атом?"), "{rendered}");

        let invalid = "(атом?";
        let error = render_repl_ast(invalid, ReplSurface::UkrainianFull, &session)
            .expect_err("незакрита форма має показати помилку");
        assert!(error.contains("line/riadok/Zeile 1:"), "{error}");
        assert!(error.contains(invalid), "{error}");
        assert!(error.contains('^'), "{error}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_parse_preview_does_not_define_bindings() {
        let mut session = Session::default();
        render_repl_ast(
            "(визначити відповідь 40)",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("перегляд має перевірити форму без виконання");

        let error = eval_t5m_repl_line("відповідь", &mut session, ReplSurface::UkrainianFull)
            .expect_err("простий перегляд не має створювати прив'язку");
        assert!(
            error.contains("unknown symbol") || error.contains("not callable"),
            "{error}"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_parse_and_execute_shows_tree_and_keeps_session_binding() {
        let mut session = Session::default();
        let base_environment = session.environment.clone();
        let user_environment = base_environment.child();
        session.environment = user_environment.clone();
        let mut state = ReplState {
            session,
            base_environment,
            user_environment,
            surface: ReplSurface::UkrainianFull,
            sens_loop: false,
        };
        let (preview, result) = render_repl_ast_and_eval("(визначити відповідь 40)", &mut state)
            .expect("команда має показати дерево й виконати форму");

        assert!(preview.contains("T5M Zig roundtrip"), "{preview}");
        assert!(preview.contains("визначити"), "{preview}");
        let result = result.expect("виконання форми має завершитися успішно");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("визначення має повернути точне число");
        };
        assert_eq!(number.to_decimal_string(), "40");

        let next = eval_t5m_repl_line("(додати відповідь 2)", &mut state.session, state.surface)
            .expect("виконана прив'язка має лишитися в поточній сесії");
        let Value::BinaryNumber(ref number) = next.value else {
            panic!("наступне обчислення має повернути точне число");
        };
        assert_eq!(number.to_decimal_string(), "42");
    }

    #[test]
    fn t5m_length_divergence_reports_first_changed_exact_word() {
        let expected = [1u16, 2, 3]
            .into_iter()
            .map(|bits| ExactDomainWord::Identity(t5m_domain_identity(3, bits).unwrap()))
            .collect::<Vec<_>>();
        let mut restored = exact_t5m_carrier_words(&expected).unwrap();
        restored.remove(1);
        let error = restore_t5m_words(&expected, &restored).unwrap_err();
        assert!(error.contains("expected=3 restored=2"), "{error}");
        assert!(error.contains("first_mismatch_index=1"), "{error}");
    }

    fn core_state() -> ReplState {
        let mut session = Session::bare();
        sens::load_core_library(&mut session).expect("core bootstrap");
        sens::load_time_library(&mut session).expect("time bootstrap");
        ReplState::new(session, ReplSurface::Core, false).expect("REPL state")
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn two_top_level_forms_have_exact_d2_separator_and_execute_after_zig_t5m() {
        let session = Session::default();
        let line = "(атом? (як-є ()))";
        let single = prepare_t5m_repl_words(line, ReplSurface::UkrainianFull, &session)
            .expect("одна виконувана D1 форма");
        let source = format!("{line}\n{line}");
        let combined = prepare_t5m_repl_words(&source, ReplSurface::UkrainianFull, &session)
            .expect("дві форми з точним D2:00");
        assert_eq!(combined.len(), single.len() * 2 + 1);
        assert_eq!(combined[..single.len()], single);
        assert_eq!(
            combined[single.len()],
            ExactDomainWord::Identity(t5m_domain_identity(2, 0b00).unwrap())
        );
        assert_eq!(combined[single.len() + 1..], single);
        let restored =
            t5m_roundtrip_words(&combined).expect("Zig/T5M має зберегти D2 роздільник і всі слова");
        let program = PhysicalT5Program::from_exact_domain_words(&restored)
            .expect("SENS має прочитати дві фізичні форми");
        let mut runtime = Session::default();
        let result = program
            .execute(&mut runtime)
            .expect("справжній SENS має виконати обидві форми");
        assert_eq!(result.value.as_predicate_bit(), Some(true));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn native_sens_mint_and_pair_execute_without_python_or_json_oracle() {
        // Один живий SENS reader є владою для обох маршрутів.
        // Python preview і JSON-маніфест сюди не потрапляють.
        let source = "(атом? (як-є ()))";
        let physical =
            mint_t5m_source_file(source).expect("SENS має видати фізичний Zig/T5M носій");
        assert!(!physical.is_empty());

        let from_source =
            eval_t5m_source_file(source).expect("SENS оцінює точну українську форму після Zig");
        let from_pair = eval_t5m_paired_file(source, &physical)
            .expect("SENS виконує ті самі фізичні слова, не Python-міграцію");
        assert_eq!(from_source.value.as_predicate_bit(), Some(true));
        assert_eq!(from_pair.value.as_predicate_bit(), Some(true));

        // Підміна людського джерела за тих самих фізичних байтів є RED.
        let substituted = "(атом? (як-є (())))";
        let error = eval_t5m_paired_file(substituted, &physical)
            .expect_err("джерело і фізичні слова мусять збігатися побітово");
        assert!(error.contains("T5M_PHYSICAL_PAIR_MISMATCH"), "{error}");

        let mut altered = physical;
        altered[0] ^= 1;
        assert!(
            eval_t5m_paired_file(source, &altered).is_err(),
            "пошкоджений фізичний носій не повинен виконатися"
        );
    }

    /// #1968: no UTF-8 source evaluator is allowed to decide the physical
    /// D3 COND outcome. Zig mints the exact words, SENS executes both cases.
    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_t5m_paired_cond_accepts_only_d1_and_reports_physical_error_form() {
        let valid = "(за-умовою (ні (атом? (як-є ()))) (так (атом? (як-є ()))))";
        let (physical, exact_view) =
            mint_t5m_source_pair(valid).expect("SENS/Zig має видати точний T5M");
        assert!(!physical.is_empty());
        assert!(!exact_view.trim().is_empty());
        let result = eval_t5m_paired_file(valid, &physical)
            .expect("точний D1:0 пропускає гілку у фізичному SENS");
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(true),
            "test_id=1968-ZIG-COND-D1 layer=SENS expected=D1:1 actual={}",
            result.value
        );

        let invalid =
            "(за-умовою ((як-є ()) (атом? (як-є ()))) (так (атом? (як-є ()))))";
        let (invalid_physical, _) =
            mint_t5m_source_pair(invalid).expect("навіть недопустима умова має кодуватися");
        let error = eval_t5m_paired_file(invalid, &invalid_physical)
            .expect_err("D3:000 як COND test має бути Type, а не D1:NO");
        assert!(
            error.contains("D3:110 COND expects exact D1")
                && error.contains("physical_form_index=0"),
            "test_id=1968-ZIG-COND-EMPTY layer=SENS expected=Type/form-0 actual={error}"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn quoted_integer_in_t5m_source_preserves_exact_d24_word() {
        let session = Session::default();
        let words = prepare_t5m_repl_words("(як-є (7))", ReplSurface::UkrainianFull, &session)
            .expect("quoted decimal must lower to the same exact D24 as ordinary source");
        assert!(
            words.iter().any(|word| matches!(word,
                ExactDomainWord::Number(number)
                    if number.numeric_domain_width() == Some(24)
                        && number.to_decimal_string() == "7"
            )),
            "the quoted number must remain exact D24, not become W7 text"
        );
        let restored = t5m_roundtrip_words(&words).expect("Zig must carry the exact word");
        assert_eq!(restored.len(), words.len());
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_roundtrips_d24_input_and_result_through_zig() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line("(додати 1 2)", &mut session, ReplSurface::UkrainianFull)
            .expect("exact D24 source -> Zig T5M -> binary SENS -> Zig T5M result");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("D5 addition must return exact D24+");
        };
        assert_eq!(number.numeric_domain_width(), Some(24));
        assert_eq!(number.to_decimal_string(), "3");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn full_ukrainian_d8_io_is_domain_qualified_not_text7_or_sid8() {
        // These five mechanisms are already admitted by D8, not by a legacy
        // eight-bit SID. No independent Rust semantics are introduced.
        for (name, bits) in [
            ("код-символу", 0b11100000),
            ("прочитати", 0b11101010),
            ("текст-у-символ", 0b11101101),
            ("символ-у-текст", 0b11101110),
            ("значення-у-текст", 0b11110100),
        ] {
            let actual = selected_surface_callable(ReplSurface::UkrainianFull, name)
                .expect("ratified Ukrainian ladder must parse")
                .expect("current D8 mechanism must remain callable");
            assert_eq!(actual.width(), 8, "{name}");
            assert_eq!(actual.packed_bits(), bits, "{name}");
        }

        // A resident without an executable mechanism stays inert; foreign
        // spelling and D7 text never become D8 by width or name similarity.
        assert!(
            selected_surface_callable(ReplSurface::UkrainianFull, "вектор")
                .expect("ratified non-callable D8 resident lookup")
                .is_none()
        );
        assert!(
            selected_surface_callable(ReplSurface::English, "string->symbol")
                .expect("English projection must not elevate new D8 calls")
                .is_none()
        );

        // The former real RED interpreted this admitted nested call as a
        // Text7 variable (#t7:...). Check it now lowers to exact SENS words,
        // not a Python/JSON oracle or a textual surrogate for the execution.
        let session = Session::default();
        let words = prepare_t5m_repl_words(
            "(текст-у-символ (значення-у-текст (як-є сполучити)))",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("current Ukrainian nested D8 source must reach exact T5M words");
        assert!(words.iter().any(|word| matches!(
            word,
            ExactDomainWord::Identity(DomainIdentity::D8(id))
                if id.word().packed_bits() == 0b11101101
        )));
        assert!(words.iter().any(|word| matches!(
            word,
            ExactDomainWord::Identity(DomainIdentity::D8(id))
                if id.word().packed_bits() == 0b11110100
        )));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn d9_witness_source_is_carried_by_zig_and_readable_by_sens() {
        let bytes =
            crate::zig_transport::d9_witness_source_bytes().expect("Zig carries D9 witness bytes");
        let source = String::from_utf8(bytes).expect("D9 witness source is UTF-8");
        let forms =
            sens::parse_mixed_exact_domain(&source).expect("SENS reads the D9 witness source");
        let call = forms.last().expect("D9 witness entry");
        let ExprKind::List(items) = &call.kind else {
            panic!("D9 witness entry must be a source call");
        };
        let ExprKind::List(witnesses) = &items[1].kind else {
            panic!("D9 witness must supply one SENS list of assertions");
        };
        assert_eq!(witnesses.len() - 1, 8, "eight native SENS witness laws");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn d9_four_ukr_witnesses_execute_individually_in_native_sens() {
        // One false witness used to collapse to a generic CAR-of-NIL error.
        // Diagnose the actual Lisp source one law at a time using precisely
        // the same SENS -> Zig T5M -> SENS path as --t5m-pair.
        // This code extracts AST spans only; Rust never calculates law truth.
        let source = String::from_utf8(
            crate::zig_transport::d9_witness_source_bytes().expect("Zig carries D9 witness bytes"),
        )
        .expect("D9 witness source is UTF-8");
        let forms = sens::parse_mixed_exact_domain(&source)
            .expect("D9 native Lisp source must be readable");
        let call = forms.last().expect("eight native witness assertions");
        let ExprKind::List(call_items) = &call.kind else {
            panic!("D9 witness entry must be a source call");
        };
        let ExprKind::List(witnesses) = &call_items[1].kind else {
            panic!("D9 witness must supply one SENS list of assertions");
        };
        assert_eq!(witnesses.len() - 1, 8, "eight existing SENS laws");
        let definitions = &source[..call.span.start];
        for (index, witness) in witnesses.iter().enumerate().skip(1) {
            let law_source = &source[witness.span.start..witness.span.end];
            let program = format!("{definitions}\n{law_source}\n");
            let result = eval_t5m_source_file(&program).unwrap_or_else(|error| {
                panic!(
                    "test_id=D9-EIGHT-{} layer=SENS_ZIG_T5M source={} actual_error={error}",
                    index, law_source
                )
            });
            assert_eq!(
                result.value.as_predicate_bit(),
                Some(true),
                "test_id=D9-EIGHT-{} layer=SENS_ZIG_T5M input={} expected=D1:true actual={}",
                index,
                law_source,
                result.value
            );
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_uses_the_same_d5_identity_across_repl_projections() {
        let cases = [
            (ReplSurface::Core, "(додати 1 2)"),
            (ReplSurface::English, "(plus 1 2)"),
            (ReplSurface::Ukrainian, "(додати 1 2)"),
            (ReplSurface::UkrainianFull, "(додати 1 2)"),
            (ReplSurface::Sanskrit, "(yoga 1 2)"),
            (ReplSurface::Lisp, "(plus 1 2)"),
        ];

        for (surface, source) in cases {
            if surface != ReplSurface::Core {
                let head = source
                    .trim_start_matches('(')
                    .split_whitespace()
                    .next()
                    .expect("projection call head");
                let identity = selected_surface_callable(surface, head)
                    .expect("projection catalog")
                    .expect("selected projection must resolve an admitted callable");
                assert_eq!(identity.width(), 5, "{}", surface.code());
                assert_eq!(identity.packed_bits(), 0b01010, "{}", surface.code());
            }
            let mut state = core_state();
            state.switch_surface(surface).unwrap_or_else(|error| {
                panic!("{} surface initialization: {error}", surface.code())
            });
            let result = eval_repl_step_t5m(&mut state, source).unwrap_or_else(|error| {
                panic!(
                    "{} surface source {source:?} must cross Zig T5M: {error}",
                    surface.code()
                )
            });
            let Value::BinaryNumber(ref number) = result.value else {
                panic!("{} surface did not return exact D24+", surface.code());
            };

            assert_eq!(
                number.numeric_domain_width(),
                Some(24),
                "{}",
                surface.code()
            );
            assert_eq!(number.to_decimal_string(), "3", "{}", surface.code());
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn callable_projection_names_lower_to_the_same_first_class_domain_code() {
        let session = Session::default();
        let cases = [
            (ReplSurface::Ukrainian, "додати"),
            (ReplSurface::UkrainianFull, "додати"),
            (ReplSurface::Lisp, "plus"),
        ];
        let expected = ExactDomainWord::Identity(DomainIdentity::from(
            selected_surface_callable(ReplSurface::UkrainianFull, "додати")
                .expect("Ukrainian full projection")
                .expect("D5 addition callable"),
        ));

        for (surface, name) in cases {
            let words = prepare_t5m_repl_words(name, surface, &session)
                .unwrap_or_else(|error| panic!("{} value {name:?}: {error}", surface.code()));
            assert_eq!(words, [expected.clone()], "{} projection", surface.code());
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn domain_code_is_a_first_class_function_value_through_zig_t5m() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line(
            "((функція (операція) (операція 1 2)) додати)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("D5 function code is passed as a value, restored by Zig T5M, then applied");

        let Value::BinaryNumber(ref number) = result.value else {
            panic!("the first-class D5 function returns exact D24+");
        };
        assert_eq!(number.to_decimal_string(), "3");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_does_not_accept_a_name_from_an_unselected_projection() {
        let mut session = Session::default();
        let error = eval_t5m_repl_line("(plus 1 2)", &mut session, ReplSurface::UkrainianFull)
            .expect_err("English alias must not leak into the selected Ukrainian projection");
        assert!(error.contains("Uk has no current D7 v2 glyph"), "{error}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_projects_ukrainian_decimal_commas_as_exact_ratios() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line(
            "(додати 2,467 1,533)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("decimal comma lowers to exact D5 ratio/D24 words before Zig T5M");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("exact decimal sum is the D24 integer four");
        };
        assert_eq!(number.numeric_domain_width(), Some(24));
        assert_eq!(number.to_decimal_string(), "4");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_roundtrips_exact_fraction_result() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line("(частка 1 3)", &mut session, ReplSurface::UkrainianFull)
            .expect("exact ratio result must cross the Zig T5M return path");
        let Value::NumericComposition(ref composition) = result.value else {
            panic!("D5 quotient returns an exact rational composition");
        };
        let (negative, numerator, denominator) = composition.as_parts();
        assert!(!negative);
        assert_eq!(numerator.to_decimal_string(), "1");
        assert_eq!(
            denominator
                .expect("nonintegral quotient has denominator")
                .to_decimal_string(),
            "3"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_roundtrips_negative_exact_fraction_result() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line(
            "(відняти 0 (частка 1 3))",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("negative exact ratio uses the admitted D5 subtraction call");
        let Value::NumericComposition(ref composition) = result.value else {
            panic!("negative quotient remains an exact rational composition");
        };
        let (negative, numerator, denominator) = composition.as_parts();
        assert!(negative);
        assert_eq!(numerator.to_decimal_string(), "1");
        assert_eq!(
            denominator
                .expect("nonintegral quotient has denominator")
                .to_decimal_string(),
            "3"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn interactive_t5m_keeps_bindings_between_repl_lines() {
        let mut session = Session::default();
        let definition = eval_t5m_repl_line(
            "(визначити значення 40)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("definition crosses the Zig T5M path");
        let Value::BinaryNumber(ref number) = definition.value else {
            panic!("definition expression returns its defined exact value");
        };
        assert_eq!(number.to_decimal_string(), "40");

        let result = eval_t5m_repl_line(
            "(додати значення 2)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("next REPL line sees the prior binding");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("D5 addition must return exact D24+");
        };
        assert_eq!(number.to_decimal_string(), "42");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn sens_loop_mode_uses_the_same_t5m_step_and_keeps_session_state() {
        let mut session = Session::default();
        let base_environment = session.environment.clone();
        let user_environment = base_environment.child();
        session.environment = user_environment.clone();
        let mut state = ReplState {
            session,
            base_environment,
            user_environment,
            surface: ReplSurface::UkrainianFull,
            sens_loop: true,
        };
        let result = eval_repl_step_t5m(&mut state, "(додати 1 2)")
            .expect("--sens-loop must use the same Zig T5M interactive step");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("SENS binary evaluator returns exact D24+");
        };
        assert_eq!(number.to_decimal_string(), "3");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_repl_rejects_changed_word_before_program_reconstruction() {
        let identity = DomainIdentity::from_coordinate(
            sens::domain_ladder::DomainCoordinate::new(5, 0b01010).unwrap(),
        );
        let expected = vec![ExactDomainWord::Identity(identity)];
        let altered =
            vec![crate::zig_transport::ExactT5MWord::new(5, vec![0, 1, 0, 1, 1]).unwrap()];

        let error = restore_t5m_words(&expected, &altered).expect_err("bit drift fails closed");
        assert!(error.starts_with("T5M_WORD_MISMATCH index=0"), "{error}");
    }

    #[test]
    fn t5m_uk_projection_separates_quoted_ascii_data_from_executable_names() {
        // Дані зовнішнього протоколу не є викличними іменами української
        // програми. Мають проходити точним D7/en маршрутом через W7 клітини.
        let source = "(як-є reason-index-1)";
        let forms = sens::parse_mixed_exact_domain(source)
            .expect("український QUOTE приймає латинські дані");
        let mut words = Vec::new();
        append_t5m_expression(&forms[0], sens::Text7Layout::Uk, &mut words, 0)
            .expect("цитований ASCII-атом має точний D7/en транспорт");
        let ascii_r = u16::from(b'r');
        assert!(
            words.iter().any(|word| matches!(
                word, ExactDomainWord::Identity(identity)
                    if identity.width() == 7 && identity.packed_bits() == ascii_r
            )),
            "цитований протокол має зберегти W7 ASCII, а не транслітерувати дані"
        );

        // Той самий текст у викличній голові НЕ набуває D7/uk або D5
        // повноважень через поблажливу англійську проєкцію.
        let invalid = sens::parse_mixed_exact_domain("(reason-index-1)")
            .expect("розбір тексту не дає викличності");
        let mut forbidden = Vec::new();
        let error = append_t5m_expression(&invalid[0], sens::Text7Layout::Uk, &mut forbidden, 0)
            .expect_err("латинський виклик не допущено");
        assert!(error.contains("symbol=\"reason-index-1\""), "{error}");
        assert!(error.contains("Uk has no current D7 v2 glyph"), "{error}");

        #[cfg(feature = "zig-transport")]
        {
            let roundtrip =
                t5m_roundtrip_words(&words).expect("справжній Zig T5M зберігає точні W7 клітини");
            assert_eq!(roundtrip.len(), words.len());
            for (before, after) in words.iter().zip(roundtrip.iter()) {
                assert_eq!(format!("{before:?}"), format!("{after:?}"));
            }
        }
    }

    #[test]
    fn t5m_dotted_pair_rejects_non_atomic_d7_tail_in_both_contexts() {
        // Для нецитованої пари діяло те саме неатомне D7 lowering,
        // проте перевірка досі спрацьовувала тільки всередині QUOTE.
        let nil = || Expr {
            kind: ExprKind::DomainIdentity(t5m_domain_identity(3, 0).unwrap()),
            span: Default::default(),
        };
        let pair = |tail: Expr| Expr {
            kind: ExprKind::Pair(std::rc::Rc::new(nil()), std::rc::Rc::new(tail)),
            span: Default::default(),
        };
        for quoted_data in [false, true] {
            let symbol_tail = pair(Expr {
                kind: ExprKind::Symbol("хвіст".into()),
                span: Default::default(),
            });
            let mut invalid = Vec::new();
            let error = append_t5m_expression_context(
                &symbol_tail,
                sens::Text7Layout::Uk,
                &mut invalid,
                0,
                quoted_data,
            )
            .expect_err("D7 glyph-list must not replace an atomic dotted tail");
            assert!(
                error.starts_with("T5M_DOTTED_TEXT_TAIL_NOT_ATOMIC"),
                "{error}"
            );

            let exact_tail = pair(nil());
            let mut valid = Vec::new();
            append_t5m_expression_context(
                &exact_tail,
                sens::Text7Layout::Uk,
                &mut valid,
                0,
                quoted_data,
            )
            .expect("a domain-qualified atomic dotted tail stays structural");
            assert!(valid.iter().any(|word| matches!(
                word,
                ExactDomainWord::Identity(identity)
                    if identity.width() == 2 && identity.packed_bits() == 0b11
            )));
        }
    }

    #[test]
    fn t5m_uk_projection_accepts_a_reversible_ukrainian_atom() {
        let forms = sens::parse_mixed_exact_domain("(як-є слово)")
            .expect("чинна українська поверхня розбирається");
        let mut words = Vec::new();
        append_t5m_expression(&forms[0], sens::Text7Layout::Uk, &mut words, 0)
            .expect("українські дані D7 v2 кодуються точними словами");
        assert!(
            !words.is_empty(),
            "позитивний свідок має мати фізичні слова"
        );
    }

    #[test]
    fn t5m_repl_names_values_without_an_exact_encoding() {
        let error = result_t5m_words(&Value::String("не кодувати мовчки".into()))
            .expect_err("unratified text-value carrier must fail explicitly");
        assert!(
            error.starts_with("T5M_RESULT_UNSUPPORTED value=String"),
            "{error}"
        );
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
    fn every_repl_surface_returns_symbol_data_in_uppercase() {
        let symbol = Value::Symbol("car".into());
        for surface in [
            ReplSurface::Core,
            ReplSurface::English,
            ReplSurface::Ukrainian,
            ReplSurface::UkrainianFull,
            ReplSurface::Sanskrit,
            ReplSurface::Lisp,
        ] {
            let reply = render_repl_reply(&symbol, surface.presentation());
            assert_eq!(reply, reply.to_uppercase(), "surface {}", surface.code());
        }
    }

    #[test]
    fn classic_repl_reply_uppercases_d1_human_projection_but_not_machine_bits() {
        let no = Value::DomainIdentity(sens::DomainIdentity::D1(sens::PredicateBit::from_word(
            sens::Bit1::new(0).unwrap(),
        )));
        let yes = Value::DomainIdentity(sens::DomainIdentity::D1(sens::PredicateBit::from_word(
            sens::Bit1::new(1).unwrap(),
        )));

        assert_eq!(render_repl_reply(&no, PresentationLanguage::Canonical), "0");
        assert_eq!(
            render_repl_reply(&yes, PresentationLanguage::Canonical),
            "1"
        );
        assert_eq!(render_repl_reply(&no, PresentationLanguage::English), "0");
        assert_eq!(render_repl_reply(&yes, PresentationLanguage::English), "1");
        assert_eq!(
            render_repl_reply(&no, PresentationLanguage::Ukrainian),
            "НІ"
        );
        assert_eq!(
            render_repl_reply(&yes, PresentationLanguage::Ukrainian),
            "ТАК"
        );
        assert_eq!(render_repl_reply(&no, PresentationLanguage::Sanskrit), "NA");
        assert_eq!(
            render_repl_reply(&yes, PresentationLanguage::Sanskrit),
            "ĀM"
        );
    }

    #[test]
    fn classic_repl_reply_accepts_lowercase_source_and_prints_uppercase_symbols() {
        let mut state = core_state();
        let result = eval_program("(quote (car cons \"MiXeD\" 42))", &mut state.session)
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
        let bytes =
            crate::zig_transport::persistent_map_source_bytes().expect("second Zig byte copy");
        assert!(!source.is_empty());
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "ZIG_PERSISTENT_MAP_REPL byte parity"
        );
        println!(
            "ZIG_PERSISTENT_MAP_REPL_PASS test_id=zig-repl-persistent-map layer=transport bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_persistent_map_no_rust_fallback() {
        let err = persistent_map_surface_source().expect_err("must not bypass Zig");
        assert_eq!(
            err,
            "RUST_ZIG_ONLY: persistent-map.lisp requires Zig; no Rust source fallback"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_knowledge_repl_preserves_exact_bytes() {
        let source = knowledge_surface_source().expect("knowledge source via Zig C ABI");
        let bytes =
            crate::zig_transport::knowledge_source_bytes().expect("independent Zig C byte copy");
        assert!(!source.is_empty(), "ZIG_KNOWLEDGE_REPL empty source");
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "ZIG_KNOWLEDGE_REPL exact byte parity"
        );
        println!(
            "ZIG_KNOWLEDGE_REPL_PASS test_id=knowledge-repl-zig-only layer=transport bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_knowledge_without_zig_fails_closed() {
        let error = knowledge_surface_source().expect_err("no Rust fallback for knowledge.lisp");
        assert_eq!(
            error,
            "RUST_ZIG_ONLY: knowledge.lisp requires Zig; no Rust source fallback"
        );
        println!(
            "ZIG_KNOWLEDGE_NO_FALLBACK_PASS test_id=knowledge-repl-no-rust-source layer=transport"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_forward_source_preserves_every_byte() {
        let source = forward_surface_source().expect("forward source via Zig C ABI");
        let bytes = crate::zig_transport::forward_source_bytes().expect("second Zig C byte copy");
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "ZIG_FORWARD_CARRIER exact byte parity"
        );
        assert!(
            source.starts_with("; Чинний рушій прямого виведення СЕНС:"),
            "wrong SENS source asset"
        );
        println!(
            "ZIG_FORWARD_CARRIER_PASS test_id=zig-forward-exact-carry layer=transport bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_forward_without_zig_denies_rust_bypass() {
        let error = forward_surface_source().expect_err("only Zig may carry forward.lisp");
        assert!(
            error.contains("RUST_ZIG_ONLY: forward.lisp requires Zig; no Rust source fallback"),
            "{error}"
        );
        println!("ZIG_FORWARD_NO_FALLBACK_PASS test_id=zig-forward-no-rust-bypass layer=transport");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_unify_repl_source_matches_opaque_c_abi_bytes() {
        let source = unify_surface_source().expect("Zig exact lib/unify.lisp bytes");
        let copied =
            crate::zig_transport::unify_source_bytes().expect("Zig copied original source");
        assert_eq!(
            source.as_bytes(),
            copied.as_slice(),
            "ZIG_UNIFY_CARRIER byte parity"
        );
        assert!(
            source.starts_with("; Уніфікація зіставляє структури"),
            "wrong unify asset"
        );
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
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "UK surface exact byte identity"
        );
        assert!(
            source.starts_with("; Компактна українська проєкція"),
            "not the current compact Ukrainian projection notice"
        );
        assert!(
            source.contains("не дублює реєстр"),
            "source must not duplicate domain identities"
        );
        println!(
            "ZIG_UK_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
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
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "UKR original byte parity"
        );
        assert!(
            source.starts_with("; Повна українська проєкція"),
            "wrong source"
        );
        assert!(
            source.contains("рівноправною мовною поверхнею"),
            "truncated source"
        );
        println!(
            "ZIG_UKR_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
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
        let bytes =
            crate::zig_transport::sanskrit_surface_bytes().expect("second Zig ABI byte copy");
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "Sanskrit exact-byte replay"
        );
        assert!(
            source.starts_with("; Санскритська проєкція"),
            "expected tracked source"
        );
        assert!(
            source.contains("svarūpa"),
            "source identity/truncation witness"
        );
        println!(
            "ZIG_SANSKRIT_CARRIER_PASS bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_sanskrit_surface_denies_rust_only_loading() {
        let err = sanskrit_surface_source().expect_err("no direct Rust source fallback");
        assert!(err.contains("RUST_ZIG_ONLY"), "{err}");
        assert!(err.contains("no Rust source fallback"), "{err}");
    }

    #[test]
    fn ukrainian_surface_uses_domain_registry_without_alias_bindings() {
        let mut state = core_state();
        assert!(state.session.environment.get("додати").is_none());

        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додати 1 2)")
                .expect("registered Ukrainian head crosses T5M")
                .value
                .to_string(),
            "3"
        );
        // Canonical spelling is resolver-owned, never a mutable surface-frame
        // alias; domain tables supply both Ukrainian projections.
        assert!(state.session.environment.get("додати").is_none());

        state.switch_surface(ReplSurface::Core).expect("core");
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додати 1 2)")
                .expect("registered canonical head crosses T5M")
                .value
                .to_string(),
            "3"
        );
        // Canon is not a UI layer: registered spellings still denote Canon
        // even when no human surface frame is loaded.
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додати 1 2)")
                .expect("canonical domain resolution is surface-independent")
                .value
                .to_string(),
            "3"
        );
    }

    #[test]
    fn switching_surface_preserves_user_frame_and_closure_view() {
        let mut state = core_state();
        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        eval_repl_step_t5m(&mut state, "(визначити крок 1)").expect("bind in Ukrainian");
        eval_repl_step_t5m(
            &mut state,
            "(визначити додай-крок (функція (х) (додати х крок)))",
        )
        .expect("closure definition crosses T5M");
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додай-крок 5)")
                .expect("local closure call crosses T5M")
                .value
                .to_string(),
            "6"
        );

        state
            .switch_surface(ReplSurface::UkrainianFull)
            .expect("ukr");
        eval_repl_step_t5m(&mut state, "(визначити крок 2)").expect("shadow in Ukrainian");
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додай-крок 5)")
                .expect("closure keeps current frame view")
                .value
                .to_string(),
            "7"
        );

        state.switch_surface(ReplSurface::Ukrainian).expect("uk");
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додай-крок 5)")
                .expect("closure survives projection switch")
                .value
                .to_string(),
            "7"
        );
    }

    #[test]
    fn uk_and_ukr_are_distinct_repl_selectors_over_one_registry() {
        assert_eq!(ReplSurface::parse("ук"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("uk"), Some(ReplSurface::Ukrainian));
        assert_eq!(ReplSurface::parse("укр"), Some(ReplSurface::UkrainianFull));
        assert_eq!(ReplSurface::parse("ukr"), Some(ReplSurface::UkrainianFull));
        assert_eq!(ReplSurface::parse("lisp"), Some(ReplSurface::Lisp));
        assert_eq!(ReplSurface::parse("лісп"), Some(ReplSurface::Lisp));
        assert_ne!(
            ReplSurface::Ukrainian.code(),
            ReplSurface::UkrainianFull.code()
        );
        assert!(surface_catalog::render_name("укр", "D6:101000")
            .expect("UKR registry lookup")
            .starts_with("identity: D6:101000"));
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
        let lisp = render_surface_names(ReplSurface::Lisp).expect("LISP catalog");
        assert!(lisp.contains("surface LISP:"));
        assert!(lisp.contains("PLUS"));
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
        assert!(!snapshot.iter().any(|(name, _)| name.as_ref() == "додати"));
        assert_eq!(
            eval_repl_step_t5m(&mut state, "(додати 1 2)")
                .expect("registered D5 head resolves without lexical alias")
                .value
                .to_string(),
            "3"
        );
    }
}
