// GENERATED PROJECTION — authority: lib/surface/domain-function-signatures.lisp
// Exact domain width+bits are the key. No legacy Function8/Sens8 identity exists here.

use crate::language_items::{Arity, LanguageItemKind};

#[derive(Clone, Copy, Debug)]
pub(crate) struct DomainFunctionSignature {
    pub(crate) width: u8,
    pub(crate) bits: u8,
    pub(crate) kind: LanguageItemKind,
    pub(crate) arity: Arity,
    pub(crate) signature: &'static str,
    pub(crate) documentation: &'static str,
}

pub(crate) const DOMAIN_FUNCTION_SIGNATURES: &[DomainFunctionSignature] = &[
    DomainFunctionSignature { width: 3, bits: 0b001, kind: LanguageItemKind::SyntaxForm, arity: Arity::Exact(1), signature: "(quote value)", documentation: "Return value unevaluated" },
    DomainFunctionSignature { width: 3, bits: 0b010, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(atom? value)", documentation: "Test whether value is not a pair" },
    DomainFunctionSignature { width: 3, bits: 0b011, kind: LanguageItemKind::SyntaxForm, arity: Arity::AtLeast(0), signature: "(cond (test result) ...)", documentation: "Evaluate the first matching clause" },
    DomainFunctionSignature { width: 3, bits: 0b100, kind: LanguageItemKind::Builtin, arity: Arity::Exact(2), signature: "(cons head tail)", documentation: "Create a pair" },
    DomainFunctionSignature { width: 3, bits: 0b101, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(car pair)", documentation: "Return the first element of a pair" },
    DomainFunctionSignature { width: 3, bits: 0b110, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(cdr pair)", documentation: "Return the tail of a pair" },
    DomainFunctionSignature { width: 3, bits: 0b111, kind: LanguageItemKind::Builtin, arity: Arity::Exact(2), signature: "(eq? left right)", documentation: "Test structural or identity equality" },

    DomainFunctionSignature { width: 4, bits: 0b0010, kind: LanguageItemKind::SyntaxForm, arity: Arity::AtLeast(2), signature: "(lambda (params) body ...)", documentation: "Create an anonymous function" },
    DomainFunctionSignature { width: 4, bits: 0b0011, kind: LanguageItemKind::SyntaxForm, arity: Arity::Exact(2), signature: "(define name value)", documentation: "Bind name in the current scope" },
    DomainFunctionSignature { width: 4, bits: 0b1010, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(caar pair)", documentation: "Compose CAR after CAR" },
    DomainFunctionSignature { width: 4, bits: 0b1011, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(cadr pair)", documentation: "Compose CAR after CDR" },
    DomainFunctionSignature { width: 4, bits: 0b1100, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(cdar pair)", documentation: "Compose CDR after CAR" },
    DomainFunctionSignature { width: 4, bits: 0b1101, kind: LanguageItemKind::Builtin, arity: Arity::Exact(1), signature: "(cddr pair)", documentation: "Compose CDR after CDR" },

    DomainFunctionSignature { width: 5, bits: 0b01010, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(0), signature: "(+ number ...)", documentation: "Sum all arguments" },
    DomainFunctionSignature { width: 5, bits: 0b01011, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(1), signature: "(- number ...)", documentation: "Subtract or negate" },
    DomainFunctionSignature { width: 5, bits: 0b01110, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(1), signature: "(< number ...)", documentation: "Less-than chain comparison" },
    DomainFunctionSignature { width: 5, bits: 0b01111, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(1), signature: "(> number ...)", documentation: "Greater-than chain comparison" },
    DomainFunctionSignature { width: 5, bits: 0b10010, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(0), signature: "(* number ...)", documentation: "Multiply all arguments" },
    DomainFunctionSignature { width: 5, bits: 0b10011, kind: LanguageItemKind::Builtin, arity: Arity::AtLeast(1), signature: "(/ number ...)", documentation: "Perform exact rational division" },
];
