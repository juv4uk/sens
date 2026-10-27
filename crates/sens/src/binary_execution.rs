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

#[cfg(test)]
mod exact_t5m_cutover_tests {
    use super::*;
    use crate::{parse_binary_source_words, ExprKind};
    #[cfg(feature = "rust-t5-reference")]
    use crate::{decode_ternary_words, encode_ternary_words};

    #[cfg(feature = "rust-t5-reference")]
    fn reference_t5_program(physical: &[u8]) -> Result<PhysicalT5Program, String> {
        let words = crate::decode_ternary_words(physical).map_err(|error| format!("{error:?}"))?;
        PhysicalT5Program::from_exact_words(&words).map_err(|error| format!("{error:?}"))
    }

    #[test]
    fn physical_admission_covers_every_ratified_domain_family_only() {
        for width in 1..=10 {
            let mut bits = vec![0; width];
            bits[width - 1] = 1;
            let admitted = ExactDomainWord::from_physical_width_bits(width, &bits)
                .unwrap_or_else(|error| panic!("ratified D{width} must be admitted: {error}"));
            assert!(
                matches!(admitted, ExactDomainWord::Identity(identity) if identity.width() == width)
            );
        }

        // Чинна числова родина — D(12 * 2^n), починаючи з D12.
        // Зберігаємо точну ширину й біти, не обмежуючи її D192.
        for width in [12, 24, 48, 96, 192, 384, 768] {
            let mut bits = vec![0; width];
            bits[0] = 1;
            let admitted =
                ExactDomainWord::from_physical_width_bits(width, &bits).unwrap_or_else(|error| {
                    panic!("ratified numeric D{width} must be admitted: {error}")
                });
            assert!(matches!(admitted, ExactDomainWord::Number(number)
                if number.numeric_domain_width() == Some(width)
                    && number.exact_numeric_domain_bits().as_deref() == Some(bits.as_slice())));
        }

        // Це межа поточного фізичного adapter, не акт ратифікації доменів.
        // Числова ширина має належати D(12 * 2^n), а не довільній кратності.
        for width in (11..=23)
            .filter(|width| *width != 12)
            .chain([25, 36, 72, 120])
        {
            assert!(
                ExactDomainWord::from_physical_width_bits(width, &[0; width]).is_err(),
                "D{width} поза поточними підтриманими родинами фізичного adapter"
            );
        }
    }

    // Д2 має один закон вкладеності у текстовому та відновленому
    // з Zig/T5M exact-domain readers. Жодного другого parser-ліміту.
    #[test]
    fn д2_фізичний_і_канонічний_читачі_збігаються_для_всіх_чотирьох_маркерів() {
        fn physical_read(source: &str) -> Result<Vec<Expr>, LanguageError> {
            let words = parse_binary_source_words(source)
                .expect("valid exact-width words")
                .into_iter()
                .map(|token| {
                    ExactDomainWord::identity(DomainIdentity::from_source_word(token.word))
                })
                .collect::<Vec<_>>();
            parse_exact_domain_words(&words)
        }

        fn shape(expr: &Expr) -> String {
            match &expr.kind {
                ExprKind::List(items) => format!(
                    "({})",
                    items.iter().map(shape).collect::<Vec<_>>().join(" ")
                ),
                ExprKind::Pair(head, tail) => format!("({} . {})", shape(head), shape(tail)),
                ExprKind::DomainIdentity(word) => {
                    format!("D{}:{}", word.width(), word.packed_bits())
                }
                other => format!("{other:?}"),
            }
        }

        for source in [
            "10 01",
            "10 001 00 100 01",
            "10 100 11 111 01",
            "10 100 00 111 11 000 01",
            "10 10 100 11 111 01 00 000 01",
            "00 10 100 00 111 01 00",
        ] {
            let canonical = crate::parse_canonical_binary(source).expect("exact D2 canonical read");
            let physical =
                physical_read(source).expect("same exact D2 structure after T5M restoration");
            assert_eq!(physical.len(), canonical.len(), "{source}");
            for (left, right) in physical.iter().zip(canonical.iter()) {
                assert_eq!(shape(left), shape(right), "D2 AST mismatch: {source}");
            }
        }
        for source in [
            "01",
            "11",
            "10 11 100 01",
            "10 100 11 01",
            "10 100 11 111 00 000 01",
            "10 100 00 01 01",
            "10 100",
            "10 100 11 111",
        ] {
            assert!(
                crate::parse_canonical_binary(source).is_err(),
                "canonical reader cannot admit malformed D2: {source}"
            );
            assert!(
                physical_read(source).is_err(),
                "Zig-restored reader cannot admit malformed D2: {source}"
            );
        }

        for depth in [1usize, 16, 64, 128, 130] {
            let source = format!("{}001{}", "10 ".repeat(depth), " 01".repeat(depth));
            let canonical = crate::parse_canonical_binary(&source);
            let physical = physical_read(&source);
            assert_eq!(
                canonical.is_ok(),
                physical.is_ok(),
                "D2 nesting policy diverged at depth={depth}"
            );
            assert_eq!(physical.is_ok(), depth <= 128);
        }
    }

    #[test]
    fn zig_restored_exact_t5m_d24_words_execute_as_binary_sens() {
        let identity = |width, bits| {
            ExactDomainWord::identity(DomainIdentity::from_coordinate(
                crate::domain_ladder::DomainCoordinate::new(width, bits).unwrap(),
            ))
        };
        let number = |value| {
            let mut bits = vec![0; 24];
            bits[23] = 1;
            if value == 2 {
                bits[22] = 1;
                bits[23] = 0;
            }
            ExactDomainWord::number(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
                .unwrap()
        };
        let program = PhysicalT5Program::from_exact_domain_words(&[
            identity(2, 0b10),
            identity(5, 0b01010),
            number(1),
            number(2),
            identity(2, 0b01),
        ])
        .expect("D2 structure + admitted D5 head + exact D24 leaves");

        let result = program
            .execute(&mut Session::default())
            .expect("the binary SENS evaluator executes the restored words");
        let crate::Value::BinaryNumber(number) = &result.value else {
            panic!("D5 addition of two D24 values returns an exact D24 number");
        };
        assert_eq!(number.numeric_domain_width(), Some(24));
        assert_eq!(number.bits(), "11");
    }

    #[test]
    fn binary_runtime_executes_exact_domain_words_without_caching_a_full_ast() {
        let identity = |width, bits| {
            ExactDomainWord::identity(DomainIdentity::from_coordinate(
                crate::domain_ladder::DomainCoordinate::new(width, bits).unwrap(),
            ))
        };
        let number = |width: usize, value: u8| {
            let mut bits = vec![0; width];
            for offset in 0..u8::BITS as usize {
                let bit = (value >> offset) & 1;
                if bit != 0 {
                    bits[width - 1 - offset] = bit;
                }
            }
            ExactDomainWord::number(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
                .unwrap()
        };
        let words = vec![
            identity(2, 0b10),
            identity(5, 0b01010),
            number(24, 1),
            number(24, 2),
            identity(2, 0b01),
            identity(2, 0b00),
            identity(2, 0b10),
            identity(5, 0b01010),
            number(48, 1),
            number(48, 2),
            identity(2, 0b01),
        ];
        let program = PhysicalT5Program::from_exact_domain_words_owned(words)
            .expect("exact binary D2/D5/D24+ program is admitted");

        assert!(
            program.forms.get().is_none(),
            "reader must retain words, not a whole AST"
        );
        assert_eq!(program.form_count(), 2);
        let result = program
            .execute(&mut Session::default())
            .expect("SENS executes the exact domain words");

        assert_eq!(result.value.to_string(), "3");
        assert!(
            program.forms.get().is_none(),
            "execution must not retain the materialized whole-program AST"
        );
    }

    #[cfg(feature = "benchmark-ast-visits")]
    #[test]
    fn binary_program_reports_actual_evaluator_dispatches() {
        let identity = |width, bits| {
            ExactDomainWord::identity(DomainIdentity::from_coordinate(
                crate::domain_ladder::DomainCoordinate::new(width, bits).unwrap(),
            ))
        };
        let number = |value| {
            let mut bits = vec![0; 24];
            bits[23] = 1;
            if value == 2 {
                bits[22] = 1;
                bits[23] = 0;
            }
            ExactDomainWord::number(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
                .unwrap()
        };
        let program = PhysicalT5Program::from_exact_domain_words(&[
            identity(2, 0b10),
            identity(5, 0b01010),
            number(1),
            number(2),
            identity(2, 0b01),
        ])
        .expect("binary D2/D5/D24+ program is admitted by SENS");

        let (result, visits) = program
            .execute_with_visit_count(&mut Session::bare())
            .expect("execute exact binary program with instrumentation");

        assert_eq!(result.value.to_string(), "3");
        assert_eq!(visits, 3, "one D5 call and two binary numeric leaves");
    }

    #[cfg(feature = "rust-t5-reference")]
    fn physical(source: &str) -> Vec<u8> {
        let words = parse_binary_source_words(source)
            .expect("only exact D1..D9 typed source words")
            .into_iter()
            .map(|word| word.word)
            .collect::<Vec<_>>();
        let physical = encode_ternary_words(&words).expect("canonical T5");
        assert_eq!(decode_ternary_words(&physical).unwrap(), words);
        physical
    }

    /// The physical SENS engine, not a host-side semantic oracle, must report
    /// which D2 form actually failed. The first form executes; the second
    /// rejects D3:000 in COND test position under current Contract 11.8.
    #[cfg(feature = "rust-t5-reference")]
    #[test]
    fn physical_runtime_type_error_identifies_the_failing_second_form() {
        let bytes = physical("10 001 00 000 01 00 10 110 00 10 000 00 1 01 01");
        let program = reference_t5_program(&bytes).expect("two admitted D2 forms");
        assert_eq!(program.form_count(), 2);
        let error = program
            .execute(&mut Session::default())
            .expect_err("second form must reject a non-D1 COND condition");
        assert_eq!(error.kind, crate::ErrorKind::Type);
        assert!(
            error.message.contains("physical_form_index=1")
                && error.message.contains("physical_word_start=5")
                && error.message.contains("physical_word_end=15"),
            "test_id=1968-PHYSICAL-FORM layer=SENS expected=form-1-words-5..15 actual={error}"
        );
    }

    #[cfg(feature = "rust-t5-reference")]
    #[test]
    fn physical_d3_quote_is_exact_domain_call_not_historical_w8_dispatch() {
        let bytes = physical("10 001 00 000 01");
        let program = reference_t5_program(&bytes).expect("admitted D3 quote");
        assert_eq!(program.form_count(), 1);
        assert!(matches!(
            program.forms()[0].kind,
            ExprKind::DomainCall(crate::CoreDomainIdentity::D3(word), _)
                if word.word().packed_bits() == 0b001
        ));
        // Syntax/transport proof only. The meaning of QUOTE is judged by
        // the binary SENS selftest below, never by a Rust expected value.
        let output = program
            .execute(&mut Session::default())
            .expect("pure D3 quote");
        assert!(output.output.is_empty());
    }

    #[cfg(feature = "rust-t5-reference")]
    #[test]
    fn physical_domain_width_cannot_be_inferred_from_equal_payload() {
        // Equal payloads in D1, D3 and D9 have DISTINCT identities; the
        // higher D9 bit must not be truncated into a historical W8 byte.
        let words = ["1", "001", "000000001", "100000001"];
        let codes = words
            .iter()
            .map(|source| physical(source))
            .collect::<Vec<_>>();
        assert!(codes
            .iter()
            .enumerate()
            .all(|(i, x)| codes.iter().enumerate().all(|(j, y)| i == j || x != y)));
        let mut widths = Vec::new();
        for physical in codes {
            let decoded = decode_ternary_words(&physical).unwrap();
            widths.push(decoded[0].width());
            let program = reference_t5_program(&physical).unwrap();
            assert_eq!(program.form_count(), 1);
            assert!(matches!(
                program.forms()[0].kind,
                ExprKind::DomainIdentity(_)
            ));
        }
        assert_eq!(widths, [1, 3, 9, 9]);
    }

    #[cfg(feature = "rust-t5-reference")]
    #[test]
    fn physical_t5_rejects_d2_as_data_before_any_side_effect() {
        let raw = parse_binary_source_words("01")
            .unwrap()
            .into_iter()
            .map(|x| x.word)
            .collect::<Vec<_>>();
        let physical = encode_ternary_words(&raw).unwrap();
        assert!(reference_t5_program(&physical).is_err());
    }

    #[test]
    fn exact_lowering_never_revives_historical_surface_into_w8_call() {
        // Synthetic AST probes the exact lowering firewall, not a legal
        // T5 encoding (T5 itself never contains symbols).
        let source = crate::parse("(print)").expect("historical syntax fixture");
        let exact = lower_exact_domain_program(&source);
        assert!(matches!(exact[0].kind, ExprKind::List(_)));
        assert!(!matches!(exact[0].kind, ExprKind::Call(_, _)));
    }

    // SENS-owned positive/negative physical selftest is executed by the
    // actual Zig-backed sens-trit binary, not embedded as project source
    // in this Rust core. See rust_zig_sens_file_link.rs in sens-cli/tests/.

    /// 2046 are POSSIBLE exact coordinates, not 2046 admitted functions.
    /// Rust checks only the physical transport, never defines semantics.
    #[cfg(feature = "rust-t5-reference")]
    #[test]
    fn all_2046_exact_coordinates_keep_every_bit_without_callability_lift() {
        use crate::domain_ladder::DomainCoordinate;
        use crate::ternary_transport::{decode_ternary_coordinates, encode_ternary_coordinates};
        let mut count = 0usize;
        let mut semantic_bits = 0usize;
        for width in 1u8..=10 {
            for payload in 0u16..(1u16 << width) {
                let word = DomainCoordinate::new(width, payload).expect("exact source coordinate");
                let physical = encode_ternary_coordinates(&[word]).expect("physical word");
                let recovered = decode_ternary_coordinates(&physical).expect("physical decode");
                assert_eq!(recovered, vec![word], "D{width}, payload={payload}");
                if width == 10 {
                    // The current D1-D9 *execution* reader MUST NOT
                    // silently infer D10 callability from physical data.
                    assert!(
                        decode_ternary_words(&physical).is_err(),
                        "D10={payload} is not callable"
                    );
                }
                semantic_bits += usize::from(width);
                count += 1;
            }
        }
        assert_eq!(count, 2046);
        assert_eq!(semantic_bits, 18_434);
    }
}
