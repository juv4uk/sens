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
                .map_or((spelling.as_str(), "1"), |parts| parts);
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
    Ok(
        sens::semantic_registry_export::exact_uk_callable_for_source_head(&ukr_name)
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
            }),
    )
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
        match &expression.kind {
            ExprKind::Pair(head, tail) => {
                collect_t5m_source_bindings(source, head, names);
                collect_t5m_source_bindings(source, tail, names);
            }
            _ => {}
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
                Some(word.word().packed_bits() as u8)
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
            if let Some(value) = session.environment.get(&name) {
                if let Value::BinaryNumber(number) = &value {
                    if number.numeric_domain_width() == Some(24) {
                        return Ok(Expr {
                            kind: ExprKind::BinaryNumber(number.clone()),
                            span: expression.span,
                        });
                    }
                }
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
            if let Some(projected) = selected_surface_callable(surface, name)? {
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
                    selected_surface_callable(surface, head)?.filter(|identity| {
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
                    kind: ExprKind::DomainIdentity(DomainIdentity::from(identity)),
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
                    selected_surface_callable(surface, head)?.is_some_and(|identity| {
                        matches!(identity, DomainIdentity::D4(word) if word.word().packed_bits() == 0b0011)
                    })
                }
                _ => false,
            };
            if define_head {
                if let Some(target) = items.get(1) {
                    if let Some(target_name) = source.get(target.span.start..target.span.end) {
                        if let Some(identity) = selected_surface_callable(surface, target_name)? {
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
                    if let Some(identity) = selected_surface_callable(surface, head)? {
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
                    if let Some(identity) = selected_surface_callable(surface, head)? {
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
        let exact_target = selected_surface_callable(surface, name)
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
fn render_repl_reply(value: &Value, language: PresentationLanguage) -> String {
    match value {
        Value::Symbol(_) => render_value_for_presentation(value, language).to_uppercase(),
        Value::DomainIdentity(sens::DomainIdentity::D1(_)) => {
            render_value_for_presentation(value, language).to_uppercase()
        }
        Value::Pair(_) => render_repl_pair(value, language),
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
            Value::Pair(node) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_repl_reply(&node.head, language));
                current = &node.tail;
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
    println!("Сире лексичне середовище без фільтрації поверхнею: (середовище) / (env)");
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
                            render_repl_reply(&result.value, state.surface.presentation())
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

fn repl_error_message(error: &str) -> String {
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
                            render_repl_reply(&result.value, state.surface.presentation())
                        );
                    }
                    Err(error) => {
                        // Відмову SENS передаємо як помилку; не маскуємо її echo-відповіддю.
                        eprintln!("{}", repl_error_message(&error));
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

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_bootstrap_evaluator_and_loop_execute_from_t5m_domain_words() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4 bootstrap");
        sens::load_time_library(&mut session).expect("time bootstrap");

        let meta_eval = crate::zig_transport::meta_eval_t5m_bytes()
            .expect("Zig carries physical MetaEval T5M bytes");
        let meta_forms = execute_zig_t5m_asset(&meta_eval, "MetaEval", &mut session)
            .expect("MetaEval executes from exact T5M domain words");
        assert!(meta_forms > 0);

        let repl_core = crate::zig_transport::repl_core_t5m_bytes()
            .expect("Zig carries physical REPL-core T5M bytes");
        let repl_forms = execute_zig_t5m_asset(&repl_core, "repl-core", &mut session)
            .expect("REPL core executes from exact T5M domain words");
        assert!(repl_forms > 0);
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn cli_source_file_executes_via_t5m_in_the_existing_sens_session() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4 bootstrap");
        let result = eval_t5m_source_in_session(
            "(додати-1 число-один)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("source is encoded by Zig T5M and executed by SENS");

        assert_eq!(result.value.to_string(), "2");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_prerequisite_pairs_execute_as_t5m_domain_words() {
        let reasoning_assets = crate::zig_transport::repl_reasoning_t5m_assets()
            .expect("REPL reasoning T5M assets via Zig");
        let names = reasoning_assets
            .iter()
            .map(|(name, _)| *name)
            .collect::<Vec<_>>();
        assert_eq!(
            names,
            ["unify", "reason", "forward", "knowledge"],
            "D4 DEFINE reasoning programs must cross Zig as ordered root T5M pairs"
        );
        let surface_assets =
            surface_prerequisite_t5m_assets().expect("REPL child-frame T5M assets via Zig");
        assert_eq!(
            surface_assets
                .iter()
                .map(|(name, _)| *name)
                .collect::<Vec<_>>(),
            ["persistent-vector"]
        );

        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4 bootstrap");
        sens::load_time_library(&mut session).expect("time bootstrap");

        for (name, physical) in reasoning_assets.into_iter().chain(surface_assets) {
            let forms =
                execute_zig_t5m_asset(&physical, name, &mut session).unwrap_or_else(|error| {
                    panic!("{name} executes from exact T5M domain words: {error}")
                });
            assert!(forms > 0, "{name} must contain executable domain forms");
        }

        for (name, physical) in [
            (
                "persistent-map",
                include_bytes!("../../../lib/persistent-map.sens").as_slice(),
            ),
            (
                "epistemic",
                include_bytes!("../../../lib/epistemic.sens").as_slice(),
            ),
        ] {
            let forms = execute_zig_t5m_asset(physical, name, &mut session)
                .unwrap_or_else(|error| panic!("{name} root T5M bootstrap: {error}"));
            assert!(forms > 0, "{name} must contain executable domain forms");
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn named_d24_roots_lower_to_exact_numeric_words_not_text7_call_heads() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4 roots");
        for name in ["число-нуль", "число-один"] {
            let words = prepare_t5m_repl_words(name, ReplSurface::UkrainianFull, &session)
                .unwrap_or_else(|error| panic!("root={name} error={error}"));
            assert_eq!(words.len(), 1, "root must be one typed D24+ word");
            assert!(
                matches!(&words[0], ExactDomainWord::Number(number) if number.numeric_domain_width() == Some(24)),
                "root={name} must not remain as a D7/Text7 call head: {words:?}"
            );
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn nested_d24_root_reference_projects_to_an_exact_numeric_word() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4 roots");
        let source = "(визначити пробний-корінь число-нуль)";
        let words = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, &session)
            .expect("nested root reference must project through the exact D24+ route");
        assert!(
            words.iter().any(|word| matches!(
                word,
                ExactDomainWord::Number(number) if number.numeric_domain_width() == Some(24)
            )),
            "nested число-нуль must stay a typed D24+ value, not a callable D7 glyph sequence"
        );
        let program = PhysicalT5Program::from_exact_domain_words(&words)
            .expect("exact D24+ root-reference program");
        let result = program
            .execute(&mut session)
            .expect("nested root lookup through physical SENS");
        let expected_root = session
            .environment
            .get("число-нуль")
            .expect("Core4 zero root");
        let Value::BinaryNumber(expected) = &expected_root else {
            panic!("Core4 zero root must retain exact D24+ number identity");
        };
        let Value::BinaryNumber(actual) = &result.value else {
            panic!("physical definition must return an exact D24+ number");
        };
        assert_eq!(actual.numeric_domain_width(), Some(24));
        assert_eq!(
            actual.numeric_domain_width(),
            expected.numeric_domain_width()
        );
        assert_eq!(
            actual
                .exact_numeric_domain_bits()
                .expect("actual D24+ bits"),
            expected
                .exact_numeric_domain_bits()
                .expect("expected D24+ bits"),
            "physical root lookup must preserve the exact typed word"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_core4_defines_its_exact_numeric_roots() {
        let source = std::fs::read_to_string("../../lib/core4.lisp").unwrap();
        let projection_session = Session::default();
        let mut binary_session = Session::default();
        let program =
            prepare_t5m_repl_program(&source, ReplSurface::UkrainianFull, &projection_session)
                .expect("full Core4 T5M projection with decimal D24+ roots in source");
        let binary_result = program
            .execute(&mut binary_session)
            .expect("T5M Core4 defines its numeric roots from decimal source values");

        let mut source_session = Session::default();
        let source_result =
            sens::load_core_library(&mut source_session).expect("source Core4 bootstrap");
        assert_eq!(
            binary_result.value.to_string(),
            source_result.value.to_string()
        );
        for probe in ["(додати-1 число-один)", "(змінити-знак число-один)"]
        {
            let source_value = eval_program(probe, &mut source_session)
                .unwrap_or_else(|error| panic!("source Core4 probe {probe}: {error}"))
                .value;
            let binary_value = eval_program(probe, &mut binary_session)
                .unwrap_or_else(|error| panic!("T5M Core4 probe {probe}: {error}"))
                .value;
            assert_eq!(
                binary_value.to_string(),
                source_value.to_string(),
                "{probe}"
            );
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_core4_parts_load_sequentially_through_one_session() {
        let parts = [
            (
                "language",
                include_str!("../../../lib/core4-parts/core4-language.lisp"),
            ),
            ("d6", include_str!("../../../lib/core4-parts/core4-d6.lisp")),
            (
                "codec",
                include_str!("../../../lib/core4-parts/core4-codec.lisp"),
            ),
            (
                "d6b",
                include_str!("../../../lib/core4-parts/core4-d6b.lisp"),
            ),
            (
                "d8-d9",
                include_str!("../../../lib/core4-parts/core4-d8-d9.lisp"),
            ),
        ];
        let mut sources = parts
            .iter()
            .map(|(name, source)| (*name, *source))
            .collect::<Vec<_>>();
        sources.push(("probe", "(додати-1 число-один)"));
        let result = eval_t5m_source_files(&sources).expect("sequential T5M loading");
        assert_eq!(result.value.to_string(), "2");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_unoccupied_d10_definition_and_calls_keep_exact_identity() {
        let name = "відібрати-визначення-іменованої-групи";
        let source = format!(
            "(визначити {name} (функція (локальне-значення) локальне-значення))\n({name} 40)"
        );
        let mut session = Session::bare();
        assert!(session.environment.get(name).is_none());

        let program = prepare_t5m_repl_program(&source, ReplSurface::UkrainianFull, &session)
            .expect("unoccupied D10 target and calls use exact domain words");
        let result = program
            .execute(&mut session)
            .expect("exact D10 definition and call execute through Zig T5M");
        assert_eq!(result.value.to_string(), "40");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_local_definition_shadows_an_occupied_d10_identity() {
        let name = "відібрати-визначення-іменованої-групи";
        let source = format!("(визначити {name} (функція (значення) значення))\n({name} 40)");
        let mut session = Session::bare();
        sens::load_core_library(&mut session).expect("Core4 occupies the exact D10 slot");
        let identity = selected_surface_callable(ReplSurface::UkrainianFull, name)
            .unwrap()
            .expect("exact D10 projection");
        assert_eq!(identity.width(), 10);
        assert!(session.environment.has_domain_code_slot(identity));

        let program = prepare_t5m_repl_program(&source, ReplSurface::UkrainianFull, &session)
            .expect("source-local definition shadows an occupied exact D10 identity");
        let result = program
            .execute(&mut session)
            .expect("local Text7 binding shadows the existing D10 mechanism");
        assert_eq!(result.value.to_string(), "40");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_local_d9_definition_shadows_an_occupied_exact_identity() {
        let name = "результат-ціль?";
        let source = format!(
            "(визначити {name} (функція (локальне-значення) локальне-значення))\n({name} 40)"
        );
        let mut session = Session::bare();
        sens::load_core_library(&mut session).expect("Core4 occupies the exact D9 slot");
        let identity = selected_surface_callable(ReplSurface::UkrainianFull, name)
            .unwrap()
            .expect("ratified D9 result-goal identity");
        assert_eq!(identity.width(), 9);
        assert!(session.environment.has_domain_code_slot(identity));

        let program = prepare_t5m_repl_program(&source, ReplSurface::UkrainianFull, &session)
            .expect("source-local D9 definition shadows an occupied exact identity");
        let result = program
            .execute(&mut session)
            .expect("local Text7 binding must win over the outer D9 slot");
        assert_eq!(result.value.to_string(), "40");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_noncallable_d10_spelling_remains_a_text7_binding() {
        let name = "канон-порожній-список";
        let identity = selected_surface_callable(ReplSurface::UkrainianFull, name)
            .unwrap()
            .expect("the spelling has a ratified D10 projection");
        assert!(sens::semantic_registry_export::is_admitted_exact_definition_target(identity));
        let source = format!("(визначити {name} (як-є ()))");
        let mut session = Session::bare();
        let program = prepare_t5m_repl_program(&source, ReplSurface::UkrainianFull, &session)
            .expect("non-callable local value stays in its Text7 namespace");
        let result = program
            .execute(&mut session)
            .expect("D10 spelling does not force a non-callable exact target");
        assert!(matches!(result.value, Value::Nil));
    }

    #[test]
    fn repl_projects_admitted_ukr_define_targets_to_exact_domain_words() {
        let session = Session::default();
        assert!(
            selected_surface_callable(
                ReplSurface::UkrainianFull,
                "інтернет-час-режим-припустимий?"
            )
            .unwrap()
            .is_some(),
            "current Ukrainian D10 surface must resolve through the selected table and definition roster"
        );
        let words = prepare_t5m_repl_words(
            "(визначити інтернет-час-режим-припустимий? (функція (режим) режим))",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("current Ukrainian D10 definition projection");
        let target = ExactDomainWord::Identity(
            t5m_domain_identity(10, 0b1011101010).expect("current D10 resident"),
        );
        assert!(
            words.contains(&target),
            "D4 DEFINE's selected D10 target must cross T5M as its exact domain identity; words={words:?}"
        );
    }

    #[test]
    fn repl_error_message_preserves_failure_without_successful_echo() {
        for error in [
            "SENS binary evaluator: domain identity is not callable under its ratified law: D7",
            "SENS binary reader: unclosed list",
            "unknown symbol: unresolved-name",
        ] {
            let message = repl_error_message(error);
            assert_eq!(message, format!("Помилка REPL/T5M: {error}"));
            assert!(!message.starts_with("echo "));
            assert!(!message.starts_with("ВІДЛУННЯ "));
        }
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
            sens_repl_bootstrapped: false,
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
    fn t5m_source_depth_must_not_exceed_physical_reader() {
        // Загальний текстовий SENS-reader допускає AST до 768, але
        // фізичний D2 reader нині обмежений 128 вкладеннями.
        // Джерело не можна mint-ити успішно, якщо SENS відхилить байти.
        let deep_source = format!("{}(як-є ()){}", "(як-є ".repeat(129), ")".repeat(129));
        let error = mint_t5m_source_pair(&deep_source)
            .expect_err("source >128 must fail before physical mint");
        assert!(
            error.contains("T5M_SOURCE_DEPTH_NOT_ADMITTED"),
            "test_id=T5M-D2-DEPTH layer=SENS-source expected=pre-mint-fail-closed actual={error}"
        );
    }

    #[test]
    fn t5m_depth_limit_accepts_a_ratio_at_the_physical_reader_boundary() {
        let source = format!("{}1/2{}", "(".repeat(127), ")".repeat(127));
        let expressions = sens::parse_mixed_exact_domain(&source)
            .expect("text reader admits 128 nested D2 frames");
        let mut words = Vec::new();
        append_t5m_expression(&expressions[0], sens::Text7Layout::Uk, &mut words, 0)
            .expect("a lowered D24+ ratio must use the source expression's reader depth");
        PhysicalT5Program::from_exact_domain_words(&words)
            .expect("the emitted words must match the reader's accepted depth");
    }

    #[test]
    fn t5m_depth_limit_counts_the_d2_frame_added_for_a_text_name() {
        let expression = Expr {
            kind: ExprKind::Symbol("я".into()),
            span: Default::default(),
        };
        let mut words = Vec::new();
        let error = append_t5m_expression_context(
            &expression,
            sens::Text7Layout::Uk,
            &mut words,
            128,
            false,
        )
        .expect_err("the D2 text wrapper would put its D7 cell beyond reader depth 128");
        assert!(error.contains("T5M_SOURCE_DEPTH_NOT_ADMITTED"), "{error}");
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

    /// #1968: той самий цілий український Lisp-свідок має реально
    /// виконуватися з байтів Zig/T5M. D7-гліфи не підмінюють атоми D3;
    /// помилки EQ залишаються помилками SENS, а не вдаваним D1:NO.
    #[cfg(feature = "zig-transport")]
    #[test]
    fn bija3_refinement_full_ukrainian_source_executes_as_exact_zig_t5m() {
        let source = include_str!("../../../tests/semantic/біджа3-уточнення-атома-1968.lisp");
        let (physical, exact_view) =
            mint_t5m_source_pair(source).expect("test_id=1968-T5M-MINT source=SENS/Zig");
        assert!(!physical.is_empty());
        assert!(!exact_view.trim().is_empty());
        let result = eval_t5m_paired_file(source, &physical).unwrap_or_else(|error| {
            panic!("test_id=1968-T5M-EVAL layer=SENS expected=D1:1 actual_error={error}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(true),
            "test_id=1968-T5M-EVAL layer=SENS expected=D1:1 actual={}",
            result.value
        );

        // Мутант джерела за незмінених байтів — не та сама програма.
        let before = "(тотожне? (перше біджа-пара) (як-є атом?))";
        let after = "(тотожне? (перше біджа-пара) (як-є решта))";
        assert_eq!(source.matches(before).count(), 1);
        let mutant = source.replacen(before, after, 1);
        let error = eval_t5m_paired_file(&mutant, &physical)
            .expect_err("test_id=1968-T5M-MUTANT expected=physical-source-mismatch");
        assert!(
            error.contains("T5M_PHYSICAL_PAIR_MISMATCH"),
            "test_id=1968-T5M-MUTANT expected=T5M_PHYSICAL_PAIR_MISMATCH actual={error}"
        );
    }

    /// Multi-glyph D7 quote payload stays a sequence, not a secretly
    /// interned atom; EQ must not accept its derived D2 list as an atom.
    /// The one-glyph scalar case has a separate exact-W7 regression test.
    #[cfg(feature = "zig-transport")]
    #[test]
    fn bija3_eq_d7_text_does_not_gain_atomic_identity_on_physical_route() {
        let source = "(тотожне? (перше (сполучити (як-є ліве) (як-є праве))) (як-є ліве))";
        let (physical, _) = mint_t5m_source_pair(source).expect("test_id=1968-T5M-D7-MINT");
        let error = eval_t5m_paired_file(source, &physical)
            .expect_err("test_id=1968-T5M-D7-EQ expected=Type");
        assert!(
            error.contains("eq expects two atoms") && error.contains("physical_form_index=0"),
            "test_id=1968-T5M-D7-EQ expected=Type/form-0 actual={error}"
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
            ("однакові?", 0b11110111),
        ] {
            let actual = selected_surface_callable(ReplSurface::UkrainianFull, name)
                .expect("ratified Ukrainian ladder must parse")
                .expect("current D8 mechanism must remain callable");
            assert_eq!(actual.width(), 8, "{name}");
            assert_eq!(actual.packed_bits(), bits, "{name}");
        }

        // A resident without an executable mechanism stays inert; each
        // projection resolves only the exact surface declared by its table.
        assert!(
            selected_surface_callable(ReplSurface::UkrainianFull, "вектор")
                .expect("ratified non-callable D8 resident lookup")
                .is_none()
        );
        let english_string_to_symbol =
            selected_surface_callable(ReplSurface::English, "string->symbol")
                .expect("English projection lookup")
                .expect("English table declares the D8 string->symbol surface");
        assert_eq!(english_string_to_symbol.width(), 8);
        assert_eq!(english_string_to_symbol.packed_bits(), 0b11101101);

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

        // Structural EQUAL is D8:11110111, not the superficially similar D3 EQ.
        // The mixed reader may already have represented its source head as a
        // DomainIdentity, so assert the complete projection-to-T5M route.
        let equality_words =
            prepare_t5m_repl_words("(однакові? а б)", ReplSurface::UkrainianFull, &session)
                .expect("D8 structural equality retains its exact identity in T5M");
        assert!(
            equality_words.iter().any(|word| matches!(
                word,
                ExactDomainWord::Identity(DomainIdentity::D8(id))
                    if id.word().packed_bits() == 0b11110111
            )),
            "D8 EQUAL must not be lowered to D3 EQ: {equality_words:?}"
        );
    }

    #[test]
    fn ukrainian_d4_not_uses_owner_ratified_source_head_before_compatibility_lookup() {
        let not = selected_surface_callable(ReplSurface::UkrainianFull, "хибне?")
            .expect("Ukrainian source-head lookup")
            .expect("D4 NOT must be selected from the current owner table");
        assert_eq!(not.width(), 4);
        assert_eq!(not.packed_bits(), 0b0100);
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn d9_string_append_source_is_carried_by_zig_and_readable_by_sens() {
        let bytes = crate::zig_transport::d9_string_append_source_bytes()
            .expect("Zig carries D9 string-append source bytes");
        let source = String::from_utf8(bytes).expect("D9 source is UTF-8");
        let forms = sens::parse_mixed_exact_domain(&source)
            .expect("SENS reads the D9 string-append source");
        assert_eq!(forms.len(), 1, "one physical D9 operation source");
        let ExprKind::List(items) = &forms[0].kind else {
            panic!("D9 string-append source must be one call");
        };
        assert!(
            matches!(
                items.first().map(|head| &head.kind),
                Some(ExprKind::Symbol(name)) if name.as_ref() == "рядок-додати"
            ),
            "human source must preserve its Ukrainian surface before lowering"
        );
        let words =
            prepare_t5m_repl_words(&source, ReplSurface::UkrainianFull, &Session::default())
                .expect("source surface lowers through the selected domain projection");
        assert!(
            words.iter().any(|word| matches!(
                word,
                ExactDomainWord::Identity(DomainIdentity::D9(identity))
                    if identity.word().packed_bits() == 0b110011110
            )),
            "lowered source head must be exact D9:110011110 STRING-APPEND"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn d9_string_append_executes_through_native_zig_t5m_repl() {
        let source = String::from_utf8(
            crate::zig_transport::d9_string_append_source_bytes()
                .expect("Zig carries D9 string-append source bytes"),
        )
        .expect("D9 string-append source is UTF-8");
        let result = eval_t5m_source_file(&source)
            .expect("admitted D9 STRING-APPEND through SENS -> Zig T5M -> SENS");
        assert!(matches!(
            result.value,
            Value::String(ref value) if value.as_ref() == "сенсмова"
        ));
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
            (ReplSurface::UkrainianFull, "додати", 5, 0b01010),
            (ReplSurface::UkrainianFull, "відняти", 5, 0b01011),
            (ReplSurface::UkrainianFull, "помножити", 5, 0b10110),
            (ReplSurface::UkrainianFull, "частка-остача", 9, 0b110111111),
            (ReplSurface::Ukrainian, "додати", 5, 0b01010),
        ];

        for (surface, name, width, bits) in cases {
            let words = prepare_t5m_repl_words(name, surface, &session)
                .unwrap_or_else(|error| panic!("{} value {name:?}: {error}", surface.code()));
            assert_eq!(
                words,
                [ExactDomainWord::Identity(
                    t5m_domain_identity(width, bits).unwrap()
                )],
                "{} projection {name:?}",
                surface.code()
            );
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
    fn first_class_d6_code_executes_after_zig_t5m_roundtrip() {
        let mut session = Session::default();
        // Д6:001111 є значенням-функцією: його можна передавати як аргумент.
        // Zig транспортує точні біти, а закон виконання належить SENS.
        let result = eval_t5m_repl_line(
            "((функція (операція) (операція 42)) відняти-1)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("SENS evaluates passed D6:001111 after exact Zig T5M");
        let Value::BinaryNumber(ref number) = result.value else {
            panic!("first-class D6 SUB1 must return an exact D24+ number");
        };
        assert_eq!(number.to_decimal_string(), "41");

        // Негатив: та сама виклична identity мусить зберігати числовий закон.
        assert!(
            eval_t5m_repl_line(
                "((функція (операція) (операція (як-є ()))) відняти-1)",
                &mut session,
                ReplSurface::UkrainianFull,
            )
            .is_err(),
            "first-class D6 SUB1 must reject a nonnumeric operand"
        );
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
    fn scientific_notation_projects_ratio_components_to_one_numeric_domain() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line("1е-7", &mut session, ReplSurface::UkrainianFull)
            .expect("exact scientific notation must lower through D12+ and Zig/T5M");
        let Value::NumericComposition(ref composition) = result.value else {
            panic!("nonintegral decimal remains an exact rational composition");
        };
        let (negative, numerator, denominator) = composition.as_parts();
        assert!(!negative);
        assert_eq!(numerator.to_decimal_string(), "1");
        assert_eq!(
            denominator
                .expect("ratio has denominator")
                .to_decimal_string(),
            "10000000"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_exact_fraction_and_float_style_source_add_without_mixed_domains() {
        let mut session = Session::default();
        let result = eval_t5m_repl_line(
            "(додати 2.0 1е-20)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("decimal and exponential exact operands share a D12+ domain");
        let Value::NumericComposition(ref composition) = result.value else {
            panic!("nonintegral exact sum remains a rational composition");
        };
        let (negative, numerator, denominator) = composition.as_parts();
        assert!(!negative);
        assert_eq!(numerator.to_decimal_string(), "200000000000000000001");
        assert_eq!(
            denominator.expect("sum denominator").to_decimal_string(),
            "100000000000000000000"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_decimal_and_slash_fractions_are_exact_not_host_floats() {
        let mut session = Session::default();
        for (source, expected_numerator, expected_denominator) in [
            ("(додати 0,1 0,2)", "3", "10"),
            ("(додати 1546/8464 1/3)", "6551", "12696"),
        ] {
            let result = eval_t5m_repl_line(source, &mut session, ReplSurface::UkrainianFull)
                .unwrap_or_else(|error| panic!("{source}: {error}"));
            let Value::NumericComposition(ref composition) = result.value else {
                panic!("{source} must produce an exact ratio composition");
            };
            let (negative, numerator, denominator) = composition.as_parts();
            assert!(!negative, "{source}");
            assert_eq!(
                numerator.to_decimal_string(),
                expected_numerator,
                "{source}"
            );
            assert_eq!(
                denominator
                    .expect("fraction denominator")
                    .to_decimal_string(),
                expected_denominator,
                "{source}"
            );
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn ukrainian_repl_runtime_errors_use_ukrainian_messages_not_physical_byte_spans() {
        let mut session = Session::default();
        let error = eval_t5m_repl_line(
            "(додати (як-є \"текст\") 1)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect_err("adding text to a number must remain a SENS type error");
        assert!(error.contains("Помилка виконання SENS/T5M"), "{error}");
        assert!(error.contains("Помилка типу"), "{error}");
        assert!(!error.contains("line/riadok/Zeile"), "{error}");
        assert!(!error.contains("expects"), "{error}");
        assert!(!error.contains("numeric"), "{error}");
        assert!(!error.contains("requires"), "{error}");
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
            sens_repl_bootstrapped: true,
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
    fn t5m_quoted_single_glyph_is_d7_atom_but_nested_singleton_is_d2_list() {
        // A one-cell quoted symbol has a scalar D7 datum identity.
        // Parentheses remain D2 syntax, so (б) is not confused with б.
        let source = "(як-є (а (б)))";
        let forms = sens::parse_mixed_exact_domain(source)
            .expect("the Ukrainian quote and D7 glyphs parse");
        let mut actual = Vec::new();
        append_t5m_expression(&forms[0], sens::Text7Layout::Uk, &mut actual, 0)
            .expect("single-cell D7 datum is exactly representable");

        let identity =
            |width, bits| ExactDomainWord::Identity(t5m_domain_identity(width, bits).unwrap());
        let expected = vec![
            identity(2, 0b10),  // source QUOTE list
            identity(3, 0b001), // canonical quote identity
            identity(2, 0b00),
            identity(2, 0b10),      // quoted proper list
            identity(7, 0b1100110), // а: scalar W7 datum, not (а)
            identity(2, 0b00),
            identity(2, 0b10),      // nested singleton list (б)
            identity(7, 0b0101100), // б: scalar *inside* the D2 list
            identity(2, 0b01),
            identity(2, 0b01),
            identity(2, 0b01),
        ];
        assert_eq!(
            actual, expected,
            "D7 scalar identity must not erase D2 nesting"
        );

        let dotted_source = "(як-є (а . б))";
        let dotted = sens::parse_mixed_exact_domain(dotted_source)
            .expect("quoted D7 scalar dotted pair parses");
        let mut dotted_words = Vec::new();
        append_t5m_expression(&dotted[0], sens::Text7Layout::Uk, &mut dotted_words, 0)
            .expect("one-cell D7 datum remains an atomic dotted tail");
        assert_eq!(
            dotted_words,
            vec![
                identity(2, 0b10),
                identity(3, 0b001),
                identity(2, 0b00),
                identity(2, 0b10),
                identity(7, 0b1100110),
                identity(2, 0b11),
                identity(7, 0b0101100),
                identity(2, 0b01),
                identity(2, 0b01),
            ],
            "only real one-cell D7 scalars may occupy an atomic dotted tail",
        );

        #[cfg(feature = "zig-transport")]
        {
            let restored = t5m_roundtrip_words(&actual)
                .expect("Zig/T5M transports the exact D7 and D2 widths");
            assert_eq!(restored, expected);
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_quoted_singleton_list_keeps_its_outer_d2_identity() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4");

        let parsed = sens::parse_mixed_exact_domain("(як-є (а))").expect("quoted list parses");
        let words = prepare_t5m_repl_words("(як-є (а))", ReplSurface::UkrainianFull, &session)
            .expect("quoted list lowers");
        assert!(matches!(&parsed[0].kind, ExprKind::List(_)));
        let identity =
            |width, bits| ExactDomainWord::Identity(t5m_domain_identity(width, bits).unwrap());
        assert_eq!(
            words,
            vec![
                identity(2, 0b10),
                identity(3, 0b001),
                identity(2, 0b00),
                identity(2, 0b10),
                identity(7, 0b1100110),
                identity(2, 0b01),
                identity(2, 0b01),
            ],
            "T5M must retain both D2 frames around the exact D7 cell"
        );

        let scalar = eval_t5m_repl_line("(як-є а)", &mut session, ReplSurface::UkrainianFull)
            .expect("quoted D7 glyph survives T5M");
        assert!(
            matches!(&scalar.value, Value::DomainIdentity(value) if value.width() == 7),
            "single D7 datum must remain atomic, got {}",
            scalar.value
        );

        let singleton = eval_t5m_repl_line("(як-є (а))", &mut session, ReplSurface::UkrainianFull)
            .expect("quoted one-element D2 list survives T5M");
        assert!(
            matches!(singleton.value, Value::Pair(_)),
            "parenthesized singleton must remain a pair, got {}",
            singleton.value
        );
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

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_dotted_lambda_rest_name_is_recovered_only_in_binder_context() {
        let source = "((функція (а . хвостик) хвостик) 1 2)";
        let (physical, view) = mint_t5m_source_pair(source)
            .expect("lambda rest binder has an explicit reversible W7 route");
        let result = eval_t5m_paired_file(source, &physical)
            .expect("Zig-restored SENS words execute the dotted lambda");
        assert_eq!(
            result.value.to_string(),
            "(2)",
            "actual value: {:?}; words: {view}",
            result.value
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_lambda_parameter_can_share_a_noncallable_domain_projection() {
        let source = "((функція (аргументи) аргументи) 7)";
        let (physical, _) =
            mint_t5m_source_pair(source).expect("lexical parameter text must survive T5M lowering");
        let result = eval_t5m_paired_file(source, &physical)
            .expect("a lexical binder keeps its source name through exact-domain lowering");
        assert_eq!(result.value.to_string(), "7");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn t5m_quoted_nonempty_d7_survives_native_physical_execution() {
        let source = "(як-є \"sha256:abc\")";
        let (physical, _) =
            mint_t5m_source_pair(source).expect("quoted D7 source must mint exact Zig/T5M");
        let result = eval_t5m_paired_file(source, &physical)
            .expect("physical SENS must execute the same D3 quotation");
        // Фізичний D2 читач повертає структуру, D7 — точні бітові гліфи.
        // Тут не існує окремого host Text7-тега: це було старе очікування тесту.
        // Еталонні біти виведені незалежно з ASCII "sha256:abc".
        let expected = Value::list(
            [
                0b1110011_u16,
                0b1101000,
                0b1100001,
                0b0110010,
                0b0110101,
                0b0110110,
                0b0111010,
                0b1100001,
                0b1100010,
                0b1100011,
            ]
            .into_iter()
            .map(|bits| {
                Value::DomainIdentity(
                    t5m_domain_identity(7, bits).expect("literal must be an exact D7 coordinate"),
                )
            }),
        );
        assert_eq!(
            result.value, expected,
            "quoted D7 glyph order and D2 structure must survive Zig/T5M"
        );
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
    fn t5m_string_values_roundtrip_through_admitted_domain_operations() {
        for text in ["", "hi", "Привіт🙂"] {
            let value = Value::String(text.into());
            assert_eq!(
                roundtrip_repl_result(value.clone()).expect("String result uses D8/D9 operations"),
                value,
                "text={text:?}"
            );
        }

        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4");
        let program = prepare_t5m_repl_program("\"Привіт\"", ReplSurface::UkrainianFull, &session)
            .expect("D7-admitted Ukrainian text lowers into physical transport");
        let actual = program
            .execute(&mut session)
            .expect("D7-admitted text executes after Zig/T5M transport");
        assert_eq!(actual.value, Value::String("Привіт".into()));

        // Emoji may appear in Unicode REPL UI, but have NO D7 identity.
        // They must not silently become D24 Unicode scalars in a program.
        let rejected =
            prepare_t5m_repl_program("\"Привіт🙂\"", ReplSurface::UkrainianFull, &session)
                .err()
                .expect("unsupported REPL glyph must not bypass D7");
        assert!(rejected.contains("T5M_D7_TEXT_NOT_ADMITTED"), "{rejected}");
    }

    #[test]
    fn t5m_quoted_string_remains_d7_data_while_executable_string_uses_domain_calls() {
        let source =
            sens::parse_mixed_exact_domain("(як-є \"\")").expect("quoted empty string source");
        let mut actual = Vec::new();
        append_t5m_expression(&source[0], sens::Text7Layout::Uk, &mut actual, 0)
            .expect("D3 quote carries an empty D7 text sequence");
        let quote = ExactDomainWord::identity(t5m_domain_identity(3, 0b001).unwrap());
        let d2_open = ExactDomainWord::identity(t5m_domain_identity(2, 0b10).unwrap());
        let d2_close = ExactDomainWord::identity(t5m_domain_identity(2, 0b01).unwrap());
        let d2_separator = ExactDomainWord::identity(t5m_domain_identity(2, 0b00).unwrap());
        assert_eq!(
            actual,
            vec![
                d2_open.clone(),
                quote.clone(),
                d2_separator.clone(),
                d2_open.clone(),
                quote,
                d2_separator,
                d2_open,
                d2_close.clone(),
                d2_close.clone(),
                d2_close,
            ],
            "quoted empty text retains both the datum quote and its D7 string carrier"
        );

        let source =
            sens::parse_mixed_exact_domain("(як-є \"а\")").expect("quoted Ukrainian text source");
        let mut actual = Vec::new();
        append_t5m_expression(&source[0], sens::Text7Layout::Uk, &mut actual, 0)
            .expect("D3 quote carries Ukrainian D7 glyphs");
        assert!(
            matches!(actual.first(), Some(ExactDomainWord::Identity(identity))
            if identity.width() == 2 && identity.packed_bits() == 0b10)
        );
        assert!(actual.iter().any(|word| matches!(word,
            ExactDomainWord::Identity(identity) if identity.width() == 3 && identity.packed_bits() == 0b001)));
        assert!(actual.iter().any(|word| matches!(word,
            ExactDomainWord::Identity(identity) if identity.width() == 7)));

        // Протокольні ASCII-рядки цитуються як дані EN, а не
        // примусово декодуються українським D7 keyboard/v2.
        let ascii_source = sens::parse_mixed_exact_domain("(як-є \"sha256:abc\")")
            .expect("quoted ASCII string source");
        actual.clear();
        append_t5m_expression(&ascii_source[0], sens::Text7Layout::Uk, &mut actual, 0)
            .expect("ASCII quoted string has a valid EN Text7 path");
        let expected = sens::encode_text7("sha256:abc", sens::Text7Layout::En)
            .expect("ASCII protocol glyphs are ratified in EN Text7");
        let restored_cells = actual
            .iter()
            .filter_map(|word| match word {
                ExactDomainWord::Identity(identity) if identity.width() == 7 => {
                    Some(identity.packed_bits() as u8)
                }
                _ => None,
            })
            .collect::<Vec<_>>();
        assert_eq!(restored_cells.as_slice(), expected.cells());
        let quotes = actual
            .iter()
            .filter(|word| {
                matches!(
                    word,
                    ExactDomainWord::Identity(identity)
                        if identity.width() == 3 && identity.packed_bits() == 0b001
                )
            })
            .count();
        assert_eq!(
            quotes, 1,
            "цитований непорожній D7-текст має один зовнішній QUOTE, без прихованої вкладеності"
        );

        let unadmitted = sens::parse_mixed_exact_domain("(як-є \"🙂\")")
            .expect("REPL Unicode syntax can be parsed before D7 admission");
        actual.clear();
        let rejection =
            append_t5m_expression(&unadmitted[0], sens::Text7Layout::Uk, &mut actual, 0)
                .expect_err("quoted Unicode outside D7 must not enter physical words");
        assert!(
            rejection.contains("T5M_D7_TEXT_NOT_ADMITTED"),
            "{rejection}"
        );

        let executable =
            sens::parse_mixed_exact_domain("\"аб\"").expect("executable Ukrainian string source");
        actual.clear();
        append_t5m_expression(&executable[0], sens::Text7Layout::Uk, &mut actual, 0)
            .expect("executable string lowers through D8/D9 domain calls");
        assert!(actual.iter().any(|word| matches!(word,
            ExactDomainWord::Identity(identity)
                if identity.width() == 8 && identity.packed_bits() == 0)));
        assert!(actual.iter().any(|word| matches!(word,
            ExactDomainWord::Identity(identity)
                if identity.width() == 9 && identity.packed_bits() == 0b110011110)));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn utf8_library_is_invoked_through_selected_uk_d7_name_after_t5m() {
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4");
        sens::load_utf8_library(&mut session).expect("UTF-8 D7 library through Zig T5M");
        let wanted = sens::encode_text7("кодування-юнікод-8-знайти-блок", sens::Text7Layout::Uk)
            .expect("ratified D7 Ukrainian projection")
            .to_canonical_wire_token();
        assert!(
            session.environment.get(&wanted).is_some(),
            "binary UTF-8 library must bind the source D7 identity {wanted}"
        );

        let result = eval_t5m_repl_line(
            "(кодування-юнікод-8-знайти-блок 100 10 1)",
            &mut session,
            ReplSurface::UkrainianFull,
        )
        .expect("selected Ukrainian D7 name resolves the already-loaded closure");

        assert_eq!(result.value.to_string(), "(80 8)");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn tcp_d9_resident_executes_through_selected_uk_t5m_repl_path() {
        let selected = selected_surface_callable(
            ReplSurface::UkrainianFull,
            "протокол-передавання-читати-байти-текст",
        )
        .expect("the ratified D9 surface resolves");
        assert!(
            matches!(selected, Some(DomainIdentity::D9(word)) if word.word().packed_bits() == 0b001101001),
            "the full Ukrainian D9 projection must preserve exact D9 identity"
        );
        let mut session = Session::default();
        sens::load_core_library(&mut session).expect("Core4");
        sens::load_tcp_library(&mut session).expect("TCP and UTF-8 libraries through Zig T5M");
        let tcp_identity = DomainIdentity::D9(sens::CoreD9::from_word(
            sens::Bit9::new(0b001101001).expect("ratified TCP D9 word"),
        ));
        assert!(
            session.environment.has_domain_code_slot(tcp_identity),
            "loaded TCP Lisp definition must occupy its exact D9 call slot"
        );
        let reverse_identity = DomainIdentity::D5(sens::CoreD5::from_word(
            sens::Bit5::new(0b10100).expect("ratified D5 reverse identity"),
        ));
        assert!(
            session.environment.has_domain_code_slot(reverse_identity),
            "loaded Core4 Lisp reverse definition must occupy its exact D5 slot"
        );
        let code_char_program = prepare_t5m_repl_program(
            "(символ-за-кодом 104)",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("D8 code-char must lower through the selected Ukrainian T5M path");
        let code_char = code_char_program
            .execute(&mut session)
            .expect("D8 code-char must execute through the selected Ukrainian T5M path");
        assert_eq!(code_char.value.to_string(), "\"h\"");

        let string_program = prepare_t5m_repl_program(
            "(юнікод-скаляри-рядок (список 104 105))",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("scalar-to-string must lower through selected Ukrainian T5M");
        let string = string_program
            .execute(&mut session)
            .expect("scalar-to-string must execute through selected Ukrainian T5M");
        assert_eq!(string.value.to_string(), "\"hi\"");

        let empty_program = prepare_t5m_repl_program(
            "(юнікод-скаляри-рядок ())",
            ReplSurface::UkrainianFull,
            &session,
        )
        .expect("empty scalar sequence lowers through selected Ukrainian T5M");
        let empty = empty_program
            .execute(&mut session)
            .expect("empty scalar sequence executes through selected Ukrainian T5M");
        assert_eq!(empty.value, Value::String("".into()));

        let source = "(протокол-передавання-читати-байти-текст (список 104 105))";
        let words = prepare_t5m_repl_words(source, ReplSurface::UkrainianFull, &session)
            .expect("D9 call must lower before T5M transport");
        assert!(
            matches!(
                words.get(1),
                Some(ExactDomainWord::Identity(DomainIdentity::D9(word)))
                    if word.word().packed_bits() == 0b001101001
            ),
            "T5M must carry the callable D9 identity, not a D7 name: {words:?}"
        );

        let d7_text = |text: &str| {
            let projection = sens::encode_text7(text, sens::Text7Layout::En)
                .expect("protocol marker uses ratified English D7 data");
            Value::Text7(projection)
        };
        for (source, expected) in [
            (
                "(протокол-передавання-читати-байти-текст (список 104 105))",
                Value::String("hi".into()),
            ),
            (
                "(протокол-передавання-читати-байти-текст (список 208 159 209 128 208 184 208 178 209 150 209 130))",
                Value::String("Привіт".into()),
            ),
            (
                "(протокол-передавання-читати-байти-текст (список 255))",
                Value::list([d7_text("rejected"), d7_text("invalid-utf8")]),
            ),
            (
                "(протокол-передавання-читати-байти-текст (як-є ()))",
                Value::String("".into()),
            ),
        ] {
            let actual = eval_t5m_repl_line(
                source,
                &mut session,
                ReplSurface::UkrainianFull,
            )
            .unwrap_or_else(|error| panic!("T5M REPL source {source} must execute: {error}"));
            assert_eq!(actual.value, expected, "source={source}");
        }
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
        let Value::Pair(node) = &value else {
            panic!("list");
        };
        assert_eq!(&node.head, &Value::Symbol("car".into()));
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
        let dotted = Value::Pair(std::rc::Rc::new(sens::PairNode {
            head: Value::Symbol("left".into()),
            tail: Value::Symbol("right".into()),
        }));
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
    fn zig_t5m_asset_persistent_map_repl_exact_bytes() {
        let bytes = crate::zig_transport::persistent_map_t5m_bytes()
            .expect("persistent map T5M via Zig root");
        let checked_in = include_bytes!("../../../lib/persistent-map.sens");
        assert_eq!(
            bytes.as_slice(),
            checked_in,
            "ZIG_PERSISTENT_MAP_REPL T5M byte parity"
        );
        println!(
            "ZIG_PERSISTENT_MAP_REPL_PASS test_id=zig-repl-persistent-map-t5m layer=transport bytes={} semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_persistent_map_no_rust_fallback() {
        let err = surface_prerequisite_t5m_assets().expect_err("must not bypass Zig");
        assert_eq!(
            err,
            "RUST_ZIG_ONLY: REPL prerequisite T5M assets require Zig transport"
        );
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
