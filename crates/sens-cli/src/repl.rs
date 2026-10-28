//! Інтерактивний stdio REPL: історія, interaction-only echo fallback і
//! перемикання програмних поверхонь. `:мова` / `:surface` не є Lisp syntax:
//! це команди оболонки над одним і тим самим семантичним ядром.

mod benchmark;
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

#[cfg(feature = "zig-transport")]
pub(crate) fn execute_zig_t5m_asset(
    physical: &[u8],
    label: &str,
    session: &mut Session,
) -> Result<usize, String> {
    let restored = crate::zig_transport::decode_t5m_exact_words(physical)
        .map_err(|error| format!("{label} Zig T5M decode: {error}"))?;
    let words = restored
        .iter()
        .map(|word| {
            ExactDomainWord::from_physical_width_bits(word.width(), word.bits())
                .map_err(|error| format!("{label} exact SENS word: {error}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let program = PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|error| format!("{label} SENS binary reader: {}", error.message))?;
    let form_count = program.form_count();
    program
        .execute(session)
        .map(|_| form_count)
        .map_err(|error| format!("{label} SENS binary evaluator: {}", error.message))
}

fn surface_uses_sens_repl(surface: ReplSurface, sens_loop: bool) -> bool {
    sens_loop
        || matches!(
            surface,
            ReplSurface::Ukrainian | ReplSurface::UkrainianFull | ReplSurface::Sanskrit
        )
}

fn load_sens_repl_bootstraps(environment: &Environment) -> Result<(), String> {
    #[cfg(feature = "zig-transport")]
    {
        // D4 DEFINE installs the mechanism at its target resident's exact
        // identity. These programs define D9/D10 target slots, and DEFINE
        // admits such installations only in root, so load them before creating
        // a projection child. The operator is D4; target identity stays exact.
        let mut root = Session {
            environment: environment.clone(),
        };
        sens::load_time_library(&mut root).map_err(|error| {
            format!(
                "REPL T5M time bootstrap: {}",
                error.render("<T5M time bootstrap>")
            )
        })?;
        let meta_eval = crate::zig_transport::meta_eval_t5m_bytes()?;
        execute_zig_t5m_asset(&meta_eval, "MetaEval", &mut root)?;
        let repl_core = crate::zig_transport::repl_core_t5m_bytes()?;
        execute_zig_t5m_asset(&repl_core, "repl-core", &mut root)?;
        for (name, physical) in crate::zig_transport::repl_reasoning_t5m_assets()? {
            execute_zig_t5m_asset(&physical, name, &mut root)?;
        }
        let persistent_map = crate::zig_transport::persistent_map_t5m_bytes()?;
        execute_zig_t5m_asset(&persistent_map, "persistent-map", &mut root)?;
        let epistemic = crate::zig_transport::repl_epistemic_t5m_bytes()?;
        execute_zig_t5m_asset(&epistemic, "epistemic", &mut root)?;
        Ok(())
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = environment;
        Err("RUST_ZIG_ONLY: SENS REPL bootstrap requires physical T5M through Zig".into())
    }
}

// REPL prerequisites cross into Rust only as physical T5M bytes.
fn surface_prerequisite_t5m_assets() -> Result<Vec<(&'static str, Vec<u8>)>, String> {
    #[cfg(feature = "zig-transport")]
    {
        Ok(vec![(
            "persistent-vector",
            crate::zig_transport::repl_persistent_vector_t5m_bytes()?,
        )])
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: REPL prerequisite T5M assets require Zig transport".into())
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

/// Закодувати список параметрів lambda в явному контексті зв'язування.
/// Крапкове ім'я rest подається як послідовність W7 у рамці D2;
/// `parse_lambda_list` відновлює його лише в позиції rest-зв'язувача.
/// Та сама послідовність W7 в усіх інших місцях лишається звичайним списком D2.
fn append_t5m_lambda_parameters(
    expression: &Expr,
    layout: sens::Text7Layout,
    words: &mut Vec<ExactDomainWord>,
    depth: usize,
) -> Result<(), String> {
    if depth > sens::MAX_EXACT_D2_READER_DEPTH {
        return Err(format!(
            "T5M_SOURCE_DEPTH_NOT_ADMITTED: exact physical D2 reader limit={}",
            sens::MAX_EXACT_D2_READER_DEPTH
        ));
    }
    let ExprKind::Pair(head, tail) = &expression.kind else {
        return append_t5m_expression_context(expression, layout, words, depth, false);
    };
    let control = |bits| t5m_domain_identity(2, bits).map(ExactDomainWord::Identity);
    words.push(control(0b10)?);
    append_t5m_expression_context(head, layout, words, depth + 1, false)?;
    words.push(control(0b11)?);
    if matches!(tail.kind, ExprKind::Pair(..)) {
        append_t5m_lambda_parameters(tail, layout, words, depth + 1)?;
    } else {
        // Символ саме в цій синтаксичній позиції є крапковим rest-зв'язувачем.
        // Звичайне кодування символу дає послідовність гліфів W7 у D2-рамці;
        // розбір замикань визнає її ім'ям лише в цьому слоті зв'язування.
        append_t5m_expression_context(tail, layout, words, depth + 1, false)?;
    }
    words.push(control(0b01)?);
    Ok(())
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
    // depth — позиція, з якої exact D2 reader почне читати цей вираз.
    // Заміна вузла його точним представленням не додає глибини; її
    // збільшують дочірні слова створеної D2-рамки.
    if depth > sens::MAX_EXACT_D2_READER_DEPTH {
        return Err(format!(
            "T5M_SOURCE_DEPTH_NOT_ADMITTED: exact physical D2 reader limit={}",
            sens::MAX_EXACT_D2_READER_DEPTH
        ));
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
                let lambda_head = matches!(items.first().map(|item| &item.kind), Some(ExprKind::DomainIdentity(DomainIdentity::D4(word))) if word.word().packed_bits() == 0b0010);
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        words.push(control(0b00)?);
                    }
                    if lambda_head && index == 1 {
                        append_t5m_lambda_parameters(item, layout, words, depth + 1)?;
                    } else {
                        append_t5m_expression_context(item, layout, words, depth + 1, quoted_data)?;
                    }
                }
            }
            words.push(control(0b01)?);
        }
        ExprKind::Pair(head, tail) => {
            // Multi-glyph Text7 still lowers as a D2/W7 sequence and cannot
            // stand in for an atomic improper tail. In quoted data, one glyph
            // is the exact scalar D7 datum encoded above, so that case is safe.
            if let ExprKind::Symbol(name) = &tail.kind {
                let single_glyph_datum = if quoted_data
                    && sens::semantic_registry_export::admitted_core_domain_for_surface(name)
                        .is_none()
                {
                    let symbol_layout = if name.is_ascii() {
                        sens::Text7Layout::En
                    } else {
                        layout
                    };
                    sens::encode_text7(name, symbol_layout).is_ok_and(|text| text.len() == 1)
                } else {
                    false
                };
                if sens::semantic_registry_export::admitted_core_domain_for_surface(name).is_none()
                    && !single_glyph_datum
                {
                    return Err(format!(
                        "T5M_DOTTED_TEXT_TAIL_NOT_ATOMIC symbol={name:?}: multi-glyph D7 sequence cannot replace a dotted-pair atom"
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
            // A single quoted free glyph is one exact D7 datum. Do not
            // wrap it as a one-element D2 list: ATOM would then observe a
            // pair instead of the source-level atomic glyph. Multi-glyph
            // quoted names remain a D2/W7 sequence; only explicit binding
            // positions derive a Text7 key from such a frame.
            if quoted_data && text.len() == 1 {
                words.push(ExactDomainWord::Identity(t5m_domain_identity(
                    7,
                    u16::from(text.cells()[0]),
                )?));
                return Ok(());
            }
            ensure_t5m_d2_children_admitted(depth)?;
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
            append_t5m_expression_context(&exact, layout, words, depth, quoted_data)?;
        }
        ExprKind::Rational(value) => {
            let spelling = value.to_string();
            let (numerator, denominator) = spelling
                .split_once('/')
                .unwrap_or((spelling.as_str(), "1"));
            let numerator = exact_integer_source_word(numerator)?;
            let denominator = exact_integer_source_word(denominator)?;
            let quotient = exact_d5_surface("частка")?;
            let ratio = Expr {
                kind: ExprKind::DomainCall(quotient, vec![numerator, denominator].into()),
                span: expression.span,
            };
            append_t5m_expression_context(&ratio, layout, words, depth, quoted_data)?;
        }
        ExprKind::String(text) => {
            // Людський Unicode існує лише на вході REPL. Перш ніж
            // знижувати літерал у фізичні слова, обов'язково встановлюємо
            // його точне D7-кодування. Неприпустимий символ НЕ повинен
            // обходити драбину через D24 Unicode scalar / D8 CODE-CHAR.
            let text_layout = if text.is_ascii() {
                sens::Text7Layout::En
            } else {
                layout
            };
            let _admitted_d7 = sens::encode_text7(text, text_layout).map_err(|error| {
                format!("T5M_D7_TEXT_NOT_ADMITTED: REPL glyph cannot enter binary SENS as Unicode: {error}")
            })?;
            if quoted_data {
                ensure_t5m_d2_children_admitted(depth)?;
                // Як і цитовані символи, ASCII-рядки є D7-даними EN,
                // навіть коли виклична поверхня вибрана українською.
                // Інакше "sha256:abc" хибно шукатиме латинське 's' у Uk.
                let text_layout = if text.is_ascii() {
                    sens::Text7Layout::En
                } else {
                    layout
                };
                let text7 = sens::encode_text7(text, text_layout)
                    .map_err(|error| format!("T5M D7 text projection: {error}"))?;
                // Зовнішній D3 QUOTE вже задає позицію даних.
                // Повторний QUOTE тут перетворював Text7 на список з
                // головою QUOTE, тому READ(WRITE(...)) розходився з джерелом.
                // Порожній Text7 поки не має окремої фізичної тотожності:
                // залишаємо його чинний носій до ратифікації закону.
                if text7.cells().is_empty() {
                    words.push(control(0b10)?);
                    words.push(ExactDomainWord::identity(t5m_domain_identity(3, 0b001)?));
                    words.push(control(0b00)?);
                }
                words.push(control(0b10)?);
                for (index, cell) in text7.cells().iter().enumerate() {
                    if index > 0 {
                        words.push(control(0b00)?);
                    }
                    words.push(ExactDomainWord::identity(t5m_domain_identity(
                        7,
                        u16::from(*cell),
                    )?));
                }
                words.push(control(0b01)?);
                if text7.cells().is_empty() {
                    words.push(control(0b01)?);
                }
            } else {
                let lowered = string_value_expression(text)?;
                append_t5m_expression_context(&lowered, layout, words, depth, false)?;
            }
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

fn ensure_t5m_d2_children_admitted(depth: usize) -> Result<(), String> {
    if depth >= sens::MAX_EXACT_D2_READER_DEPTH {
        return Err(format!(
            "T5M_SOURCE_DEPTH_NOT_ADMITTED: generated D2 frame at reader depth {depth} has children beyond limit {}",
            sens::MAX_EXACT_D2_READER_DEPTH
        ));
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
    // The current exact executable identity carrier models D1–D10. D11
    // projection data is retained in the surface catalog, but it cannot be
    // lowered into this runtime carrier until its exact identity type exists.
    if width > 10 {
        return Ok(None);
    }
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
    session: &Session,
) -> Result<Option<DomainIdentity>, String> {
    let projected_name = match surface {
        // The projection is displayed in its canonical uppercase spelling,
        // while the interactive reader accepts the same Lisp name lowercase.
        ReplSurface::Lisp => name.to_uppercase(),
        _ => name.to_owned(),
    };

    // In a Ukrainian source position, the owner-ratified source-head index
    // outranks the compatibility surface catalog. The latter may not contain
    // every D4/D5/D8 callable (or may name an older route); falling through to
    // Text7 would turn a valid Ukrainian call head into a non-callable D7 glyph.
    if matches!(surface, ReplSurface::UkrainianFull | ReplSurface::Ukrainian) {
        if let Some(identity) =
            sens::semantic_registry_export::exact_uk_callable_for_source_head(&projected_name)
        {
            if let Some(core) = identity.core_operation() {
                return Ok(Some(DomainIdentity::from(core)));
            }
            if sens::semantic_registry_export::is_admitted_exact_definition_target(identity) {
                return Ok(Some(identity));
            }
        }
    }

    // `sym` is an orthogonal projection shared by every REPL surface, not a
    // selectable language mode. Prefer the selected human spelling, then
    // resolve a symbolic spelling from the same domain table. The result is
    // still only a candidate identity; the admission checks below decide
    // whether this resident has a callable mechanism.
    if let Some(identity_text) =
        surface_catalog::identity_for_surface_name(surface.code(), &projected_name)?
    {
        if let Some(identity) = admitted_catalog_callable(surface, &projected_name, &identity_text)?
        {
            return Ok(Some(identity));
        }
    }

    // Resolve every exact table surface against mechanisms that are actually
    // present: built-in evaluator laws or a concrete runtime code slot. This
    // keeps the REPL projection general across D1–D10 instead of maintaining
    // a second list of callable spellings here. A table row alone is only an
    // identity; it becomes a call head only when SENS has an implementation.
    if let Some(identity_text) =
        surface_catalog::identity_for_surface_name(surface.code(), &projected_name)?
    {
        if let Some(identity) = catalog_domain_identity(&identity_text)? {
            if sens::semantic_registry_export::has_exact_domain_mechanism(identity)
                || session.environment.has_domain_code_slot(identity)
            {
                return Ok(Some(identity));
            }
        }
    }

    // `sym` is shared by every surface. A symbolic alias may occur in more
    // than one domain, so resolve all exact candidates and retain only
    // identities with an already admitted mechanism. Accept it only when one
    // exact callable identity remains.
    let mut admitted = Vec::new();
    for identity_text in surface_catalog::identities_for_surface_name("sym", name)? {
        if let Some(identity) = admitted_catalog_callable(surface, &projected_name, &identity_text)? {
            admitted.push(identity);
        }
    }
    admitted.sort_by_key(|identity| (identity.width(), identity.packed_bits()));
    admitted.dedup();
    match admitted.as_slice() {
        [] => Ok(None),
        [identity] => Ok(Some(*identity)),
        identities => {
            let coordinates = identities
                .iter()
                .map(|identity| {
                    format!(
                        "D{}:{:0width$b}",
                        identity.width(),
                        identity.packed_bits(),
                        width = identity.width()
                    )
                })
                .collect::<Vec<_>>()
                .join(", ");
            Err(format!(
                "ambiguous sym spelling {name:?}; callable identities: {coordinates}"
            ))
        }
    }
}

fn admitted_catalog_callable(
    surface: ReplSurface,
    projected_name: &str,
    identity_text: &str,
) -> Result<Option<DomainIdentity>, String> {
    let Some(identity) = catalog_domain_identity(identity_text)? else {
        return Ok(None);
    };
    let Some(ukr_name) = surface_catalog::ukr_name_for_identity(identity_text)? else {
        return Ok(None);
    };
    Ok(sens::semantic_registry_export::exact_uk_callable_for_source_head(&ukr_name)
        .filter(|admitted| *admitted == identity)
        .and_then(DomainIdentity::core_operation)
        .map(DomainIdentity::from)
        .or_else(|| {
            sens::semantic_registry_export::is_admitted_exact_definition_target(identity)
                .then_some(identity)
        })
        .or_else(|| {
            (identity.width() == 8
                && projected_name == ukr_name
                && matches!(surface, ReplSurface::UkrainianFull | ReplSurface::Ukrainian))
            .then(|| identity.core_operation().map(DomainIdentity::from))
            .flatten()
        }))
}

fn is_t5m_callable_definition_form(expression: &Expr) -> bool {
    let lambda = |identity: DomainIdentity| matches!(identity, DomainIdentity::D4(word) if word.word().packed_bits() == 0b0010);
    match &expression.kind {
        ExprKind::DomainCall(identity, _) => lambda(DomainIdentity::from(*identity)),
        ExprKind::List(items) => {
            let head_is_lambda = items.first().is_some_and(|head| match &head.kind {
                ExprKind::DomainIdentity(identity) => lambda(*identity),
                ExprKind::Symbol(name) => name.as_ref() == "функція",
                _ => false,
            });
            if head_is_lambda {
                return true;
            }

            let macro_identity =
                sens::semantic_registry_export::admitted_core_domain_for_surface("макрос")
                    .map(DomainIdentity::from);
            let head_is_macro = items.first().is_some_and(|head| match &head.kind {
                ExprKind::DomainIdentity(identity) => Some(*identity) == macro_identity,
                ExprKind::Symbol(name) => name.as_ref() == "макрос",
                _ => false,
            });
            head_is_macro && items.get(1).is_some_and(is_t5m_callable_definition_form)
        }
        _ => false,
    }
}

/// Збирає локальні імена DEFINE та позначає визначення, що створюють замикання.
/// Ім'я лишається текстовим зв'язувачем, якщо воно не встановлюється у вільну
/// допущену identity D6/D9/D10.
/// Collect source-local DEFINE names and whether the definition constructs a
/// closure. A binder shadows a domain projection unless it is an unoccupied,
/// admitted D6/D9/D10 target whose value is explicitly a lambda.
fn collect_t5m_source_bindings(
    source: &str,
    expression: &Expr,
    names: &mut Vec<(std::rc::Rc<str>, bool)>,
) {
    let ExprKind::List(items) = &expression.kind else {
        if let ExprKind::Pair(head, tail) = &expression.kind {
            collect_t5m_source_bindings(source, head, names);
            collect_t5m_source_bindings(source, tail, names);
        }
        return;
    };
    if matches!(
        items.first().map(|item| &item.kind),
        Some(ExprKind::DomainIdentity(identity))
            if identity.width() == 3 && identity.packed_bits() == 0b001
    ) {
        return;
    }
    if matches!(items.first().map(|item| &item.kind), Some(ExprKind::DomainIdentity(DomainIdentity::D4(word))) if word.word().packed_bits() == 0b0011)
    {
        if let Some(target) = items.get(1) {
            if let Some(name) = source.get(target.span.start..target.span.end) {
                names.push((
                    name.into(),
                    items.get(2).is_some_and(is_t5m_callable_definition_form),
                ));
            }
        }
    }
    for item in items.iter() {
        collect_t5m_source_bindings(source, item, names);
    }
}

fn t5m_text7_surface_name(expression: &Expr, layout: sens::Text7Layout) -> Option<String> {
    // The mixed reader may preserve a source name as a Symbol directly.
    // Exact D7-cell lists still cover the physical Text7 representation.
    if let ExprKind::Symbol(name) = &expression.kind {
        return Some(name.to_string());
    }
    let ExprKind::List(items) = &expression.kind else {
        return None;
    };
    if items.is_empty() {
        return None;
    }
    let cells = items
        .iter()
        .map(|item| match &item.kind {
            ExprKind::DomainIdentity(DomainIdentity::D7(word)) => {
                Some(word.word().packed_bits())
            }
            _ => None,
        })
        .collect::<Option<Vec<_>>>()?;
    let text = sens::Text7::from_cells(cells).ok()?;
    sens::render_text7(&text, layout).ok()
}

fn project_repl_surface_expression_in_scope(
    expression: &Expr,
    session: &Session,
    surface: ReplSurface,
    source: &str,
    depth: usize,
    bound: &[std::rc::Rc<str>],
) -> Result<Expr, String> {
    if depth > 768 {
        return Err("REPL projection lowering exceeds the SENS nesting limit".into());
    }
    // The two ratified D24+ roots are immutable named values in the
    // Core environment. Identify them from their exact W7 cells, not source
    // byte spans: mixed-source projection can create a D2/W7 atom whose AST
    // span is not a trustworthy way to rediscover the original spelling.
    // This narrow rule substitutes only these two existing Core bindings;
    // it does not fold arbitrary variables or computed expressions.
    if let Some(name) = t5m_text7_surface_name(expression, t5m_surface_layout(surface)) {
        if matches!(name.as_str(), "число-нуль" | "число-один")
            && !bound
                .iter()
                .any(|candidate| candidate.as_ref() == name.as_str())
        {
            if let Some(number) = session.environment.get(&name).as_ref().and_then(|value| {
                match value {
                    Value::BinaryNumber(number) if number.numeric_domain_width() == Some(24) => {
                        Some(number)
                    }
                    _ => None,
                }
            }) {
                return Ok(Expr {
                    kind: ExprKind::BinaryNumber(number.clone()),
                    span: expression.span,
                });
            }
        }
    }

    if let ExprKind::DomainIdentity(identity) = &expression.kind {
        if let Some(name) = source.get(expression.span.start..expression.span.end) {
            // The source-binding collector has already removed names whose
            // unoccupied exact D9/D10 target must remain a domain identity.
            // Every remaining lexical or source-local binding shadows a
            // pre-resolved projection, even when the outer Core environment
            // already has the same name or its exact domain-code slot occupied.
            if bound.iter().any(|candidate| candidate.as_ref() == name) {
                return Ok(Expr {
                    kind: ExprKind::Symbol(name.into()),
                    span: expression.span,
                });
            }
            // The mixed source reader can pre-resolve a human spelling through
            // the generated callable index before this projection runs.
            // In source position, the selected owner table is authoritative:
            // D8 structural equality must not stay a stale D3 EQ identity.
            // Quote/data is shielded by the enclosing QUOTE branch above; bound
            // lexical names are shielded by the binder check immediately above.
            if let Some(projected) = selected_surface_callable(surface, name, session)? {
                return Ok(Expr {
                    kind: ExprKind::DomainIdentity(projected),
                    span: expression.span,
                });
            }
        }
        return Ok(Expr {
            kind: ExprKind::DomainIdentity(*identity),
            span: expression.span,
        });
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
            let lambda_identity = match &items[0].kind {
                ExprKind::DomainIdentity(identity) if matches!(identity, DomainIdentity::D4(word) if word.word().packed_bits() == 0b0010) => {
                    Some(*identity)
                }
                ExprKind::Symbol(head) if session.environment.get(head).is_none() => {
                    selected_surface_callable(surface, head, session)?.filter(|identity| {
                        matches!(
                            identity,
                            DomainIdentity::D4(word) if word.word().packed_bits() == 0b0010
                        )
                    })
                }
                _ => None,
            };
            if let Some(identity) = lambda_identity {
                let mut lambda_bound = bound.to_vec();
                let parameters = items
                    .get(1)
                    .map(|parameters| project_lambda_binder_names(parameters, source))
                    .transpose()?;
                if let Some(parameters) = &parameters {
                    collect_repl_binders(parameters, &mut lambda_bound);
                }
                let mut projected = Vec::with_capacity(items.len());
                projected.push(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span: items[0].span,
                });
                if let Some(parameters) = parameters {
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
                                source,
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
                        source,
                        depth + 1,
                        bound,
                    )
                })
                .collect::<Result<Vec<_>, _>>()?;
            let define_head = match &items[0].kind {
                ExprKind::DomainIdentity(DomainIdentity::D4(word)) => {
                    word.word().packed_bits() == 0b0011
                }
                ExprKind::Symbol(head) if session.environment.get(head).is_none() => {
                    selected_surface_callable(surface, head, session)?.is_some_and(|identity| {
                        matches!(identity, DomainIdentity::D4(word) if word.word().packed_bits() == 0b0011)
                    })
                }
                _ => false,
            };
            if define_head {
                if let Some(target) = items.get(1) {
                    if let Some(target_name) = source.get(target.span.start..target.span.end) {
                        if let Some(identity) =
                            selected_surface_callable(surface, target_name, session)?
                        {
                            if sens::semantic_registry_export::is_admitted_exact_definition_target(
                                identity,
                            ) && items.get(2).is_some_and(is_t5m_callable_definition_form)
                            {
                                projected[1] = Expr {
                                    kind: if session.environment.has_domain_code_slot(identity)
                                        || session.environment.get(target_name).is_some()
                                    {
                                        ExprKind::Symbol(target_name.into())
                                    } else {
                                        ExprKind::DomainIdentity(identity)
                                    },
                                    span: target.span,
                                };
                            }
                        }
                    }
                }
            }
            if let ExprKind::Symbol(head) = &items[0].kind {
                // A user binding in the persistent REPL frame shadows a projection
                // alias, preserving ordinary interactive rebinding behavior.
                if !bound
                    .iter()
                    .any(|candidate| candidate.as_ref() == head.as_ref())
                    && session.environment.get(head).is_none()
                {
                    if let Some(identity) = selected_surface_callable(surface, head, session)? {
                        let arguments = projected.drain(1..).collect::<Vec<_>>();
                        if let Some(core_identity) = identity.core_operation() {
                            return Ok(Expr {
                                kind: ExprKind::DomainCall(core_identity, arguments.into()),
                                span: expression.span,
                            });
                        }
                        let mut call = Vec::with_capacity(arguments.len() + 1);
                        call.push(Expr {
                            kind: ExprKind::DomainIdentity(identity),
                            span: items[0].span,
                        });
                        call.extend(arguments);
                        return Ok(Expr {
                            kind: ExprKind::List(call.into()),
                            span: expression.span,
                        });
                    }
                }
                // A loaded language definition may occupy both its Text7 name
                // and the exact domain call slot. In that case carry the
                // ratified identity through T5M so the binary reader dispatches
                // the same closure; otherwise a D7 text atom is mistaken for code.
                if !bound
                    .iter()
                    .any(|candidate| candidate.as_ref() == head.as_ref())
                {
                    if let Some(identity) = selected_surface_callable(surface, head, session)? {
                        if session.environment.has_domain_code_slot(identity) {
                            let arguments = projected.drain(1..).collect::<Vec<_>>();
                            let mut call = Vec::with_capacity(arguments.len() + 1);
                            call.push(Expr {
                                kind: ExprKind::DomainIdentity(identity),
                                span: items[0].span,
                            });
                            call.extend(arguments);
                            return Ok(Expr {
                                kind: ExprKind::List(call.into()),
                                span: expression.span,
                            });
                        }
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
        if let Some(identity) = selected_surface_callable(surface, name, session)? {
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(identity),
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

/// Lambda parameter names are lexical text even when their spelling is also
/// a ratified domain projection. Keep the source spelling in this binder-only
/// position; the SENS binary reader still rejects names reserved by its laws.
fn project_lambda_binder_names(expression: &Expr, source: &str) -> Result<Expr, String> {
    let mut projected = expression.clone();
    projected.kind = match &expression.kind {
        ExprKind::List(items) => ExprKind::List(
            items
                .iter()
                .map(|item| project_lambda_binder_names(item, source))
                .collect::<Result<Vec<_>, _>>()?
                .into(),
        ),
        ExprKind::Pair(head, tail) => ExprKind::Pair(
            std::rc::Rc::new(project_lambda_binder_names(head, source)?),
            std::rc::Rc::new(project_lambda_binder_names(tail, source)?),
        ),
        ExprKind::Symbol(_) | ExprKind::DomainIdentity(_) => {
            let spelling = source
                .get(expression.span.start..expression.span.end)
                .ok_or("T5M_LAMBDA_BINDER_SOURCE_SPAN_INVALID")?;
            ExprKind::Symbol(spelling.into())
        }
        _ => expression.kind.clone(),
    };
    Ok(projected)
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
    let (_, decoded) = crate::zig_transport::encode_t5m_exact_words_and_restore(&carrier)?;
    restore_t5m_words(words, &decoded)
}

#[cfg(not(feature = "zig-transport"))]
fn t5m_roundtrip_words(_words: &[ExactDomainWord]) -> Result<Vec<ExactDomainWord>, String> {
    Err("RUST_ZIG_ONLY: REPL requires the Zig T5M transport; no Rust fallback".into())
}

// Turn returned values into ordinary SENS constructors. This keeps symbols
// distinct from their D7 spelling and preserves proper/improper D3 pairs.
fn exact_t5m_result_expression(value: &Value, depth: usize) -> Result<Expr, String> {
    if depth > 768 {
        return Err("T5M_RESULT_DEPTH: D3 result exceeds exact reader limit".into());
    }
    let expression = match value {
        Value::Nil => Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::from(CoreDomainIdentity::from(
                sens::Bija3::from_word(sens::Bit3::new(0).expect("D3 nil coordinate")),
            ))),
            span: Default::default(),
        },
        Value::String(text) => string_value_expression(text)?,
        Value::Text7(text) => {
            if text.is_empty() {
                return Err(
                    "T5M_RESULT_UNSUPPORTED value=Text7: empty D7 text has no distinct canonical datum".into(),
                );
            }
            let quoted_text = Expr {
                kind: ExprKind::List(
                    text.to_source_words()
                        .into_iter()
                        .map(|word| Expr {
                            kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(word)),
                            span: Default::default(),
                        })
                        .collect::<Vec<_>>()
                        .into(),
                ),
                span: Default::default(),
            };
            Expr {
                kind: ExprKind::DomainCall(
                    exact_core_identity("як-є", 3)?,
                    vec![quoted_text].into(),
                ),
                span: Default::default(),
            }
        }
        Value::Symbol(symbol) => Expr {
            kind: ExprKind::DomainCall(
                exact_core_identity("текст-у-символ", 8)?,
                vec![string_value_expression(symbol)?].into(),
            ),
            span: Default::default(),
        },
        Value::Pair(node) => Expr {
            kind: ExprKind::DomainCall(
                exact_core_identity("сполучити", 3)?,
                vec![
                    exact_t5m_result_expression(&node.head, depth + 1)?,
                    exact_t5m_result_expression(&node.tail, depth + 1)?,
                ]
                .into(),
            ),
            span: Default::default(),
        },
        Value::BinaryNumber(number) => Expr {
            kind: ExprKind::BinaryNumber(number.clone()),
            span: Default::default(),
        },
        Value::DomainIdentity(identity) if !matches!(identity, DomainIdentity::D2(_)) => Expr {
            kind: ExprKind::DomainIdentity(*identity),
            span: Default::default(),
        },
        other => {
            return Err(format!(
                "T5M_RESULT_UNSUPPORTED value={other}: no exact D1–24+ constructor"
            ));
        }
    };
    Ok(expression)
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
        Value::String(text) => {
            let expression = string_value_expression(text)?;
            let mut words = Vec::new();
            append_t5m_expression(&expression, sens::Text7Layout::En, &mut words, 0)?;
            Ok(words)
        }
        Value::Text7(_) | Value::Pair(..) => {
            let expression = exact_t5m_result_expression(value, 0)?;
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

/// Build an ordinary domain expression for a String value. Unicode scalar
/// numbers are exact D24+ operands to the ratified D8 CODE-CHAR resident;
/// D9 APPEND combines nonempty text and D9 REST constructs the empty string
/// from a valid one-character string. No private T5M marker is introduced.
fn string_value_expression(text: &str) -> Result<Expr, String> {
    let code_char = exact_core_identity("символ-за-кодом", 8)?;
    let append = exact_core_identity("рядок-додати", 9)?;
    let rest = exact_core_identity("рядок-решта", 9)?;
    let scalar_expression = |scalar: u32| -> Result<Expr, String> {
        let bits = (0..24)
            .rev()
            .map(|shift| ((scalar >> shift) & 1) as u8)
            .collect::<Vec<_>>();
        let number = BinaryNumber::from_numeric_domain_bits(24, &bits)
            .ok_or("T5M String projection could not form an exact D24+ scalar")?;
        Ok(Expr {
            kind: ExprKind::DomainCall(
                code_char,
                vec![Expr {
                    kind: ExprKind::BinaryNumber(number),
                    span: Default::default(),
                }]
                .into(),
            ),
            span: Default::default(),
        })
    };

    let mut characters = text.chars();
    let Some(first) = characters.next() else {
        return Ok(Expr {
            kind: ExprKind::DomainCall(rest, vec![scalar_expression(0)?].into()),
            span: Default::default(),
        });
    };
    let mut expression = scalar_expression(first as u32)?;
    for character in characters {
        expression = Expr {
            kind: ExprKind::DomainCall(
                append,
                vec![expression, scalar_expression(character as u32)?].into(),
            ),
            span: Default::default(),
        };
    }
    Ok(expression)
}

fn exact_core_identity(surface: &str, width: usize) -> Result<CoreDomainIdentity, String> {
    if matches!(width, 8 | 9) {
        let mut found = None;
        for packed in 0..(1u16 << width) {
            let bits = format!("{packed:0width$b}");
            if matches!(
                sens::domain_projection_catalog::lookup(
                sens::domain_projection_catalog::ProjectionSource::DomainTable,
                width as u16,
                &bits,
                "укр",
                ),
                Some(sens::domain_projection_catalog::ProjectionValue::Symbol(name)) if name == surface
            ) {
                if found.is_some() {
                    return Err(format!("ambiguous ratified D8 surface {surface}"));
                }
                found = Some(match width {
                    8 => CoreDomainIdentity::D8(sens::CoreD8::from_word(
                        sens::Bit8::new(packed as u8).expect("bounded D8 word"),
                    )),
                    9 => CoreDomainIdentity::D9(sens::CoreD9::from_word(
                        sens::Bit9::new(packed).expect("bounded D9 word"),
                    )),
                    _ => unreachable!("the loop is restricted to D8/D9"),
                });
            }
        }
        return found
            .ok_or_else(|| format!("SENS surface {surface} has no ratified D{width} identity"));
    }
    sens::semantic_registry_export::admitted_core_domain_for_surface(surface)
        .filter(|identity| identity.width() == width)
        .ok_or_else(|| format!("SENS surface {surface} has no admitted D{width} identity"))
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
    let parsed = sens::parse_mixed_exact_domain(line).map_err(|error| {
        sens::render_error_for_presentation(&error, line, surface.presentation())
    })?;
    let mut source_bindings = Vec::new();
    for expression in &parsed {
        collect_t5m_source_bindings(line, expression, &mut source_bindings);
    }
    // A source-local name shadows a domain projection only if the selected
    // domain slot is already occupied in this session. Otherwise the ratified
    // D10 target and its call sites must remain exact DomainIdentity words.
    source_bindings.retain(|(name, is_lambda)| {
        let exact_target = selected_surface_callable(surface, name, session)
            .ok()
            .flatten()
            .filter(|identity| {
                sens::semantic_registry_export::is_admitted_exact_definition_target(*identity)
            });
        let will_be_exact = *is_lambda
            && exact_target.is_some_and(|identity| {
                !session.environment.has_domain_code_slot(identity)
                    && session.environment.get(name).is_none()
            });
        !will_be_exact
    });
    let bound_names = source_bindings
        .iter()
        .map(|(name, _)| name.clone())
        .collect::<Vec<_>>();
    let expressions = parsed
        .iter()
        .map(|expression| {
            project_repl_surface_expression_in_scope(
                expression,
                session,
                surface,
                line,
                0,
                &bound_names,
            )
        })
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
fn core4_t5m_source_session() -> Result<Session, String> {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .map_err(|error| format!("T5M_CORE4_BOOTSTRAP: {}", error.message))?;
    Ok(session)
}

#[cfg(feature = "zig-transport")]
pub(crate) fn mint_t5m_source_pair_with_bindings(
    source: &str,
    bindings: &[String],
) -> Result<(Vec<u8>, String), String> {
    // Пряме виконання .lisp працює з Core4, а не лише з D4 MACRO.
    // Без того самого SENS bootstrap корені D24+ (число-нуль/один)
    // лишаються непов'язаними D7 гліфами і помилково викликаються як Lisp.
    // Визначення і числа надає тільки SENS Core4, не Rust-підстановка.
    let mut session = core4_t5m_source_session()?;
    preload_t5m_binding_sources(&mut session, bindings)?;
    mint_t5m_source_pair_in_session(source, &session)
}

#[cfg(feature = "zig-transport")]
fn mint_t5m_source_pair_in_session(
    source: &str,
    session: &Session,
) -> Result<(Vec<u8>, String), String> {
    let words = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, session)?;
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
    eval_t5m_paired_file_with_runtime(source, physical, bindings, false)
}

#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_paired_file_with_core4(
    source: &str,
    physical: &[u8],
    bindings: &[String],
) -> Result<sens::EvalResult, String> {
    eval_t5m_paired_file_with_runtime(source, physical, bindings, true)
}

#[cfg(feature = "zig-transport")]
fn eval_t5m_paired_file_with_runtime(
    source: &str,
    physical: &[u8],
    bindings: &[String],
    load_core4: bool,
) -> Result<sens::EvalResult, String> {
    // Mint always projects with Core4's exact D24+ roots available. Use the
    // same projection environment here, but keep runtime Core4 opt-in and
    // separate so source identity is established before runtime admission.
    let mut projection_session = core4_t5m_source_session()?;
    preload_t5m_binding_sources(&mut projection_session, bindings)?;
    let expected = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, &projection_session)?;
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
    let mut session = Session::default();
    // Optional runtime profile is loaded only after the source has established
    // its exact words. This keeps Core4 mechanisms available without allowing
    // their surface bindings to erase D8 identities during projection.
    if load_core4 {
        sens::load_core_library(&mut session)
            .map_err(|error| format!("SENS paired Core4 bootstrap: {}", error.render(source)))?;
    }
    preload_t5m_binding_sources(&mut session, bindings)?;
    // Фізичні вхідні слова вже пройшли точну перевірку Zig/SENS.
    // Не відхиляємо справжні результати SENS (списки, пари) лише
    // через те, що кодер зворотного представлення результатів їх не знає.
    // Це не засвідчує оберненість виходу; release=NOT_CERTIFIED.
    // PhysicalT5Program spans index decoded D2/T5M WORDS, not source UTF-8
    // bytes. Rendering those indices against the original Lisp falsely
    // highlights unrelated text (often the first comment) and misdirects
    // repair. SENS still owns the actual verdict; report exact word offsets.
    program.execute(&mut session).map_err(|error| format!(
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
    let mut result = program.execute(session).map_err(|error| {
        let presentation = surface.presentation();
        let heading = if presentation == sens::PresentationLanguage::Ukrainian {
            "Помилка виконання SENS/T5M"
        } else {
            "SENS/T5M execution error"
        };
        format!(
            "{heading}:\n{}",
            sens::render_error_summary_for_presentation(&error, presentation)
        )
    })?;
    // A defined closure is retained in the persistent SENS environment, but
    // it is not itself an exact-domain data word to send back through T5M.
    // Keep the evaluator's opaque runtime result for REPL presentation; all
    // subsequent invocations still cross Zig T5M as exact source words.
    if matches!(&result.value, Value::Closure(_)) {
        return Ok(result);
    }
    match roundtrip_repl_result(result.value.clone()) {
        Ok(restored) => result.value = restored,
        // Runtime values such as the lexical environment can contain closures
        // and host mechanisms. They remain valid SENS results even though
        // today's exact T5M result constructors do not serialize those values.
        Err(error) if error.starts_with("T5M_RESULT_UNSUPPORTED") => {}
        Err(error) => return Err(error),
    }
    Ok(result)
}

/// Виконати повний файл української Lisp-проєкції тим самим фізичним
/// шляхом, що й один крок REPL: точні слова → Zig T5M roundtrip → SENS.
/// Сесія навмисно без host-capabilities; цей режим є runtime-свідком, а не
/// способом запускати довільні системні дії з CI.
#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_source_file(source: &str) -> Result<sens::EvalResult, String> {
    let mut session = Session::default();
    eval_t5m_source_in_session(source, &mut session, ReplSurface::UkrainianFull)
}

/// Execute a human source form in an existing host session through the same
/// exact-word → Zig T5M → SENS path used by the REPL. The session supplies
/// already admitted language definitions, command-line arguments, and host
/// capabilities; it does not provide a textual evaluator fallback.
#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_source_in_session(
    source: &str,
    session: &mut Session,
    surface: ReplSurface,
) -> Result<sens::EvalResult, String> {
    eval_t5m_repl_line(source, session, surface)
}

/// Виконати джерело через T5M у вже завантаженій сесії, зберігши непрозорий
/// результат синтаксичного дерева для мовних інструментів на кшталт лінтера.
#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_source_in_session_preserving_result(
    source: &str,
    session: &mut Session,
    surface: ReplSurface,
) -> Result<sens::EvalResult, String> {
    let program = prepare_t5m_repl_program(source, surface, session)?;
    program
        .execute(session)
        .map_err(|error| format!("SENS binary evaluator: {}", error.render(source)))
}

/// Виконати впорядковані Lisp-частини через Zig/T5M в одній SENS-сесії.
/// Кожен файл проходить окремий фізичний T5M roundtrip; визначення з попередніх
/// файлів лишаються доступними наступним. Це композиція файлів у CLI, не
/// мовний `include` і не дозвіл на виклик D7-резидентів.
#[cfg(feature = "zig-transport")]
pub(crate) fn eval_t5m_source_files(files: &[(&str, &str)]) -> Result<sens::EvalResult, String> {
    if files.is_empty() {
        return Err("T5M_FILES_EMPTY: pass at least one .lisp source".into());
    }
    let mut session = Session::default();
    let mut value = Value::Nil;
    let mut output = Vec::new();
    for (path, source) in files {
        let mut result = eval_t5m_repl_line(source, &mut session, ReplSurface::UkrainianFull)
            .map_err(|error| format!("T5M source {path}: {error}"))?;
        value = result.value;
        output.append(&mut result.output);
    }
    Ok(sens::EvalResult { value, output })
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

fn build_surface_layer(base: &Environment, surface: ReplSurface) -> Result<Environment, String> {
    // D4 DEFINE may install a mechanism at an exact D10 target identity, and
    // that target slot is root-only. Ensure shared time mechanisms before
    // creating a projection child; loading is idempotent after prior bootstrap.
    let mut base_session = Session {
        environment: base.clone(),
    };
    sens::load_time_library(&mut base_session).map_err(|error| {
        format!(
            "не вдалося завантажити часове ядро T5M: {}",
            error.render("<T5M time bootstrap>")
        )
    })?;
    let layer = base.child();
    let needs_surface = matches!(
        surface,
        ReplSurface::Ukrainian | ReplSurface::UkrainianFull | ReplSurface::Sanskrit
    );
    if needs_surface {
        let mut session = Session {
            environment: layer.clone(),
        };
        let prerequisite_assets = surface_prerequisite_t5m_assets()?;
        for (name, physical) in prerequisite_assets {
            execute_zig_t5m_asset(&physical, name, &mut session)?;
        }
        // Ukrainian surface files are documentation-only. Their names and
        // exact identities already come from the live domain registry; do not
        // parse empty comment-only Lisp sources in the Rust runtime.
        // sa.lisp has candidate/legacy aliases, so Sanskrit also resolves only
        // current table names through selected_surface_callable.
    }
    Ok(layer)
}

struct ReplState {
    session: Session,
    base_environment: Environment,
    user_environment: Environment,
    surface: ReplSurface,
    sens_loop: bool,
    sens_repl_bootstrapped: bool,
}

impl ReplState {
    fn new(mut session: Session, surface: ReplSurface, sens_loop: bool) -> Result<Self, String> {
        let base_environment = session.environment.clone();
        let sens_repl_bootstrapped = surface_uses_sens_repl(surface, sens_loop);
        if sens_repl_bootstrapped {
            load_sens_repl_bootstraps(&base_environment)?;
        }
        let surface_environment = build_surface_layer(&base_environment, surface)?;
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
            sens_repl_bootstrapped,
        })
    }

    fn switch_surface(&mut self, surface: ReplSurface) -> Result<(), String> {
        if self.surface == surface {
            return Ok(());
        }
        if !self.sens_repl_bootstrapped && surface_uses_sens_repl(surface, self.sens_loop) {
            load_sens_repl_bootstraps(&self.base_environment)?;
            self.sens_repl_bootstrapped = true;
        }
        let surface_environment = build_surface_layer(&self.base_environment, surface)?;
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
fn render_repl_reply(value: &Value, surface: ReplSurface) -> String {
    match value {
        Value::Symbol(symbol) => {
            if let Ok(text7) = sens::Text7::from_canonical_wire_token(symbol) {
                sens::render_text7(&text7, t5m_surface_layout(surface))
                    .unwrap_or_else(|_| render_value_for_presentation(value, surface.presentation()))
                    .to_uppercase()
            } else {
                render_value_for_presentation(value, surface.presentation()).to_uppercase()
            }
        }
        Value::DomainIdentity(sens::DomainIdentity::D1(_)) => {
            render_value_for_presentation(value, surface.presentation()).to_uppercase()
        }
        Value::Pair(_) => render_repl_pair(value, surface),
        Value::Vector(vector) => {
            let items = vector
                .borrow()
                .iter()
                .map(|item| render_repl_reply(item, surface))
                .collect::<Vec<_>>();
            format!("#({})", items.join(" "))
        }
        _ => render_value_for_presentation(value, surface.presentation()),
    }
}

fn render_repl_pair(value: &Value, surface: ReplSurface) -> String {
    let mut output = String::from("(");
    let mut current = value;
    let mut first = true;

    loop {
        match current {
            Value::Pair(node) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_repl_reply(&node.head, surface));
                current = &node.tail;
                first = false;
            }
            Value::Nil => {
                output.push(')');
                return output;
            }
            tail => {
                output.push_str(" . ");
                output.push_str(&render_repl_reply(tail, surface));
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
        "Зворотний шлях Zig/T5M: {} точних слів; виконання не запускалося.",
        restored.len()
    ));
    for (index, form) in forms.iter().enumerate() {
        lines.push(format!("Форма {}", index + 1));
        let mut ast = Vec::new();
        sens::render_ast_node(source, form, 1, PresentationLanguage::Ukrainian, &mut ast);
        lines.extend(ast.into_iter().map(|line| line.text));
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

/// `~/.sens-history`, якщо home directory доступний.
pub(crate) fn history_path() -> Option<PathBuf> {
    let home = env::var_os("HOME").or_else(|| env::var_os("USERPROFILE"))?;
    Some(PathBuf::from(home).join(".sens-history"))
}

// REPL host inspection only: snapshot the bindings visible to lexical lookup.
// This is NOT a D10 ENV call, not a SENS value and not a semantic oracle.
// Avoid rendering arbitrary recursive/large data or leaking opaque host tokens.
fn render_lexical_bindings(session: &Session, surface: ReplSurface) -> String {
    let bindings = session.environment.snapshot();
    let mut lines = Vec::with_capacity(bindings.len() + 2);
    lines.push(format!(
        "Лексичне середовище REPL: {} прив'язок (без фільтра поверхнею; складні значення — типами).",
        bindings.len()
    ));
    for (name, value) in bindings {
        let shown = match &value {
            Value::Closure(_) => "<замикання SENS>".to_owned(),
            Value::Macro(_) => "<макрос SENS>".to_owned(),
            Value::Builtin(_) => "<механізм хоста>".to_owned(),
            Value::HostHandle { .. } => "<непрозорий ресурс>".to_owned(),
            Value::Pair(_) => "<список або пара>".to_owned(),
            Value::Vector(_) => "<вектор>".to_owned(),
            Value::NumericBuffer(_) => "<числовий буфер>".to_owned(),
            Value::String(text) if text.len() > 256 => "<довгий рядок>".to_owned(),
            _ => render_repl_reply(&value, surface),
        };
        lines.push(format!("{name} = {shown}"));
    }
    lines.join("\n")
}

fn print_surface_help() {
    println!("Завантажити файл у поточну сесію: :завантажити <шлях>");
    println!("Показати дерево розбору без виконання: :розбір <форма>");
    println!("Показати дерево й виконати форму: :розбір-виконати <форма>");
    println!("Поверхні: :мова ук | укр | en | sa | LISP | core");
    println!("Додаткова команда: :surface ук | укр | en | sa | LISP | core");
    println!("Каталог поточної людської поверхні: :імена / :names");
    println!("Одна й та сама тотожність у всіх людських поверхнях: :ім'я <назва> / :name <name>");
    println!("Стан людських поверхонь: :поверхні / :surfaces");
    println!(
        "Виміряти REPL через Zig T5M і переглянути термінальний звіт: :бенч [вимірів 100..10000]"
    );
    println!("Мовний перегляд лексичного середовища: (середовище) / (env); D8: (відобразити-середовище).");
    println!("Технічний знімок REPL: :env / :середовище (команда оболонки).");
    println!("LISP — окрема проєкція з доменних таблиць; core — канонічний машинний шар.");
    println!("Перемикання змінює лише поверхню; ваші визначення й замикання лишаються доступними.");
}

fn handle_meta_command(line: &str, state: &mut ReplState) -> bool {
    let mut parts = line.split_whitespace();
    let Some(command) = parts.next() else {
        return false;
    };

    match command {
        ":завантажити" | ":load" => {
            let raw_path = line.trim_start().strip_prefix(command).unwrap_or("").trim();
            let path = raw_path
                .strip_prefix('"')
                .and_then(|value| value.strip_suffix('"'))
                .or_else(|| {
                    raw_path
                        .strip_prefix('\'')
                        .and_then(|value| value.strip_suffix('\''))
                })
                .unwrap_or(raw_path);
            if path.is_empty() {
                eprintln!("Використання: :завантажити <шлях>");
                return true;
            }
            #[cfg(feature = "zig-transport")]
            {
                let source = match std::fs::read_to_string(path) {
                    Ok(source) => source,
                    Err(error) => {
                        eprintln!("Помилка читання файла {}: {error}", path);
                        return true;
                    }
                };
                match eval_t5m_source_in_session(&source, &mut state.session, state.surface) {
                    Ok(result) => {
                        for out in result.output {
                            println!("{out}");
                        }
                        println!("Завантажено: {path}");
                        println!(
                            "{}",
                            render_repl_reply(&result.value, state.surface)
                        );
                    }
                    Err(error) => eprintln!("Помилка завантаження {path}: {error}"),
                }
            }
            #[cfg(not(feature = "zig-transport"))]
            eprintln!(
                "Помилка: :завантажити потребує Zig T5M; RUST_ZIG_ONLY означає відсутній транспорт."
            );
            true
        }
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
        ":середовище" | ":env" => {
            if parts.next().is_some() {
                eprintln!("Команда :середовище не приймає аргументів.");
            } else {
                println!("{}", render_lexical_bindings(&state.session, state.surface));
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
        ":бенч" | ":bench" => {
            let samples = match parts.next() {
                Some(value) => match value.parse::<usize>() {
                    Ok(samples) if (100..=10_000).contains(&samples) => samples,
                    _ => {
                        eprintln!("Використання: :бенч [вимірів 100..10000]");
                        return true;
                    }
                },
                None => benchmark::DEFAULT_SAMPLES,
            };
            if parts.next().is_some() {
                eprintln!("Використання: :бенч [вимірів 100..10000]");
                return true;
            }
            if let Err(error) = benchmark::render_in_repl(state, samples) {
                eprintln!("Помилка вимірювання REPL: {error}");
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
                                    render_repl_reply(&result.value, state.surface)
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

fn render_repl_error(error: &str) -> String {
    format!("Помилка REPL/T5M: {error}")
}

pub(crate) fn run_repl(session: Session, initial_surface: ReplSurface, sens_loop: bool) {
    let mut state = match ReplState::new(session, initial_surface, sens_loop) {
        Ok(state) => state,
        Err(error) => {
            eprintln!("Помилка: не вдалося налаштувати поверхню REPL: {error}");
            process::exit(1);
        }
    };

    println!(
        "SENS REPL версії {} · Zig T5M → двійкові слова SENS → механізми Rust",
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
    println!("D1 у канонічному поданні — 1/0; українська проєкція D1 — ТАК/НІ.");
    println!("Ctrl-C або Ctrl-D — вихід.");

    let mut rl = match DefaultEditor::new() {
        Ok(editor) => editor,
        Err(err) => {
            eprintln!("Помилка: не вдалося запустити редактор рядка REPL: {err}");
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
                            render_repl_reply(&result.value, state.surface)
                        );
                    }
                    Err(error) => {
                        // Хост лише показує відмову; він не перетворює її на успішний результат.
                        eprintln!("{}", render_repl_error(&error));
                    }
                }
            }
            Err(ReadlineError::Interrupted | ReadlineError::Eof) => break,
            Err(err) => {
                eprintln!("Помилка введення REPL: {err:?}");
                break;
            }
        }
    }
}


