//! Exact source-shaped program-data representation.
//!
//! Converts already-lowered SENS AST into ordinary runtime data without
//! reintroducing human spellings or legacy SID8 identity.
//! DomainCall(identity,args...) becomes a proper list headed by the exact
//! first-class DomainIdentity. This module owns representation only.

use crate::{DomainIdentity, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};
use std::rc::Rc;

fn invalid_program_data(message: impl Into<String>) -> LanguageError {
    LanguageError::new(ErrorKind::InvalidForm, message, Span::default())
}

/// Convert one already-lowered expression into source-shaped exact program-data.
///
/// The old recursive visitor exhausted a host thread's stack on deeply nested
/// (but otherwise source-shaped) data. Work is now explicit, retaining each
/// domain-qualified head as data, not treating its payload as a legacy opcode.
/// The parser's existing structural depth limit remains the single safety
/// contract, also for ASTs built directly by an embedding host.
pub fn expr_to_exact_program_data(expr: &Expr) -> Result<Value, LanguageError> {
    use crate::syntax::MAX_STRUCTURE_DEPTH;

    enum Step<'a> {
        Visit(&'a Expr, u32),
        List(usize),
        Pair,
        DomainCall(crate::CoreDomainIdentity, usize),
    }

    let mut pending = vec![Step::Visit(expr, 0)];
    let mut finished = Vec::new();

    while let Some(task) = pending.pop() {
        match task {
            Step::Visit(node, depth) => {
                let next_depth = || {
                    if depth >= MAX_STRUCTURE_DEPTH {
                        Err(invalid_program_data(
                            "точнодоменна програма: перевищено глибину структури",
                        ))
                    } else {
                        Ok(depth + 1)
                    }
                };
                match &node.kind {
                    ExprKind::Number(_, _) | ExprKind::Rational(_) | ExprKind::NumericBuffer(_) => {
                        return Err(invalid_program_data(
                            "точнодоменна програма: історичні числові літерали не мають D24+",
                        ));
                    }
                    ExprKind::BinaryNumber(number) if number.numeric_domain_width().is_some() => {
                        finished.push(Value::BinaryNumber(number.clone()));
                    }
                    ExprKind::BinaryNumber(_) => {
                        return Err(invalid_program_data(
                            "точнодоменна програма: двійкове число потребує явного домену D24+",
                        ));
                    }
                    ExprKind::DomainIdentity(identity) => {
                        finished.push(Value::DomainIdentity(*identity));
                    }
                    ExprKind::String(value) => finished.push(Value::String(value.clone())),
                    ExprKind::Symbol(value) => finished.push(Value::Symbol(value.clone())),
                    ExprKind::List(items) => {
                        let child_depth = next_depth()?;
                        pending.try_reserve(items.len().saturating_add(1)).map_err(|_| {
                            invalid_program_data("точнодоменна програма: немає місткості стеку")
                        })?;
                        pending.push(Step::List(items.len()));
                        for child in items.iter().rev() {
                            pending.push(Step::Visit(child, child_depth));
                        }
                    }
                    ExprKind::Pair(head, tail) => {
                        let child_depth = next_depth()?;
                        pending.try_reserve(3).map_err(|_| {
                            invalid_program_data("точнодоменна програма: немає місткості стеку")
                        })?;
                        pending.push(Step::Pair);
                        pending.push(Step::Visit(tail, child_depth));
                        pending.push(Step::Visit(head, child_depth));
                    }
                    ExprKind::DomainCall(identity, arguments) => {
                        let child_depth = next_depth()?;
                        pending.try_reserve(arguments.len().saturating_add(1)).map_err(|_| {
                            invalid_program_data("точнодоменна програма: немає місткості стеку")
                        })?;
                        pending.push(Step::DomainCall(*identity, arguments.len()));
                        for argument in arguments.iter().rev() {
                            pending.push(Step::Visit(argument, child_depth));
                        }
                    }
                    ExprKind::Sid(_) | ExprKind::Call(_, _) => {
                        return Err(invalid_program_data(
                            "exact program-data must not contain legacy Sid/Call nodes",
                        ));
                    }
                    ExprKind::Local { .. } => {
                        return Err(invalid_program_data(
                            "source-shaped exact program-data must not contain resolved Local nodes",
                        ));
                    }
                }
            }
            Step::List(len) => {
                let begin = finished.len().checked_sub(len).ok_or_else(|| {
                    invalid_program_data("точнодоменна програма: пошкоджена структура списку")
                })?;
                let items = finished.split_off(begin);
                finished.push(Value::list(items));
            }
            Step::Pair => {
                let tail = finished.pop().ok_or_else(|| {
                    invalid_program_data("точнодоменна програма: немає хвоста пари")
                })?;
                let head = finished.pop().ok_or_else(|| {
                    invalid_program_data("точнодоменна програма: немає голови пари")
                })?;
                finished.push(Value::Pair(Rc::new(head), Rc::new(tail)));
            }
            Step::DomainCall(identity, len) => {
                let begin = finished.len().checked_sub(len).ok_or_else(|| {
                    invalid_program_data("точнодоменна програма: пошкоджений доменний виклик")
                })?;
                let mut args = finished.split_off(begin);
                args.try_reserve_exact(1).map_err(|_| {
                    invalid_program_data("точнодоменна програма: немає місткості виклику")
                })?;
                args.insert(0, Value::DomainIdentity(DomainIdentity::from(identity)));
                finished.push(Value::list(args));
            }
        }
    }
    let result = finished.pop().ok_or_else(|| {
        invalid_program_data("точнодоменна програма: порожній результат")
    })?;
    debug_assert!(finished.is_empty());
    Ok(result)
}

/// Convert an already-lowered top-level program into a proper data list.
pub fn lowered_program_to_exact_data(program: &[Expr]) -> Result<Value, LanguageError> {
    let mut converted = Vec::new();
    converted.try_reserve_exact(program.len()).map_err(|_| {
        invalid_program_data("точнодоменна програма: немає місткості для форм")
    })?;
    for expr in program {
        converted.push(expr_to_exact_program_data(expr)?);
    }
    Ok(Value::list(converted))
}

#[cfg(test)]
mod тести_міграції_чисел_d24 {
    use super::*;
    use crate::{Bija3, BinaryNumber, Bit3, CoreDomainIdentity, Exactness};

    fn вузол(kind: ExprKind) -> Expr {
        Expr {
            kind,
            span: Span::default(),
        }
    }

    fn кваліфіковане_число(width: usize) -> Expr {
        let mut bits = vec![0u8; width];
        bits[width - 1] = 1;
        вузол(ExprKind::BinaryNumber(
            BinaryNumber::from_numeric_domain_bits(width, &bits)
                .expect("доведене числове слово D24+"),
        ))
    }

    #[test]
    fn рівне_значення_зберігає_відмінні_домени_d24_d48() {
        let d24 = expr_to_exact_program_data(&кваліфіковане_число(24)).unwrap();
        let d48 = expr_to_exact_program_data(&кваліфіковане_число(48)).unwrap();
        assert_ne!(d24, d48, "D24 та D48 не тотожні через спільне значення");
        assert!(matches!(d24, Value::BinaryNumber(ref n) if n.numeric_domain_width() == Some(24)));
        assert!(matches!(d48, Value::BinaryNumber(ref n) if n.numeric_domain_width() == Some(48)));
    }

    #[test]
    fn заборонено_історичні_числові_літерали_без_d24() {
        let старі = [
            вузол(ExprKind::Number(1.0, Exactness::Exact)),
            вузол(ExprKind::Rational(
                crate::Rational::from_literal("1", "2").expect("історичний літерал"),
            )),
            вузол(ExprKind::BinaryNumber(BinaryNumber::parse("1").unwrap())),
        ];
        for старе in старі {
            assert_eq!(
                expr_to_exact_program_data(&старе).unwrap_err().kind,
                ErrorKind::InvalidForm,
            );
        }
    }

    #[test]
    fn вкладені_числа_не_відмиваються_через_списки_й_доменні_виклики() {
        let старе = вузол(ExprKind::Number(3.0, Exactness::Exact));
        let список = вузол(ExprKind::List(Rc::from([старе.clone()])));
        assert!(expr_to_exact_program_data(&список).is_err());
        let пара = вузол(ExprKind::Pair(Rc::new(кваліфіковане_число(24)), Rc::new(старе.clone())));
        assert!(expr_to_exact_program_data(&пара).is_err());
        let quote = CoreDomainIdentity::D3(
            Bija3::from_word(Bit3::new(0b001).unwrap()),
        );
        let виклик = вузол(ExprKind::DomainCall(quote, Rc::from([старе])));
        assert!(expr_to_exact_program_data(&виклик).is_err());
    }

    #[test]
    fn точний_доменний_виклик_з_числом_d24_залишається_програмою() {
        let quote = CoreDomainIdentity::D3(
            Bija3::from_word(Bit3::new(0b001).unwrap()),
        );
        let source = вузол(ExprKind::DomainCall(quote, Rc::from([кваліфіковане_число(24)])));
        let result = expr_to_exact_program_data(&source).expect("доведена форма");
        assert!(matches!(result, Value::Pair(_, _)));
    }
}
