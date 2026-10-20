//! Direct physical T5 execution. The byte stream already carries exact
//! domain widths; its meaning is owned by the current SENS evaluator.
//!
//! No visible-text source, host Lisp alias, invented resident, or native CPU
//! machine-code claim is constructed by this adapter.

use crate::{
    decode_ternary_words,
    eval::{lower::lower_exact_domain_program, validate_exact_executable_heads},
    eval_lowered_expressions, BinaryNumber, BinarySourceWord, DomainIdentity, EvalResult, Expr,
    LanguageError, Session, TernaryTransportError,
};

/// Transport and language failures have distinct, fail-closed provenance.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

/// SENS-owned word after physical T5M restoration. Identity is explicit:
/// exact domain words are not inferred from payload width, and D24+ numbers
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
            return Err("T5M number must retain an exact D24+ identity and exact-width bits");
        }
        Ok(Self::Number(number))
    }
}

/// Canonically validated physical T5 program, stored as the current lowered AST.
///
/// Decode+parse+the exact-domain interpreter lowering happens once. Repeated
/// evaluation reuses those exact immutable lowered forms,
/// but every evaluation still consults the current interpreter/Session.
/// This is NOT compiled machine code and grants no additional capabilities.
pub struct PhysicalT5Program {
    forms: Vec<Expr>,
}

impl PhysicalT5Program {
    /// Physical bytes -> exact D1-D9 words -> ratified D2 forms, without
    /// creating any text or parsing human identifier surfaces.
    /// Never admit a historical CoreDomainIdentity head from physical bits or from
    /// an accidental compatibility-only symbol in a partially lowered AST.
    pub fn decode(physical: &[u8]) -> Result<Self, T5ExecutionError> {
        let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
        Self::from_exact_words(&words).map_err(T5ExecutionError::Language)
    }

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
        Self::from_exact_domain_words(&exact)
    }

    /// Build an executable SENS program from words already restored by a
    /// physical carrier such as Zig T5M. This reader accepts only explicit
    /// domain identities plus explicitly qualified D24+ numbers.
    pub fn from_exact_domain_words(words: &[ExactDomainWord]) -> Result<Self, LanguageError> {
        let parsed = parse_exact_domain_words(words)?;
        let forms = lower_exact_domain_program(&parsed);
        validate_exact_executable_heads(&forms)?;
        Ok(Self { forms })
    }

    /// Number of top-level D2 forms; no assumption of a single expression.
    pub fn form_count(&self) -> usize {
        self.forms.len()
    }

    /// Exact SENS AST reconstructed from the supplied domain-qualified words.
    /// This is a read-only witness for hosts that need SENS-owned meta-eval;
    /// callers still use `execute` or their explicitly selected evaluator.
    pub fn forms(&self) -> &[Expr] {
        &self.forms
    }

    /// Execute decoded forms in an explicitly supplied interpreter session.
    ///
    /// The program does not retain a mutable runtime between calls. Bootstrap,
    /// host capabilities, and session reuse remain the caller's decision.
    pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
        eval_lowered_expressions(&self.forms, session)
    }
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
        if depth > 768 {
            return Err(error("exact D2 nesting exceeds AST depth limit", index));
        }
        if d2(word, OPEN) {
            return parse_list(words, cursor, depth + 1);
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

/// One-shot version of the same source-free program path.
///
/// Keep this wrapper to preserve the stable public API and ensure it shares
/// the precise decode/parse/evaluate law with `sens-trit eval`.
pub fn eval_t5_program(
    physical: &[u8],
    session: &mut Session,
) -> Result<EvalResult, T5ExecutionError> {
    let program = PhysicalT5Program::decode(physical)?;
    program.execute(session).map_err(T5ExecutionError::Language)
}

#[cfg(test)]
mod exact_t5_cutover_tests {
    use super::*;
    use crate::{encode_ternary_words, parse_binary_source_words, ExprKind};

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
        assert_eq!(number.to_decimal_string(), "3");
    }

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

    #[test]
    fn physical_d3_quote_is_exact_domain_call_not_historical_w8_dispatch() {
        let bytes = physical("10 001 00 000 01");
        let program = PhysicalT5Program::decode(&bytes).expect("admitted D3 quote");
        assert_eq!(program.form_count(), 1);
        assert!(matches!(
            program.forms[0].kind,
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
            let program = PhysicalT5Program::decode(&physical).unwrap();
            assert_eq!(program.form_count(), 1);
            assert!(matches!(program.forms[0].kind, ExprKind::DomainIdentity(_)));
        }
        assert_eq!(widths, [1, 3, 9, 9]);
    }

    #[test]
    fn physical_t5_rejects_d2_as_data_before_any_side_effect() {
        let raw = parse_binary_source_words("01")
            .unwrap()
            .into_iter()
            .map(|x| x.word)
            .collect::<Vec<_>>();
        let physical = encode_ternary_words(&raw).unwrap();
        assert!(matches!(
            PhysicalT5Program::decode(&physical),
            Err(T5ExecutionError::Language(_))
        ));
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
