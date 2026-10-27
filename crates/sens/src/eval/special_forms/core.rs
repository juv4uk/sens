//! The McCarthy primitives (`eq`, `car`, `cdr`, `cons`, `cond`, `quote`'s
//! helper), plus the compatibility `def` surface. Language-owned `defmacro`
//! is bootstrapped from `lib/macro.lisp`; the Rust kernel no longer implements it.

use crate::eval::canon;
use crate::eval::{evaluate, evaluate_step, EvalStep};
use crate::{
    Bit4, CoreD4, CoreDomainIdentity, Environment, ErrorKind, Expr, ExprKind, LanguageError,
    PairNode, Span, Value,
};

use std::rc::Rc;

/// Mechanism-only ATOM result: D1 predicate, never a host Bool, list-scale,
/// Core profile, or historical T/NIL carrier.
/// The domain-word contracts own the meaning of the returned bit.
pub(crate) fn atom_value(value: &Value, _environment: &Environment) -> Value {
    Value::predicate_bit(!matches!(value, Value::Pair(_)))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ExactD3CondControl {
    Select,
    SkipNo,
}

/// Canonical D3:110 control projection.
///
/// Контракт 11.8 (#3161 CURRENT FOUNDATION SUPERSESSION, 2026-10-08):
/// лише точні відповіді D1 керують COND. D1:1 вибирає, D1:0 пропускає.
/// D3:000 є структурним результатом вичерпання, НЕ допустимою умовою.
/// Будь-яке інше значення має спричинити адресну помилку типу.
fn exact_d3_cond_control(value: &Value, span: Span) -> Result<ExactD3CondControl, LanguageError> {
    match value.as_predicate_bit() {
        Some(true) => Ok(ExactD3CondControl::Select),
        Some(false) => Ok(ExactD3CondControl::SkipNo),
        None => Err(LanguageError::new(
            ErrorKind::Type,
            format!("D3:110 COND expects exact D1:1 / D1:0; got {value}"),
            span,
        )),
    }
}

/// Exact-domain D3:110 COND.
///
/// This path is deliberately separate from historical CoreDomainIdentity/profile COND.
/// It is two-part only and never consults host/Lisp truthiness.
pub(crate) fn evaluate_domain_cond(
    clauses: &[Expr],
    environment: &Environment,
    _span: Span,
) -> Result<EvalStep, LanguageError> {
    for clause in clauses {
        let ExprKind::List(parts) = &clause.kind else {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "D3:110 COND expects list clauses",
                clause.span,
            ));
        };
        // Contract 11.8: canonical D3 COND has exactly two fields.
        // Reject old explicit-result clauses *before* evaluating their query:
        // evaluating a malformed clause would produce observable side effects.
        if parts.len() != 2 {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "D3:110 COND requires exactly (test expression); three-part compatibility is forbidden",
                clause.span,
            ));
        }
        let value = evaluate(&parts[0], environment)?;
        match exact_d3_cond_control(&value, parts[0].span)? {
            ExactD3CondControl::Select => return evaluate_step(&parts[1], environment),
            ExactD3CondControl::SkipNo => {}
        }
    }

    Ok(EvalStep::Value(Value::Nil))
}

pub(crate) fn evaluate_definition(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // DEFINE — точна D4:0011, а не історична W8:00001011.
    let identity = CoreDomainIdentity::D4(CoreD4::from_word(
        Bit4::new(0b0011).expect("ратифікована координата D4 DEFINE"),
    ));
    exact_domain_arity(identity, arguments, 2, span)?;

    // A D2-framed W7 sequence is a Text7 identifier only in this explicit
    // DEFINE target role. The canonical reader remains structural and makes
    // no global W7→Text7 inference.
    if let Some(name) = crate::canonical_reader::text7_binding_key(&arguments[0]) {
        canon::ensure_bindable(&name, arguments[0].span)?;
        let value = evaluate(&arguments[1], environment)?;
        // The wire token is the stable identifier carried by the binary
        // source. Resolve its selected Ukrainian projection only to find the
        // ratified domain-table row; the row's exact bits, not its spelling,
        // populate the callable slot.
        let surface = crate::Text7::from_canonical_wire_token(&name)
            .ok()
            .and_then(|text| crate::render_text7(&text, crate::Text7Layout::Uk).ok());
        canon::bind_language_definition(
            surface.as_deref().unwrap_or(name.as_ref()),
            &value,
            environment,
        );
        environment.define(name.clone(), value.clone());
        // A physical Core4 DEFINE target arrives as a canonical D7 word token,
        // but the definition must also be resolvable by its ratified Ukrainian
        // source spelling: the D7-frame call reader and direct environment
        // readers (named D24+ roots) key on that spelling, not the wire token.
        // Mirror bind_core_runtime_mechanisms: project only the already
        // evaluated callable, never a bare resident.
        if let Some(surface) = surface {
            if surface.as_str() != name.as_ref()
                && environment.get(&surface).is_none()
                && canon::ensure_bindable(&surface, arguments[0].span).is_ok()
            {
                environment.define(surface, value.clone());
            }
        }
        return Ok(value);
    }

    match &arguments[0].kind {
        ExprKind::Symbol(name) => {
            canon::ensure_bindable(name, arguments[0].span)?;
            let value = evaluate(&arguments[1], environment)?;
            // The shared lexical frame makes recursive definitions visible to their closure after binding.
            // Spilnyi leksychnyi freim robyt rekursyvne vyznachennia vydymym zamykanniu pislia zv’yazuvannia.
            // Der gemeinsame lexikalische Frame macht rekursive Definitionen nach der Bindung für ihre Closure sichtbar.
            canon::bind_language_definition(name, &value, environment);
            environment.define(name.clone(), value.clone());
            Ok(value)
        }
        ExprKind::DomainIdentity(identity) => {
            let Some(target) = identity
                .core_operation()
                .map(crate::DomainIdentity::from)
                .or_else(|| {
                    crate::semantic_registry::is_admitted_exact_definition_target(*identity)
                        .then_some(*identity)
                })
            else {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "exact DEFINE target must have an admitted domain identity",
                    arguments[0].span,
                ));
            };

            if !environment.is_root() {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "exact DEFINE target may install a language-owned mechanism only at the root frame",
                    arguments[0].span,
                ));
            }

            if environment.domain_code_slot(target).is_some() {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("exact DEFINE target already has a language-owned binding: {target}"),
                    arguments[0].span,
                ));
            }

            let value = evaluate(&arguments[1], environment)?;
            // Ратифікована точна голова може мати Lisp-визначений макрос:
            // це виконуваний мовний механізм, не довільне значення даних.
            // Той самий перелік допускає canon::bind_language_definition.
            if !matches!(value, Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)) {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "exact DEFINE target requires a callable closure, macro or builtin mechanism",
                    arguments[1].span,
                ));
            }

            if !environment.bind_domain_code_slot_once(target, value.clone()) {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("exact DEFINE target was concurrently bound: {target}"),
                    arguments[0].span,
                ));
            }

            // The physical Core4 carrier encodes a ratified D9/D10 DEFINE
            // target as its exact domain coordinate, so the reader binds no
            // text name for it. Also bind the ratified Ukrainian source
            // spelling of this concrete definition, so callers resolve it as a
            // source head instead of failing with `unknown symbol`. Residency
            // alone still grants nothing: the slot was bound only above, and a
            // missing coordinate never reaches this arm.
            if let Some(surface) =
                crate::semantic_registry::surface_for_domain_identity(target, "ukr")
            {
                if environment.get(surface).is_none()
                    && canon::ensure_bindable(surface, arguments[0].span).is_ok()
                {
                    environment.define(surface, value.clone());
                }
            }

            Ok(value)
        }
        _ => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "def expects a symbol name or exact callable DomainIdentity · def ochikuie nazvu-symvol abo tochnyi vyklychnyi DomainIdentity · def erwartet einen Symbolnamen oder eine exakte aufrufbare DomainIdentity",
            arguments[0].span,
        )),
    }
}

pub fn exact_arity(
    operator: &str,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{operator}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            arguments.len()
        ),
        span,
    ))
}

/// Перевірка арності лише за точною доменною координатою.
///
/// Вона не конструює SID8, не відкидає біти і не дозволяє однаковому
/// числовому payload у D3/D4/D5 бути однією функцією.
pub(crate) fn exact_domain_arity(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "D{}:{identity}: очікувано {expected} аргументів; отримано {}",
            identity.width(),
            arguments.len()
        ),
        span,
    ))
}

pub(crate) fn quoted(expression: &Expr) -> Result<Value, LanguageError> {
    quoted_with_macro_syntax(expression, false)
}

/// Цитування аргументів макроса. Те саме, що `quoted`, але чиста D2/W7-рамка
/// імені відновлюється до канонічного атома `Value::Text7` — точного значення,
/// яке звичайний читач дає для голих джерельних імен. Канонічний читач лишається
/// структурним (див. `quote_keeps_a_d2_framed_w7_run_as_a_structural_list`), а
/// `macro_expansion_to_expr` повертає `Text7` у ту саму W7-рамку, тож макрос, що
/// повертає аргумент без змін, відтворює побайтово ідентичний синтаксис.
/// Тлумачення імені отримують лише аргументи макроса — ніколи QUOTE чи дані.
/// Без цього `атом?` бачив би рамку імені як пару, і макрос `нехай` хибно
/// потрапляв у свою гілку-помилку `(перше (як-є ()))`.
///
/// Macro-argument quoting: a pure D2/W7 name frame becomes the canonical
/// `Value::Text7` atom, matching a bare source name. QUOTE and data are
/// unchanged; `macro_expansion_to_expr` restores the identical frame.
pub(crate) fn quoted_macro_argument(expression: &Expr) -> Result<Value, LanguageError> {
    quoted_with_macro_syntax(expression, true)
}

fn quoted_with_macro_syntax(expression: &Expr, macro_syntax: bool) -> Result<Value, LanguageError> {
    fn go(expression: &Expr, depth: u32, macro_syntax: bool) -> Result<Value, LanguageError> {
        if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "quoted structure exceeds reader limit · struktura perevyshchuie mezhu chytacha · zitierte Struktur überschreitet das Reader-Limit",
                Span { start: 0, end: 0 },
            ));
        }
        Ok(match &expression.kind {
            ExprKind::Number(number, exactness) => Value::Number(*number, *exactness),
            ExprKind::Rational(rational) => Value::Rational(rational.clone()),
            ExprKind::BinaryNumber(number) => Value::BinaryNumber(number.clone()),
            ExprKind::Sid(sid) => Value::Sid(*sid),
            // D3:000 is the language's canonical empty list, not a callable/data
            // identity when quoted. Preserve every other domain identity at data
            // position so exact-width residents do not collapse into names/numbers.
            ExprKind::DomainIdentity(identity) => match identity {
                crate::DomainIdentity::D3(word) if word.word().packed_bits() == 0 => Value::Nil,
                _ => Value::DomainIdentity(*identity),
            },
            ExprKind::NumericBuffer(buffer) => Value::NumericBuffer(buffer.clone()),
            ExprKind::String(value) => Value::String(value.clone()),
            // Канонічний носій D7 має відновлювати точні W7-комірки під час
            // READ(WRITE(...)), зокрема всередині вкладених списків.
            // Пошкоджений #t7-запис не перетворюється мовчки на Symbol.
            ExprKind::Symbol(symbol) if symbol.starts_with(crate::Text7::WIRE_TAG) => {
                let text = crate::Text7::from_canonical_wire_token(symbol).map_err(|error| {
                    LanguageError::new(
                        ErrorKind::Parse,
                        format!("неканонічний носій D7: {error:?}"),
                        expression.span,
                    )
                })?;
                Value::Text7(text)
            }
            ExprKind::Symbol(symbol) => Value::Symbol(symbol.clone()),
            // Слот — координата виконання, не дані: у quote-позиції його не буває
            // (розв'язувач її не чіпає), тож така поява — порушення інваріанта.
            ExprKind::Local { .. } => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "a lexical slot has no source datum · leksychnyi slot ne maie danykh dzherela · ein lexikalischer Slot hat kein Quelldatum",
                    expression.span,
                ));
            }
            ExprKind::List(items) => {
                // У позиції аргументу макроса чиста D2/W7-рамка є іменем, а не
                // структурою даних: повертаємо канонічний D7-атом. Звичайне
                // цитування лишає рамку структурним списком.
                if macro_syntax {
                    if let Some(text) = crate::canonical_reader::text7_atom(expression) {
                        return Ok(Value::Text7(text));
                    }
                }
                let mut out = Vec::with_capacity(items.len());
                for item in items.iter() {
                    out.push(go(item, depth + 1, macro_syntax)?);
                }
                Value::list(out)
            }
            ExprKind::Pair(head, tail) => Value::Pair(Rc::new(PairNode {
                head: go(head, depth + 1, macro_syntax)?,
                tail: go(tail, depth + 1, macro_syntax)?,
            })),
            // Зведений виклик як дані — список із функцією СЕНС у голові.
            ExprKind::Call(sid, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::Sid(*sid));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1, macro_syntax)?);
                }
                Value::list(out)
            }
            ExprKind::DomainCall(identity, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::DomainIdentity((*identity).into()));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1, macro_syntax)?);
                }
                Value::list(out)
            }
        })
    }
    go(expression, 0, macro_syntax)
}

// ── contract 2.1: value-level entry points (first-class builtins) ──
// Same compute as the expr-handlers above; arguments arrive
// pre-evaluated. The expr-handlers delegate here after evaluating.

// Один механізм вибірки для D3 і складених селекторів: семантична
// помилка на непридатному вході визначається тут, без дублювання в D10.
pub(crate) fn car_ref(value: &Value, span: Span) -> Result<&Value, LanguageError> {
    match value {
        Value::Pair(node) => Ok(&node.head),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "car expects a non-empty list · car ochikuie neporozhnii spysok · car erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cdr_ref(value: &Value, span: Span) -> Result<&Value, LanguageError> {
    match value {
        Value::Pair(node) => Ok(&node.tail),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "cdr expects a non-empty list · cdr ochikuie neporozhnii spysok · cdr erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cons_values(
    head: Value,
    tail: Value,
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if environment.try_alloc_cons().is_err() {
        return Err(LanguageError::new(
            ErrorKind::OutOfMemory,
            "cons: resource limit reached · cons: dosiahnuto mezhi resursu · cons: Ressourcengrenze erreicht",
            span,
        ));
    }
    // Єдина точка алокації cons. За увімкненого перемикача арени комірка
    // народжується в арені, а значення читається назад крізь арену; інакше —
    // незмінне подання `Value::Pair(Rc<PairNode>)`.
    if environment.arena_cons_enabled() {
        return Ok(environment.arena_cons(head, tail));
    }
    Ok(Value::Pair(std::rc::Rc::new(PairNode { head, tail })))
}

/// Контракт 11.8: EQ — атомна операція; пара або значення поза
/// доменом спричиняє іменовану помилку Type, не D1:NO чи D3:000.
/// Актуальна ратифікація 2026-10-08 supersedes старе #3161 формулювання.
thread_local! {
    /// Останній доменний виклик у потоці. Друкується лише за SENS_EQ_TRACE:
    /// без нього адресу виклику eq не видно, бо SENS інтерпретується
    /// і стек містить тільки Rust-кадри.
    static LAST_DOMAIN: std::cell::RefCell<String> =
        const { std::cell::RefCell::new(String::new()) };
}

/// Записати поточний доменний виклик для діагностики eq.
pub(crate) fn note_domain_call(identity: &crate::DomainIdentity) {
    if std::env::var_os("SENS_EQ_TRACE").is_some() {
        LAST_DOMAIN.with(|cell| *cell.borrow_mut() = format!("{identity}"));
    }
}

pub(crate) fn eq_values(left: Value, right: Value, span: Span) -> Result<Value, LanguageError> {
    if !left.is_atom() || !right.is_atom() {
        // Діагностика називає БІК і вид носія. Без цього повідомлення
        // «eq expects two atoms» не відрізняє `(eq пара x)` від `(eq x пара)`,
        // і пошук причини йде навмання по всьому lib/.
        // Значення не рендеримо: воно може бути величезним списком.
        let side = match (left.is_atom(), right.is_atom()) {
            (false, true) => "left",
            (true, false) => "right",
            _ => "both",
        };
        let carrier = if matches!(left, Value::Pair(_)) || matches!(right, Value::Pair(_)) {
            "pair"
        } else {
            "non-atom"
        };
        // Діагностика типів БЕЗ рендеру значень (вони можуть бути величезними):
        // лише тег виду. Саме цього бракувало, щоб знайти виклик наосліп.
        fn kind_tag(v: &Value) -> &'static str {
            match v {
                Value::Pair(_) => "pair",
                Value::Symbol(_) => "symbol",
                Value::BinaryNumber(_) => "number",
                Value::Builtin(_) => "builtin",
                Value::Closure(_) => "closure",
                Value::Macro(_) => "macro",
                _ => "other",
            }
        }
        let (lk, rk) = (kind_tag(&left), kind_tag(&right));
        // SENS_EQ_TRACE: друкує доменну ідентичність виклику і стек. Без цього
        // адресу виклику eq не видно: SENS інтерпретується, і стек містить
        // лише Rust-кадри. У звичайному режимі повідомлення лишається коротким.
        let trace = if std::env::var_os("SENS_EQ_TRACE").is_some() {
            let identity = LAST_DOMAIN.with(|cell| cell.borrow().clone());
            format!(
                " · domain {identity}\n{}",
                std::backtrace::Backtrace::force_capture()
            )
        } else {
            String::new()
        };
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!(
                "eq expects two atoms · eq ochikuie dva atomy · eq erwartet zwei Atome · \
                 non-atomic {side} · carrier {carrier} · kinds {lk}/{rk}{trace}"
            ),
            span,
        ));
    }
    Ok(Value::predicate_bit(left == right))
}

#[cfg(test)]
mod exact_d4_define_arity_tests {
    use super::*;

    fn expression() -> Expr {
        Expr {
            kind: ExprKind::Symbol(Rc::from("ім'я")),
            span: Span::default(),
        }
    }

    #[test]
    fn quote_of_canonical_d3_empty_coordinate_is_structural_nil() {
        let empty = Expr {
            kind: ExprKind::DomainIdentity(crate::DomainIdentity::D3(crate::Bija3::from_word(
                crate::Bit3::new(0).unwrap(),
            ))),
            span: Span::default(),
        };
        assert!(matches!(quoted(&empty).unwrap(), Value::Nil));
    }

    #[test]
    fn quote_preserves_nonempty_d3_domain_identity() {
        let quote = crate::Bija3::from_word(crate::Bit3::new(0b001).unwrap());
        let expression = Expr {
            kind: ExprKind::DomainIdentity(crate::DomainIdentity::D3(quote)),
            span: Span::default(),
        };
        assert!(matches!(
            quoted(&expression).unwrap(),
            Value::DomainIdentity(crate::DomainIdentity::D3(value)) if value == quote
        ));
    }

    #[test]
    fn quote_keeps_a_d2_framed_w7_run_as_a_structural_list() {
        let expression = crate::parse_canonical_binary("10 1100001 00 1110100 01")
            .expect("canonical D2/W7 quote datum parses")
            .remove(0);
        let value = quoted(&expression).expect("quoted D2/W7 structure");
        assert_eq!(
            value,
            Value::list([
                Value::DomainIdentity(crate::DomainIdentity::from_source_word(
                    crate::BinarySourceWord::W7(crate::Bit7::new(0b1100001).unwrap()),
                )),
                Value::DomainIdentity(crate::DomainIdentity::from_source_word(
                    crate::BinarySourceWord::W7(crate::Bit7::new(0b1110100).unwrap()),
                )),
            ]),
            "D2 framing remains structure; W7 cells retain exact domain identity"
        );
    }

    #[test]
    fn цитоване_канонічне_d7_слово_зберігає_комірки_і_вкладеність() {
        let mut expressions = crate::parse("(#t7:6174 (#t7:))")
            .expect("канонічний D7-носій повинен читатися як джерело");
        let actual = quoted(&expressions.remove(0)).expect("точне цитування D7");
        let expected = Value::list([
            Value::Text7(crate::Text7::from_cells(vec![0x61, 0x74]).unwrap()),
            Value::list([Value::Text7(crate::Text7::from_cells(Vec::new()).unwrap())]),
        ]);
        assert_eq!(actual, expected);
    }

    #[test]
    fn пошкоджений_канонічний_d7_носій_не_стає_символом() {
        for source in ["#t7:0", "#t7:80", "#t7:4A", "#t7:gg"] {
            let mut expressions = crate::parse(source).expect("лексичний носій");
            let error = quoted(&expressions.remove(0))
                .expect_err("пошкоджений D7 повинен мати іменовану помилку");
            assert_eq!(error.kind, ErrorKind::Parse, "{source}");
        }
    }

    #[test]
    fn визначення_діагностує_тільки_точну_d4_координату() {
        let environment = Environment::root();
        for count in [0usize, 1, 3] {
            let arguments = vec![expression(); count];
            let error = evaluate_definition(&arguments, &environment, Span::default())
                .expect_err("хибна арність має бути відхилена раніше за виконання");
            assert_eq!(error.kind, ErrorKind::Arity);
            assert!(error.message.contains("D4:0011"), "{error:?}");
            assert!(!error.message.contains("00001011"), "{error:?}");
        }
    }

    #[test]
    fn правильна_арність_і_неоднакові_ширини_доменів() {
        let d4 = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0011).unwrap()));
        let two = vec![expression(), expression()];
        assert!(exact_domain_arity(d4, &two, 2, Span::default()).is_ok());
        let wrong =
            CoreDomainIdentity::D3(crate::Bija3::from_word(crate::Bit3::new(0b011).unwrap()));
        let error = exact_domain_arity(wrong, &[], 1, Span::default()).unwrap_err();
        assert!(error.message.contains("D3:011"), "{error:?}");
        assert!(!error.message.contains("D4:0011"), "{error:?}");
    }
}
