//! Ratified D4:1110 LIST and D4:1111 APPEND execution mechanisms.
//!
//! Authority: lib/domains/d4.lisp; structural derivation #2347.
//! The exact D4 resident selects a mechanism; Rust does not allocate a
//! new SENS operation or reinterpret historical eight-bit SID identities.
//! APPEND copies only the left proper spine and preserves the right value
//! unchanged (including a dotted tail). Improper left tails fail closed.

use crate::{CoreDomainIdentity, ErrorKind, LanguageError, Span, Value};
use std::rc::Rc;

pub(super) fn invoke(
    identity: CoreDomainIdentity,
    arguments: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        0b1110 => Some(Ok(Value::list(arguments.iter().cloned()))),
        0b1111 => Some(append(arguments, span)),
        _ => None,
    }
}

fn append(arguments: &[Value], span: Span) -> Result<Value, LanguageError> {
    if arguments.len() != 2 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!("D4:1111 APPEND requires two values, received {}", arguments.len()),
            span,
        ));
    }

    // Exactly the independently derived #2347 structural Lisp law:
    // append((), right) = right; append(cons(head, tail), right) =
    // cons(head, append(tail, right)). The right argument is never traversed.
    let mut left_spine = Vec::<Value>::new();
    let mut cursor = &arguments[0];
    loop {
        match cursor {
            Value::Nil => break,
            Value::Pair(head, tail) => {
                left_spine.push(head.as_ref().clone());
                cursor = tail.as_ref();
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "D4:1111 APPEND requires a proper left list (dotted/improper left rejected)",
                    span,
                ));
            }
        }
    }

    let mut result = arguments[1].clone();
    for head in left_spine.into_iter().rev() {
        result = Value::Pair(Rc::new(head), Rc::new(result));
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit3, Bit4, CoreD4, Bija3};

    fn d4(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(bits).unwrap()))
    }

    #[test]
    fn list_is_variadic_and_retains_nested_nil() {
        let span = Span { start: 0, end: 0 };
        let nil = Value::Nil;
        let empty = invoke(d4(0b1110), &[], span).unwrap().unwrap();
        assert_eq!(empty, nil);
        let one = invoke(d4(0b1110), &[nil.clone()], span).unwrap().unwrap();
        assert_eq!(one.to_string(), "(())");
        let two = invoke(d4(0b1110), &[nil.clone(), nil], span).unwrap().unwrap();
        assert_eq!(two.to_string(), "(() ())");
    }

    #[test]
    fn append_preserves_dotted_right_and_never_accepts_improper_left() {
        let span = Span { start: 0, end: 0 };
        let atom = Value::Symbol(Rc::from("a"));
        let tail = Value::Symbol(Rc::from("z"));
        let dotted = Value::Pair(Rc::new(atom.clone()), Rc::new(tail.clone()));
        assert_eq!(invoke(d4(0b1111), &[Value::Nil, dotted.clone()], span).unwrap().unwrap(), dotted);
        let left = Value::list([atom.clone()]);
        let result = invoke(d4(0b1111), &[left, dotted], span).unwrap().unwrap();
        assert_eq!(result.to_string(), "(a a . z)");
        let error = invoke(d4(0b1111), &[atom, tail], span).unwrap().unwrap_err();
        assert_eq!(error.kind, ErrorKind::Type);
    }

    #[test]
    fn wrong_arity_and_non_d4_never_gain_a_mechanism() {
        let span = Span { start: 0, end: 0 };
        for count in [0usize, 1, 3] {
            let args = vec![Value::Nil; count];
            let error = invoke(d4(0b1111), &args, span).unwrap().unwrap_err();
            assert_eq!(error.kind, ErrorKind::Arity);
        }
        assert!(invoke(d4(0b1000), &[Value::Nil], span).is_none());
        assert!(invoke(
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b110).unwrap())),
            &[Value::Nil], span
        ).is_none());
    }
}
