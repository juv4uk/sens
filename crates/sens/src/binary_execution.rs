//! Direct physical T5 execution. The byte stream already carries exact
//! domain widths; its meaning is owned by the current SENS evaluator.
//!
//! No visible-text source, host Lisp alias, invented resident, or native CPU
//! machine-code claim is constructed by this adapter.

use crate::{
    eval::{lower::lower_exact_domain_program, validate_exact_executable_heads},
    eval_lowered_expressions, BinaryNumber, BinarySourceWord, DomainIdentity, EvalResult, Expr,
    LanguageError, Session, Value,
};
use std::sync::OnceLock;

/// SENS-owned word after physical T5M restoration. Identity is explicit:
/// exact domain words are not inferred from payload width, and D12+ numbers
/// retain their numeric-domain qualification.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExactDomainWord {
    Identity(DomainIdentity),
    Number(BinaryNumber),
}

impl ExactDomainWord {
    pub fn identity(identity: DomainIdentity) -> Self {
        Self::Identity(identity)
    }

    pub fn number(number: BinaryNumber) -> Result<Self, &'static str> {
        if number.numeric_domain_width().is_none() || number.exact_numeric_domain_bits().is_none() {
            return Err("T5M number must retain an exact D12+ identity and exact-width bits");
        }
        Ok(Self::Number(number))
    }

    /// Допускає відновлене фізичне слово до чинних ідентичностей SENS.
    /// D1–D10 — точні координати драбини; числа D12+ належать до окремо
    /// ратифікованої родини ширин. Інші ширини не відображаються: сама
    /// ширина не вигадує резидента.
    pub fn from_physical_width_bits(width: usize, bits: &[u8]) -> Result<Self, String> {
        if width == 0 || bits.len() != width || bits.iter().any(|&bit| bit > 1) {
            return Err("physical SENS word must have exact positive width and 0/1 bits".into());
        }
        if (1..=10).contains(&width) {
            let payload = bits
                .iter()
                .fold(0u16, |value, &bit| (value << 1) | u16::from(bit));
            let coordinate = crate::domain_ladder::DomainCoordinate::new(width as u8, payload)
                .ok_or_else(|| "invalid exact D1–D10 coordinate".to_string())?;
            return Ok(Self::Identity(DomainIdentity::from_coordinate(coordinate)));
        }
        if BinaryNumber::is_numeric_domain_width(width) {
            let number = BinaryNumber::from_numeric_domain_bits(width, bits)
                .ok_or_else(|| "invalid exact D12+ numeric word".to_string())?;
            return Self::number(number).map_err(str::to_owned);
        }
        Err(format!(
            "no ratified SENS identity for exact word width {width}"
        ))
    }
}

/// Канонічна програма зберігає точні доменні слова, відновлені з фізичного
/// носія. AST будується по одній верхній формі під час виконання; повний AST
/// матеріалізується лише для сумісного діагностичного доступу через `forms()`.
/// Це не машинний код і не надає додаткових можливостей.
pub struct PhysicalT5Program {
    words: Vec<ExactDomainWord>,
    form_count: usize,
    forms: OnceLock<Vec<Expr>>,
}

impl PhysicalT5Program {
    /// The SAME SENS admission/evaluator for typed words restored from ANY
    /// physical carrier, including the Zig-owned T5 ABI boundary.
    /// The caller must already have validated the physical carrier; this
    /// entry performs canonical SENS D2 reading and callable admission only.
    /// No text, re-encoding, hidden Rust T5 decoding or historical dispatch.
    pub fn from_exact_words(words: &[BinarySourceWord]) -> Result<Self, LanguageError> {
        let exact = words
            .iter()
            .copied()
            .map(|word| ExactDomainWord::Identity(DomainIdentity::from_source_word(word)))
            .collect::<Vec<_>>();
        Self::from_exact_domain_words_owned(exact)
    }

    /// Build an executable SENS program from words already restored by a
    /// physical carrier such as Zig T5M. This reader accepts only explicit
    /// domain identities plus explicitly qualified D12+ numbers.
    pub fn from_exact_domain_words(words: &[ExactDomainWord]) -> Result<Self, LanguageError> {
        Self::from_exact_domain_words_owned(words.to_vec())
    }

    /// Move the exact domain-word stream into the runtime without retaining a
    /// second copy of the decoded physical input.
    pub fn from_exact_domain_words_owned(
        words: Vec<ExactDomainWord>,
    ) -> Result<Self, LanguageError> {
        let mut cursor = 0;
        let mut form_count = 0;
        while next_lowered_exact_form(&words, &mut cursor)?.is_some() {
            form_count += 1;
        }
        if form_count == 0 {
            return Err(empty_program_error());
        }
        Ok(Self {
            words,
            form_count,
            forms: OnceLock::new(),
        })
    }

    /// Number of top-level D2 forms; no assumption of a single expression.
    pub fn form_count(&self) -> usize {
        self.form_count
    }

    /// Exact SENS AST reconstructed from the supplied domain-qualified words.
    /// This is a read-only witness for hosts that need SENS-owned meta-eval;
    /// callers still use `execute` or their explicitly selected evaluator.
    pub fn forms(&self) -> &[Expr] {
        self.forms.get_or_init(|| {
            let parsed = parse_exact_domain_words(&self.words)
                .expect("validated exact binary words remain parseable");
            let forms = lower_exact_domain_program(&parsed);
            validate_exact_executable_heads(&forms)
                .expect("validated exact binary forms remain admitted");
            forms
        })
    }

    /// Execute decoded forms in an explicitly supplied interpreter session.
    ///
    /// The program does not retain a mutable runtime between calls. Bootstrap,
    /// host capabilities, and session reuse remain the caller's decision.
    pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
        let mut cursor = 0;
        let mut form_index = 0usize;
        let mut value = Value::Nil;
        loop {
            let physical_word_start = cursor;
            let Some(form) = next_lowered_exact_form(&self.words, &mut cursor)? else {
                break;
            };
            // SENS evaluates each D2-framed form itself. The evaluator's span
            // is local to that form, so a paired-T5M error cannot otherwise
            // identify which source form failed in a multi-form program.
            value = eval_lowered_expressions(std::slice::from_ref(&form), session)
                .map_err(|mut error| {
                    error.message = format!(
                        "{} [physical_form_index={} physical_word_start={} physical_word_end={}]",
                        error.message, form_index, physical_word_start, cursor
                    );
                    error
                })?
                .value;
            form_index += 1;
        }
        Ok(EvalResult {
            value,
            output: session.environment.output_snapshot(),
        })
    }

    /// Execute this physical binary AST and report actual evaluator dispatches.
    /// Available only in the explicitly enabled optimization-benchmark build.
    #[cfg(feature = "benchmark-ast-visits")]
    pub fn execute_with_visit_count(
        &self,
        session: &mut Session,
    ) -> Result<(EvalResult, u64), LanguageError> {
        let mut cursor = 0;
        let mut value = Value::Nil;
        let mut visits = 0u64;
        while let Some(form) = next_lowered_exact_form(&self.words, &mut cursor)? {
            let (result, form_visits) = crate::eval::eval_expressions_with_visit_count(
                std::slice::from_ref(&form),
                session,
            )?;
            value = result.value;
            visits = visits.saturating_add(form_visits);
        }
        Ok((
            EvalResult {
                value,
                output: session.environment.output_snapshot(),
            },
            visits,
        ))
    }
}

fn empty_program_error() -> LanguageError {
    LanguageError::new(
        crate::ErrorKind::Parse,
        "T5M SENS program has no exact words",
        crate::Span { start: 0, end: 1 },
    )
}

fn next_lowered_exact_form(
    words: &[ExactDomainWord],
    cursor: &mut usize,
) -> Result<Option<Expr>, LanguageError> {
    use crate::DomainIdentity::D2;
    const OPEN: u8 = 0b10;
    const CLOSE: u8 = 0b01;
    const SEPARATOR: u8 = 0b00;

    let is_d2 = |word: &ExactDomainWord, bits| matches!(word, ExactDomainWord::Identity(D2(value)) if value.word().packed_bits() == bits);
    while words
        .get(*cursor)
        .is_some_and(|word| is_d2(word, SEPARATOR))
    {
        *cursor += 1;
    }
    let Some(first) = words.get(*cursor) else {
        return Ok(None);
    };
    let start = *cursor;
    let end = if is_d2(first, OPEN) {
        let mut depth = 0usize;
        let mut end = words.len();
        for (index, word) in words.iter().enumerate().skip(start) {
            if is_d2(word, OPEN) {
                depth += 1;
            } else if is_d2(word, CLOSE) {
                depth = depth.saturating_sub(1);
                if depth == 0 {
                    end = index + 1;
                    break;
                }
            }
        }
        end
    } else {
        start + 1
    };
    *cursor = end;

    let parsed = parse_exact_domain_words(&words[start..end])?;
    if parsed.len() != 1 {
        return Err(empty_program_error());
    }
    let mut lowered = lower_exact_domain_program(&parsed);
    let form = lowered.pop().expect("one parsed form lowers to one form");
    validate_exact_executable_heads(std::slice::from_ref(&form))?;
    Ok(Some(form))
}

fn parse_exact_domain_words(words: &[ExactDomainWord]) -> Result<Vec<Expr>, LanguageError> {
    use crate::{DomainIdentity::D2, ErrorKind};
    const OPEN: u8 = 0b10;
    const CLOSE: u8 = 0b01;
    const SEPARATOR: u8 = 0b00;
    const DOT: u8 = 0b11;

    fn d2(word: &ExactDomainWord, bits: u8) -> bool {
        matches!(word, ExactDomainWord::Identity(D2(value)) if value.word().packed_bits() == bits)
    }
    fn error(message: &'static str, index: usize) -> LanguageError {
        LanguageError::new(
            ErrorKind::Parse,
            message,
            crate::Span {
                start: index,
                end: index + 1,
            },
        )
    }
    fn parse_expr(
        words: &[ExactDomainWord],
        cursor: &mut usize,
        depth: usize,
    ) -> Result<Expr, LanguageError> {
        let index = *cursor;
        let word = words
            .get(index)
            .ok_or_else(|| error("expected an exact SENS domain word", index))?;
        if depth > crate::MAX_EXACT_D2_READER_DEPTH {
            return Err(error("exact D2 nesting exceeds AST depth limit", index));
        }
        if d2(word, OPEN) {
            return parse_list(words, cursor, depth);
        }
        if matches!(word, ExactDomainWord::Identity(D2(_))) {
            return Err(error(
                "D2 control word is not valid in expression position",
                index,
            ));
        }
        *cursor += 1;
        let kind = match word {
            ExactDomainWord::Identity(DomainIdentity::D3(value))
                if value.word().packed_bits() == 0 =>
            {
                crate::ExprKind::List(std::rc::Rc::from(Vec::<Expr>::new().into_boxed_slice()))
            }
            ExactDomainWord::Identity(identity) => crate::ExprKind::DomainIdentity(*identity),
            ExactDomainWord::Number(number) => crate::ExprKind::BinaryNumber(number.clone()),
        };
        Ok(Expr {
            kind,
            span: crate::Span {
                start: index,
                end: *cursor,
            },
        })
    }
    fn parse_list(
        words: &[ExactDomainWord],
        cursor: &mut usize,
        depth: usize,
    ) -> Result<Expr, LanguageError> {
        let start = *cursor;
        *cursor += 1;
        let mut items = Vec::new();
        loop {
            while words.get(*cursor).is_some_and(|word| d2(word, SEPARATOR)) {
                *cursor += 1;
            }
            let Some(word) = words.get(*cursor) else {
                return Err(error("unterminated exact D2 structure", start));
            };
            if d2(word, CLOSE) {
                *cursor += 1;
                return Ok(Expr {
                    kind: crate::ExprKind::List(std::rc::Rc::from(items.into_boxed_slice())),
                    span: crate::Span {
                        start,
                        end: *cursor,
                    },
                });
            }
            if d2(word, DOT) {
                if items.is_empty() {
                    return Err(error("D2 dot requires a pair head", *cursor));
                }
                *cursor += 1;
                while words.get(*cursor).is_some_and(|word| d2(word, SEPARATOR)) {
                    *cursor += 1;
                }
                let tail = parse_expr(words, cursor, depth + 1)?;
                while words.get(*cursor).is_some_and(|word| d2(word, SEPARATOR)) {
                    *cursor += 1;
                }
                if !words.get(*cursor).is_some_and(|word| d2(word, CLOSE)) {
                    return Err(error(
                        "dotted D2 structure requires one tail and a close word",
                        *cursor,
                    ));
                }
                *cursor += 1;
                let mut result = tail;
                for head in items.into_iter().rev() {
                    result = Expr {
                        kind: crate::ExprKind::Pair(
                            std::rc::Rc::new(head),
                            std::rc::Rc::new(result),
                        ),
                        span: crate::Span {
                            start,
                            end: *cursor,
                        },
                    };
                }
                return Ok(result);
            }
            items.push(parse_expr(words, cursor, depth + 1)?);
        }
    }

    if words.is_empty() {
        return Err(error("T5M SENS program has no exact words", 0));
    }
    let mut cursor = 0;
    let mut forms = Vec::new();
    while cursor < words.len() {
        while words.get(cursor).is_some_and(|word| d2(word, SEPARATOR)) {
            cursor += 1;
        }
        if cursor < words.len() {
            forms.push(parse_expr(words, &mut cursor, 0)?);
        }
    }
    Ok(forms)
}

/// E1 is a physical carrier, not another semantic evaluator.
#[derive(Debug)]
pub enum E1ExecutionError {
    Transport(crate::universal_frame3::Frame3Error),
    Language(LanguageError),
}

/// E1 bytes -> canonical exact-width words -> SAME SENS D2/admission/evaluator.
/// This never adds a language identity, environment capability or T5 roundtrip.
pub fn eval_e1_program(
    physical_e1: &[u8],
    session: &mut Session,
) -> Result<EvalResult, E1ExecutionError> {
    let words = crate::envelope_e1::decode(physical_e1).map_err(E1ExecutionError::Transport)?;
    let program =
        PhysicalT5Program::from_exact_words(&words).map_err(E1ExecutionError::Language)?;
    program.execute(session).map_err(E1ExecutionError::Language)
}
