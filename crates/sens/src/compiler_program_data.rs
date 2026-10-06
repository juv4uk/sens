//! Canonical current-SENS program data passed across the self-host bootstrap seam.
//!
//! This module is representation only. It preserves exact domain width, child
//! ordering and lexical coordinates, but never selects compiler roles,
//! callability, proofs or backend mechanisms.

use crate::{
    sha256_source, Bija3, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, CoreD4, CoreD5,
    CoreD6, CoreD8, DomainIdentity, Expr, ExprKind, PredicateBit, Racana2, SoundD7, Value,
};
use std::{fmt, rc::Rc};

pub const COMPILER_PROGRAM_DATA_SCHEMA: &str = "sens-compiler-program-data/1";

#[derive(Clone, Debug, PartialEq)]
pub struct CompilerProgramData {
    pub forms: Vec<CompilerProgramNode>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum CompilerProgramNode {
    DomainCall {
        identity: DomainIdentity,
        children: Vec<CompilerProgramNode>,
    },
    Local {
        depth: u32,
        index: u32,
    },
    DomainValue(DomainIdentity),
    Symbol(Rc<str>),
    String(Rc<str>),
    List(Vec<CompilerProgramNode>),
    Pair(Box<CompilerProgramNode>, Box<CompilerProgramNode>),
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CompilerProgramDataError {
    LegacySid8,
    LegacyCall,
    UnsupportedExpr(&'static str),
    Malformed(String),
}

impl fmt::Display for CompilerProgramDataError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::LegacySid8 => write!(formatter, "legacy Sid8 is forbidden in compiler program data"),
            Self::LegacyCall => write!(formatter, "legacy Sid8 Call is forbidden in compiler program data"),
            Self::UnsupportedExpr(kind) => {
                write!(formatter, "expression kind is outside compiler-program-data/1: {kind}")
            }
            Self::Malformed(message) => write!(formatter, "malformed compiler program data: {message}"),
        }
    }
}

impl std::error::Error for CompilerProgramDataError {}

fn symbol(name: &str) -> Value {
    Value::Symbol(Rc::from(name))
}

fn string(value: impl Into<String>) -> Value {
    Value::String(Rc::from(value.into()))
}

fn proper_list<'a>(value: &'a Value) -> Result<Vec<&'a Value>, CompilerProgramDataError> {
    let mut out = Vec::new();
    let mut current = value;
    loop {
        match current {
            Value::Nil => return Ok(out),
            Value::Pair(head, tail) => {
                out.push(head.as_ref());
                current = tail.as_ref();
            }
            other => {
                return Err(CompilerProgramDataError::Malformed(format!(
                    "expected proper list, found {other}"
                )));
            }
        }
    }
}

fn tag(value: &Value) -> Result<&str, CompilerProgramDataError> {
    match value {
        Value::Symbol(name) => Ok(name.as_ref()),
        other => Err(CompilerProgramDataError::Malformed(format!(
            "node tag is not a symbol: {other}"
        ))),
    }
}

fn quoted_string(value: &Value, field: &str) -> Result<&str, CompilerProgramDataError> {
    match value {
        Value::String(text) => Ok(text.as_ref()),
        other => Err(CompilerProgramDataError::Malformed(format!(
            "{field} is not a string: {other}"
        ))),
    }
}

fn identity_parts(identity: DomainIdentity) -> (String, String) {
    (
        identity.width().to_string(),
        format!(
            "{:0width$b}",
            identity.packed_bits(),
            width = identity.width()
        ),
    )
}

fn parse_exact_u32(text: &str, field: &str) -> Result<u32, CompilerProgramDataError> {
    text.parse::<u32>().map_err(|_| {
        CompilerProgramDataError::Malformed(format!("{field} is not an exact u32: {text:?}"))
    })
}

/// Mechanical reconstruction of an exact-width carrier.
///
/// This function selects only the carrier type from the explicitly transported
/// width. It does not project callability or compiler meaning.
fn identity_from_parts(
    width_text: &str,
    bits: &str,
) -> Result<DomainIdentity, CompilerProgramDataError> {
    let width = width_text.parse::<usize>().map_err(|_| {
        CompilerProgramDataError::Malformed(format!("invalid domain width: {width_text:?}"))
    })?;
    if !(1..=8).contains(&width) {
        return Err(CompilerProgramDataError::Malformed(format!(
            "domain width outside D1-D8: {width}"
        )));
    }
    if bits.len() != width || !bits.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        return Err(CompilerProgramDataError::Malformed(format!(
            "domain bits {bits:?} do not match exact width {width}"
        )));
    }
    let payload = u8::from_str_radix(bits, 2).map_err(|_| {
        CompilerProgramDataError::Malformed(format!("invalid exact domain bits: {bits:?}"))
    })?;

    let identity = match width {
        1 => DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(payload).expect("validated D1 payload"),
        )),
        2 => DomainIdentity::D2(Racana2::from_word(
            Bit2::new(payload).expect("validated D2 payload"),
        )),
        3 => DomainIdentity::D3(Bija3::from_word(
            Bit3::new(payload).expect("validated D3 payload"),
        )),
        4 => DomainIdentity::D4(CoreD4::from_word(
            Bit4::new(payload).expect("validated D4 payload"),
        )),
        5 => DomainIdentity::D5(CoreD5::from_word(
            Bit5::new(payload).expect("validated D5 payload"),
        )),
        6 => DomainIdentity::D6(CoreD6::from_word(
            Bit6::new(payload).expect("validated D6 payload"),
        )),
        7 => DomainIdentity::D7(SoundD7::from_word(
            Bit7::new(payload).expect("validated D7 payload"),
        )),
        8 => DomainIdentity::D8(CoreD8::from_word(
            Bit8::new(payload).expect("validated D8 payload"),
        )),
        _ => unreachable!("width range checked above"),
    };
    Ok(identity)
}

impl CompilerProgramNode {
    pub fn from_expr(expr: &Expr) -> Result<Self, CompilerProgramDataError> {
        match &expr.kind {
            ExprKind::DomainCall(identity, children) => Ok(Self::DomainCall {
                identity: (*identity).into(),
                children: children
                    .iter()
                    .map(Self::from_expr)
                    .collect::<Result<Vec<_>, _>>()?,
            }),
            ExprKind::Local { depth, index } => Ok(Self::Local {
                depth: *depth,
                index: *index,
            }),
            ExprKind::DomainIdentity(identity) => Ok(Self::DomainValue(*identity)),
            ExprKind::Symbol(value) => Ok(Self::Symbol(value.clone())),
            ExprKind::String(value) => Ok(Self::String(value.clone())),
            ExprKind::List(items) => Ok(Self::List(
                items
                    .iter()
                    .map(Self::from_expr)
                    .collect::<Result<Vec<_>, _>>()?,
            )),
            ExprKind::Pair(head, tail) => Ok(Self::Pair(
                Box::new(Self::from_expr(head)?),
                Box::new(Self::from_expr(tail)?),
            )),
            ExprKind::Sid(_) => Err(CompilerProgramDataError::LegacySid8),
            ExprKind::Call(_, _) => Err(CompilerProgramDataError::LegacyCall),
            ExprKind::Number(_, _) => Err(CompilerProgramDataError::UnsupportedExpr("number")),
            ExprKind::Rational(_) => Err(CompilerProgramDataError::UnsupportedExpr("rational")),
            ExprKind::BinaryNumber(_) => {
                Err(CompilerProgramDataError::UnsupportedExpr("binary-number"))
            }
            ExprKind::NumericBuffer(_) => {
                Err(CompilerProgramDataError::UnsupportedExpr("numeric-buffer"))
            }
        }
    }

    pub fn to_value(&self) -> Value {
        match self {
            Self::DomainCall { identity, children } => {
                let (width, bits) = identity_parts(*identity);
                Value::list([
                    symbol("domain-call"),
                    string(width),
                    string(bits),
                    Value::list(children.iter().map(Self::to_value)),
                ])
            }
            Self::Local { depth, index } => Value::list([
                symbol("local"),
                string(depth.to_string()),
                string(index.to_string()),
            ]),
            Self::DomainValue(identity) => {
                let (width, bits) = identity_parts(*identity);
                Value::list([symbol("domain-value"), string(width), string(bits)])
            }
            Self::Symbol(value) => {
                Value::list([symbol("symbol"), Value::String(value.clone())])
            }
            Self::String(value) => {
                Value::list([symbol("string"), Value::String(value.clone())])
            }
            Self::List(items) => {
                Value::list([symbol("list"), Value::list(items.iter().map(Self::to_value))])
            }
            Self::Pair(head, tail) => {
                Value::list([symbol("pair"), head.to_value(), tail.to_value()])
            }
        }
    }

    pub fn from_value(value: &Value) -> Result<Self, CompilerProgramDataError> {
        let fields = proper_list(value)?;
        let Some(first) = fields.first() else {
            return Err(CompilerProgramDataError::Malformed("empty node".into()));
        };
        match tag(first)? {
            "domain-call" => {
                if fields.len() != 4 {
                    return Err(CompilerProgramDataError::Malformed(
                        "domain-call requires width, bits, ordered children".into(),
                    ));
                }
                let identity = identity_from_parts(
                    quoted_string(fields[1], "domain-call width")?,
                    quoted_string(fields[2], "domain-call bits")?,
                )?;
                let children = proper_list(fields[3])?
                    .into_iter()
                    .map(Self::from_value)
                    .collect::<Result<Vec<_>, _>>()?;
                Ok(Self::DomainCall { identity, children })
            }
            "local" => {
                if fields.len() != 3 {
                    return Err(CompilerProgramDataError::Malformed(
                        "local requires depth and index".into(),
                    ));
                }
                Ok(Self::Local {
                    depth: parse_exact_u32(quoted_string(fields[1], "local depth")?, "local depth")?,
                    index: parse_exact_u32(quoted_string(fields[2], "local index")?, "local index")?,
                })
            }
            "domain-value" => {
                if fields.len() != 3 {
                    return Err(CompilerProgramDataError::Malformed(
                        "domain-value requires width and bits".into(),
                    ));
                }
                Ok(Self::DomainValue(identity_from_parts(
                    quoted_string(fields[1], "domain-value width")?,
                    quoted_string(fields[2], "domain-value bits")?,
                )?))
            }
            "symbol" => {
                if fields.len() != 2 {
                    return Err(CompilerProgramDataError::Malformed(
                        "symbol requires exact text".into(),
                    ));
                }
                Ok(Self::Symbol(Rc::from(quoted_string(
                    fields[1],
                    "symbol text",
                )?)))
            }
            "string" => {
                if fields.len() != 2 {
                    return Err(CompilerProgramDataError::Malformed(
                        "string requires exact text".into(),
                    ));
                }
                Ok(Self::String(Rc::from(quoted_string(
                    fields[1],
                    "string text",
                )?)))
            }
            "list" => {
                if fields.len() != 2 {
                    return Err(CompilerProgramDataError::Malformed(
                        "list requires one ordered-children list".into(),
                    ));
                }
                Ok(Self::List(
                    proper_list(fields[1])?
                        .into_iter()
                        .map(Self::from_value)
                        .collect::<Result<Vec<_>, _>>()?,
                ))
            }
            "pair" => {
                if fields.len() != 3 {
                    return Err(CompilerProgramDataError::Malformed(
                        "pair requires head and tail".into(),
                    ));
                }
                Ok(Self::Pair(
                    Box::new(Self::from_value(fields[1])?),
                    Box::new(Self::from_value(fields[2])?),
                ))
            }
            other => Err(CompilerProgramDataError::Malformed(format!(
                "unknown program-data node tag: {other}"
            ))),
        }
    }
}

impl CompilerProgramData {
    pub fn from_exprs(expressions: &[Expr]) -> Result<Self, CompilerProgramDataError> {
        Ok(Self {
            forms: expressions
                .iter()
                .map(CompilerProgramNode::from_expr)
                .collect::<Result<Vec<_>, _>>()?,
        })
    }

    pub fn to_value(&self) -> Value {
        Value::list([
            symbol(COMPILER_PROGRAM_DATA_SCHEMA),
            Value::list(self.forms.iter().map(CompilerProgramNode::to_value)),
        ])
    }

    pub fn from_value(value: &Value) -> Result<Self, CompilerProgramDataError> {
        let root = proper_list(value)?;
        if root.len() != 2 {
            return Err(CompilerProgramDataError::Malformed(
                "program root must contain schema and forms".into(),
            ));
        }
        if tag(root[0])? != COMPILER_PROGRAM_DATA_SCHEMA {
            return Err(CompilerProgramDataError::Malformed(format!(
                "unsupported program-data schema: {}",
                tag(root[0])?
            )));
        }
        Ok(Self {
            forms: proper_list(root[1])?
                .into_iter()
                .map(CompilerProgramNode::from_value)
                .collect::<Result<Vec<_>, _>>()?,
        })
    }

    pub fn canonical_wire_string(&self) -> String {
        self.to_value().to_canonical_wire_string()
    }

    pub fn canonical_sha256(&self) -> String {
        sha256_source(self.canonical_wire_string().as_bytes())
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{lower_program, parse, CoreDomainIdentity};

    const NUCLEUS_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");

    fn domain_call(identity: CoreDomainIdentity, children: Vec<CompilerProgramNode>) -> CompilerProgramNode {
        CompilerProgramNode::DomainCall {
            identity: identity.into(),
            children,
        }
    }

    #[test]
    fn current_compiler_nucleus_fits_the_bounded_program_data_vocabulary() {
        let parsed = parse(NUCLEUS_SOURCE).expect("current nucleus parses");
        let lowered = lower_program(&parsed);
        let program = CompilerProgramData::from_exprs(&lowered)
            .expect("current compiler nucleus must fit program-data/1");
        assert!(!program.forms.is_empty());
        assert_eq!(
            CompilerProgramData::from_value(&program.to_value()).unwrap(),
            program
        );
    }

    #[test]
    fn same_payload_under_different_widths_remains_distinct() {
        let d3 = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b001).unwrap()));
        let d4 = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0001).unwrap()));
        let a = CompilerProgramData {
            forms: vec![domain_call(d3, vec![])],
        };
        let b = CompilerProgramData {
            forms: vec![domain_call(d4, vec![])],
        };

        assert_ne!(a, b);
        assert_ne!(a.canonical_wire_string(), b.canonical_wire_string());
        assert!(a.canonical_wire_string().contains("\"3\" \"001\""));
        assert!(b.canonical_wire_string().contains("\"4\" \"0001\""));
    }

    #[test]
    fn d8_is_transportable_without_becoming_admitted_semantics() {
        let d8_identity = DomainIdentity::D8(CoreD8::from_word(Bit8::new(0b1000_0000).unwrap()));
        let program = CompilerProgramData {
            forms: vec![CompilerProgramNode::DomainCall {
                identity: d8_identity,
                children: vec![CompilerProgramNode::List(vec![])],
            }],
        };

        let decoded = CompilerProgramData::from_value(&program.to_value()).unwrap();
        assert_eq!(decoded, program);
        let CompilerProgramNode::DomainCall { identity, .. } = &decoded.forms[0] else {
            panic!("expected D8 transport call");
        };
        assert_eq!(*identity, d8_identity);
        assert_eq!(identity.core_operation(), None);
    }

    #[test]
    fn child_order_and_lexical_coordinates_survive_round_trip() {
        let d3 = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b111).unwrap()));
        let program = CompilerProgramData {
            forms: vec![domain_call(
                d3,
                vec![
                    CompilerProgramNode::Local { depth: 2, index: 7 },
                    CompilerProgramNode::Symbol(Rc::from("alpha")),
                    CompilerProgramNode::Pair(
                        Box::new(CompilerProgramNode::String(Rc::from("head"))),
                        Box::new(CompilerProgramNode::List(vec![])),
                    ),
                ],
            )],
        };

        let value = program.to_value();
        let decoded = CompilerProgramData::from_value(&value).unwrap();
        assert_eq!(decoded, program);
        assert_eq!(decoded.canonical_wire_string(), program.canonical_wire_string());
        assert_eq!(decoded.canonical_sha256(), program.canonical_sha256());
        assert_eq!(program.canonical_sha256().len(), 64);
    }

    #[test]
    fn legacy_sid_and_call_fail_closed_at_transport_boundary() {
        let sid = crate::Sens8::from_packed_byte(0b0000_0101);
        let sid_expr = Expr {
            kind: ExprKind::Sid(sid),
            span: Default::default(),
        };
        assert_eq!(
            CompilerProgramNode::from_expr(&sid_expr).unwrap_err(),
            CompilerProgramDataError::LegacySid8
        );

        let call_expr = Expr {
            kind: ExprKind::Call(sid, Rc::from(Vec::<Expr>::new().into_boxed_slice())),
            span: Default::default(),
        };
        assert_eq!(
            CompilerProgramNode::from_expr(&call_expr).unwrap_err(),
            CompilerProgramDataError::LegacyCall
        );
    }
}
