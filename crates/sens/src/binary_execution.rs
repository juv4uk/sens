//! Direct physical T5 execution. The byte stream already carries exact
//! domain widths; its meaning is owned by the current SENS evaluator.
//!
//! No visible-text source, host Lisp alias, invented resident, or native CPU
//! machine-code claim is constructed by this adapter.

use crate::{
    decode_ternary_words, eval_lowered_expressions,
    eval::{lower::lower_exact_domain_program, validate_exact_executable_heads},
    ternary_transport::parse_t5_domain_words, EvalResult, Expr,
    LanguageError, Session, TernaryTransportError,
};

/// Transport and language failures have distinct, fail-closed provenance.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
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
    /// Never admit a historical Sens8 head from physical bits or from
    /// an accidental compatibility-only symbol in a partially lowered AST.
    pub fn decode(physical: &[u8]) -> Result<Self, T5ExecutionError> {
        let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
        let parsed = parse_t5_domain_words(&words).map_err(T5ExecutionError::Language)?;
        // Physical T5 has *already* preserved every exact W1..W9 width.
        // Historical lowering would consult flat W8 surfaces and could
        // reinterpret the source after a successful typed decode.
        let forms = lower_exact_domain_program(&parsed);
        // Use the SAME fail-closed executable-head gate as the human
        // exact-domain entry, before evaluating any form/side effect.
        validate_exact_executable_heads(&forms).map_err(T5ExecutionError::Language)?;
        Ok(Self { forms })
    }

    /// Number of top-level D2 forms; no assumption of a single expression.
    pub fn form_count(&self) -> usize {
        self.forms.len()
    }

    /// Execute decoded forms in an explicitly supplied interpreter session.
    ///
    /// The program does not retain a mutable runtime between calls. Bootstrap,
    /// host capabilities, and session reuse remain the caller's decision.
    pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
        eval_lowered_expressions(&self.forms, session)
    }
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
    use crate::{encode_ternary_words, parse_binary_source_words, ExprKind, Value};

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
        let output = program.execute(&mut Session::default()).expect("pure D3 quote");
        assert!(matches!(output.value, Value::Nil));
        assert!(output.output.is_empty());
    }

    #[test]
    fn physical_domain_width_cannot_be_inferred_from_equal_payload() {
        // Equal payloads in D1, D3 and D9 have DISTINCT identities; the
        // higher D9 bit must not be truncated into a historical W8 byte.
        let words = ["1", "001", "000000001", "100000001"];
        let codes = words.iter().map(|source| physical(source)).collect::<Vec<_>>();
        assert!(codes.iter().enumerate().all(|(i, x)|
            codes.iter().enumerate().all(|(j, y)| i == j || x != y)));
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
            .unwrap().into_iter().map(|x| x.word).collect::<Vec<_>>();
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
}
